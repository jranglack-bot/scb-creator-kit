"""Stellt die Person in einem Video frei - fuer den 'Text hinter Subjekt'-Effekt.

    <python> freistellen.py video.mp4 cutout [von_sek] [bis_sek] [optionen]

Erzeugt zwei Dateien, weil kein Format beides kann:

    cutout.mkv    ffv1 mit Alpha, verlustfrei - DAS liest ffmpeg (prolook)
    cutout.webm   VP9 mit Alpha               - DAS liest der Browser

Die Bilder werden direkt an ffmpeg durchgereicht, nicht als Einzelbilder auf
die Platte geschrieben. Das ist deutlich schneller: das Schreiben war der
Flaschenhals, nicht die Erkennung.


ZWEI VERFAHREN
--------------

  rvm         Robust Video Matting. Echter Alphakanal in voller Aufloesung,
              rekurrent ueber die Zeit (das Netz kennt das vorherige Bild).
              Braucht keine kuenstliche Glaettung und erzeugt deshalb auch
              keine Schlieren. Rechnet rund 1 Bild/s auf der CPU.
              Braucht: onnxruntime + models/rvm_mobilenetv3_fp32.onnx (14 MB)

  mediapipe   Selfie Segmenter. Sehr schnell (rund 6 Bilder/s), aber die Maske
              entsteht in 256x256 und wird hochgezogen, und jedes Bild wird
              einzeln entschieden. Gegen das Flackern hilft nur die zeitliche
              Glaettung - die bei schnellen Bewegungen die Maske nachziehen
              laesst. Solange nichts hinter der Person liegt, sieht man das
              nicht; mit Grafik darunter erscheint eine Geisterkopie.

Ohne Angabe wird rvm genommen, wenn es verfuegbar ist, sonst mediapipe.

FAUSTREGEL: liegt Grafik hinter der Person, immer rvm. mediapipe reicht, wenn
die Freistellung nur weichgezeichnet oder eingefaerbt wird.


ABSCHNITT STATT GANZES VIDEO
----------------------------

Mit von/bis wird nur dieser Bereich freigestellt. Weil rvm gut eine Sekunde
pro Bild braucht, lohnt sich das sehr: liegt die Grafik nur vier Sekunden lang
hinter der Person, sind das 130 statt 600 Bilder. Die Ausgabe beginnt dann bei
von_sek - im overlays-Eintrag entsprechend "start" setzen.


OPTIONEN
--------

    --modell rvm|mediapipe   Verfahren erzwingen
    --glaettung 0.55         nur mediapipe: 0 = aus, 1 = einfrieren
    --erosion N              Matte hereinziehen (Standard: rvm 0, mediapipe 2)
    --weich 5                weiche Kante in Pixeln (ungerade Zahl)
    --farbe original|fgr     nur rvm: original = Pixel des Quellbilds
                             (Standard; artefaktfrei ueber demselben Video),
                             fgr = RVM-Farbschaetzung fuer fremde Hintergruende
    --lowcut 0.12            nur rvm: schwache Fehlmaskierung verwerfen
    --richtung vor|beide     nur rvm: "beide" rechnet zusaetzlich einen
                             Rueckwaertslauf und vereinigt beide Masken.
                             RVM schaut nur nach hinten und verpasst deshalb
                             die VORDERkante schneller Bewegungen (Arm
                             verschwindet fuer Bilder) - rueckwaerts ist die
                             Vorderkante eine Hinterkante. Doppelte Rechenzeit.
    --bruecke 0              nur bei --richtung beide: zusaetzlich N Nachbar-
                             bilder je Seite einblenden (Maximum). Schliesst
                             letzte Einzelbild-Aussetzer, macht die Maske bei
                             schneller Bewegung aber sichtbar BREITER als die
                             Person - Vorsicht vor grossen Flaechen dahinter.

Laeuft auf der CPU, ohne Konto und ohne Netzzugriff (Modelle liegen lokal).
Die Zusatzpakete braucht NUR dieses Script - wer das Kit ohne diesen Effekt
nutzt, braucht davon nichts.
"""

