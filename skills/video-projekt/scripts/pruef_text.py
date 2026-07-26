#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PFLICHT-Kontrolle nach jedem Setzen von Schnitten: Zeigt den Text, der
nach den Schnitten UEBRIG bleibt, und warnt bei typischen Fehlern.

Aufruf:
  python pruef_text.py <projekt.json>

Prueft:
  - Welche Woerter fallen weg? (Schnitt mitten im Satz?)
  - Direkte Wortdopplungen an Schnittnaehten ("das das")
  - Schnitte, die einen Wortanfang anschneiden (Wort verschwindet)
Claude MUSS die Ausgabe lesen und den Text auf Sinn pruefen, bevor
gerendert wird.

WICHTIG: Diese Logik entspricht 1:1 der in render_projekt.py — ein Wort
gilt nur dann als ENTFERNT, wenn auch sein ENDE im Schnitt liegt (ASR-Start-
Zeitstempel sind an Pausen oft unzuverlaessig / zu frueh; ragt ein Wort mit
seinem Ende ueber den Schnitt hinaus, bleibt es erhalten und startet exakt
am Schnittende).
"""
import json
import os
import sys


def main():
    pj_path = os.path.abspath(sys.argv[1])
    pj = json.load(open(pj_path, encoding='utf-8-sig'))
    words = [w for w in (pj.get('words') or [])
             if w.get('type', 'word') == 'word']
    cuts = [c for c in (pj.get('cuts') or [])
            if c.get('active', True) and (c.get('track') or 'both') == 'both']
    if not words:
        print('Kein Transkript im Projekt — nichts zu pruefen.')
        return

    drin, raus = [], []
    for w in words:
        ws, we = float(w['start']), float(w['end'])
        voll_im_schnitt = any(float(c['start']) <= ws and we <= float(c['end'])
                              for c in cuts)
        if voll_im_schnitt:
            raus.append(w['text'])
        else:
            drin.append(w['text'])

    print('=== TEXT NACH DEN SCHNITTEN ({} von {} Woertern) ==='
          .format(len(drin), len(words)))
    print(' '.join(drin))
    if raus:
        print('\n=== ENTFERNT ({}) ==='.format(len(raus)))
        print(' '.join(raus))

    low = [t.lower().strip('.,!?') for t in drin]
    dups = [(i, low[i]) for i in range(len(low) - 1) if low[i] == low[i + 1]]
    if dups:
        print('\n!! WORTDOPPLUNGEN pruefen:',
              ', '.join('"{} {}"'.format(d[1], d[1]) for d in dups))

    # Schnitte, die nur einen Teil eines Wortes treffen (Wort bleibt, aber
    # sein Ton wird angeschnitten -> klingt abgehackt)
    for c in cuts:
        a, b = float(c['start']), float(c['end'])
        angeschnitten = [w['text'] for w in words
                         if float(w['start']) < a < float(w['end'])
                         or float(w['start']) < b < float(w['end'])]
        if angeschnitten:
            print('(Hinweis, meist unproblematisch — ASR-Zeiten an Pausen '
                  'oft ungenau) Schnitt {:.2f}-{:.2f} beruehrt Wortspanne: {}'
                  .format(a, b, ', '.join(angeschnitten[:3])))
    print('\nJetzt den Text oben lesen: Klingt er fluessig und vollstaendig?')


if __name__ == '__main__':
    main()
