#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Findet die Stellen im Video, an denen ein Visual ueberhaupt gerechtfertigt
ist — und nur die.

WARUM ES DAS GIBT. Ohne eine harte Auswahl bekommt jeder zweite Satz ein
Icon, und das Video sieht aus wie eine Powerpoint. Die Regel dagegen heisst
NO VISUAL IS BETTER THAN A WEAK VISUAL. Damit sie nicht nur ein guter Vorsatz
bleibt, macht dieses Script die Vorauswahl messbar:

    WORT  ->  GEDANKENEINHEIT  ->  AUSSAGE  ->  VISUAL

- WORT: die Wortzeiten aus der projekt.json.
- GEDANKENEINHEIT: zusammenhaengend Gesprochenes zwischen zwei ECHTEN
  Sprechpausen. Gemessen an der Lautstaerke, nicht an Wortluecken —
  Transkripte dehnen Woerter ueber Pausen hinweg und setzen Wortanfaenge
  regelmaessig schon in die Stille davor (gemessen: bis 0,83 s zu frueh).
- AUSSAGE: eine Gedankeneinheit, die der Sprecher hervorhebt. Vier messbare
  Anzeichen: er laesst sie stehen (Pause danach), er wird lauter, sie ist
  kurz, sie enthaelt eine Zahl oder einen Gegensatz.
- VISUAL: entscheidet der Mensch. Das Script schlaegt nur vor.

Es waehlt bewusst WENIGE Stellen und haelt Abstand zwischen ihnen, damit
zusammenhaengende Bilder stehen bleiben duerfen statt sich zu jagen.

Aufruf:
  python aussagen_finden.py <projekt.json> [Optionen]
    --max 6           Hoechstens so viele Vorschlaege (Standard 6)
    --abstand 6       Mindestabstand zwischen zwei Vorschlaegen in Sekunden
    --pause 0.35      Ab dieser Stille beginnt eine neue Gedankeneinheit
    --alle            Alle Gedankeneinheiten zeigen, nicht nur die Auswahl
    --speichern       Auswahl zusaetzlich als aussagen.json ablegen

