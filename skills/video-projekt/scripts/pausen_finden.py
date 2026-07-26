#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Findet Sprechpausen ueber die ECHTE Lautstaerke und liefert FERTIGE,
sichere Schnittvorschlaege — inklusive exakter Grenzen.

WARUM NICHT NACH TRANSKRIPT-WORTLUECKEN? Transkriptionen dehnen Woerter
ueber Pausen hinweg (ein gemurmeltes "das" laeuft dann laut Transkript
1,4 s), dadurch bleiben echte Pausen unsichtbar. Dieses Script misst den
Ton direkt und bestimmt die Schnittgrenzen so, dass KEIN gesprochenes Wort
angeschnitten wird.

Aufruf:
  python pausen_finden.py <projekt.json> [--min 0.45] [--setzen]
    --min      Mindestlaenge einer Pause in Sekunden (Standard 0,45)
    --setzen   Vorschlaege direkt als Schnitte in die projekt.json schreiben
    --puffer   Sicherheitsabstand zum naechsten Ton (Standard 0,08 s)

Ausgabe: EINE kompakte Zeile je Vorschlag (Zeit, Laenge, Sprachkontext).
Claude soll danach nur noch den Inhalt pruefen (doppelte Aussagen,
Versprecher) und pruef_text.py laufen lassen.
"""
import array
import json
import os
import subprocess
import sys


def arg(name, default):
    if name in sys.argv:
        return float(sys.argv[sys.argv.index(name) + 1])
    return default


def audio_peaks(src, sr=8000, fenster=0.02):
    """Lautstaerke-Huellkurve: eine Spitze je 20 ms."""
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(sr),
         '-f', 's16le', '-'], capture_output=True, check=True).stdout
    s = array.array('h')
    s.frombytes(raw[:len(raw) // 2 * 2])
    win = int(sr * fenster)
    return [max(abs(x) for x in s[i:i + win])
            for i in range(0, len(s) - win, win)], fenster


def main():
    pj_path = os.path.abspath(sys.argv[1])
    projdir = os.path.dirname(pj_path)
    os.chdir(projdir)
    pj = json.load(open(pj_path, encoding='utf-8-sig'))
    videos = pj.get('videos') or ([pj['video']] if pj.get('video') else [])
    videos = [v for v in videos if v]
    if not videos:
        sys.exit('Kein Video im Projekt.')

    # Tonquelle: bei mehreren Clips einmal zusammenhaengen (nur Ton noetig)
    src = videos[0]
    if len(videos) > 1:
        src = 'p_analyse.mp4'
        if not os.path.exists(src):
            with open('p_an.txt', 'w', encoding='utf-8') as f:
                for v in videos:
                    f.write("file '{}'\n".format(v))
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat',
                            '-safe', '0', '-i', 'p_an.txt', '-c', 'copy',
                            src], check=True)

    peaks, fenster = audio_peaks(src)
    if not peaks:
        sys.exit('Kein Ton gefunden.')
    mx = max(peaks) or 1
    laut = [p / mx for p in peaks]

    THR_STILL = 0.10        # darunter = Stille
    THR_TON = 0.18          # darueber = sicher gesprochen
    minlen = arg('--min', 0.45)
    puffer = arg('--puffer', 0.08)

    def t(i):
        return i * fenster

    # 1) Stille-Bereiche finden
    roh, start = [], None
    for i, p in enumerate(laut):
        if p < THR_STILL:
            if start is None:
                start = i
        else:
            if start is not None and t(i - start) >= minlen:
                roh.append((start, i))
            start = None
    if start is not None and t(len(laut) - start) >= minlen:
        roh.append((start, len(laut)))

    # 2) Grenzen absichern: bis zum letzten/naechsten SICHEREN Ton schrumpfen
    vorschlaege = []
    for a, b in roh:
        while a < b and laut[a] >= THR_TON:
            a += 1
        while b > a and b - 1 < len(laut) and laut[b - 1] >= THR_TON:
            b -= 1
        s_zeit, e_zeit = t(a) + puffer, t(b) - puffer
        if e_zeit - s_zeit >= minlen * 0.6:
            vorschlaege.append((round(s_zeit, 2), round(e_zeit, 2)))

    words = [w for w in (pj.get('words') or [])
             if w.get('type', 'word') == 'word']

    def ctx(a, b):
        vor = [w['text'] for w in words if w['end'] <= a + 0.2][-3:]
        nach = [w['text'] for w in words if w['start'] >= b - 0.2][:3]
        return '"{}" || "{}"'.format(' '.join(vor), ' '.join(nach))

    print('SCHNITT-VORSCHLAEGE (Lautstaerke gemessen, Grenzen abgesichert):')
    for a, b in vorschlaege:
        marke = ' <- VIDEOSTART' if a < 0.3 else ''
        print('  {:6.2f} - {:6.2f}  ({:.1f}s)  {}{}'
              .format(a, b, b - a, ctx(a, b), marke))
    if not vorschlaege:
        print('  (keine)')
    print('\nHinweis: Beginnt das Video mit Stille, den ersten Vorschlag bis '
          'zum ersten Wort ausdehnen (Video muss mit dem 1. Wort starten).')

    if '--setzen' in sys.argv:
        cuts = [c for c in (pj.get('cuts') or [])]
        for a, b in vorschlaege:
            cuts.append({'start': a, 'end': b, 'active': True,
                         'track': 'both',
                         'reason': 'Sprechpause {:.1f}s'.format(b - a)})
        cuts.sort(key=lambda c: c['start'])
        pj['cuts'] = cuts
        with open(pj_path, 'w', encoding='utf-8') as f:
            json.dump(pj, f, ensure_ascii=False, indent=2)
        print('\n{} Schnitte gesetzt. PFLICHT: python pruef_text.py '
              'projekt.json'.format(len(vorschlaege)))


if __name__ == '__main__':
    main()
