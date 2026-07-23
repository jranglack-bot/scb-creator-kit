#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut/aktualisiert das Video-Cockpit fuer ein Projekt (Ein-Tab-Prinzip).

Schreibt zwei Dateien neben die projekt.json:
  - editor.html      (statisch, aus dem Template — laedt die Daten selbst)
  - projekt_data.js  (die Projektdaten; das offene Cockpit laedt diese Datei
                       alle 2,5 s nach -> Aenderungen von Claude erscheinen
                       IM OFFENEN TAB von selbst, kein neues Fenster noetig)

Aufruf:
  python build_editor.py <projekt.json>

WICHTIG fuer Claude: editor.html nur beim ERSTEN Mal oeffnen
(Start-Process). Danach reicht dieses Script — der offene Tab holt sich
die neuen Daten automatisch.
"""
import json
import os
import shutil
import sys
import time


def main():
    pj_path = os.path.abspath(sys.argv[1])
    projdir = os.path.dirname(pj_path)
    with open(pj_path, encoding='utf-8-sig') as f:
        projekt = json.load(f)
    projekt['rev'] = int(time.time())

    payload = json.dumps(projekt, ensure_ascii=False)
    payload = payload.replace('</', '<\\/')
    with open(os.path.join(projdir, 'projekt_data.js'), 'w',
              encoding='utf-8') as f:
        f.write('window.PROJEKT = ' + payload + ';\n')

    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'templates', 'editor.html')
    dest = os.path.join(projdir, 'editor.html')
    existed = os.path.exists(dest)
    shutil.copyfile(tpl, dest)

    print('OK: Daten aktualisiert ->', os.path.join(projdir, 'projekt_data.js'))
    if existed:
        print('Cockpit-Tab aktualisiert sich innerhalb von ~3 Sekunden von '
              'selbst. (Falls das Editor-Template selbst neuer ist: einmal '
              'F5 im Tab.)')
    else:
        print('NEU: Cockpit erstellt ->', dest,
              '(einmal oeffnen, danach nie wieder — alles Weitere kommt '
              'automatisch in diesen Tab)')


if __name__ == '__main__':
    main()
