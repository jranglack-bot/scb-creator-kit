#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut/aktualisiert das Video-Cockpit fuer ein Projekt (Ein-Tab-Prinzip).

Schreibt zwei Dateien neben die projekt.json:
  - editor.html      (statisch, aus dem Template — laedt die Daten selbst)
  - projekt_data.js  (die Projektdaten; das offene Cockpit laedt diese Datei
                       alle 2,5 s nach -> Aenderungen von Claude erscheinen
                       IM OFFENEN TAB von selbst, kein neues Fenster noetig)

Aufruf:
  Windows:   python  build_editor.py <projekt.json>
  Mac/Linux: python3 build_editor.py <projekt.json>

WICHTIG fuer Claude: editor.html nur beim ERSTEN Mal oeffnen — je nach
System mit Start-Process (Windows), open (macOS) oder xdg-open (Linux).
Danach reicht dieses Script — der offene Tab holt sich die neuen Daten
automatisch.
"""
import array
import json
import os
import platform
import shutil
import subprocess
import sys
import time


# Schriften, die auf dem jeweiligen System wirklich installiert sind.
# WICHTIG: Untertitel werden ins Video GEBRANNT. Steht dort eine Schrift,
# die es auf dem System nicht gibt, ersetzt ffmpeg sie stillschweigend
# durch irgendeine andere — das Ergebnis sieht dann anders aus als die
# Vorschau im Cockpit. Deshalb bekommt jedes System nur seine eigenen.
FONTS_GEMEINSAM = ['Arial', 'Arial Black', 'Impact', 'Georgia', 'Verdana',
                   'Tahoma', 'Trebuchet MS', 'Times New Roman',
                   'Courier New', 'Comic Sans MS']
FONTS_WINDOWS = ['Segoe UI', 'Segoe UI Black', 'Bahnschrift', 'Calibri',
                 'Cambria', 'Candara', 'Consolas', 'Corbel',
                 'Franklin Gothic Demi', 'Gabriola', 'Garamond',
                 'Lucida Sans', 'Palatino Linotype', 'Rockwell',
                 'Sitka Display', 'Arial Rounded MT Bold']
FONTS_MACOS = ['Helvetica Neue', 'Helvetica', 'Avenir Next', 'Avenir',
               'Futura', 'Gill Sans', 'Optima', 'Baskerville', 'Didot',
               'American Typewriter', 'Chalkboard SE', 'Marker Felt',
               'Copperplate', 'Menlo', 'Monaco']
FONTS_LINUX = ['DejaVu Sans', 'DejaVu Serif', 'Liberation Sans',
               'Liberation Serif', 'Ubuntu', 'Noto Sans', 'FreeSans']


def schriften():
    """(Liste, Standardschrift) fuer das laufende System."""
    sys_name = platform.system()
    if sys_name == 'Windows':
        eigen, std = FONTS_WINDOWS, 'Segoe UI'
    elif sys_name == 'Darwin':
        eigen, std = FONTS_MACOS, 'Helvetica Neue'
    else:
        eigen, std = FONTS_LINUX, 'DejaVu Sans'
    liste = []
    for f in [std] + eigen + FONTS_GEMEINSAM:
        if f not in liste:
            liste.append(f)
    return liste, std


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
    mus = (projekt.get('music') or {}).get('file')
    if mus and mus not in videos:
        videos.append(mus)
    voi = (projekt.get('voiceover') or {}).get('file')
    if voi and voi not in videos:
        videos.append(voi)
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
    # Videodateien im Projektordner -> Dropdown "anderes kleines Video"
    # (nur Anzeige-Info; das Cockpit speichert _dateien nicht zurueck)
    projekt['_dateien'] = sorted(
        f for f in os.listdir(projdir)
        if f.lower().endswith(('.mp4', '.mov', '.mkv', '.m4v')))
    projekt['_audiodateien'] = sorted(
        f for f in os.listdir(projdir)
        if f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg',
                               '.webm', '.flac')))
    # Laenge jedes Clips gleich mitliefern — das Cockpit kann sie im Browser
    # nicht zuverlaessig messen (Metadaten laden bei file:// oft nicht) und
    # wuesste sonst nicht, wo Clip 1 endet und Clip 2 beginnt.
    vids = projekt.get('videos') or ([projekt['video']]
                                     if projekt.get('video') else [])
    dauern = []
    for v in vids:
        p = os.path.join(projdir, v)
        try:
            out = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', p], capture_output=True, text=True,
                check=True).stdout.strip()
            dauern.append(round(float(out), 3))
        except Exception:
            dauern.append(0)
    projekt['_clipdauern'] = dauern
    if dauern and all(d > 0 for d in dauern):
        projekt['duration'] = round(sum(dauern), 2)
    projekt['_schriften'], projekt['_standardschrift'] = schriften()

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

    # Eigene Erweiterungen des Nutzers: cockpit_custom.js wird NIE
    # ueberschrieben — Kit-Updates ersetzen nur editor.html. Fehlt die Datei,
    # wird die globale Vorlage des Nutzers kopiert (falls vorhanden) oder ein
    # leerer Platzhalter angelegt.
    custom = os.path.join(projdir, 'cockpit_custom.js')
    if not os.path.exists(custom):
        glob_custom = os.path.join(os.path.expanduser('~'),
                                   '.scb-creator-kit', 'cockpit_custom.js')
        if os.path.exists(glob_custom):
            shutil.copyfile(glob_custom, custom)
            print('OK: Eigene Cockpit-Erweiterungen uebernommen ->', custom)
        else:
            with open(custom, 'w', encoding='utf-8') as f:
                f.write(
                    '// Eigene Cockpit-Erweiterungen — diese Datei wird bei\n'
                    '// Kit-Updates NIE ueberschrieben. Alle Funktionen des\n'
                    '// Cockpits sind global und koennen hier ergaenzt oder\n'
                    '// ersetzt werden (danach ggf. renderTL() aufrufen).\n'
                    '// Soll eine Erweiterung in ALLEN Projekten gelten:\n'
                    '// Datei ablegen unter\n'
                    '//   Windows:   %USERPROFILE%\\.scb-creator-kit\\'
                    'cockpit_custom.js\n'
                    '//   Mac/Linux: ~/.scb-creator-kit/cockpit_custom.js\n')

    # Doppelklick-Render: rendert das fertige MP4 ohne Claude (0 Tokens).
    # BEIDE Systeme muessen das koennen — Windows bekommt eine .bat,
    # Mac/Linux eine ausfuehrbare .command. Siehe SKILL.md, Grundregel
    # "Windows UND Mac": nie einen Weg bauen, den nur ein System hat.
    rp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'render_projekt.py')
    if platform.system() == 'Windows':
        starter = os.path.join(projdir, 'video_rendern.bat')
        with open(starter, 'w', encoding='cp1252', errors='replace',
                  newline='') as f:
            f.write('@echo off\r\n'
                    'echo SCB Video-Render laeuft - Fenster offen lassen ...\r\n'
                    'python "{}" "%~dp0projekt.json"\r\n'
                    'echo.\r\n'
                    'echo Fertig! Das Video liegt in diesem Ordner.\r\n'
                    'pause\r\n'.format(rp))
    else:
        starter = os.path.join(projdir, 'video_rendern.command')
        with open(starter, 'w', encoding='utf-8', newline='\n') as f:
            f.write('#!/bin/bash\n'
                    'cd "$(dirname "$0")"\n'
                    'echo "SCB Video-Render laeuft - Fenster offen lassen ..."\n'
                    'python3 "{}" "$(pwd)/projekt.json"\n'
                    'echo ""\n'
                    'echo "Fertig! Das Video liegt in diesem Ordner."\n'
                    'read -n 1 -s -r -p "Zum Schliessen eine Taste druecken"\n'
                    .format(rp))
        os.chmod(starter, 0o755)

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
