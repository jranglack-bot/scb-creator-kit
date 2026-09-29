"""Schneidet ein Feld aus einem 3x3-Storyboard und rechnet es auf Kling-Größe hoch.

Gebraucht für den Kling-Weg im Skill paper-cut-motion: Kling 3.0 nimmt kein
Referenzbild, nur ein Start- und ein Endbild. Das ganze Storyboard als
Startbild würde das Raster ins Video bringen, deshalb geht nur Feld 1 hinein.

Aufruf:
    <python> feld_ausschneiden.py <storyboard.png> <ziel.png> [--feld 1]

Die weißen Trennlinien findet das Skript selbst. Die Zeilen des Rasters sind
durchgehende waagrechte Linien. Die senkrechten Linien sucht es je Zeile
getrennt, weil GPT Image 2 die Spalten nicht in jeder Zeile an dieselbe Stelle
legt (gemessen am 17.09.2026: oben bei 263 px, darunter bei 238 px). Findet es
keine Linien, nimmt es das Drittel mit Sicherheitsrand und sagt das.

Braucht nur Python und ffmpeg, keine Zusatzpakete.
"""
import argparse
import json
import subprocess
import sys

HELL = 200      # ab diesem Wert in allen drei Farbkanälen zählt ein Pixel als weiß
ANTEIL = 0.85   # so viel einer Linie muss weiß sein, damit sie als Trennlinie zählt
RAND = 0.015    # Abstand zur Trennlinie, Anteil der Feldgröße
ZIELE = {"9:16": (720, 1280), "16:9": (1280, 720), "1:1": (720, 720)}


def groesse(pfad):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", pfad],
        capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"]


def weiss_maske(pfad, w, h):
    """Ein Byte je Pixel: 1 heißt weiß, 0 heißt Motiv."""
    roh = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", pfad, "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    n = w * h
    if len(roh) < 3 * n:
        sys.exit(f"Bild nicht lesbar: {pfad}")
    tabelle = bytes(1 if i >= HELL else 0 for i in range(256))
    m = roh[:3 * n].translate(tabelle)
    r, g, b = (int.from_bytes(m[k::3], "big") for k in range(3))
    return (r & g & b).to_bytes(n, "big")


def laeufe(anteile):
    """Zusammenhängende Bereiche [a, b), in denen die Linie fast ganz weiß ist."""
    out, start = [], None
    for i, v in enumerate(anteile):
        if v >= ANTEIL and start is None:
            start = i
        elif v < ANTEIL and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(anteile)))
    return out


def felder(anteile):
    """Grenzen der drei Felder entlang einer Achse, oder None, wenn unklar."""
    n = len(anteile)
    runs = laeufe(anteile)
    anfang, ende = 0, n
    for a, b in runs:
        if a == 0:
            anfang = b
        if b == n:
            ende = a
    spanne = ende - anfang
    if spanne < 0.5 * n:
        return None
    linien = []
    for k in (1, 2):
        ziel = anfang + spanne * k / 3
        nah = [(a, b) for a, b in runs
               if a > anfang and b < ende and abs((a + b) / 2 - ziel) < 0.12 * spanne]
        if not nah:
            return None
        linien.append(min(nah, key=lambda r: abs((r[0] + r[1]) / 2 - ziel)))
    (a1, b1), (a2, b2) = linien
    teile = [(anfang, a1), (b1, a2), (b2, ende)]
    if any(not 0.2 * n <= b - a <= 0.45 * n for a, b in teile):
        return None
    return teile


def drittel(n):
    """Ersatz, wenn keine Linien erkannt werden: gleich große Drittel."""
    d = n / 3
    return [(round(i * d), round((i + 1) * d)) for i in range(3)]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Ein Feld aus einem 3x3-Storyboard ausschneiden")
    ap.add_argument("storyboard")
    ap.add_argument("ziel")
    ap.add_argument("--feld", type=int, default=1, choices=range(1, 10),
                    help="Feld 1 bis 9, von links oben zeilenweise gezählt (Standard: 1)")
    a = ap.parse_args()

    w, h = groesse(a.storyboard)
    weiss = weiss_maske(a.storyboard, w, h)
    hinweise = []

    zeilen = [weiss.count(1, y * w, (y + 1) * w) / w for y in range(h)]
    reihen = felder(zeilen)
    if reihen is None:
        reihen = drittel(h)
        hinweise.append("keine waagrechten Trennlinien erkannt")
    zeile, spalte = divmod(a.feld - 1, 3)
    y0, y1 = reihen[zeile]

    spalten = [weiss[y0 * w + x: y1 * w: w].count(1) / (y1 - y0) for x in range(w)]
    teile = felder(spalten)
    if teile is None:
        teile = drittel(w)
        hinweise.append("keine senkrechten Trennlinien erkannt")
    x0, x1 = teile[spalte]

    # Abstand zu den Linien, beim Ersatz mit Dritteln etwas mehr
    anteil = 0.04 if hinweise else RAND
    dx, dy = max(3, round(anteil * (x1 - x0))), max(3, round(anteil * (y1 - y0)))
    x0, x1, y0, y1 = x0 + dx, x1 - dx, y0 + dy, y1 - dy

    # Zielformat aus dem Storyboard ableiten und mittig darauf zuschneiden
    fmt = "9:16" if w < 0.9 * h else ("16:9" if w > 1.1 * h else "1:1")
    tw, th = ZIELE[fmt]
    bw, bh = x1 - x0, y1 - y0
    if bw / bh > tw / th:
        neu = round(bh * tw / th)
        x0 += (bw - neu) // 2
        bw = neu
    else:
        neu = round(bw * th / tw)
        y0 += (bh - neu) // 2
        bh = neu

    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", a.storyboard,
         "-vf", f"crop={bw}:{bh}:{x0}:{y0},scale={tw}:{th}:flags=lanczos",
         "-frames:v", "1", "-update", "1", a.ziel],
        check=True)
    print(f"Feld {a.feld}: {bw}x{bh} px ab x={x0}, y={y0}, hochgerechnet auf {tw}x{th} ({fmt}): {a.ziel}")
    if hinweise:
        print("ACHTUNG: " + " und ".join(hinweise) + ". Drittel mit Rand genommen, "
              "Ausschnitt ansehen, bevor er zu Kling geht.")


if __name__ == "__main__":
    main()
