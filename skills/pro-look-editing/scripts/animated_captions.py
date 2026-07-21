#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Animierte Wort-fuer-Wort-Untertitel (Pop + Highlight) als .ass-Datei.

Liest ein Transkript-JSON (ElevenLabs/Whisper-Format: words[] mit
start/end/text) und erzeugt deterministisch eine ASS-Datei im
CapCut-Stil: 2-3-Wort-Gruppen, Pop-Animation beim Erscheinen,
farbiges Highlight auf dem gerade gesprochenen Wort, nur waehrend
Sprache sichtbar. Safe-Zone-Werte fuer Reel und Story eingebaut.

Aufruf:
  python animated_captions.py transkript.json out.ass --mode reel
    [--font "Segoe UI"] [--size 0] [--highlight FFD400] [--group 3]
    [--playresx 1080] [--playresy 1920]

--size 0 = Standardgroesse des Modus (Reel 64 / Story 92).
"""
import json
import argparse


def ass_color(rgbhex):
    """'FFD400' (RGB) -> ASS-Farbcode &H00BGR& (BGR gedreht)."""
    rgbhex = rgbhex.lstrip('#')
    r, g, b = rgbhex[0:2], rgbhex[2:4], rgbhex[4:6]
    return '&H00{}{}{}&'.format(b, g, r).upper()


def fmt_time(sec):
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec - h * 3600 - m * 60
    return '{}:{:02d}:{:05.2f}'.format(h, m, s)


MODES = {
    # Safe-Zone-geprueft: Reel = unteres Drittel, rechte Buttons frei;
    # Story = gross, unter dem Kinn (Brusthoehe).
    'reel':  dict(size=64, marginv=460, marginl=55, marginr=165),
    'story': dict(size=92, marginv=730, marginl=55, marginr=55),
}

MAX_GAP = 0.6      # Sekunden: groessere Luecke beendet die Wortgruppe
POP_MS = 90        # Dauer der Pop-Animation in Millisekunden


def build_cues(words, group_size):
    """Gruppiert Woerter zu Cues (max. group_size, Bruch bei Sprechpausen)."""
    cues, current = [], []
    for w in words:
        if current and (len(current) >= group_size
                        or w['start'] - current[-1]['end'] > MAX_GAP):
            cues.append(current)
            current = []
        current.append(w)
    if current:
        cues.append(current)
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('transcript')
    ap.add_argument('output')
    ap.add_argument('--mode', choices=('reel', 'story'), default='reel')
    ap.add_argument('--font', default='Segoe UI')
    ap.add_argument('--size', type=int, default=0)
    ap.add_argument('--primary', default='FFFFFF',
                    help='Textfarbe als RGB-Hex')
    ap.add_argument('--highlight', default='FFD400')
    ap.add_argument('--outline', type=int, default=0,
                    help='Konturstaerke in px (0 = automatisch)')
    ap.add_argument('--box', action='store_true',
                    help='halbtransparente Box hinter dem Text')
    ap.add_argument('--group', type=int, default=3)
    ap.add_argument('--playresx', type=int, default=1080)
    ap.add_argument('--playresy', type=int, default=1920)
    args = ap.parse_args()

    mode = MODES[args.mode]
    size = args.size or mode['size']
    hi = ass_color(args.highlight)
    white = ass_color(args.primary)

    with open(args.transcript, encoding='utf-8') as f:
        data = json.load(f)
    words = [w for w in data.get('words', []) if w.get('type', 'word') == 'word'
             and str(w.get('text', '')).strip()]
    if not words:
        raise SystemExit('Keine Woerter im Transkript gefunden.')

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: {px}
PlayResY: {py}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},{primary},{primary},&H00000000,&H96000000,-1,0,0,0,100,100,0,0,{borderstyle},{outline},2,2,{ml},{mr},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(px=args.playresx, py=args.playresy, font=args.font, size=size,
           primary=white,
           borderstyle=3 if args.box else 1,
           outline=args.outline or max(4, size // 10), ml=mode['marginl'],
           mr=mode['marginr'], mv=mode['marginv'])

    lines = [header]
    for cue in build_cues(words, args.group):
        cue_end = cue[-1]['end']
        for k, w in enumerate(cue):
            start = w['start']
            end = cue[k + 1]['start'] if k + 1 < len(cue) else cue_end
            if end - start < 0.02:
                end = start + 0.02
            parts = []
            for j, cw in enumerate(cue):
                txt = str(cw['text']).strip()
                if j == k:
                    parts.append('{{\\1c{}}}{}{{\\1c{}}}'.format(hi, txt, white))
                else:
                    parts.append(txt)
            text = ' '.join(parts)
            # Pop-Animation nur beim ersten Einblenden der Gruppe
            if k == 0:
                text = ('{{\\fscx118\\fscy118\\t(0,{},\\fscx100\\fscy100)}}'
                        .format(POP_MS)) + text
            lines.append('Dialogue: 0,{},{},Cap,,0,0,0,,{}'.format(
                fmt_time(start), fmt_time(end), text))

    with open(args.output, 'w', encoding='utf-8-sig') as f:
        f.write('\n'.join(lines) + '\n')
    print('OK: {} Woerter, ASS geschrieben: {}'.format(len(words), args.output))


if __name__ == '__main__':
    main()
