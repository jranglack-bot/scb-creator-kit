#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setzt Soundeffekte automatisch an die Stellen, an denen im Projekt etwas
passiert - ohne Bilderkennung, weil die Zeiten schon in der projekt.json
stehen.

    Windows:   python  sfx_auto.py projekt.json --schnitte --texte
    Mac/Linux: python3 sfx_auto.py projekt.json --schnitte --untertitel --alle-schnitte

Zuordnung (siehe Tabelle in SKILL.md):

    --schnitte     whoosh auf jeden aktiven Video-Schnitt
    --texte        swish, wenn ein Text-Overlay einfliegt
    --untertitel   click auf jeden Untertitel-Block (NICHT jedes Wort)
    --zooms        impact, wenn ein harter Zoom ("fest") einsetzt

EISERNE REGEL des Kits: Nie ungefragt aufrufen. Erst anbieten, dann nur das
bauen, was der Nutzer gewaehlt hat.

Schreibt die Events nach effekte.sfx in die projekt.json. Zeiten sind
Ausgabezeiten des fertigen Videos - die Umrechnung ueber die Schnitte macht
dieses Script selbst.
"""

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
SFX = os.path.join(HIER, 'sfx')

# Standard-Pegel je Sound. Klicks liegen bewusst sehr leise - bei jedem
# Untertitel-Block wird es sonst nach zehn Sekunden anstrengend.
PEGEL = {'whoosh': 0.45, 'swish': 0.40, 'click': 0.18,
         'ding': 0.50, 'impact': 0.55, 'riser': 0.45, 'pop': 0.40}


def aktive_schnitte(pj):
    """Nur aktive Schnitte, die das Bild betreffen, nach Startzeit sortiert."""
    raus = []
    for c in pj.get('cuts') or []:
        if c.get('active') is False:
            continue
        if c.get('track') not in (None, 'both', 'video'):
            continue
        raus.append((float(c['start']), float(c['end'])))
    return sorted(raus)


def nach_ausgabezeit(t, schnitte):
    """Quellzeit -> Zeit im fertigen Video. None, wenn sie weggeschnitten ist."""
    entfernt = 0.0
    for start, ende in schnitte:
        if ende <= t:
            entfernt += ende - start
        elif start <= t < ende:
            return None
        else:
            break
    return round(t - entfernt, 3)


def nahtzeit(start, schnitte):
    """Ausgabezeit der Nahtstelle EINES Schnitts.

    Nicht ueber nach_ausgabezeit loesen: die Startzeit eines Schnitts liegt
    per Definition in ihm drin und wuerde als 'weggeschnitten' gelten. Hier
    zaehlen nur die Schnitte, die davor komplett entfernt wurden.
    """
    entfernt = sum(e - s for s, e in schnitte if e <= start)
    return round(start - entfernt, 3)


def datei(name):
    p = os.path.join(SFX, name + '.mp3')
    return p if os.path.isfile(p) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('projekt')
    ap.add_argument('--schnitte', action='store_true')
    ap.add_argument('--texte', action='store_true')
    ap.add_argument('--untertitel', action='store_true')
    ap.add_argument('--zooms', action='store_true')
    ap.add_argument('--alle-schnitte', action='store_true',
                    help='auch bei sehr dichten Schnitten jeden vertonen')
    ap.add_argument('--min-abstand', type=float, default=1.2,
                    help='Sekunden, die zwischen zwei Whooshes liegen muessen')
    args = ap.parse_args()

    if not (args.schnitte or args.texte or args.untertitel or args.zooms):
        print('Nichts gewaehlt. Mindestens eine Option angeben.')
        return 2

    # utf-8-sig statt utf-8: schluckt ein BOM, falls die Datei einmal in
    # Notepad o.ae. gespeichert wurde. Ohne das bricht json.load hart ab.
    with open(args.projekt, encoding='utf-8-sig') as f:
        pj = json.load(f)

    schnitte = aktive_schnitte(pj)
    events = []
    zaehler = {}

    def lege_ab(zeit, sound):
        p = datei(sound)
        if p is None or zeit is None or zeit < 0:
            return
        events.append({'time': zeit, 'file': p, 'gain': PEGEL.get(sound, 0.5)})
        zaehler[sound] = zaehler.get(sound, 0) + 1

    # --- Schnitte: whoosh an der Nahtstelle ---------------------------------
    if args.schnitte:
        letzte = -999.0
        for start, _ in schnitte:
            t = nahtzeit(start, schnitte)
            # Zu dichte Schnitte nicht alle vertonen - sonst wird es Brei.
            if not args.alle_schnitte and (t - letzte) < args.min_abstand:
                continue
            lege_ab(t, 'whoosh')
            letzte = t

    # --- Text-Overlays: swish beim Einfliegen -------------------------------
    if args.texte:
        for tx in pj.get('texts') or []:
            lege_ab(nach_ausgabezeit(float(tx.get('start', 0)), schnitte), 'swish')

    # --- Untertitel: click pro Block, nicht pro Wort -------------------------
    if args.untertitel:
        gruppe = int(((pj.get('captions') or {}).get('group')) or 3)
        woerter = pj.get('words') or []
        for i in range(0, len(woerter), max(1, gruppe)):
            w = woerter[i]
            lege_ab(nach_ausgabezeit(float(w.get('start', 0)), schnitte), 'click')

    # --- Zoom: impact nur beim harten Punch-In ------------------------------
    if args.zooms:
        for z in pj.get('zooms') or []:
            if z.get('mode') == 'fest':
                # zooms stehen in Quellzeit - render_projekt verschiebt sie
                # ebenfalls, also hier genauso umrechnen.
                lege_ab(nach_ausgabezeit(float(z.get('start', 0)), schnitte),
                        'impact')

    if not events:
        print('Keine passenden Stellen gefunden - nichts eingetragen.')
        return 0

    events.sort(key=lambda e: e['time'])
    pj.setdefault('effekte', {})['sfx'] = events
    with open(args.projekt, 'w', encoding='utf-8') as f:
        json.dump(pj, f, ensure_ascii=False, indent=2)

    zus = ', '.join('{}x {}'.format(n, s) for s, n in sorted(zaehler.items()))
    print('{} Events eingetragen ({})'.format(len(events), zus))
    print('Jetzt rendern: render_projekt.py {}'.format(args.projekt))
    return 0


if __name__ == '__main__':
    sys.exit(main())
