#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kamera folgt der Person — automatischer Bildausschnitt beim Formatwechsel.

    <python> person_folgen.py <projekt>          # Spur berechnen (gecacht) + Kurzbericht

Wird ein Video in ein schmaleres Format gebracht (z. B. 16:9 → 9:16, Einpassen
„fuellen"), faehrt der Ausschnitt dem Kopf der Person nach — wie ein
Kameramann: ruhig, solange sie ungefaehr am Platz bleibt (Totzone), weich
nachziehend, wenn sie sich bewegt, und bei harten Schnitten springt er
sofort um statt durchs Bild zu schwenken.

Erkannt wird mit dem Personen-Modell, das das Kit ohnehin mitbringt
(MediaPipe Selfie Segmenter, models/selfie_segmenter.tflite — dasselbe wie
bei der Freistellung): Kopf = oberster Teil der Person. Das klappt auch im
Profil und von hinten, wo reine Gesichtserkennung aussteigt. Kein Download.

projekt.json:  "ausschnitt": {"folgen": true}  (+ "format", "einpassen": "fuellen")
Ergebnis:      r_person.json im Projekt (gecacht ueber Dateien + Stand)
               {"fps": 5, "punkte": [[t_roh, kopf_x, kopf_y], ...]}
               Kopf-Lage als Anteil des Bildes (0..1), None = keine Person.
Daraus rechnen Cockpit (Vorschau) und Render denselben Ausschnitt —
kamerafahrt() ist die eine Formel, das Cockpit bekommt die fertige Fahrt.

Windows UND Mac: nur ffmpeg, numpy, mediapipe (installiert das Setup).
"""
import json
import math
import os
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import bildformat  # noqa: E402

VERSION = 2
FPS = 5                    # Abtastung (Bilder pro Sekunde)
BREITE = 256               # Rechenbreite — das Modell arbeitet mit 256 px
MODELL = os.path.normpath(os.path.join(HIER, '..', '..', 'pro-look-editing',
                                       'scripts', 'models', 'selfie_segmenter.tflite'))

# Kameramann
TOTZONE = 0.06             # so weit darf der Kopf wandern, ohne dass die Kamera folgt
TRAEGHEIT = 0.7            # Sekunden, bis die Kamera einer Bewegung nachgezogen ist
SPRUNG = 0.3               # groessere Spruenge = Schnitt → Kamera springt mit
KOPF_OBEN = 0.36           # bei Hochkant-Ausschnitt: Kopf auf 36 % der Hoehe


# ------------------------------------------------------------ Erkennung
def _bilder(video, start=0.0):
    """(Zeit, RGB-Bild) mit FPS Bildern pro Sekunde, BREITE px breit."""
    import numpy as np
    m = bildformat.quelle_masse(video)
    if not m:
        return
    w = BREITE
    h = max(2, int(round(m[1] * w / m[0] / 2)) * 2)
    proc = subprocess.Popen(
        ['ffmpeg', '-v', 'error', '-i', video, '-vf',
         'fps={},scale={}:{}'.format(FPS, w, h), '-pix_fmt', 'rgb24',
         '-f', 'rawvideo', '-'], stdout=subprocess.PIPE)
    groesse = w * h * 3
    n = 0
    while True:
        roh = proc.stdout.read(groesse)
        if len(roh) < groesse:
            break
        yield start + n / FPS, np.frombuffer(roh, np.uint8).reshape(h, w, 3)
        n += 1
    proc.wait()


def kopf_lage(maske):
    """Kopfmitte (x, y) und Personenflaeche als Anteil des Bildes.

    Nur der GROESSTE zusammenhaengende Bereich zaehlt als Person — das Modell
    meldet gelegentlich dunkle Moebel oder Regalkanten (gemessen 03.10.2026:
    ein schwarzer Buerostuhl als „Person"); die liegen meist abseits."""
    import numpy as np
    import cv2
    p = (maske > 0.5).astype(np.uint8)
    h, w = p.shape
    n, etiketten, stat, _ = cv2.connectedComponentsWithStats(p, connectivity=8)
    if n <= 1:
        return None
    groesster = 1 + int(np.argmax(stat[1:, cv2.CC_STAT_AREA]))
    p = etiketten == groesster
    flaeche = float(p.sum()) / (h * w)
    if flaeche < 0.005:
        return None
    zeilen = np.where(p.sum(axis=1) >= max(2, 0.01 * w))[0]
    if not len(zeilen):
        return None
    oben, unten = int(zeilen[0]), int(zeilen[-1])
    band = max(int(0.12 * h), int(0.22 * (unten - oben + 1)))
    kopf = p[oben:oben + band]
    spalten = kopf.sum(axis=0).astype(float)
    if spalten.sum() <= 0:
        return None
    x = float((spalten * np.arange(w)).sum() / spalten.sum()) + 0.5
    return round(x / w, 4), round((oben + band / 2) / h, 4), round(flaeche, 4)


def spur_messen(clips_mit_start):
    """[[t_roh, x, y] | [t_roh, None, None]] fuer alle Clips nacheinander."""
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
    opt = vision.ImageSegmenterOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODELL),
        running_mode=vision.RunningMode.IMAGE,
        output_category_mask=False, output_confidence_masks=True)
    punkte = []
    import numpy as np
    with vision.ImageSegmenter.create_from_options(opt) as seg:
        for pfad, start in clips_mit_start:
            for t, rgb in _bilder(pfad, start):
                erg = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB,
                                           data=np.ascontiguousarray(rgb)))
                m = erg.confidence_masks
                maske = np.array((m[1] if len(m) > 1 else m[0]).numpy_view(),
                                 dtype=np.float32, copy=True)
                if maske.ndim == 3:
                    maske = maske[..., 0]
                lage = kopf_lage(maske)
                punkte.append([round(t, 3)] + (list(lage) if lage else [None, None, None]))
    return punkte


