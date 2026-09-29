#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rechnet die Person aus einem Video heraus: ergibt ein Bild der leeren Wand
fuer die Ebenen-Szene ("Hintergrund").

Aufruf:
  python leere_wand.py <video.mp4> <freisteller.webm|.mkv> <ausgabe.jpg>

Besser ist immer eine echte Aufnahme: vor dem Dreh 2 Sekunden den leeren Raum
filmen (Stativ, gleiche Einstellung) und davon ein Standbild nehmen. Dieses
Script ist der Ersatz, wenn es die nicht gibt.

Verfahren (getestet 29.09.2026 an einer hellen Zimmerwand):
  1. Alle Stellen sammeln, an denen die Wand in irgendeinem Bild sichtbar ist
     (Freisteller grosszuegig aufgeblaeht, damit kein Haar-Saum mitkommt),
     und dort mitteln.
  2. Was nie sichtbar war, mit einer glatten Flaeche fuellen: Polynom
     3. Grades je Farbkanal, angepasst an die sichtbare Wand, plus feines
     Rauschen. cv2.inpaint erzeugte stattdessen einen dunklen Umriss der
     Person und ist deshalb nicht der Weg.
Taugt fuer ruhige, glatte Hintergruende. Regale, Bilder, Fenster hinter der
Person lassen sich so nicht erfinden: dann eine Leeraufnahme drehen.
Braucht numpy und opencv-python (bringt der Setup-Assistent mit).
"""
import json
import subprocess
import sys

import cv2
import numpy as np


def masse(pfad):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height', '-of', 'json', pfad], capture_output=True, text=True)
    s = json.loads(r.stdout)['streams'][0]
    return int(s['width']), int(s['height'])


def lies(cmd, w, h, kanaele):
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, kanaele)


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    video, freisteller, ziel = sys.argv[1:]
    w, h = masse(video)
    bild = lies(['ffmpeg', '-v', 'error', '-i', video, '-vf', 'fps=6',
                 '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], w, h, 3)
    # VP9 traegt das Alpha in einem Zusatzblock: nur libvpx liest es mit
    vor = ['-c:v', 'libvpx-vp9'] if freisteller.lower().endswith('.webm') else []
    alpha = lies(['ffmpeg', '-v', 'error', *vor, '-i', freisteller,
                  '-vf', f'fps=6,scale={w}:{h},alphaextract',
                  '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], w, h, 1)[..., 0]
    n = min(len(bild), len(alpha))
    if n == 0:
        raise SystemExit('Konnte Video oder Freisteller nicht lesen')
    bild, alpha = bild[:n], alpha[:n]

    kern = np.ones((71, 71), np.uint8)
    frei = np.stack([cv2.dilate(a, kern) < 4 for a in alpha])
    anzahl = frei.sum(0)
    platte = (np.where(frei[..., None], bild, 0).astype(np.float32).sum(0)
              / np.maximum(anzahl, 1)[..., None])
    bekannt = anzahl >= 2
    if bekannt.mean() < 0.1:
        raise SystemExit('Zu wenig Wand sichtbar (unter 10 %): bitte eine Leeraufnahme drehen')

    ys, xs = np.nonzero(bekannt[::8, ::8])
    ys, xs = ys * 8, xs * 8

    def basis(x, y):
        x = x / w - 0.5
        y = y / h - 0.5
        return np.stack([x ** i * y ** j for i in range(4) for j in range(4 - i)], -1)

    A = basis(xs.astype(np.float32), ys.astype(np.float32))
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    B = basis(gx, gy)
    glatt = np.zeros((h, w, 3), np.float32)
    for k in range(3):
        koef, *_ = np.linalg.lstsq(A, platte[ys, xs, k], rcond=None)
        glatt[..., k] = B @ koef
    rng = np.random.default_rng(3)
    glatt += cv2.GaussianBlur(rng.normal(0, 2.2, (h, w)).astype(np.float32), (0, 0), 1.2)[..., None]

    m = cv2.GaussianBlur((~bekannt).astype(np.float32), (0, 0), 18)
    m = np.maximum(m, (~bekannt).astype(np.float32))[..., None]
    ergebnis = np.clip(platte * (1 - m) + glatt * m, 0, 255).astype(np.uint8)
    cv2.imwrite(ziel, ergebnis, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print(f'OK {ziel} | berechnete Flaeche {(~bekannt).mean() * 100:.0f} %')


if __name__ == '__main__':
    main()
