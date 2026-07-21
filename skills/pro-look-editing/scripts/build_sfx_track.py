#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut aus vielen Sound-Events EINE fertige Tonspur (WAV).

Fuer Faelle mit vielen Events (z.B. Typewriter-Klicks auf jeder
Untertitel-Einblendung): statt Dutzende ffmpeg-Inputs zu mischen,
entsteht hier eine einzige Datei, die prolook.py dann als EIN
sfx-Eintrag (time 0) einmischt.

Aufruf:
  python build_sfx_track.py events.json out.wav --duration 30.0

events.json: [{"time": 1.23, "file": "click.mp3", "gain": 0.5}, ...]
"""
import argparse
import array
import json
import subprocess

RATE = 48000


def decode(path):
    """Beliebige Audiodatei -> 48k mono s16 Samples (ffmpeg)."""
    out = subprocess.run(
        ['ffmpeg', '-v', 'quiet', '-i', path, '-ac', '1', '-ar', str(RATE),
         '-f', 's16le', '-'],
        capture_output=True, check=True)
    return array.array('h', out.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('events')
    ap.add_argument('output')
    ap.add_argument('--duration', type=float, required=True)
    args = ap.parse_args()

    with open(args.events, encoding='utf-8') as f:
        events = json.load(f)

    total = int(args.duration * RATE) + RATE
    mix = array.array('l', [0]) * total
    cache = {}
    for ev in events:
        path = ev['file']
        if path not in cache:
            cache[path] = decode(path)
        samples = cache[path]
        gain = float(ev.get('gain', 0.6))
        start = int(float(ev['time']) * RATE)
        for i, s in enumerate(samples):
            j = start + i
            if j >= total:
                break
            mix[j] += int(s * gain)

    # Clipping vermeiden
    peak = max(1, max(abs(v) for v in mix))
    scale = min(1.0, 30000.0 / peak)
    pcm = array.array('h', (int(v * scale) for v in mix))

    import wave
    with wave.open(args.output, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    print('OK: {} Events -> {}'.format(len(events), args.output))


if __name__ == '__main__':
    main()
