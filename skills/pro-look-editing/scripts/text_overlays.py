#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt eine .ass-Datei aus den freien Text-Overlays des Cockpits
(projekt.json -> "texts"): Hook/Titel fuer B-Roll-Reels mit Position,
Zeilen-Hintergrund und Einflug-Animationen.

Aufruf:
  python text_overlays.py <projekt.json> <output.ass>

Einbrennen: prolook-Config  "text_overlays": "<output.ass>"
Animations-Mapping (Cockpit "anim"): fade | left | right | up | pop | none
"""
import json
import sys


def bgr(rgbhex):
    h = str(rgbhex).lstrip('#')
    return '{}{}{}'.format(h[4:6], h[2:4], h[0:2]).upper()


def fmt_time(sec):
    sec = max(0.0, float(sec))
    return '{}:{:02d}:{:05.2f}'.format(int(sec // 3600),
                                       int(sec % 3600 // 60), sec % 60)


def main():
    pj = json.load(open(sys.argv[1], encoding='utf-8-sig'))
    texts = pj.get('texts') or []
    W, H = 1080, 1920
    styles, events = [], []
    for i, tx in enumerate(texts):
        box = tx.get('box', True)
        block = tx.get('box_style') == 'block'
        alpha = max(0, min(255, int(round(
            (1 - float(tx.get('box_alpha', 0.55))) * 255))))
        boxcol = '&H{:02X}{}'.format(alpha, bgr(tx.get('box_color', '000000')))
        # libass (empirisch verifiziert):
        #   BorderStyle 3 (Box pro Zeile)   -> Box = OutlineColour
        #   BorderStyle 4 (EIN Viereck um den ganzen Text) -> Box = BackColour,
        #                                      Textkontur = OutlineColour
        styles.append(
            'Style: T{i},{font},{size},&H00{col},&H00{col},{outcol},{back},'
            '{bold},0,0,0,100,100,0,0,{bs},{out},{shadow},5,20,20,20,1'.format(
                i=i, font=tx.get('font', 'Segoe UI'),
                size=int(tx.get('size', 72)),
                col=bgr(tx.get('color', 'FFFFFF')),
                outcol='&H00000000' if (not box or block) else boxcol,
                back=boxcol if (box and block) else '&H96000000',
                bold=0 if tx.get('bold') is False else -1,
                bs=(4 if block else 3) if box else 1,
                out=3 if box else 5,
                shadow=0 if box else 2))
        x = float(tx.get('x', 0.5)) * W
        y = float(tx.get('y', 0.3)) * H
        anim = tx.get('anim', 'fade')
        if anim in ('left', 'right', 'up'):
            dx = -260 if anim == 'left' else 260 if anim == 'right' else 0
            dy = 220 if anim == 'up' else 0
            pos = ('\\move({:.0f},{:.0f},{:.0f},{:.0f},0,400)\\fad(120,200)'
                   .format(x + dx, y + dy, x, y))
        elif anim == 'pop':
            pos = ('\\pos({:.0f},{:.0f})\\fscx40\\fscy40'
                   '\\t(0,280,\\fscx100\\fscy100)\\fad(80,200)'.format(x, y))
        elif anim == 'none':
            pos = '\\pos({:.0f},{:.0f})'.format(x, y)
        else:
            pos = '\\pos({:.0f},{:.0f})\\fad(300,250)'.format(x, y)
        # 'lines' = vom Cockpit vermessene Zeilen (Text-Breiten-Flaeche);
        # Fallback: Text mit manuellen Umbruechen
        raw = ('\n'.join(str(l) for l in tx['lines']) if tx.get('lines')
               else str(tx.get('text', '')))
        text = raw.replace('{', '(').replace('}', ')').replace('\n', '\\N')
        events.append('Dialogue: 1,{},{},T{},,0,0,0,,{{\\an5{}}}{}'.format(
            fmt_time(tx.get('start', 0)), fmt_time(tx.get('end', 0)),
            i, pos, text))

    header = (
        '[Script Info]\nScriptType: v4.00+\nPlayResX: {}\nPlayResY: {}\n'
        'WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n'
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, '
        'OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, '
        'ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, '
        'Alignment, MarginL, MarginR, MarginV, Encoding\n'.format(W, H)
        + '\n'.join(styles)
        + '\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, '
          'MarginR, MarginV, Effect, Text\n')
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        f.write(header + '\n'.join(events) + '\n')
    print('OK:', len(texts), 'Text-Overlays ->', sys.argv[2])


if __name__ == '__main__':
    main()
