"""Stellt die Person in einem Video frei - fuer den 'Text hinter Subjekt'-Effekt.

    python freistellen.py video.mp4 cutout

Erzeugt zwei Dateien, weil kein Format beides kann:

    cutout.mkv    ffv1 mit Alpha, verlustfrei - DAS liest ffmpeg (prolook)
    cutout.webm   VP9 mit Alpha               - DAS liest der Browser

Die Bilder werden direkt an ffmpeg durchgereicht, nicht als Einzelbilder auf
die Platte geschrieben. Das ist deutlich schneller: das Schreiben war der
Flaschenhals, nicht die Erkennung.

Laeuft auf der CPU, ohne Konto und ohne Netzzugriff (Modell liegt lokal).
Braucht mediapipe, opencv-python und numpy - aber NUR dieses Script. Wer das
Kit ohne diesen Effekt nutzt, braucht davon nichts.
"""

import os
import subprocess
import sys
import time

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

HIER = os.path.dirname(os.path.abspath(__file__))
MODELL = os.path.join(os.path.dirname(HIER), "models", "selfie_segmenter.tflite")
if not os.path.isfile(MODELL):  # im Kit liegt das Modell neben dem Script
    MODELL = os.path.join(HIER, "models", "selfie_segmenter.tflite")

# Zeitliche Glaettung: 0 = aus, 1 = einfrieren. Daempft das Kantenflimmern,
# das entsteht, weil jedes Bild einzeln segmentiert wird.
GLAETTUNG = 0.55
# Matte leicht hereinziehen, damit kein Hintergrundsaum stehen bleibt.
EROSION = 2
# Weiche Kante in Pixeln (ungerade Zahl).
WEICHZEICHNEN = 5


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2

    quelle, basis = sys.argv[1], sys.argv[2]
    if not os.path.isfile(MODELL):
        print(f"Modell fehlt: {MODELL}")
        return 1

    cap = cv2.VideoCapture(quelle)
    if not cap.isOpened():
        print(f"Video nicht lesbar: {quelle}")
        return 1

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    breite = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    hoehe = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    gesamt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    mkv = basis + ".mkv"
    webm = basis + ".webm"
    for p in (mkv, webm):
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)

    # Ein ffmpeg-Prozess, zwei Ausgaben - die Segmentierung laeuft nur einmal.
    # bgra passt direkt zu OpenCVs Kanalreihenfolge, spart eine Umrechnung.
    ffmpeg = subprocess.Popen(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "bgra",
            "-s", f"{breite}x{hoehe}", "-r", f"{fps:g}", "-i", "-",
            # fuer ffmpeg lesbar: ffv1 ist verlustfrei und deutlich
            # kompakter als ProRes 4444 (gemessen 205 MB statt 632 MB)
            "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuva420p",
            "-threads", "8", mkv,
            # fuer den Browser lesbar
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
            "-b:v", "0", "-crf", "32", "-row-mt", "1",
            "-cpu-used", "8", "-deadline", "realtime", webm,
        ],
        stdin=subprocess.PIPE,
    )

    optionen = vision.ImageSegmenterOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODELL),
        running_mode=vision.RunningMode.IMAGE,
        output_category_mask=False,
        output_confidence_masks=True,
    )

    kern = np.ones((3, 3), np.uint8)
    vorher = None
    n = 0
    start = time.time()

    try:
        with vision.ImageSegmenter.create_from_options(optionen) as segmenter:
            while True:
                ok, bild = cap.read()
                if not ok:
                    break

                rgb = cv2.cvtColor(bild, cv2.COLOR_BGR2RGB)
                mp_bild = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                ergebnis = segmenter.segment(mp_bild)

                masken = ergebnis.confidence_masks
                # Zwei Masken = [Hintergrund, Person]; eine = direkt die Person.
                maske = masken[1] if len(masken) > 1 else masken[0]
                # WICHTIG: numpy_view() zeigt in MediaPipes Speicher, der beim
                # naechsten Aufruf freigegeben wird - hier zwingend kopieren.
                alpha = np.array(maske.numpy_view(), dtype=np.float32, copy=True)

                if alpha.shape[:2] != bild.shape[:2]:
                    alpha = cv2.resize(
                        alpha, (bild.shape[1], bild.shape[0]),
                        interpolation=cv2.INTER_LINEAR,
                    )

                # Zeitliche Glaettung gegen Flimmern
                if vorher is not None:
                    alpha = GLAETTUNG * vorher + (1.0 - GLAETTUNG) * alpha
                vorher = alpha

                a8 = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
                if EROSION > 0:
                    a8 = cv2.erode(a8, kern, iterations=EROSION)
                if WEICHZEICHNEN > 1:
                    a8 = cv2.GaussianBlur(a8, (WEICHZEICHNEN, WEICHZEICHNEN), 0)

                # Vollstaendig transparente Bereiche auf Schwarz setzen: sie
                # sind unsichtbar, kosten den Codec aber sonst volle Bandbreite.
                # Randpixel behalten ihre Farbe, sonst gaebe es dunkle Saeume.
                bild[a8 == 0] = 0

                bgra = np.dstack([bild, a8])
                ffmpeg.stdin.write(bgra.tobytes())

                n += 1
                if gesamt and n % 60 == 0:
                    print(f"  {n}/{gesamt}", flush=True)
    finally:
        cap.release()
        if ffmpeg.stdin:
            ffmpeg.stdin.close()
        ffmpeg.wait()

    if ffmpeg.returncode != 0:
        print(f"ffmpeg ist fehlgeschlagen (Exit {ffmpeg.returncode})")
        return 1

    dauer = time.time() - start
    print(f"Fertig: {n} Bilder in {dauer:.1f}s ({n / max(dauer, 0.01):.1f} Bilder/s)")
    for p in (mkv, webm):
        print(f"  {p}  ({os.path.getsize(p) / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
