#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wandelt Text in Glyphen-Umrisse (SVG-Pfade) fuer echte 3D-Schrift in Three.js.

Wird von projekt_anlegen.py aufgerufen. Einzeln:
  python text_zu_pfad.py <ausgabe.js> <schrift.ttf> "TEXT 1" ["TEXT 2" ...]

Die Pfade stehen in Font-Einheiten mit y nach oben (wie Three.js), je Glyphe
mit ihrem x-Versatz. Schluessel in SCHRIFT.zeilen ist der Text selbst.
Braucht fontTools (pip install fonttools).
"""
import json
import os
import platform
import sys

# Standardschrift je System: Arial Rounded wie die Kit-Untertitel, sonst Arial fett
KANDIDATEN = {
    'Windows': [r'C:\Windows\Fonts\ARLRDBD.TTF', r'C:\Windows\Fonts\arialbd.ttf'],
    'Darwin': ['/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf',
               '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
               '/Library/Fonts/Arial Rounded Bold.ttf'],
    'Linux': ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'],
}


def standard_schrift():
    for pfad in KANDIDATEN.get(platform.system(), []):
        if os.path.exists(pfad):
            return pfad
    return None


def glyphen(font, text):
    from fontTools.pens.svgPathPen import SVGPathPen
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    kern = {}
    if 'kern' in font:
        for tab in font['kern'].kernTables:
            kern.update(getattr(tab, 'kernTable', {}))
    x, vorher, aus = 0, None, []
    for ch in text:
        name = cmap.get(ord(ch))
        if name is None:
            raise SystemExit('Zeichen fehlt in der Schrift: ' + ch)
        if vorher:
            x += kern.get((vorher, name), 0)
        pen = SVGPathPen(gs)
        gs[name].draw(pen)
        d = pen.getCommands()
        if d:
            aus.append({'z': ch, 'd': d, 'x': x})
        x += gs[name].width
        vorher = name
    return aus, x


def schrift_modul(ttf, texte):
    """Liefert den Inhalt von schrift.js fuer alle Texte."""
    from fontTools.ttLib import TTFont
    font = TTFont(ttf)
    upm = font['head'].unitsPerEm
    daten = {'upm': upm,
             'hoehe': getattr(font['OS/2'], 'sCapHeight', 0) or round(upm * 0.72),
             'zeilen': {}}
    for text in dict.fromkeys(texte):
        g, breite = glyphen(font, text)
        daten['zeilen'][text] = {'breite': breite, 'glyphen': g}
    return ('// Automatisch erzeugt von scripts/text_zu_pfad.py - nicht von Hand aendern.\n'
            'export const SCHRIFT = ' + json.dumps(daten, ensure_ascii=False) + ';\n')


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    ziel, ttf, texte = sys.argv[1], sys.argv[2], sys.argv[3:]
    with open(ziel, 'w', encoding='utf-8') as f:
        f.write(schrift_modul(ttf, texte))
    print('OK', ziel, texte)


if __name__ == '__main__':
    main()