import os
import subprocess
import sys
import time

import cv2
import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))


def _modellpfad(name: str) -> str:
    """Modelle liegen je nach Installation neben oder ueber dem Script."""
    for kandidat in (os.path.join(os.path.dirname(HIER), "models", name),
                     os.path.join(HIER, "models", name)):
        if os.path.isfile(kandidat):
            return kandidat
    return ""


MODELL_MP = _modellpfad("selfie_segmenter.tflite")
MODELL_RVM = _modellpfad("rvm_mobilenetv3_fp32.onnx")

# Zeitliche Glaettung (nur mediapipe): 0 = aus, 1 = einfrieren. Daempft das
# Kantenflimmern, laesst die Maske aber bei schnellen Bewegungen nachziehen.
GLAETTUNG = 0.55
# Matte leicht hereinziehen, damit kein Hintergrundsaum stehen bleibt.
EROSION = 2
# Weiche Kante in Pixeln (ungerade Zahl).
WEICHZEICHNEN = 5
# Interne Rechenaufloesung von rvm. Empfohlen ist, dass die verkleinerte Seite
# zwischen 256 und 512 px liegt - bei 1080 Breite sind 0.4 genau 432 px.
RVM_VERKLEINERUNG = 0.4


def rvm_verfuegbar() -> bool:
    if not MODELL_RVM:
        return False
    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        return False
    return True


