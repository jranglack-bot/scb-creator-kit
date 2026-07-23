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
import array
import json
import os
import shutil
import subprocess
import sys
import time


def waveform_peaks(path, buckets=600):
    """Lautstaerke-Peaks (0-100) fuer die Tonspur-Anzeige im Cockpit."""
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '8000',
         '-f', 's16le', '-'], capture_output=True, check=True).stdout
    samples = array.array('h')
    samples.frombytes(raw[:len(raw) // 2 * 2])
    n = len(samples)
    if not n:
        return {'d': 0, 'p': []}
    step = max(1, n // buckets)
    peaks = []
    for i in range(0, n, step):
        seg = samples[i:i + step]
        peaks.append(round(max(abs(s) for s in seg) / 32768 * 100))
    return {'d': round(n / 8000.0, 2), 'p': peaks[:buckets]}


def build_waveforms(projekt, projdir):
    """waveform_data.js schreiben — nur fuer neue/geaenderte Videodateien."""
    videos = []
    if projekt.get('video'):
        videos.append(projekt['video'])
    src = (projekt.get('pip') or {}).get('source')
    if src and src not in videos:
        videos.append(src)
    wf_path = os.path.join(projdir, 'waveform_data.js')
    wf = {}
    if os.path.exists(wf_path):
        try:
            txt = open(wf_path, encoding='utf-8').read()
            wf = json.loads(txt[txt.index('=') + 1:].rstrip().rstrip(';'))
        except Exception:
            wf = {}
    changed = False
    for name in videos:
        vpath = os.path.join(projdir, name)
        if not os.path.exists(vpath):
            continue
        if (name in wf and os.path.exists(wf_path)
                and os.path.getmtime(wf_path) >= os.path.getmtime(vpath)):
            continue
        try:
            wf[name] = waveform_peaks(vpath)
            changed = True
        except Exception as e:
            print('WARNUNG: Keine Waveform fuer', name, '-', e)
    if changed or not os.path.exists(wf_path):
        with open(wf_path, 'w', encoding='utf-8') as f:
            f.write('window.WAVEFORM = ' + json.dumps(wf) + ';\n')
        print('OK: Tonspur-Daten ->', wf_path)


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

    build_waveforms(projekt, projdir)

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
