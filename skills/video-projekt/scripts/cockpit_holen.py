#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Holt die zuletzt im Cockpit gespeicherte Projektdatei ab.

    <python> cockpit_holen.py [sammelordner]

Ohne Angabe wird der zuletzt benutzte Sammelordner verwendet (gemerkt in
~/.scb-creator-kit/sammelordner.txt).

Das Cockpit speichert nach <Sammelordner>/<projekt>/projekt.json und schreibt
dabei seine Herkunft mit hinein:

    "_projekt"      Name des Projekts
    "_projektpfad"  voller Pfad des Projektordners
    "_gespeichert"  Zeitpunkt (ISO)

Damit findet dieses Script auch bei zehn Projekten die richtige Fassung:
die mit dem juengsten Zeitstempel. Es kopiert sie in ihren Projektordner
(aus "_projektpfad") und meldet, was sich gegenueber der dortigen Fassung
geaendert hat. Danach kann direkt gerendert werden.

Ohne Argumente ausgefuehrt zeigt es nur an, ohne zu kopieren: --nur-zeigen
"""
import json
import os
import shutil
import sys
from datetime import datetime

MERK = os.path.join(os.path.expanduser('~'), '.scb-creator-kit',
                    'sammelordner.txt')


def merk_lesen():
    try:
        with open(MERK, encoding='utf-8') as f:
            p = f.read().strip()
        return p if os.path.isdir(p) else None
    except OSError:
        return None


def merk_schreiben(pfad):
    try:
        os.makedirs(os.path.dirname(MERK), exist_ok=True)
        with open(MERK, 'w', encoding='utf-8') as f:
            f.write(pfad)
    except OSError:
        pass


def alle_projekte(sammel):
    """Alle projekt.json unter <sammel>/<projekt>/, juengste zuerst."""
    treffer = []
    for name in os.listdir(sammel):
        pfad = os.path.join(sammel, name, 'projekt.json')
        if not os.path.isfile(pfad):
            continue
        try:
            with open(pfad, encoding='utf-8-sig') as f:
                daten = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        treffer.append({
            'datei': pfad,
            'projekt': daten.get('_projekt') or name,
            'ziel': daten.get('_projektpfad'),
            'gespeichert': daten.get('_gespeichert') or '',
            'mtime': os.path.getmtime(pfad),
            'daten': daten,
        })
    treffer.sort(key=lambda t: (t['gespeichert'], t['mtime']), reverse=True)
    return treffer


def kurz(iso):
    try:
        return datetime.fromisoformat(iso.replace('Z', '+00:00')) \
            .astimezone().strftime('%d.%m. %H:%M:%S')
    except (ValueError, AttributeError):
        return '?'


def unterschiede(neu, alt_pfad):
    """Was hat der Nutzer geaendert? Kurz und lesbar."""
    if not os.path.isfile(alt_pfad):
        return ['Projektordner hat noch keine projekt.json']
    try:
        with open(alt_pfad, encoding='utf-8-sig') as f:
            alt = json.load(f)
    except (OSError, json.JSONDecodeError):
        return ['bestehende projekt.json nicht lesbar']

    aus = []
    ac = alt.get('captions') or {}
    nc = neu.get('captions') or {}
    for k in ('font', 'size', 'y', 'primary', 'highlight', 'group', 'bold',
              'box', 'highlight_on'):
        if ac.get(k) != nc.get(k):
            a, n = ac.get(k), nc.get(k)
            if isinstance(a, float):
                a = round(a, 3)
            if isinstance(n, float):
                n = round(n, 3)
            aus.append(f'Untertitel {k}: {a} -> {n}')

    def marken(p):
        return [(round(float(c['start']), 2), round(float(c['end']), 2))
                for c in (p.get('cuts') or []) if c.get('active')]
    if marken(alt) != marken(neu):
        aus.append(f'Schnitte: {marken(alt)} -> {marken(neu)}')

    for k in ('texts', 'zooms', 'volumes'):
        if len(alt.get(k) or []) != len(neu.get(k) or []):
            aus.append(f'{k}: {len(alt.get(k) or [])} -> {len(neu.get(k) or [])}')
    if (alt.get('words') or []) != (neu.get('words') or []):
        aus.append('Untertiteltext geaendert')
    return aus or ['keine inhaltlichen Unterschiede']


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    nur_zeigen = '--nur-zeigen' in sys.argv

    sammel = args[0] if args else merk_lesen()
    if not sammel or not os.path.isdir(sammel):
        print('Sammelordner angeben:  <python> cockpit_holen.py <ordner>')
        print('(einmal angegeben, wird er gemerkt)')
        return 2
    merk_schreiben(sammel)

    treffer = alle_projekte(sammel)
    if not treffer:
        print(f'Keine projekt.json unter {sammel}\\<projekt>\\ gefunden.')
        return 1

    print(f'Sammelordner: {sammel}')
    for i, t in enumerate(treffer):
        markierung = '->' if i == 0 else '  '
        print(f'{markierung} {t["projekt"]:<28} {kurz(t["gespeichert"])}')

    neuste = treffer[0]
    ziel = neuste['ziel']
    print()
    print(f'Zuletzt bearbeitet: {neuste["projekt"]}')
    if not ziel or not os.path.isdir(ziel):
        print(f'  Projektordner unbekannt oder weg ({ziel!r}) — bitte manuell '
              'kopieren.')
        return 1
    print(f'  gehoert nach: {ziel}')

    zielpfad = os.path.join(ziel, 'projekt.json')
    for zeile in unterschiede(neuste['daten'], zielpfad):
        print(f'  - {zeile}')

    if nur_zeigen:
        print('\n(nur angezeigt, nichts kopiert)')
        return 0

    shutil.copy2(neuste['datei'], zielpfad)
    print(f'\nUebernommen -> {zielpfad}')
    print('Jetzt rendern:  <python> render_projekt.py "%s"' % zielpfad)
    return 0


if __name__ == '__main__':
    sys.exit(main())