def argumente(argv: list[str]) -> dict:
    """Stellungsargumente und --optionen trennen."""
    pos, opt = [], {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            opt[a[2:]] = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        else:
            pos.append(a)
            i += 1
    return {"pos": pos, "opt": opt}


def ffmpeg_start(breite: int, hoehe: int, fps: float, mkv: str, webm: str):
    """Ein Prozess, zwei Ausgaben - die Erkennung laeuft nur einmal.

    bgra passt direkt zu OpenCVs Kanalreihenfolge, spart eine Umrechnung.
    Beim webm ist crf 22 wichtig: bei hoeheren Werten wird der ALPHAkanal
    matschig, und die Browservorschau sieht schlechter aus als das Ergebnis.
    """
    return subprocess.Popen(
        [
            "ffmpeg", "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "bgra",
            "-s", f"{breite}x{hoehe}", "-r", f"{fps:g}", "-i", "-",
            # fuer ffmpeg lesbar: ffv1 ist verlustfrei und deutlich kompakter
            # als ProRes 4444 (gemessen 205 MB statt 632 MB)
            "-c:v", "ffv1", "-level", "3", "-pix_fmt", "yuva420p",
            "-threads", "8", mkv,
            # fuer den Browser lesbar
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
            "-b:v", "0", "-crf", "22", "-row-mt", "1",
            "-cpu-used", "8", "-deadline", "good", webm,
        ],
        stdin=subprocess.PIPE,
    )


def main() -> int:
    args = argumente(sys.argv[1:])
    if len(args["pos"]) < 2:
        print(__doc__)
        return 2

    quelle, basis = args["pos"][0], args["pos"][1]
    von = float(args["pos"][2]) if len(args["pos"]) > 2 else 0.0
    bis = float(args["pos"][3]) if len(args["pos"]) > 3 else float("inf")

    glaettung = float(args["opt"].get("glaettung", GLAETTUNG))
    weich = int(args["opt"].get("weich", WEICHZEICHNEN))

    modell = args["opt"].get("modell") or ("rvm" if rvm_verfuegbar() else "mediapipe")
    # Erosion frisst echte Kanten an. Sie ist ein Gegenmittel fuer den
    # Saum des MediaPipe-Segmentierers - bei rvm standardmaessig AUS.
    erosion = int(args["opt"].get("erosion", 0 if modell == "rvm" else EROSION))
    # rvm: Farbe der Ebene. "original" = Pixel des Quellbilds - ueber dem
    # (identischen) Video artefaktfrei, halbtransparente Kanten mischen
    # echten Arm mit Grafik statt einer GESCHAETZTEN Farbe (keine Geister).
    # "fgr" = RVM-Schaetzung, nur sinnvoll vor komplett fremdem Hintergrund.
    farbe = args["opt"].get("farbe", "original")
    # Schwache Fehlmaskierung (nachziehende Reste bei schnellen Bewegungen)
    # verwerfen: alles unter diesem Alpha-Wert faellt auf 0.
    lowcut = float(args["opt"].get("lowcut", 0.12))
    richtung = args["opt"].get("richtung", "vor")
    bruecke = int(args["opt"].get("bruecke", 0))
    if modell == "rvm" and not rvm_verfuegbar():
        print("rvm nicht verfuegbar. Es fehlt:")
        if not MODELL_RVM:
            print("  models/rvm_mobilenetv3_fp32.onnx  (14 MB, Robust Video Matting)")
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            print("  onnxruntime  ->  <python> -m pip install onnxruntime")
        return 1
    if modell == "mediapipe" and not MODELL_MP:
        print("models/selfie_segmenter.tflite fehlt")
        return 1

    cap = cv2.VideoCapture(quelle)
    if not cap.isOpened():
        print(f"Video nicht lesbar: {quelle}")
        return 1

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    breite = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    hoehe = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    gesamt = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    mkv, webm = basis + ".mkv", basis + ".webm"
    for p in (mkv, webm):
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)

    # Der rekurrente Zustand von rvm braucht ein paar Bilder Anlauf. Beginnt
    # der Abschnitt spaeter, rechnen wir kurz davor mit, schreiben aber nichts.
    anlauf = 12 if modell == "rvm" else 0
    erstes = max(0, int(round(von * fps)))
    letztes = int(round(bis * fps)) if bis != float("inf") else 10 ** 9
    ab = max(0, erstes - anlauf)
    zu_schreiben = min(letztes, gesamt or letztes) - erstes

    print("Verfahren: " + modell
          + (f" (Glaettung {glaettung})" if modell == "mediapipe"
             else f" ({farbe}, Low-Cut {lowcut:g}, Richtung {richtung})"))
    if modell == "mediapipe":
        print("  Hinweis: liegt Grafik HINTER der Person, besser --modell rvm -")
        print("  die Glaettung zieht sonst bei schnellen Bewegungen Schlieren.")

    ffmpeg = ffmpeg_start(breite, hoehe, fps, mkv, webm)
    kern = np.ones((3, 3), np.uint8)
    n, i = 0, 0
    start = time.time()

    try:
        if modell == "rvm" and richtung == "beide":
            erzeuger = _rvm_masken_beide(cap, ab, erstes, letztes,
                                         farbe, lowcut, bruecke)
        elif modell == "rvm":
            erzeuger = _rvm_masken(cap, ab, letztes, farbe, lowcut)
        else:
            erzeuger = _mediapipe_masken(cap, ab, letztes, glaettung)
        for nr, bgr, a8 in erzeuger:
            if erosion > 0:
                a8 = cv2.erode(a8, kern, iterations=erosion)
            if weich > 1:
                a8 = cv2.GaussianBlur(a8, (weich, weich), 0)

            # Vollstaendig transparente Bereiche auf Schwarz setzen: sie sind
            # unsichtbar, kosten den Codec aber sonst volle Bandbreite.
            # Randpixel behalten ihre Farbe, sonst gaebe es dunkle Saeume.
            bgr[a8 == 0] = 0

            if nr < erstes:
                continue    # Anlauf: nur Zustand aufbauen, nichts schreiben

            ffmpeg.stdin.write(np.dstack([bgr, a8]).tobytes())
            n += 1
            if n % 30 == 0:
                v = n / max(time.time() - start, 0.01)
                rest = (zu_schreiben - n) / max(v, 0.01)
                print(f"  {n}/{zu_schreiben}  ({v:.1f} B/s, noch ~{rest:.0f}s)",
                      flush=True)
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
    if von > 0:
        print(f"  Ausgabe beginnt bei {von}s -> im overlays-Eintrag "
              f'"start": {von} setzen')
    for p in (mkv, webm):
        print(f"  {p}  ({os.path.getsize(p) / 1024 / 1024:.1f} MB)")
    return 0