Ausgabe: EINE Zeile je Vorschlag. Die Wortliste landet nie im Kontext.
"""
import array
import json
import math
import os
import re
import subprocess
import sys

GEGENSATZ = ('aber', 'nicht', 'nie', 'kein', 'keine', 'keiner', 'sondern',
             'statt', 'stattdessen', 'trotzdem', 'obwohl', 'niemals')
ZAHLWORT = ('null', 'ein', 'eine', 'zwei', 'drei', 'vier', 'fuenf', 'fünf',
            'sechs', 'sieben', 'acht', 'neun', 'zehn', 'hundert', 'tausend',
            'prozent', 'euro', 'mal')


def opt(name, default):
    if name in sys.argv:
        return type(default)(sys.argv[sys.argv.index(name) + 1])
    return default


def huellkurve(dateien, sr=8000, fenster=0.02):
    """Lautstaerke je 20 ms ueber alle Clips hintereinander (Rohzeitlinie)."""
    env = []
    for d in dateien:
        roh = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', d, '-ac', '1', '-ar', str(sr),
             '-f', 's16le', '-'], capture_output=True, check=True).stdout
        a = array.array('h')
        a.frombytes(roh[:len(roh) // 2 * 2])
        w = int(sr * fenster)
        for i in range(0, len(a) - w, w):
            s = 0
            for v in a[i:i + w]:
                s += v * v
            env.append(math.sqrt(s / w))
    return env, fenster


def still(env, f, von, bis, schwelle):
    """Laenge der laengsten Stille zwischen zwei Zeitpunkten."""
    i0, i1 = int(von / f), min(len(env), int(bis / f))
    lang = lauf = 0
    for i in range(max(0, i0), i1):
        lauf = lauf + 1 if env[i] < schwelle else 0
        lang = max(lang, lauf)
    return lang * f


def pegel(env, f, von, bis):
    i0, i1 = max(0, int(von / f)), min(len(env), int(bis / f))
    teil = env[i0:i1]
    return sum(teil) / len(teil) if teil else 0.0


def einheiten_bilden(woerter, env, f, schwelle, min_pause):
    """Woerter zu Gedankeneinheiten gruppieren."""
    einheiten, jetzt = [], []
    for i, w in enumerate(woerter):
        jetzt.append(w)
        satzende = str(w['text']).rstrip()[-1:] in '.!?'
        pause = 0.0
        if i + 1 < len(woerter):
            pause = still(env, f, float(w['end']),
                          float(woerter[i + 1]['start']) + 0.25, schwelle)
        if satzende or pause >= min_pause or i + 1 == len(woerter):
            einheiten.append({'woerter': jetzt, 'pause_danach': round(pause, 2)})
            jetzt = []
    return einheiten


def bewerten(einheiten, env, f, gesamtpegel):
    for nr, e in enumerate(einheiten):
        ws = e['woerter']
        e['start'] = float(ws[0]['start'])
        e['ende'] = float(ws[-1]['end'])
        e['text'] = ' '.join(str(w['text']).strip() for w in ws)
        klein = e['text'].lower()
        p = pegel(env, f, e['start'], e['ende'])

        e['laut'] = round(p / gesamtpegel, 2) if gesamtpegel else 1.0
        e['zahl'] = bool(re.search(r'\d', e['text'])) or any(
            z in klein.split() for z in ZAHLWORT)
        e['gegensatz'] = any(g in klein.split() for g in GEGENSATZ)
        e['kurz'] = len(ws) <= 6
        e['rand'] = nr == 0 or nr == len(einheiten) - 1

        e['wert'] = round(
            min(e['pause_danach'], 1.2) * 0.9
            + max(0.0, e['laut'] - 1.0) * 2.0
            + (0.5 if e['zahl'] else 0.0)
            + (0.5 if e['gegensatz'] else 0.0)
            + (0.3 if e['kurz'] else 0.0)
            + (0.4 if e['rand'] else 0.0), 2)
    return einheiten


def auswaehlen(einheiten, hoechstens, abstand):
    """Beste zuerst, aber nie zwei dicht beieinander."""
    gewaehlt = []
    for e in sorted(einheiten, key=lambda x: -x['wert']):
        if len(gewaehlt) >= hoechstens:
            break
        if all(abs(e['start'] - g['start']) >= abstand for g in gewaehlt):
            gewaehlt.append(e)
    return sorted(gewaehlt, key=lambda x: x['start'])


def gruende(e):
    g = []
    if e['pause_danach'] >= 0.35:
        g.append('Pause %.1fs' % e['pause_danach'])
    if e['laut'] > 1.05:
        g.append('lauter')
    if e['zahl']:
        g.append('Zahl')
    if e['gegensatz']:
        g.append('Gegensatz')
    if e['kurz']:
        g.append('kurz')
    if e['rand']:
        g.append('Anfang/Ende')
    return ' · '.join(g) or 'nichts Auffaelliges'


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return 1
    pfad = sys.argv[1]
    with open(pfad, encoding='utf-8-sig') as f:
        pj = json.load(f)
    woerter = pj.get('words') or []
    if not woerter:
        print('Keine Wortzeiten in der projekt.json — erst transkribieren.')
        return 1

    basis = os.path.dirname(os.path.abspath(pfad))
    videos = [v if os.path.isabs(v) else os.path.join(basis, v)
              for v in (pj.get('videos') or ([pj['video']] if pj.get('video') else []))]
    videos = [v for v in videos if os.path.exists(v)]
    if not videos:
        print('Kein Quellvideo gefunden (Feld "videos" in der projekt.json).')
        return 1

    env, f = huellkurve(videos)
    if not env:
        print('Tonspur liess sich nicht lesen.')
        return 1
    schwelle = max(env) * 0.06
    # Bezugswert fuer "lauter" ist der Durchschnitt der GESPROCHENEN Stellen,
    # nicht der des ganzen Bandes. Mit den Pausen im Nenner liegt jede
    # Sprachstelle darueber und das Merkmal unterscheidet nichts mehr.
    laute = [v for v in env if v >= schwelle]
    gesamt = sum(laute) / len(laute) if laute else 0.0

    einheiten = bewerten(
        einheiten_bilden(woerter, env, f, schwelle, opt('--pause', 0.35)),
        env, f, gesamt)
    wahl = auswaehlen(einheiten, opt('--max', 6), opt('--abstand', 6.0))

    dauer = float(pj.get('duration') or (woerter[-1]['end']))
    print('%d Gedankeneinheiten in %.0f s. Vorschlaege fuer ein Visual:\n'
          % (len(einheiten), dauer))
    for e in (einheiten if '--alle' in sys.argv else wahl):
        mark = '*' if e in wahl else ' '
        text = e['text'] if len(e['text']) <= 58 else e['text'][:55] + '...'
        print('%s %6.2f-%6.2f  %4.2f  "%s"\n              %s'
              % (mark, e['start'], e['ende'], e['wert'], text, gruende(e)))

    print('\nNO VISUAL IS BETTER THAN A WEAK VISUAL. Ein Visual muss erklaeren,')
    print('zeigen, vergleichen oder ordnen. Kein Wort-zu-Icon. Lieber zwei')
    print('starke Stellen als sechs mittelmaessige — die Liste ist eine')
    print('Obergrenze, kein Soll.')

    if '--speichern' in sys.argv:
        ziel = os.path.join(basis, 'aussagen.json')
        with open(ziel, 'w', encoding='utf-8') as fh:
            json.dump([{k: e[k] for k in ('start', 'ende', 'text', 'wert')}
                       for e in wahl], fh, ensure_ascii=False, indent=1)
        print('\nGespeichert: aussagen.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
