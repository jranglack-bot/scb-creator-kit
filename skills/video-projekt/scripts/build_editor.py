#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut das Video-Cockpit fuer ein Projekt: editor.html neben das Video.

Injiziert die projekt.json in das Editor-Template (kein fetch noetig —
file://-Seiten duerfen kein JSON nachladen, Videos aber schon).

Aufruf:
  python build_editor.py <projekt.json>
-> schreibt editor.html in den Ordner der projekt.json.
"""
import json
import os
import sys


def main():
    pj_path = os.path.abspath(sys.argv[1])
    projdir = os.path.dirname(pj_path)
    with open(pj_path, encoding='utf-8-sig') as f:
        projekt = json.load(f)

    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'templates', 'editor.html')
    with open(tpl, encoding='utf-8') as f:
        html = f.read()

    payload = json.dumps(projekt, ensure_ascii=False)
    # </script> im JSON wuerde das Script-Tag sprengen
    payload = payload.replace('</', '<\\/')
    html = html.replace('/*__PROJEKT_JSON__*/{}', payload)

    out = os.path.join(projdir, 'editor.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('OK: Cockpit ->', out)
    print('Oeffnen per Doppelklick; Speichern legt projekt.json in Downloads ab.')


if __name__ == '__main__':
    main()