def parameter():
    """Fuers Cockpit: dieselben Zahlen, mit denen es die Fahrt nachrechnet."""
    return {'fps': FPS, 'totzone': TOTZONE, 'traegheit': TRAEGHEIT,
            'sprung': SPRUNG, 'kopf_oben': KOPF_OBEN}


# ------------------------------------------------------------ Kameramann
def kamerafahrt(punkte, quelle_wh, ziel_wh):
    """Aus Kopf-Lagen die Kamera: [[t, ax, ay], ...] — ax/ay wie
    "ausschnitt" (0 = ganz links/oben, 1 = ganz rechts/unten)."""
    sw, sh = quelle_wh
    zw, zh = ziel_wh
    # Anteil der Quelle, den der Ausschnitt zeigt (beim Fuellen)
    wf = min(1.0, (zw / zh) / (sw / sh))
    hf = min(1.0, (zh / zw) / (sh / sw))

    def ziel(x, y):
        ax = 0.5 if wf >= 0.999 else min(1.0, max(0.0, (x - wf / 2) / (1 - wf)))
        ay = 0.5 if hf >= 0.999 else min(1.0, max(0.0, (y - KOPF_OBEN * hf) / (1 - hf)))
        return ax, ay

    # Fehlalarme: deutlich kleiner als die typische Person dieses Videos
    # (Median aller Erkennungen) = keine Person. Echte Person 25-30 % des
    # Bildes, Moebel-Fehlalarm um 10 % (gemessen 03.10.2026).
    flaechen = sorted(p[3] for p in punkte if p[1] is not None and len(p) > 3
                      and p[3] is not None)
    if flaechen:
        grenze = 0.45 * flaechen[len(flaechen) // 2]
        punkte = [p if (p[1] is None or len(p) < 4 or p[3] is None or p[3] >= grenze)
                  else [p[0], None, None, None] for p in punkte]
    # Luecken: kurze (bis 1 s) = letzte Lage halten (Person kurz verdeckt),
    # lange = Bildmitte (Titelkarte, Grafik, leeres Bild — dort ist die Mitte
    # fast immer richtig). Anfang ohne Person = erste bekannte Lage.
    bekannt = [(p[1], p[2]) for p in punkte if p[1] is not None]
    if not bekannt:
        return [[p[0], 0.5, 0.5] for p in punkte[:1]] or [[0.0, 0.5, 0.5]]
    luecke = [0] * len(punkte)          # Laenge der Luecke, in der i liegt
    i = 0
    while i < len(punkte):
        if punkte[i][1] is None:
            j = i
            while j < len(punkte) and punkte[j][1] is None:
                j += 1
            for k in range(i, j):
                luecke[k] = j - i
            i = j
        else:
            i += 1
    zuletzt = bekannt[0]
    roh = []
    for i, p in enumerate(punkte):
        if p[1] is not None:
            zuletzt = (p[1], p[2])
            roh.append((p[0],) + ziel(*zuletzt))
        elif luecke[i] > FPS:
            roh.append((p[0], 0.5, 0.5))
        else:
            roh.append((p[0],) + ziel(*zuletzt))
    # Ausreisser weg: gleitender Median ueber 5 Werte (1 s)
    def median(werte, i):
        f = sorted(werte[max(0, i - 2):i + 3])
        return f[len(f) // 2]
    xs = [r[1] for r in roh]
    ys = [r[2] for r in roh]
    xs = [median(xs, i) for i in range(len(xs))]
    ys = [median(ys, i) for i in range(len(ys))]
    # Kameramann: Totzone + weiches Nachziehen, Spruenge = Schnitt. Einmal
    # vorwaerts und einmal rueckwaerts gerechnet und gemittelt: die Kamera
    # bewegt sich so leicht VOR der Person statt hinterher (das ganze Video
    # ist ja vorher bekannt) — Schnitte springen in beiden Richtungen gleich.
    vx, vy = _kamera(xs, ys)
    rx, ry = _kamera(xs[::-1], ys[::-1])
    rx, ry = rx[::-1], ry[::-1]
    return [[r[0], round((vx[i] + rx[i]) / 2, 4), round((vy[i] + ry[i]) / 2, 4)]
            for i, r in enumerate(roh)]


def _kamera(xs, ys):
    """Eine Richtung: Totzone, Traegheit, Spruenge = Schnitt."""
    alpha = 1 - math.exp(-(1.0 / FPS) / TRAEGHEIT)
    cx, cy = xs[0], ys[0]
    zx, zy = cx, cy
    ox, oy = [], []
    for i in range(len(xs)):
        x, y = xs[i], ys[i]
        if i and (abs(x - xs[i - 1]) > SPRUNG or abs(y - ys[i - 1]) > SPRUNG):
            cx, cy, zx, zy = x, y, x, y            # harter Schnitt: mitspringen
        else:
            if abs(x - zx) > TOTZONE:
                zx = x - math.copysign(TOTZONE * 0.5, x - zx)
            if abs(y - zy) > TOTZONE:
                zy = y - math.copysign(TOTZONE * 0.5, y - zy)
            cx += (zx - cx) * alpha
            cy += (zy - cy) * alpha
        ox.append(cx)
        oy.append(cy)
    return ox, oy


def wert_bei(fahrt, t):
    """Kamera zur Rohzeit t (linear zwischen den Punkten)."""
    if not fahrt:
        return 0.5, 0.5
    if t <= fahrt[0][0]:
        return fahrt[0][1], fahrt[0][2]
    if t >= fahrt[-1][0]:
        return fahrt[-1][1], fahrt[-1][2]
    lo, hi = 0, len(fahrt) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if fahrt[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    a, b = fahrt[lo], fahrt[hi]
    f = (t - a[0]) / max(1e-9, b[0] - a[0])
    return a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f


def cuts_vereinen(cuts):
    aus = []
    for s, e in sorted((float(a), float(b)) for a, b in cuts):
        if aus and s <= aus[-1][1]:
            aus[-1] = (aus[-1][0], max(aus[-1][1], e))
        else:
            aus.append((s, e))
    return aus


def roh_aus_fertig(t, cuts):
    """Zeit im fertigen Video → Rohzeit (cuts vereint und sortiert)."""
    r = t
    for s, e in cuts:
        if r >= s:
            r += e - s
        else:
            break
    return r


# ------------------------------------------------------------ Projekt
def _clips(pj, projdir):
    vids = pj.get('videos') or ([pj['video']] if pj.get('video') else [])
    aus, start = [], 0.0
    for v in vids:
        p = os.path.join(projdir, v)
        if not os.path.isfile(p):
            return None
        aus.append((p, start))
        try:
            d = float(subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip())
        except ValueError:
            d = 0.0
        start += d
    return aus


def gebraucht(pj, projdir):
    """Nur noetig, wenn das Format ein ANDERES Seitenverhaeltnis hat als das
    Video und „fuellen" gewaehlt ist (sonst gibt es nichts zu verfolgen)."""
    if bildformat.einpassen(pj) != 'fuellen':
        return False
    clips = _clips(pj, projdir)
    if not clips:
        return False
    m = bildformat.quelle_masse(clips[0][0])
    if not m:
        return False
    w, h, _ = bildformat.ziel(pj)
    return abs(m[0] / m[1] - w / h) > 0.01


def spur(pj, projdir, rechnen=True):
    """Kopf-Spur des Projekts (gecacht in r_person.json) oder None."""
    clips = _clips(pj, projdir)
    if not clips or not os.path.isfile(MODELL):
        return None
    stand = {'v': VERSION, 'fps': FPS, 'dateien': [
        [os.path.basename(p), round(os.path.getmtime(p), 3), os.path.getsize(p), s]
        for p, s in clips]}
    cache = os.path.join(projdir, 'r_person.json')
    try:
        with open(cache, encoding='utf-8') as f:
            alt = json.load(f)
        if alt.get('stand') == stand:
            return alt
    except (OSError, ValueError):
        pass
    if not rechnen:
        return None
    punkte = spur_messen(clips)
    erg = {'stand': stand, 'fps': FPS, 'quelle': list(bildformat.quelle_masse(clips[0][0])),
           'punkte': punkte}
    with open(cache, 'w', encoding='utf-8') as f:
        json.dump(erg, f)
    return erg


def fahrt_fuer(pj, projdir, rechnen=True):
    """Fertige Kamerafahrt fuer das aktuelle Format (Rohzeit) oder None."""
    s = spur(pj, projdir, rechnen)
    if not s or not s.get('punkte'):
        return None
    w, h, _ = bildformat.ziel(pj)
    return kamerafahrt(s['punkte'], tuple(s['quelle']), (w, h))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    pfad = os.path.abspath(sys.argv[1])
    if os.path.isdir(pfad):
        pfad = os.path.join(pfad, 'projekt.json')
    projdir = os.path.dirname(pfad)
    with open(pfad, encoding='utf-8-sig') as f:
        pj = json.load(f)
    import time
    t0 = time.time()
    s = spur(pj, projdir)
    if not s:
        print('Keine Spur: Video oder Modell fehlt.')
        return 1
    p = s['punkte']
    mit = sum(1 for x in p if x[1] is not None)
    print('OK Person gefunden in {} von {} Bildern ({:.0f} %) · {:.1f} s'.format(
        mit, len(p), 100 * mit / max(1, len(p)), time.time() - t0))
    return 0


if __name__ == '__main__':
    sys.exit(main())