def _rvm_sitzung():
    """DirectML wenn vorhanden (gemessen ~2x schneller, identisches Ergebnis),
    sonst - und auf macOS - ganz normal die CPU."""
    import onnxruntime as ort

    opt = ort.SessionOptions()
    opt.intra_op_num_threads = max(1, (os.cpu_count() or 4) - 1)
    anbieter: list = ["CPUExecutionProvider"]
    if "DmlExecutionProvider" in ort.get_available_providers():
        anbieter = [("DmlExecutionProvider", {"device_id": 0}),
                    "CPUExecutionProvider"]
    try:
        sitzung = ort.InferenceSession(MODELL_RVM, opt, providers=anbieter)
    except Exception:  # noqa: BLE001 - im Zweifel zuverlaessig auf CPU
        sitzung = ort.InferenceSession(MODELL_RVM, opt,
                                       providers=["CPUExecutionProvider"])
    print(f"  Recheneinheit: {sitzung.get_providers()[0]}", flush=True)
    return sitzung


def _rvm_alpha_lauf(sitzung, bilder):
    """EIN rekurrenter Durchlauf: liefert je (nr, bild) das rohe Alpha 0..1
    plus fgr. bilder = Iterable von (nr, bgr-Frame) in Laufrichtung."""
    zustand = {f"r{k}i": np.zeros((1, 1, 1, 1), np.float32) for k in range(1, 5)}
    verkleinerung = np.array([RVM_VERKLEINERUNG], np.float32)
    k = 0
    for nr, bild in bilder:
        rgb = cv2.cvtColor(bild, cv2.COLOR_BGR2RGB)
        src = rgb.transpose(2, 0, 1)[None].astype(np.float32) / 255.0
        fgr, pha, *neu = sitzung.run(
            ["fgr", "pha", "r1o", "r2o", "r3o", "r4o"],
            {"src": src, "downsample_ratio": verkleinerung, **zustand},
        )
        zustand = {f"r{j}i": neu[j - 1] for j in range(1, 5)}
        k += 1
        if k % 30 == 0:
            print(f"    {k} Bilder ...", flush=True)
        yield nr, bild, pha[0, 0], fgr


def _fertig_machen(nr, bild, a, fgr, farbe, lowcut):
    """Alpha nachbehandeln + Farbebene waehlen -> (nr, bgr, alpha8)."""
    if lowcut > 0:
        # Nachziehende Maskenreste (Geister) verwerfen, Rest zurueckspreizen.
        a = np.clip((a - lowcut) / (1.0 - lowcut), 0.0, 1.0)
    a8 = np.clip(a * 255.0, 0, 255).astype(np.uint8)
    if farbe == "fgr" and fgr is not None:
        # RVM-Farbschaetzung: nur vor komplett fremdem Hintergrund noetig.
        vorder = np.clip(fgr[0].transpose(1, 2, 0) * 255.0, 0, 255)
        return nr, cv2.cvtColor(vorder.astype(np.uint8), cv2.COLOR_RGB2BGR), a8
    # Originalpixel: liegt die Ebene ueber demselben Video, mischen
    # halbtransparente Kanten echten Inhalt mit der Grafik darunter -
    # sieht aus wie echte Bewegungsunschaerfe, nie wie ein Geist.
    return nr, bild, a8


def _rvm_masken(cap, ab: int, letztes: int, farbe: str, lowcut: float):
    """Vorwaertslauf direkt vom Videostrom - Robust Video Matting."""
    def strom():
        i = 0
        while True:
            ok, bild = cap.read()
            if not ok:
                break
            nr, i = i, i + 1
            if nr < ab:
                continue
            if nr >= letztes:
                break
            yield nr, bild

    sitzung = _rvm_sitzung()
    for nr, bild, a, fgr in _rvm_alpha_lauf(sitzung, strom()):
        yield _fertig_machen(nr, bild, a, fgr, farbe, lowcut)


