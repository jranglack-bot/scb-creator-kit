#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zieht Untertitel-Wortzeiten an eine zweite, sauber aufgenommene Tonspur
nach — und raeumt Wort-Ueberlappungen weg, die den Untertitel DOPPELT
anzeigen lassen.

WOFUER? Beim Aufzaehlungs-Reel liegt ueber dem Hauptvideo eine zweite
Aufnahme: je gesprochener Begriff ein WAV-Schnipsel auf der Effektspur,
darunter ist die Hauptspur stumm. Sobald diese Schnipsel im Cockpit
verschoben werden, stimmen die Wortzeiten aus dem Transkript nicht mehr —
der Untertitel laeuft dem Ton voraus (gemessen: bis 0,83 s).

ZWEI FEHLERQUELLEN, die dieses Script beide behebt:

1. VERSATZ. Die Woerter eines Begriffs muessen dort stehen, wo der
   Schnipsel wirklich KLINGT — nicht am Dateianfang: WAV-Schnipsel haben
   typisch 0,07-0,10 s Vorlauf. Das Script misst den Sprechbeginn in der
   Datei und legt die Woerter proportional auf die gemessene Spanne.

2. DOPPELTER UNTERTITEL. Transkriptionen setzen Wortanfaenge regelmaessig
   schon in die Stille davor. Reicht ein Wort dadurch ueber den Beginn der
   naechsten Wortgruppe hinaus, stehen BEIDE Gruppen gleichzeitig im Bild.
   Das Script zieht jeden Wortstart hinter das Ende des Vorgaengers. Das
   Wort-ENDE bleibt unangetastet, es ist der zuverlaessige Wert — dieselbe
   Regel benutzt render_projekt.py an Schnittkanten.

ZUORDNUNG WORT -> SCHNIPSEL: am saubersten ueber ein Feld `worte` im
sfx-Eintrag, gesetzt beim Schneiden der Schnipsel, wo die Zuordnung
ohnehin bekannt ist:

    {"time": 20.90, "file": "stimme/08_amazon_fba.wav",
     "worte": "Amazon FBA"}

Fehlt das Feld, hilft --zuordnung mit Wortindizes.

Aufruf:
  python stimme_synchronisieren.py <projekt.json> [Optionen]
    --ordner stimme   Nur sfx-Eintraege aus diesem Unterordner gelten als
                      Stimme (Standard: stimme). Woosh & Co. bleiben aussen vor.
    --zuordnung 0-2,6-8,12
                      Wortindizes je Schnipsel, falls `worte` fehlt.
    --nur-klemmen     Nur Ueberlappungen entfernen, nichts verschieben.
    --test            Nichts schreiben, nur zeigen was passieren wuerde.
