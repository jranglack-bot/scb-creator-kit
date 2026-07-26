#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ein-Befehl-Render: baut das fertige Reel KOMPLETT aus der projekt.json.

Aufruf:
  python render_projekt.py <projekt.json>
oder Doppelklick auf video_rendern.bat im Projektordner (legt build_editor an).

Macht alles selbst: Schnittlisten pro Spur, Dateien schneiden,
Lautstaerke-Abschnitte einrechnen, Musik/Voiceover vorbereiten,
Untertitel- und Text-ASS erzeugen, prolook-Config bauen, rendern,
QC-Kontaktbogen (qc_final.png) ziehen.

Qualitaet steuern (optional, in projekt.json):
  "render": {"crf": 18, "preset": "slow", "output": "mein_reel.mp4"}
  (crf: kleiner = besser/groesser, Standard 20)
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRO = os.path.join(HERE, '..', '..', 'pro-look-editing', 'scripts')
AC = os.path.join(PRO, 'animated_captions.py')
TO = os.path.join(PRO, 'text_overlays.py')
PL = os.path.join(PRO, 'prolook.py')
sys.path.insert(0, PRO)
try:
    from prolook import video_encoder   # Hardware-Encoder (5-10x schneller)
except Exception:
    def video_encoder(cfg):
        return ['-c:v', 'libx264', '-crf', '20', '-preset', 'medium']


def run(cmd):
    subprocess.run(cmd, check=True)


def ffdur(path):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def has_video(path):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v', '-show_entries',
         'stream=codec_type', '-of', 'csv=p=0', path],
        capture_output=True, text=True).stdout.strip()
    return bool(out)


def active_cuts(pj, tracks):
    default = pj.get('cuts_apply') or 'both'
    cs = [c for c in (pj.get('cuts') or [])
          if c.get('active', True) and (c.get('track') or default) in tracks]
    return sorted((float(c['start']), float(c['end'])) for c in cs)


def to_source_cuts(lane_cuts):
    """Schnitte sind bereits QUELLzeit (so auf der Timeline gezogen) —
    unveraendert zurueckgeben. KEINE Umrechnung."""
    return list(lane_cuts)


def shift(t, cuts):
    """Quell-Zeit -> Zeit nach Entfernen der Schnitte."""
    d = 0.0
    for s, e in cuts:
        if t > s:
            d += min(e, t) - s
    return t - d


def vol_expr(regions, base):
    expr = str(base)
    for s, e, g in reversed(sorted(regions)):
        expr = 'if(between(t,{},{}),{},{})'.format(s, e, g, expr)
    return expr


def prep(src, out, cuts, regions, base=1.0):
    """Lautstaerke (Quellzeiten) einrechnen + Schnitte entfernen."""
    if not cuts and not regions:
        return src
    af, vf = [], None
    if regions:
        af.append("volume='{}':eval=frame".format(vol_expr(regions, base)))
    if cuts:
        sel = '+'.join('between(t,{},{})'.format(s, e) for s, e in cuts)
        vf = "select='not({0})',setpts=N/FRAME_RATE/TB".format(sel)
        af.append("aselect='not({0})',asetpts=N/SR/TB".format(sel))
    cmd = ['ffmpeg', '-y', '-v', 'error', '-i', src]
    if has_video(src):
        if vf:
            cmd += ['-vf', vf]
        if af:
            cmd += ['-af', ','.join(af)]
        cmd += (video_encoder({}, zwischenstufe=True)
                + ['-c:a', 'aac', '-b:a', '192k', out])
    else:
        out = os.path.splitext(out)[0] + '.m4a'
        if af:
            cmd += ['-af', ','.join(af)]
        cmd += ['-vn', '-c:a', 'aac', '-b:a', '192k', out]
    run(cmd)
    return out


def regions_for(pj, track):
    return [(float(r['start']), float(r['end']), float(r['gain']))
            for r in (pj.get('volumes') or []) if r.get('track') == track]


