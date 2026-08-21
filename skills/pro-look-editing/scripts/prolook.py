#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pro-Look-Renderer: eine Config, ein ffmpeg-Lauf, fertiges Reel.

Effekte (alle optional, frei kombinierbar):
  - pip:      Nutzer-Video verkleinert ueber animiertem Hintergrund-Video
  - punchin:  abwechselnder Zoom pro Schnitt-Segment (dynamischer Schnitt-Look)
  - grade:    Kontrast/Saettigung-Look
  - grain:    dezentes Filmkorn
  - captions: animierte ASS-Untertitel einbrennen (aus animated_captions.py)
  - sfx:      Sound-Akzente (z.B. Whoosh) an definierten Zeitpunkten

Aufruf:
  python prolook.py config.json

config.json Beispiel:
{
  "input": "video_geschnitten.mp4",
  "output": "video_prolook.mp4",
  "width": 1080, "height": 1920,
  "pip": {"enabled": true, "background": "bg_loop.mp4",
           "fg_scale": 0.82, "y_pos": 0.30,
           "border_px": 6, "border_color": "white",
           "von": 12.4, "bis": 21.0},
           // von/bis (Sekunden im FERTIGEN Video) sind optional: nur in
           // diesem Fenster wird das Bild klein und der Hintergrund
           // sichtbar, davor und danach laeuft das normale Vollbild.
           // Ohne von/bis gilt das PiP fuer das ganze Video.
  "punchin": {"enabled": true, "zoom": 1.06,
               "cuts": [3.2, 7.8, 12.1]},
  "grade": {"enabled": true, "contrast": 1.06, "saturation": 1.12},
  "grain": {"enabled": true, "strength": 6},
  "captions": "untertitel.ass",
  "sfx": [{"time": 3.2, "file": "whoosh.mp3", "gain": 0.5}]
}
"""
import json
import os
import subprocess
import sys


_HW_CACHE = {}


def hw_encoder():
    """Schnellsten verfuegbaren Hardware-Encoder finden (5-10x schneller als
    CPU). Ergebnis wird gecacht; None = nur CPU verfuegbar."""
    if 'enc' in _HW_CACHE:
        return _HW_CACHE['enc']
    found = None
    have = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'],
                          capture_output=True, text=True).stdout
    # videotoolbox = Mac (jeder Mac seit Jahren), Rest = Windows/Linux.
    # Reihenfolge egal: ffmpeg listet immer nur die real vorhandenen.
    for enc in ('h264_nvenc', 'h264_qsv', 'h264_amf', 'h264_videotoolbox'):
        if enc not in have:
            continue
        test = subprocess.run(
            ['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi',
             '-i', 'testsrc=size=320x240:duration=1:rate=30',
             '-c:v', enc, '-f', 'null', '-'],
            capture_output=True, timeout=90)
        if test.returncode == 0:
            found = enc
            break
    _HW_CACHE['enc'] = found
    return found


def video_encoder(cfg, zwischenstufe=False):
    """Encoder-Argumente: Hardware wenn moeglich, sonst CPU (x264).
    cfg['hardware'] = False erzwingt CPU.
    zwischenstufe=True -> schnellste Einstellungen bei hoher Qualitaet
    (Datei wird ohnehin nochmal verarbeitet, also zaehlt nur Tempo)."""
    crf = 18 if zwischenstufe else int(cfg.get('crf', 20))
    if cfg.get('hardware') is not False:
        enc = hw_encoder()
        if enc == 'h264_nvenc':
            a = ['-c:v', enc, '-preset', 'p1' if zwischenstufe else 'p5',
                 '-rc', 'vbr', '-cq', str(crf), '-b:v', '0']
            if not zwischenstufe:
                a += ['-maxrate', '8M', '-bufsize', '16M']
            return a
        if enc == 'h264_qsv':
            a = ['-c:v', enc, '-global_quality', str(crf),
                 '-preset', 'veryfast' if zwischenstufe else 'medium']
            if not zwischenstufe:      # Dateigroesse zuegeln (Instagram)
                a += ['-maxrate', '8M', '-bufsize', '16M']
            return a
        if enc == 'h264_amf':
            return ['-c:v', enc, '-quality',
                    'speed' if zwischenstufe else 'balanced',
                    '-rc', 'cqp', '-qp_i', str(crf), '-qp_p', str(crf)]
        if enc == 'h264_videotoolbox':
            # Mac: kennt weder crf noch global_quality zuverlaessig ->
            # ueber Bitrate steuern. 12M fuer Zwischenstufen (wird ohnehin
            # nochmal verarbeitet), 8M final = gleiche Deckelung wie oben.
            return ['-c:v', enc,
                    '-b:v', '12M' if zwischenstufe else '8M',
                    '-maxrate', '12M' if zwischenstufe else '8M',
                    '-bufsize', '24M' if zwischenstufe else '16M',
                    '-allow_sw', '1']
    return ['-c:v', 'libx264', '-crf', str(crf), '-preset',
            'veryfast' if zwischenstufe else str(cfg.get('preset', 'medium'))]


def ffprobe_duration(path):
    out = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', path],
        capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)['format']['duration'])


def main():
    with open(sys.argv[1], encoding='utf-8') as f:
        cfg = json.load(f)

    W = cfg.get('width', 1080)
    H = cfg.get('height', 1920)
    dur = ffprobe_duration(cfg['input'])

    inputs = ['-i', cfg['input']]
    n_in = 1
    fc = []          # Filtergraph-Teile
    vlabel = '[0:v]'

    # --- Basis: auf Zielformat bringen -------------------------------------
    fc.append('{}scale={}:{}:force_original_aspect_ratio=decrease,'
              'pad={}:{}:(ow-iw)/2:(oh-ih)/2,setsar=1[base]'
              .format(vlabel, W, H, W, H))
    vlabel = '[base]'

    # --- Picture-in-Picture ------------------------------------------------
    pip = cfg.get('pip') or {}
    if pip.get('enabled'):
        # background_end: 'loop' (Standard) laesst das grosse Video neu
        # starten, wenn es kuerzer ist als das kleine; 'freeze' friert den
        # letzten Frame ein (z. B. Erklaervideo: kleines Video ungeschnitten
        # als Ton-/Zeit-Master, grosses geschnitten).
        freeze = pip.get('background_end', 'loop') == 'freeze'
        if freeze:
            inputs += ['-i', pip['background']]
        else:
            inputs += ['-stream_loop', '-1', '-i', pip['background']]
        bg_idx = n_in
        n_in += 1
        fgw = int(W * float(pip.get('fg_scale', 0.82)) // 2 * 2)
        border = int(pip.get('border_px', 6))
        bcolor = pip.get('border_color', 'white')
        # y_pos = Abstand der OBERKANTE vom oberen Rand (Anteil der Hoehe).
        # x = ZENTRUM des Fensters als Anteil der Breite (wie im Cockpit).
        ypos = float(pip.get('y_pos', 0.30))
        xpos = float(pip.get('x', 0.5))
        tpad = ',tpad=stop_mode=clone:stop=-1' if freeze else ''
        # Zeitfenster in Sekunden des FERTIGEN Videos: "von"/"bis".
        # Ohne Angabe gilt das PiP fuer das ganze Video (bisheriges
        # Verhalten, unveraendert).
        von = pip.get('von', pip.get('from'))
        bis = pip.get('bis', pip.get('to'))
        fenster = von is not None or bis is not None
        quelle = vlabel
        if fenster:
            # Das Original einmal spalten: eine Spur bleibt in voller
            # Groesse. Ohne sie waere ausserhalb des Fensters der
            # Hintergrund zu sehen statt des normalen Bildes.
            fc.append('{}split=2[pipfull][pipsrc]'.format(vlabel))
            quelle = '[pipsrc]'
        fc.append('[{}:v]scale={}:{}:force_original_aspect_ratio=increase,'
                  'crop={}:{},setsar=1{}[bg]'.format(bg_idx, W, H, W, H, tpad))
        fc.append('{}scale={}:-2,pad=iw+{}:ih+{}:{}:{}:{}[fg]'
                  .format(quelle, fgw, border * 2, border * 2,
                          border, border, bcolor))
        fc.append("[bg][fg]overlay='{}*W-w/2':{}*H:shortest=1[pipd]"
                  .format(xpos, ypos))
        if fenster:
            a = float(von) if von is not None else 0.0
            b = float(bis) if bis is not None else 999999.0
            fc.append("[pipfull][pipd]overlay=0:0:"
                      "enable='between(t,{},{})'[pipw]".format(a, b))
            vlabel = '[pipw]'
        else:
            vlabel = '[pipd]'

    # --- Punch-In pro Segment ---------------------------------------------
    pi = cfg.get('punchin') or {}
    if pi.get('enabled') and pi.get('cuts'):
        zoom = float(pi.get('zoom', 1.06))
        bounds = [0.0] + sorted(float(t) for t in pi['cuts']) + [dur]
        segs = []
        for i in range(len(bounds) - 1):
            a, b = bounds[i], min(bounds[i + 1], dur)
            if b - a >= 0.05:
                segs.append((len(segs), a, b, zoom if i % 2 == 1 else 1.0))
        fc.append('{}split={}{}'.format(
            vlabel, len(segs), ''.join('[s{}]'.format(i) for i, _, _, _ in segs)))
        style = pi.get('style', 'static')
        for i, a, b, z in segs:
            if style == 'smooth':
                # kontinuierlicher Zoom von 1.0 auf 'zoom' ueber das Segment
                # (scale kann per-Frame auswerten, crop-Groesse nicht)
                rate = (float(pi.get('zoom', 1.06)) - 1.0) / max(b - a, 0.1)
                zf = (",scale=w='trunc(iw*(1+{r}*t)/2)*2'"
                      ":h='trunc(ih*(1+{r}*t)/2)*2':eval=frame"
                      ',crop={w}:{h}:(iw-{w})/2:(ih-{h})/2'
                      .format(r=rate, w=W, h=H))
            elif z > 1.0:
                zf = (',scale=ceil(iw*{z}/2)*2:ceil(ih*{z}/2)*2,'
                      'crop={w}:{h}:(iw-{w})/2:(ih-{h})/2'
                      .format(z=z, w=W, h=H))
            else:
                zf = ''
            fc.append('[s{}]trim={}:{},setpts=PTS-STARTPTS{},setsar=1[v{}]'
                      .format(i, a, b, zf, i))
            fc.append('[0:a]atrim={}:{},asetpts=PTS-STARTPTS[a{}]'
                      .format(a, b, i))
        tr = cfg.get('transition') or {}
        if tr.get('enabled') and len(segs) > 1:
            # Wisch-/Blenden-Uebergang zwischen den Segmenten (xfade) +
            # optional automatisch gekoppelter Sound an jedem Uebergang.
            ttype = tr.get('type', 'wipeleft')
            td = float(tr.get('duration', 0.3))
            lengths = [b - a for _, a, b, _ in segs]
            vcur, acur = '[v0]', '[a0]'
            cum = lengths[0]
            for k in range(1, len(segs)):
                off = cum - td
                vout = '[vx{}]'.format(k)
                aout = '[ax{}]'.format(k)
                fc.append('{}[v{}]xfade=transition={}:duration={}:offset={:.3f}{}'
                          .format(vcur, k, ttype, td, off, vout))
                fc.append('{}[a{}]acrossfade=d={}{}'
                          .format(acur, k, td, aout))
                if tr.get('sfx_file'):
                    cfg.setdefault('sfx', []).append(
                        {'time': round(off, 3), 'file': tr['sfx_file'],
                         'gain': tr.get('sfx_gain', 0.6)})
                vcur, acur = vout, aout
                cum = cum + lengths[k] - td
            vlabel, alabel = vcur, acur
        else:
            fc.append('{}concat=n={}:v=1:a=1[vseg][aseg]'.format(
                ''.join('[v{}][a{}]'.format(i, i) for i, _, _, _ in segs),
                len(segs)))
            vlabel, alabel = '[vseg]', '[aseg]'
    else:
        alabel = '0:a'

    # --- Zoom-Abschnitte mit Zielpunkt (Cockpit-Zoom, "Zoom aufs Gesicht") -
    # cfg['zooms'] = [{start, end, zoom, x, y, mode}] — x/y = Zielpunkt als
    # Anteil (0-1), mode 'fahrt' (sanft reinziehen) oder 'fest' (harter
    # Punch-In). Wirkt auf das komponierte Bild VOR Captions/Texten.
    zooms = sorted((cfg.get('zooms') or []), key=lambda z: float(z['start']))
    if zooms:
        # WICHTIG: EIN durchgehender zoompan ueber das ganze Video — NIEMALS
        # in Segmente schneiden und wieder zusammensetzen (das verschiebt die
        # Zeitachse: Frames doppeln sich, Bild springt, Untertitel verrutschen).
        # Der z-Ausdruck schaltet zeitabhaengig zwischen den Phasen um.
        # Technik: crop mit eval=frame auf der ZEIT-Variable t (zuverlaessig),
        # danach zurueck auf Zielgroesse skalieren. KEIN zoompan (dessen
        # Frame-Zaehler laeuft nicht synchron zur Zeitachse -> Bildspruenge)
        # und KEIN Segment-Split (verschiebt die Zeitachse).
        # EIN Abschnitt je Zoom: reinfahren (ramp_in) -> halten -> rausfahren
        # (ramp_out). ramp 0 = sofortiger, harter Zoom.
        z_expr, x_expr, y_expr = '1', '0.5', '0.5'
        for z in reversed(zooms):
            s, e = float(z['start']), float(z['end'])
            if e - s < 0.1:
                continue
            zv = float(z.get('zoom', 1.15))
            tx, ty = float(z.get('x', 0.5)), float(z.get('y', 0.5))
            ri = max(0.03, float(z.get('ramp_in', z.get('ramp', 0.6)) or 0.03))
            ro = max(0.03, float(z.get('ramp_out', 0.6) or 0.03))
            ri = min(ri, (e - s) / 2)
            ro = min(ro, (e - s) / 2)
            prog = 'max(0,min(1,min((t-{s})/{ri},({e}-t)/{ro})))'.format(
                s=s, e=e, ri=ri, ro=ro)
            this_z = '(1+({zv}-1)*{p})'.format(zv=zv, p=prog)
            cond = 'between(t,{s},{e})'.format(s=s, e=e)
            z_expr = 'if({c},{a},{b})'.format(c=cond, a=this_z, b=z_expr)
            x_expr = 'if({c},{v},{b})'.format(c=cond, v=tx, b=x_expr)
            y_expr = 'if({c},{v},{b})'.format(c=cond, v=ty, b=y_expr)
        # scale wertet pro Frame aus (eval=frame), crop schneidet daraus das
        # Zielfenster heraus. Die Formel (iw-W)*x ist mathematisch IDENTISCH
        # zur Cockpit-Vorschau (CSS transform-origin) — nachgerechnet:
        # beide zeigen bei y=0.26 und 2x-Zoom den Bereich 0.130-0.630.
        # NICHT auf "Punkt ins Zentrum" umbauen, das weicht ab!
        # ACHTUNG: crop kennt iw/ih nur vom ERSTEN Frame (da ist der Zoom noch
        # 1.0) -> mit (iw-W)*x landet der Ausschnitt immer in der Ecke.
        # Deshalb die Position direkt aus dem Zoomfaktor rechnen.
        # Bedeutung von x/y: der Bildpunkt, der in die MITTE kommt.
        fc.append("{v}scale=w='trunc(iw*({z})/2)*2':h='trunc(ih*({z})/2)*2'"
                  ":eval=frame,crop={w}:{h}"
                  ":'clip({w}*({z})*({x})-{w}/2,0,{w}*(({z})-1))'"
                  ":'clip({h}*({z})*({y})-{h}/2,0,{h}*(({z})-1))'"
                  ',setsar=1[zvc]'
                  .format(v=vlabel, z=z_expr, x=x_expr, y=y_expr, w=W, h=H))
        vlabel = '[zvc]'

    # Finale Dauer (Uebergaenge verkuerzen die Timeline) — frueh berechnen
    _tr = cfg.get('transition') or {}
    _pi = cfg.get('punchin') or {}
    final_dur = dur
    if _tr.get('enabled') and _pi.get('cuts'):
        final_dur = dur - len(_pi['cuts']) * float(_tr.get('duration', 0.3))

    # --- B-Roll-Inserts (Bild wechselt, Ton laeuft weiter) -----------------
    for bi, b in enumerate(cfg.get('broll') or []):
        inputs += ['-i', b['file']]
        bidx = n_in
        n_in += 1
        st = float(b['start'])
        bdur = float(b.get('duration', 2.5))
        fc.append('[{}:v]trim=0:{},scale={}:{}:'
                  'force_original_aspect_ratio=increase,crop={}:{},setsar=1,'
                  'setpts=PTS-STARTPTS+{}/TB[br{}]'
                  .format(bidx, bdur, W, H, W, H, st, bi))
        fc.append("{}[br{}]overlay=0:0:enable='between(t,{},{})'[vbr{}]"
                  .format(vlabel, bi, st, st + bdur, bi))
        vlabel = '[vbr{}]'.format(bi)

    # --- Animierte Overlays ------------------------------------------------
    # Zwei Sorten, unterschieden ueber "alpha":
    #
    #   ohne "alpha"        Green-Screen-Element, wird per Chromakey
    #                       freigestellt (bisheriges Verhalten, unveraendert)
    #
    #   "alpha": true       bringt einen echten Alphakanal mit - kein
    #                       Chromakey, keine Farbsaeume. Quelle darf ein
    #                       Ordner mit PNG-Sequenz sein oder eine Datei.
    #                       "fullframe": true legt die Ebene 1:1 ueber das
    #                       ganze Bild (Motion-Canvas-Effektebenen und
    #                       freigestellte Personen). Ohne "duration" laeuft
    #                       die Ebene so lange, wie sie selbst ist.
    #
    # Die Reihenfolge in der Liste ist die Stapelreihenfolge: ein Effekt vor
    # der freigestellten Person ergibt "Text hinter der Person".
    #
    # ACHTUNG: VP9-WebM traegt seinen Alphakanal nur im Browser - ffmpeg
    # liest ihn NICHT. Hier PNG-Sequenz oder .mov (qtrle/prores4444) nutzen.
    for oi, o in enumerate(cfg.get('overlays') or []):
        datei = o['file']
        alpha = bool(o.get('alpha'))
        st = float(o.get('start', 0))

        if alpha and os.path.isdir(datei):
            # Bildrate muss VOR dem Input stehen, sonst nimmt ffmpeg 25.
            inputs += ['-framerate', str(o.get('fps', 30)),
                       '-i', os.path.join(datei, '%06d.png')]
        else:
            inputs += ['-i', datei]
        oidx = n_in
        n_in += 1

        if alpha:
            hat_dauer = o.get('duration') is not None
            trim = 'trim=0:{},'.format(float(o['duration'])) if hat_dauer else ''
            if o.get('fullframe'):
                fc.append('[{}:v]{}setpts=PTS-STARTPTS+{}/TB[ov{}]'
                          .format(oidx, trim, st, oi))
                ox, oy = '0', '0'
            else:
                ow = int(W * float(o.get('scale', 0.35)) // 2 * 2)
                fc.append('[{}:v]{}setpts=PTS-STARTPTS+{}/TB,scale={}:-2[ov{}]'
                          .format(oidx, trim, st, ow, oi))
                ox = 'W*{}-w/2'.format(float(o.get('x', 0.5)))
                oy = 'H*{}-h/2'.format(float(o.get('y', 0.3)))
            enable = ''
            if hat_dauer:
                enable = ":enable='between(t,{},{})'".format(
                    st, st + float(o['duration']))
            fc.append("{}[ov{}]overlay=x='{}':y='{}':eof_action=pass{}[vov{}]"
                      .format(vlabel, oi, ox, oy, enable, oi))
        else:
            odur = float(o.get('duration', 2.0))
            oscale = float(o.get('scale', 0.35))
            ow = int(W * oscale // 2 * 2)
            chroma = o.get('chroma', '0x00FF00')
            sim = float(o.get('similarity', 0.22))
            blend = float(o.get('blend', 0.08))
            # Position als Anteil der Flaeche (0-1), Element wird zentriert
            ox = 'W*{}-w/2'.format(float(o.get('x', 0.5)))
            oy = 'H*{}-h/2'.format(float(o.get('y', 0.3)))
            fc.append('[{}:v]trim=0:{},setpts=PTS-STARTPTS+{}/TB,scale={}:-2,'
                      'chromakey={}:{}:{},despill=type=green[ov{}]'
                      .format(oidx, odur, st, ow, chroma, sim, blend, oi))
            fc.append("{}[ov{}]overlay=x='{}':y='{}':enable='between(t,{},{})'[vov{}]"
                      .format(vlabel, oi, ox, oy, st, st + odur, oi))
        vlabel = '[vov{}]'.format(oi)

    # --- Look: Grade + Grain ----------------------------------------------
    post = []
    g = cfg.get('grade') or {}
    if g.get('enabled'):
        post.append('eq=contrast={}:saturation={}'.format(
            g.get('contrast', 1.06), g.get('saturation', 1.12)))
    gr = cfg.get('grain') or {}
    if gr.get('enabled'):
        post.append('noise=alls={}:allf=t'.format(int(gr.get('strength', 6))))

    # --- Captions einbrennen ----------------------------------------------
    if cfg.get('captions'):
        # relativer Pfad noetig (Windows-Doppelpunkt im ass-Filter)
        post.append('ass={}'.format(os.path.basename(cfg['captions'])))

    # --- Freie Text-Overlays (Hook/Titel, aus text_overlays.py) ------------
    if cfg.get('text_overlays'):
        post.append('ass={}'.format(os.path.basename(cfg['text_overlays'])))

    if post:
        fc.append('{}{}[vout]'.format(vlabel, ','.join(post)))
        vlabel = '[vout]'

    # --- Fortschrittsbalken (Balken schiebt sich von links herein) ---------
    pb = cfg.get('progressbar') or {}
    if pb.get('enabled'):
        bh = int(pb.get('height', 10))
        fc.append('color=c={}:s={}x{}[pbar]'.format(
            pb.get('color', 'white@0.85'), W, bh))
        fc.append("{}[pbar]overlay=x='-main_w+main_w*t/{:.3f}':"
                  'y=main_h-{}:shortest=1[vpb]'.format(vlabel, final_dur, bh))
        vlabel = '[vpb]'

    def lab(a):
        return a if a.startswith('[') else '[{}]'.format(a)

    # Finale Audiodauer (Uebergaenge verkuerzen die Timeline)
    tr_cfg = cfg.get('transition') or {}
    pi_cfg = cfg.get('punchin') or {}
    final_dur = dur
    if tr_cfg.get('enabled') and pi_cfg.get('cuts'):
        final_dur = dur - len(pi_cfg['cuts']) * float(tr_cfg.get('duration', 0.3))

    # --- Basis-Lautstaerke der input-Tonspur (Cockpit: Lautstaerke-Regler) --
    in_gain = float(cfg.get('audio_gain', 1.0))
    if in_gain != 1.0:
        fc.append('{}volume={}[aing]'.format(lab(alabel), in_gain))
        alabel = '[aing]'

    # --- Ton beider Videos mischen (audio_from: both aus dem Cockpit) ------
    # pip.mix_audio: true -> Ton des pip.background wird zum Ton der
    # input-Datei dazugemischt (Lautstaerke via pip.audio_gain, Standard 1.0)
    if pip.get('enabled') and pip.get('mix_audio'):
        fc.append('[{}:a]volume={}[bga]'.format(
            bg_idx, pip.get('audio_gain', 1.0)))
        fc.append('{}[bga]amix=inputs=2:duration=first:normalize=0[apip]'
                  .format(lab(alabel)))
        alabel = '[apip]'

    # --- Voiceover: zusaetzliche Sprechspur (Cockpit: Audio-Kachel) --------
    # Wird VOR Mastering/Musik gemischt -> Ducking reagiert auch aufs
    # Voiceover. Datei vorher wie den Ton-Master schneiden (siehe SKILL).
    voc = cfg.get('voiceover') or {}
    if voc.get('file'):
        inputs += ['-i', voc['file']]
        vo_idx = n_in
        n_in += 1
        fc.append('[{}:a]volume={}[voa]'.format(vo_idx, voc.get('gain', 1.0)))
        fc.append('{}[voa]amix=inputs=2:duration=first:normalize=0[avoc]'
                  .format(lab(alabel)))
        alabel = '[avoc]'

    # --- Audio-Suite: Stimm-Mastering --------------------------------------
    vmc = cfg.get('voice_master') or {}
    if vmc.get('enabled'):
        fc.append('{}highpass=f=80,'
                  'acompressor=threshold=0.09:ratio=3:attack=5:release=150:'
                  'makeup=2,equalizer=f=3200:t=q:w=1:g=2[vmast]'
                  .format(lab(alabel)))
        alabel = '[vmast]'

    # --- Audio-Suite: Musikbett mit Auto-Ducking ---------------------------
    mu = cfg.get('music') or {}
    if mu.get('enabled'):
        inputs += ['-stream_loop', '-1', '-i', mu['file']]
        midx = n_in
        n_in += 1
        fc.append('[{}:a]atrim=0:{:.3f},asetpts=PTS-STARTPTS,'
                  'afade=t=out:st={:.3f}:d=1.2,volume={}[mus]'
                  .format(midx, final_dur, max(0.0, final_dur - 1.2),
                          mu.get('gain', 0.30)))
        fc.append('{}asplit=2[vc1][vc2]'.format(lab(alabel)))
        # Musik wird automatisch leiser, sobald gesprochen wird
        fc.append('[mus][vc1]sidechaincompress=threshold=0.03:ratio=12:'
                  'attack=20:release=400[mduck]')
        fc.append('[vc2][mduck]amix=inputs=2:duration=first:normalize=0[amus]')
        alabel = '[amus]'

    # --- SFX-Akzente -------------------------------------------------------
    # Je Eintrag: {"time", "file", "gain"} und optional
    #   "trim" — Stille am Dateianfang ueberspringen, damit der Effekt GENAU
    #            bei "time" hoerbar ist (viele Rohdateien haben 1-2 s Vorlauf)
    #   "len"  — hoerbare Laenge begrenzen (sonst tippt eine 19-s-Datei durch)
    #   "fade" — kurze Ausblende am gekuerzten Ende
    sfx = cfg.get('sfx') or []
    if sfx:
        amix_in = ['[{}]'.format(alabel) if not alabel.startswith('[')
                   else alabel]
        for k, s in enumerate(sfx):
            inputs += ['-i', s['file']]
            idx = n_in
            n_in += 1
            delay = int(float(s['time']) * 1000)
            trim = float(s.get('trim') or 0)
            laenge = float(s.get('len') or 0)
            kette = []
            if trim > 0.001 or laenge > 0.001:
                schnitt = 'atrim=start={:.3f}'.format(trim)
                if laenge > 0.001:
                    schnitt += ':end={:.3f}'.format(trim + laenge)
                kette.append(schnitt)
                kette.append('asetpts=PTS-STARTPTS')
            if laenge > 0.001:
                fade = min(float(s.get('fade') or 0), laenge)
                if fade > 0.001:
                    kette.append('afade=t=out:st={:.3f}:d={:.3f}'
                                 .format(max(0.0, laenge - fade), fade))
            kette.append('volume={}'.format(s.get('gain', 0.6)))
            kette.append('adelay={}|{}'.format(delay, delay))
            fc.append('[{}:a]{}[sfx{}]'.format(idx, ','.join(kette), k))
            amix_in.append('[sfx{}]'.format(k))
        fc.append('{}amix=inputs={}:duration=first:normalize=0[aout]'
                  .format(''.join(amix_in), len(amix_in)))
        alabel = '[aout]'

    # --- Audio-Suite: finaler Loudness-Pass (Social-Standard -14 LUFS) -----
    if (cfg.get('loudnorm') or {}).get('enabled'):
        fc.append('{}loudnorm=I=-14:TP=-1.5:LRA=11[afin]'.format(lab(alabel)))
        alabel = '[afin]'

    amap = alabel if alabel.startswith('[') else '{}'.format(alabel)
    cmd = (['ffmpeg', '-y'] + inputs +
           ['-filter_complex', ';'.join(fc),
            '-map', vlabel, '-map', amap] +
           video_encoder(cfg) +
           ['-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart', cfg['output']])
    print('FFMPEG:', ' '.join(cmd))
    subprocess.run(cmd, check=True,
                   cwd=os.path.dirname(os.path.abspath(cfg['output'])) or '.')
    print('OK:', cfg['output'])


if __name__ == '__main__':
    main()