def _rvm_masken_beide(cap, ab: int, erstes: int, letztes: int,
                      farbe: str, lowcut: float, bruecke: int = 0):
    """Vor- UND Rueckwaertslauf, Masken vereinigt, +-1 Bild ueberbrueckt.

    RVM ist kausal - die Maske hinkt der VORDERkante schneller Bewegungen
    hinterher (ein hereinschiessender Arm ist fuer das Netz noch "nicht da").
    Rueckwaerts gerechnet ist dieselbe Kante eine Hinterkante. Das Maximum
    beider Laeufe deckt beide Seiten ab; die zeitliche Brueckung schliesst
    Einzelbild-Aussetzer. Die Abschnitts-Frames liegen dafuer einmal im
    Speicher - gedacht fuer ABSCHNITTE (bis ~15 s), nicht ganze Videos.
    Impliziert farbe=original (fgr wird nicht vorgehalten).
    """
    ANLAUF = 12
    ende = letztes + ANLAUF          # Anlauf fuer den Rueckwaertslauf
    frames = {}
    i = 0
    while True:
        ok, bild = cap.read()
        if not ok:
            break
        nr, i = i, i + 1
        if nr < ab:
            continue
        if nr >= ende:
            break
        frames[nr] = bild
    nummern = sorted(n for n in frames if erstes <= n < letztes)
    if not nummern:
        return

    sitzung = _rvm_sitzung()
    alphas = {}
    print("  Vorwaertslauf ...", flush=True)
    vor = ((n, frames[n]) for n in sorted(frames) if n < letztes)
    for nr, _b, a, _f in _rvm_alpha_lauf(sitzung, vor):
        if nr >= erstes:
            alphas[nr] = a
    print("  Rueckwaertslauf ...", flush=True)
    rueck = ((n, frames[n]) for n in sorted(frames, reverse=True))
    for nr, _b, a, _f in _rvm_alpha_lauf(sitzung, rueck):
        if erstes <= nr < letztes:
            alphas[nr] = np.maximum(alphas[nr], a)

    for nr in nummern:
        a = alphas[nr]
        for nb in range(nr - bruecke, nr + bruecke + 1):
            if nb != nr and nb in alphas:
                a = np.maximum(a, alphas[nb])
        yield _fertig_machen(nr, frames[nr], a, None, farbe, lowcut)


def _mediapipe_masken(cap, ab: int, letztes: int, glaettung: float):
    """Liefert (bildnummer, bgr, alpha8) je Bild - MediaPipe Selfie Segmenter."""
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    optionen = vision.ImageSegmenterOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODELL_MP),
        running_mode=vision.RunningMode.IMAGE,
        output_category_mask=False,
        output_confidence_masks=True,
    )

    vorher = None
    i = 0
    with vision.ImageSegmenter.create_from_options(optionen) as segmenter:
        while True:
            ok, bild = cap.read()
            if not ok:
                break
            nr, i = i, i + 1
            if nr < ab:
                continue
            if nr >= letztes:
                break

            rgb = cv2.cvtColor(bild, cv2.COLOR_BGR2RGB)
            ergebnis = segmenter.segment(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))

            masken = ergebnis.confidence_masks
            # Zwei Masken = [Hintergrund, Person]; eine = direkt die Person.
            maske = masken[1] if len(masken) > 1 else masken[0]
            # WICHTIG: numpy_view() zeigt in MediaPipes Speicher, der beim
            # naechsten Aufruf freigegeben wird - hier zwingend kopieren.
            alpha = np.array(maske.numpy_view(), dtype=np.float32, copy=True)

            if alpha.shape[:2] != bild.shape[:2]:
                alpha = cv2.resize(alpha, (bild.shape[1], bild.shape[0]),
                                   interpolation=cv2.INTER_LINEAR)

            if vorher is not None and glaettung > 0:
                alpha = glaettung * vorher + (1.0 - glaettung) * alpha
            vorher = alpha

            yield nr, bild, np.clip(alpha * 255.0, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    sys.exit(main())
