#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt eine .ass-Datei aus den freien Text-Overlays des Cockpits
(projekt.json -> "texts"): Hook/Titel fuer B-Roll-Reels mit Position,
Zeilen-Hintergrund und Einflug-Animationen.

Aufruf:
  python text_overlays.py <projekt.json> <output.ass>

Einbrennen: prolook-Config  "text_overlays": "<output.ass>"
Animations-Mapping (Cockpit "anim"): fade | left | right | up | pop | none
Je Text ausserdem: "italic": true (kursiv) und "schatten": "weich" (dunkle,
stark verwischte Wolke nach unten links statt harter Kontur, Zweifachschrift).
Die Kit-Schriften (Poppins Black, Playfair Display) findet ffmpeg ueber den
Ordner schriften/ im Projekt: render_projekt.py legt ihn an, prolook.py
reicht ihn als fontsdir weiter.
"""
import json
import os
import platform
import struct
import sys


def standard_schrift():
    """Schrift, die es auf dem laufenden System wirklich gibt — 'Segoe UI'
    existiert auf einem Mac nicht; ffmpeg wuerde beim Einbrennen still
    irgendeine Ersatzschrift nehmen."""
    s = platform.system()
    if s == 'Windows':
        return 'Segoe UI'
    if s == 'Darwin':
        return 'Helvetica Neue'
    return 'DejaVu Sans'



# Weicher Schatten: Anteile der Schriftgroesse, GLEICH wie TX_SCHATTEN im
# Cockpit (editor.html). CSS-Radius r entspricht libass \blur r/2.
SCHATTEN = {'dx': -0.06, 'dy': 0.10, 'r': 0.40, 'a': 0.65, 'a_farbig': 0.45}

KIT_SCHRIFTEN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', '..', 'video-projekt', 'schriften')
_metrik = {}


def kit_metrik(font):
    """(Groessenfaktor, Hoehenversatz in em) fuer eine Kit-Schrift, sonst None.

    libass setzt die Schriftgroesse auf winAscent+winDescent, der Browser auf
    das Geviert (em). Bei Poppins Black ist das Faktor 0,57, bei Playfair 0,71
    (gemessen 13.10.2026: Hook im Video halb so gross wie im Cockpit).
    Ausserdem liegt die Grundlinie bei \\an5 anders als im Cockpit (CSS,
    hhea-Werte): Versatz = ((A-D) - (WA-WD)) / 2 in em."""
    if font in _metrik:
        return _metrik[font]
    _metrik[font] = None
    if not os.path.isdir(KIT_SCHRIFTEN):
        return None
    for d in os.listdir(KIT_SCHRIFTEN):
        if not d.lower().endswith(('.ttf', '.otf')):
            continue
        try:
            b = open(os.path.join(KIT_SCHRIFTEN, d), 'rb').read()
            t = {}
            for i in range(struct.unpack('>H', b[4:6])[0]):
                tag, _, off, _ = struct.unpack('>4sIII', b[12 + 16 * i:28 + 16 * i])
                t[tag] = off
            n = t[b'name']
            _, anz, so = struct.unpack('>HHH', b[n:n + 6])
            fam = None
            for i in range(anz):
                pid, _, lid, nid, ln, o = struct.unpack(
                    '>6H', b[n + 6 + 12 * i:n + 18 + 12 * i])
                if pid == 3 and lid == 0x409 and nid == 1:
                    fam = b[n + so + o:n + so + o + ln].decode('utf-16-be')
            if fam != font:
                continue
            upm = struct.unpack('>H', b[t[b'head'] + 18:t[b'head'] + 20])[0]
            a, de = struct.unpack('>hh', b[t[b'hhea'] + 4:t[b'hhea'] + 8])
            wa, wd = struct.unpack('>HH', b[t[b'OS/2'] + 74:t[b'OS/2'] + 78])
            _metrik[font] = (upm / float(wa + wd),
                             ((a + de) - (wa - wd)) / 2.0 / upm)
        except Exception:
            pass
    return _metrik[font]


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
    # Ausgabeformat: kommt aus der Aufrufdatei, sonst Reel-Standard. Ohne das
    # wuerde libass die 1080x1920-Flaeche auf ein anderes Format ziehen und
    # die Schrift verzerren (z. B. bei Querformat-Projekten).
    W = int(pj.get('width') or 1080)
    H = int(pj.get('height') or 1920)
    styles, events = [], []
    for i, tx in enumerate(texts):
        box = tx.get('box', True)
        # "schatten": "weich" = Zweifachschrift: keine harte Kontur, dafuer
        # eine dunkle, verwischte Wolke als eigene Zeile darunter (Ebene 0)
        weich = tx.get('schatten') == 'weich' and not box
        m = kit_metrik(tx.get('font'))
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
            '{bold},{ital},0,0,100,100,0,0,{bs},{out},{shadow},5,20,20,20,1'.format(
                i=i, font=tx.get('font', standard_schrift()),
                size=int(round(float(tx.get('size', 72)) / m[0])) if m
                else int(tx.get('size', 72)),
                col=bgr(tx.get('color', 'FFFFFF')),
                outcol='&H00000000' if (not box or block) else boxcol,
                back=boxcol if (box and block) else '&H96000000',
                bold=0 if tx.get('bold') is False else -1,
                ital=-1 if tx.get('italic') else 0,
                bs=(4 if block else 3) if box else 1,
                # "rand": feine schwarze Kontur in px (1080er Raum), z. B.
                # fuer duenne Woerter auf hellem Grund (Zweifachschrift)
                out=3 if box else (float(tx.get('rand') or 0) if weich else 5),
                shadow=0 if (box or weich) else 2))
        x = float(tx.get('x', 0.5)) * W
        y = float(tx.get('y', 0.3)) * H
        if m:   # Grundlinie wie im Cockpit
            y += m[1] * float(tx.get('size', 72))
        anim = tx.get('anim', 'fade')

        def lage(x, y):
            if anim in ('left', 'right', 'up'):
                dx = -260 if anim == 'left' else 260 if anim == 'right' else 0
                dy = 220 if anim == 'up' else 0
                return ('\\move({:.0f},{:.0f},{:.0f},{:.0f},0,400)\\fad(120,200)'
                        .format(x + dx, y + dy, x, y))
            if anim == 'pop':
                return ('\\pos({:.0f},{:.0f})\\fscx40\\fscy40'
                        '\\t(0,280,\\fscx100\\fscy100)\\fad(80,200)'.format(x, y))
            if anim == 'none':
                return '\\pos({:.0f},{:.0f})'.format(x, y)
            return '\\pos({:.0f},{:.0f})\\fad(300,250)'.format(x, y)
        pos = lage(x, y)
        # 'lines' = vom Cockpit vermessene Zeilen (Text-Breiten-Flaeche);
        # Fallback: Text mit manuellen Umbruechen
        raw = ('\n'.join(str(l) for l in tx['lines']) if tx.get('lines')
               else str(tx.get('text', '')))
        text = raw.replace('{', '(').replace('}', ')').replace('\n', '\\N')
        if weich:
            g = float(tx.get('size', 72))
            weiss = str(tx.get('color', 'FFFFFF')).lstrip('#').upper() == 'FFFFFF'
            a = tx.get('schatten_alpha')
            a = float(a) if a is not None else (
                SCHATTEN['a'] if weiss else SCHATTEN['a_farbig'])
            wolke = (lage(x + SCHATTEN['dx'] * g, y + SCHATTEN['dy'] * g)
                     + '\\bord0\\c&H000000&\\1a&H{:02X}&\\blur{:.1f}'.format(
                         int(round((1 - a) * 255)), SCHATTEN['r'] * g / 2))
            events.append('Dialogue: 0,{},{},T{},,0,0,0,,{{\\an5{}}}{}'.format(
                fmt_time(tx.get('start', 0)), fmt_time(tx.get('end', 0)),
                i, wolke, text))
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