def main():
    pj_path = os.path.abspath(sys.argv[1])
    projdir = os.path.dirname(pj_path)
    os.chdir(projdir)
    pj = json.load(open(pj_path, encoding='utf-8-sig'))
    render = pj.get('render') or {}
    out_name = render.get('output') or (
        (os.path.basename(projdir) or 'Reel') + '_final.mp4')
    gains = pj.get('gains') or {'main': 1.0}
    videos = pj.get('videos') or ([pj['video']] if pj.get('video') else [])
    videos = [v for v in videos if v]

    # --- Videos zusammenfuegen (mehrere Clips nacheinander) ----------------
    if len(videos) > 1:
        # SCHNELLWEG: Haben alle Clips dieselben Parameter, koennen sie ohne
        # Neuberechnung aneinandergehaengt werden (Sekunden statt Minuten).
        with open('r_concat.txt', 'w', encoding='utf-8') as f:
            for v in videos:
                f.write("file '{}'\n".format(v))
        schnell = subprocess.run(
            ['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
             '-i', 'r_concat.txt', '-c', 'copy', 'r_source.mp4'],
            capture_output=True)
        if schnell.returncode != 0 or not os.path.exists('r_source.mp4'):
            parts = []
            for i, v in enumerate(videos):
                p = 'r_clip{}.mp4'.format(i)
                run(['ffmpeg', '-y', '-v', 'error', '-i', v, '-vf',
                     'scale=1080:1920:force_original_aspect_ratio=decrease,'
                     'pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1', '-r', '30']
                    + video_encoder({}, zwischenstufe=True)
                    + ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', p])
                parts.append(p)
            with open('r_concat.txt', 'w', encoding='utf-8') as f:
                for p in parts:
                    f.write("file '{}'\n".format(p))
            run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
                 '-i', 'r_concat.txt', '-c', 'copy', 'r_source.mp4'])
        source = 'r_source.mp4'
    else:
        source = videos[0]

    # --- Bildstabilisierung (optional: "stabilisieren": true) --------------
    # 2-Pass vidstab; Ergebnis wird gecacht (nur neu bei geaenderter Quelle).
    stab = pj.get('stabilisieren')
    if stab:
        opt = stab if isinstance(stab, dict) else {}
        out_st = 'r_stabil.mp4'
        trf = 'r_transforms.trf'
        fresh = (os.path.exists(out_st) and os.path.exists(trf)
                 and os.path.getmtime(out_st) >= os.path.getmtime(source))
        if not fresh:
            run(['ffmpeg', '-y', '-v', 'error', '-i', source, '-vf',
                 'vidstabdetect=shakiness={}:accuracy=15:result={}'.format(
                     int(opt.get('staerke', 10)), trf), '-f', 'null', '-'])
            run(['ffmpeg', '-y', '-v', 'error', '-i', source, '-vf',
                 'vidstabtransform=input={}:smoothing={}:optzoom=0:zoom={}'
                 ':interpol=bicubic,unsharp=5:5:0.6:3:3:0.3'.format(
                     trf, int(opt.get('glaettung', 60)),
                     int(opt.get('randbeschnitt', 6)))]
                + video_encoder({}, zwischenstufe=True)
                + ['-c:a', 'copy', out_st])
        source = out_st

    # --- Schnitte (Quellzeit) + Lautstaerke-Abschnitte einrechnen ----------
    g_main = float(gains.get('main', 1))
    r_main = regions_for(pj, 'main')
    if r_main:
        g_bake_main, g_main = g_main, 1.0
    main_lane = active_cuts(pj, ('main', 'both'))
    input_file = prep(source, 'r_main.mp4', to_source_cuts(main_lane),
                      r_main, g_bake_main if r_main else 1.0)
    master_lane = main_lane
    master_cuts = to_source_cuts(master_lane)

    cfg = {'input': input_file, 'output': out_name,
           'width': 1080, 'height': 1920}
    for k in ('crf', 'preset'):
        if render.get(k):
            cfg[k] = render[k]
    if abs(g_main - 1.0) > 0.001:
        cfg['audio_gain'] = g_main

    # --- Untertitel (Wortzeiten folgen dem Zeit-Master) --------------------
    cap = pj.get('captions') or {}
    if cap.get('enabled') and pj.get('words'):
        # ASR-Zeitstempel sind an Pausen oft ungenau (ein Wort "beginnt"
        # laut Transkript oft schon in der vorangehenden Stille). Ein Wort
        # nur dann KOMPLETT verwerfen, wenn auch sein ENDE im Schnitt liegt
        # — liegt nur der (unzuverlaessige) Start im Schnitt, das Ende aber
        # dahinter, gilt das Wort als erhalten (Start wird auf Schnittende
        # geklemmt), sonst verschwaende es faelschlich aus den Untertiteln.
        words = []
        for w in pj['words']:
            ws, we = float(w['start']), float(w['end'])
            voll_im_schnitt = any(s <= ws and we <= e for s, e in master_cuts)
            if voll_im_schnitt:
                continue
            for s, e in master_cuts:
                if s <= ws < e:
                    ws = e
                    break
            if ws >= we:
                continue
            words.append({'text': w['text'], 'type': 'word',
                          'start': round(shift(ws, master_cuts), 3),
                          'end': round(shift(we, master_cuts), 3)})
        with open('r_words.json', 'w', encoding='utf-8') as f:
            json.dump({'words': words}, f, ensure_ascii=False)
        cmd = [sys.executable, AC, 'r_words.json', 'untertitel.ass',
               '--font', cap.get('font', 'Segoe UI'),
               '--size', str(int(cap.get('size', 64))),
               '--primary', str(cap.get('primary', 'FFFFFF')).lstrip('#'),
               '--highlight',
               (str(cap.get('primary', 'FFFFFF'))
                if cap.get('highlight_on') is False
                else str(cap.get('highlight', 'FFD400'))).lstrip('#'),
               '--group', str(int(cap.get('group', 3)))]
        if cap.get('bold') is False:
            cmd.append('--no-bold')
        if cap.get('box'):
            cmd += ['--box',
                    '--box-color', str(cap.get('box_color', '000000')).lstrip('#'),
                    '--box-alpha', str(cap.get('box_alpha', 0.55)),
                    '--box-style', cap.get('box_style', 'line')]
        run(cmd)
        cfg['captions'] = 'untertitel.ass'

    # --- Freie Text-Overlays ----------------------------------------------
    texts = []
    for t in (pj.get('texts') or []):
        s = shift(float(t['start']), master_lane)
        e = shift(float(t['end']), master_lane)
        if e - s >= 0.05:
            texts.append(dict(t, start=round(s, 2), end=round(e, 2)))
    if texts:
        with open('r_texts.json', 'w', encoding='utf-8') as f:
            json.dump({'texts': texts}, f, ensure_ascii=False)
        run([sys.executable, TO, 'r_texts.json', 'texte.ass'])
        cfg['text_overlays'] = 'texte.ass'

    # --- Zoom-Abschnitte (Zielpunkt-Zoom aus dem Cockpit) ------------------
    zooms = []
    for z in (pj.get('zooms') or []):
        s = shift(float(z['start']), master_lane)
        e = shift(float(z['end']), master_lane)
        if e - s >= 0.1:
            zooms.append(dict(z, start=round(s, 2), end=round(e, 2)))
    if zooms:
        cfg['zooms'] = zooms

    # --- Musik: Startpunkt + Musik-Schnitte + Abschnitte -------------------
    mus = pj.get('music') or {}
    if mus.get('file') and mus.get('enabled', True):
        off = float(mus.get('offset') or 0)
        song_cuts, vorher = [], 0.0
        for s, e in active_cuts(pj, ('music',)):
            s, e = shift(s, master_lane), shift(e, master_lane)
            if e - s < 0.05:
                continue
            song_cuts.append((off + s + vorher, off + e + vorher))
            vorher += e - s
        if off > 0.05:
            song_cuts = [(0.0, off)] + song_cuts
        song = prep(mus['file'], 'r_musik.m4a', song_cuts, [])
        r_mus = regions_for(pj, 'music')     # Zeiten = fertige Musikdatei
        if r_mus:
            song = prep(song, 'r_musik_vol.m4a', [], r_mus, 1.0)
        cfg['music'] = {'enabled': True, 'file': song,
                        'gain': float(mus.get('gain', 0.3))}

    # --- Voiceover: klebt am Zeit-Master, voice-Schnitte = stumm -----------
    vo = pj.get('voiceover') or {}
    if vo.get('file'):
        mutes = [(s, e, 0.0) for s, e in active_cuts(pj, ('voice',))]
        vo_file = prep(vo['file'], 'r_voice.m4a', master_cuts,
                       regions_for(pj, 'voice') + mutes)
        cfg['voiceover'] = {'file': vo_file,
                           'gain': float(vo.get('gain', 1.0))}

    # --- Effekt-Durchreiche: prolook-Effekte direkt aus der projekt.json ---
    # z.B. "effekte": {"punchin": {"enabled": true, "zoom": 1.05,
    #        "cuts": [10, 15], "style": "smooth"}}
    # Zeitangaben beziehen sich auf das FERTIGE Video (Output-Zeit).
    for k, v in (pj.get('effekte') or pj.get('effects') or {}).items():
        if k in ('punchin', 'grade', 'grain', 'transition', 'progressbar',
                 'broll', 'overlays', 'sfx', 'voice_master', 'loudnorm'):
            cfg[k] = v

    with open('render_config.json', 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=1)
    run([sys.executable, PL, 'render_config.json'])

    dur = ffdur(out_name)
    t = [dur * 0.15, dur * 0.5, dur * 0.85]
    run(['ffmpeg', '-y', '-v', 'error',
         '-ss', str(t[0]), '-i', out_name, '-ss', str(t[1]), '-i', out_name,
         '-ss', str(t[2]), '-i', out_name, '-filter_complex',
         '[0:v]scale=360:-1[a];[1:v]scale=360:-1[b];[2:v]scale=360:-1[c];'
         '[a][b][c]hstack=3', '-frames:v', '1', 'qc_final.png'])
    print('FERTIG: {} | {:.1f}s | QC: qc_final.png'.format(out_name, dur))


if __name__ == '__main__':
    main()
