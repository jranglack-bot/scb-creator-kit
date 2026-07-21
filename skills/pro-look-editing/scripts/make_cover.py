#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hook-Cover: Standbild aus dem Video + grosser Hook-Text -> JPG.

Das Cover entscheidet im Grid ueber den Klick. Nutzt denselben Stil wie
die Captions (Untertitel-Profil), Text sitzt gross im oberen Drittel
(unterhalb der Instagram-Tabuzone).

Aufruf:
  python make_cover.py video.mp4 cover.jpg --time 1.5 --text "DEIN HOOK|IN ZWEI ZEILEN"
    [--font "Segoe UI"] [--size 96] [--primary FFFFFF] [--highlight FFD400]
    [--box]

"|" im Text = Zeilenumbruch. Das ERSTE Wort nach jedem "*" wird in der
Highlight-Farbe gesetzt (z.B. "So sparst du *TOKENS").
"""
import argparse
import os
import subprocess
import tempfile


def ass_color(rgbhex):
    rgbhex = rgbhex.lstrip('#')
    r, g, b = rgbhex[0:2], rgbhex[2:4], rgbhex[4:6]
    return '&H00{}{}{}&'.format(b, g, r).upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('output')
    ap.add_argument('--time', type=float, default=1.0)
    ap.add_argument('--text', required=True)
    ap.add_argument('--font', default='Segoe UI')
    ap.add_argument('--size', type=int, default=96)
    ap.add_argument('--primary', default='FFFFFF')
    ap.add_argument('--highlight', default='FFD400')
    ap.add_argument('--box', action='store_true')
    args = ap.parse_args()

    hi = ass_color(args.highlight)
    prim = ass_color(args.primary)

    text = args.text.replace('|', '\\N')
    # "*WORT" -> Wort in Highlight-Farbe
    parts = text.split('*')
    if len(parts) > 1:
        out = [parts[0]]
        for p in parts[1:]:
            sp = p.split(' ', 1)
            out.append('{{\\1c{}}}{}{{\\1c{}}}'.format(hi, sp[0], prim))
            if len(sp) > 1:
                out.append(' ' + sp[1])
        text = ''.join(out)

    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,{font},{size},{prim},{prim},&H00000000,&H96000000,-1,0,0,0,100,100,0,0,{bs},{outline},3,8,60,60,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:10.00,Hook,,0,0,0,,{text}
""".format(font=args.font, size=args.size, prim=prim,
           bs=3 if args.box else 1, outline=max(5, args.size // 12),
           text=text)

    workdir = os.path.dirname(os.path.abspath(args.output)) or '.'
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.ass', dir=workdir,
                                      delete=False, encoding='utf-8-sig')
    tmp.write(ass)
    tmp.close()
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-ss', str(args.time), '-i',
             os.path.abspath(args.video),
             '-frames:v', '1',
             '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,'
                    'crop=1080:1920,ass={}'.format(os.path.basename(tmp.name)),
             '-q:v', '2', os.path.basename(args.output)],
            check=True, cwd=workdir,
            capture_output=True)
    finally:
        os.unlink(tmp.name)
    print('OK:', args.output)


if __name__ == '__main__':
    main()