"""
import array
import json
import math
import os
import subprocess
import sys


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def norm(t):
    """Vergleichsform: nur Kleinbuchstaben und Ziffern, Umlaute aufgeloest."""
    t = str(t).lower()
    for a, b in ((u'\xe4', 'ae'), (u'\xf6', 'oe'), (u'\xfc', 'ue'),
                 (u'\xdf', 'ss')):
        t = t.replace(a, b)
    return ''.join(c for c in t if c.isalnum())


def im_ordner(pfad, ordner):
    teile = str(pfad).replace('\\', '/').lower().split('/')
    return ordner.lower() in teile[:-1]


def huellkurve(datei, sr=8000, fenster=0.01):
    """Lautstaerke je Fenster. Ueber ffmpeg, damit auch mp3/m4a gehen."""
    roh = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', datei, '-ac', '1', '-ar', str(sr),
         '-f', 's16le', '-'], capture_output=True, check=True).stdout
    a = array.array('h')
    a.frombytes(roh[:len(roh) // 2 * 2])
    w = max(1, int(sr * fenster))
    return [math.sqrt(sum(v * v for v in a[i:i + w]) / w)
            for i in range(0, len(a) - w, w)], fenster


def sprechspanne(datei, anteil=0.10):
    """(Sekunde des ersten Tons, Sekunde des letzten Tons) IN der Datei."""
    env, f = huellkurve(datei)
    if not env:
        return 0.0, 0.0
    schwelle = max(env) * anteil
    ein = next((i for i, v in enumerate(env) if v > schwelle), 0)
    aus = len(env) - 1 - next((i for i, v in enumerate(reversed(env))
                               if v > schwelle), 0)
    return ein * f, (aus + 1) * f


def lauf_finden(woerter, text, ab=0):
    """Index-Spanne der Woerter, die zusammen `text` ergeben."""
    ziel = norm(text)
    for i in range(ab, len(woerter)):
        gesammelt = ''
        for j in range(i, len(woerter)):
            gesammelt += norm(woerter[j]['text'])
            if gesammelt == ziel:
                return i, j
            if not ziel.startswith(gesammelt):
                break
    return None


def nachziehen(pj, basis, ordner, spannen):
    """Woerter der Stimm-Schnipsel auf deren gemessenen Ton legen."""
    woerter = pj['words']
    stimmen = [s for s in (pj.get('effekte') or {}).get('sfx', [])
               if im_ordner(s.get('file', ''), ordner)]
    stimmen.sort(key=lambda s: float(s['time']))
    if not stimmen:
        print('Keine Stimm-Schnipsel in effekte.sfx gefunden '
              '(gesucht im Unterordner "%s").' % ordner)
        return 0

    print('%-28s %14s %14s %8s'
          % ('Schnipsel', 'Untertitel alt', 'Untertitel neu', 'Versatz'))
    getan, ab = 0, 0
    for nr, s in enumerate(stimmen):
        datei = s['file']
        if not os.path.isabs(datei):
            datei = os.path.join(basis, datei)
        if not os.path.exists(datei):
            print('  fehlt:', s['file'])
            continue

        if s.get('worte'):
            lauf = lauf_finden(woerter, s['worte'], ab)
            if lauf is None:
                print('  "%s" nicht im Wortlauf gefunden' % s['worte'])
                continue
            i0, i1 = lauf
        elif nr < len(spannen):
            teil = spannen[nr].split('-')
            i0, i1 = int(teil[0]), int(teil[-1])
        else:
            print('  %s: keine Zuordnung. Feld "worte" setzen oder '
                  '--zuordnung benutzen.' % os.path.basename(datei))
            continue
        ab = i1 + 1

        ein, aus = sprechspanne(datei)
        von, bis = float(s['time']) + ein, float(s['time']) + aus
        alt0, alt1 = float(woerter[i0]['start']), float(woerter[i1]['end'])
        spanne = (alt1 - alt0) or 1.0
        for i in range(i0, i1 + 1):
            rs = (float(woerter[i]['start']) - alt0) / spanne
            re_ = (float(woerter[i]['end']) - alt0) / spanne
            woerter[i]['start'] = round(von + rs * (bis - von), 3)
            woerter[i]['end'] = round(von + re_ * (bis - von), 3)
        getan += 1
        print('%-28s %6.2f-%6.2f %6.2f-%6.2f %+8.2f'
              % (os.path.basename(datei), alt0, alt1, von, bis, von - alt0))
    return getan


def klemmen(woerter):
    """Jeden Wortstart hinter das Ende des Vorgaengers ziehen."""
    vorher = sum(1 for i in range(len(woerter) - 1)
                 if float(woerter[i]['end'])
                 > float(woerter[i + 1]['start']) + 1e-6)
    getan = 0
    for i in range(1, len(woerter)):
        if float(woerter[i]['start']) < float(woerter[i - 1]['end']):
            woerter[i]['start'] = round(float(woerter[i - 1]['end']), 3)
            getan += 1
    offen = sum(1 for i in range(len(woerter) - 1)
                if float(woerter[i]['end'])
                > float(woerter[i + 1]['start']) + 1e-6)
    return vorher, getan, offen


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return 1
    pfad = sys.argv[1]
    with open(pfad, encoding='utf-8-sig') as f:
        pj = json.load(f)
    if not pj.get('words'):
        print('Keine Wortzeiten in der projekt.json — erst transkribieren.')
        return 1

    verschoben = 0
    if '--nur-klemmen' not in sys.argv:
        zu = opt('--zuordnung')
        verschoben = nachziehen(pj, os.path.dirname(os.path.abspath(pfad)),
                                opt('--ordner', 'stimme'),
                                zu.split(',') if zu else [])

    vorher, geklemmt, offen = klemmen(pj['words'])
    print('\nSchnipsel nachgezogen: %d' % verschoben)
    print('Wortstarts geklemmt:   %d  (doppelte Untertitel vorher: %d)'
          % (geklemmt, vorher))
    if offen:
        print('ACHTUNG: %d Ueberlappungen bleiben — Wortliste pruefen.' % offen)

    if '--test' in sys.argv:
        print('\n--test: nichts geschrieben.')
        return 0
    with open(pfad, 'w', encoding='utf-8') as f:
        json.dump(pj, f, ensure_ascii=False, indent=1)
    print('\n%s geschrieben. Jetzt render_projekt.py.' % os.path.basename(pfad))
    return 0


if __name__ == '__main__':
    sys.exit(main())
