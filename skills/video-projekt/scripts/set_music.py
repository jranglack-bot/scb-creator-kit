#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setzt die Musik eines Projekts in einem Schritt: Datei (Pfad oder URL)
in den Projektordner holen, music-Eintrag schreiben, Cockpit neu bauen
(inkl. Musik-Waveform). Claude sieht nur diese Zusammenfassung.

Aufruf:
  python set_music.py <projekt.json> <musikdatei-oder-url>
                      [--gain 0.3] [--offset 0] [--titel "Name (Quelle)"]
"""
import json
import os
import subprocess
import sys


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    pj_path = os.path.abspath(sys.argv[1])
    src = sys.argv[2]
    projdir = os.path.dirname(pj_path)
    dest = os.path.join(projdir, 'musik' + os.path.splitext(src)[1][:5]
                        if not src.lower().startswith('http') else 'musik.mp3')
    if src.lower().startswith('http'):
        subprocess.run(['curl', '-sL', src, '-o', dest], check=True)
    elif os.path.abspath(src) != os.path.abspath(dest):
        import shutil
        shutil.copyfile(src if os.path.isabs(src)
                        else os.path.join(projdir, src), dest)

    probe = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', dest], capture_output=True, text=True, check=True)
    song_dur = float(probe.stdout.strip())

    pj = json.load(open(pj_path, encoding='utf-8-sig'))
    pj['music'] = {'file': os.path.basename(dest),
                   'offset': float(arg('--offset', 0)),
                   'gain': float(arg('--gain', 0.3))}
    titel = arg('--titel', None)
    if titel:
        pj['music']['titel'] = titel
    with open(pj_path, 'w', encoding='utf-8') as f:
        json.dump(pj, f, ensure_ascii=False, indent=2)

    build = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'build_editor.py')
    subprocess.run([sys.executable, build, pj_path], check=True)
    print('OK: Musik gesetzt ->', os.path.basename(dest),
          '| {:.0f}s | gain {}'.format(song_dur, pj['music']['gain']))


if __name__ == '__main__':
    main()
