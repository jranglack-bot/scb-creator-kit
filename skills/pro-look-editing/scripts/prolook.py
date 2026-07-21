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
           "border_px": 6, "border_color": "white"},
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
        inputs += ['-stream_loop', '-1', '-i', pip['background']]
        bg_idx = n_in
        n_in += 1
        fgw = int(W * float(pip.get('fg_scale', 0.82)) // 2 * 2)
        border = int(pip.get('border_px', 6))
        bcolor = pip.get('border_color', 'white')
        ypos = float(pip.get('y_pos', 0.30))
        fc.append('[{}:v]scale={}:{}:force_original_aspect_ratio=increase,'
                  'crop={}:{},setsar=1[bg]'.format(bg_idx, W, H, W, H))
        fc.append('{}scale={}:-2,pad=iw+{}:ih+{}:{}:{}:{}[fg]'
                  .format(vlabel, fgw, border * 2, border * 2,
                          border, border, bcolor))
        # y_pos = Abstand der OBERKANTE des Fensters vom oberen Rand
        # (Anteil der Hoehe). 0.06 = knapp unter der Instagram-Tabuzone.
        fc.append('[bg][fg]overlay=(W-w)/2:{}*H:shortest=1[pipd]'
                  .format(ypos))
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
        for i, a, b, z in segs:
            zf = (',scale=ceil(iw*{z}/2)*2:ceil(ih*{z}/2)*2,'
                  'crop={w}:{h}:(iw-{w})/2:(ih-{h})/2'
                  .format(z=z, w=W, h=H)) if z > 1.0 else ''
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

    if post:
        fc.append('{}{}[vout]'.format(vlabel, ','.join(post)))
        vlabel = '[vout]'

    def lab(a):
        return a if a.startswith('[') else '[{}]'.format(a)

    # Finale Audiodauer (Uebergaenge verkuerzen die Timeline)
    tr_cfg = cfg.get('transition') or {}
    pi_cfg = cfg.get('punchin') or {}
    final_dur = dur
    if tr_cfg.get('enabled') and pi_cfg.get('cuts'):
        final_dur = dur - len(pi_cfg['cuts']) * float(tr_cfg.get('duration', 0.3))

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
    sfx = cfg.get('sfx') or []
    if sfx:
        amix_in = ['[{}]'.format(alabel) if not alabel.startswith('[')
                   else alabel]
        for k, s in enumerate(sfx):
            inputs += ['-i', s['file']]
            idx = n_in
            n_in += 1
            delay = int(float(s['time']) * 1000)
            fc.append('[{}:a]volume={},adelay={}|{}[sfx{}]'
                      .format(idx, s.get('gain', 0.6), delay, delay, k))
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
            '-map', vlabel, '-map', amap,
            '-c:v', 'libx264', '-crf', '20', '-preset', 'medium',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart', cfg['output']])
    print('FFMPEG:', ' '.join(cmd))
    subprocess.run(cmd, check=True,
                   cwd=os.path.dirname(os.path.abspath(cfg['output'])) or '.')
    print('OK:', cfg['output'])


if __name__ == '__main__':
    main()
