#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Misst EINMALIG, wie schnell dieser Rechner Video verarbeitet.

Warum: Der Ablauf soll sich an die Maschine anpassen, statt zu raten.
Auf einem 15-Watt-Laptop ist die Freistellung der teure Schritt und
gehoert auf wenige Sekunden begrenzt; auf einem starken Rechner darf
grosszuegiger gerechnet werden. Ohne Messung faellt das erst beim
ersten Video auf - und dann kostet es Wartezeit (real: >20 Minuten).

    python tempo_check.py            # messen und speichern
    python tempo_check.py --zeigen   # gespeichertes Ergebnis anzeigen

Ergebnis landet in ~/.scb-creator-kit/tempo.json und wird von den
Video-Skills gelesen. Dauer der Messung: etwa 30-60 Sekunden.

Exit 0 = Messung steht, Exit 1 = ffmpeg fehlt (vorher install_tools.py).
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ZIEL = Path.home() / ".scb-creator-kit" / "tempo.json"
# Kandidaten in der Reihenfolge, in der sie geprueft werden.
HW_ENCODER = ["h264_videotoolbox", "h264_qsv", "h264_nvenc", "h264_amf"]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def ffmpeg_da():
    return bool(shutil.which("ffmpeg"))


def encoder_liste():
    r = run(["ffmpeg", "-hide_banner", "-encoders"])
    return r.stdout or ""


def testvideo(pfad, sekunden=6, breite=1080, hoehe=1920):
    """Erzeugt ein neutrales Testvideo in Reel-Groesse."""
    run(["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i",
         "testsrc2=size={}x{}:rate=30:duration={}".format(
             breite, hoehe, sekunden),
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         pfad])
    return os.path.exists(pfad)


def messe_encode(quelle, args, ziel):
    """Sekunden fuer einen Durchlauf - oder None bei Fehler."""
    start = time.time()
    r = run(["ffmpeg", "-v", "error", "-y", "-i", quelle]
            + args + ["-an", ziel])
    if r.returncode != 0 or not os.path.exists(ziel):
        return None
    dauer = time.time() - start
    os.remove(ziel)
    return round(dauer, 2)


def pruefe_freistellung():
    """Was steht fuer die Freistellung bereit? (RVM > MediaPipe)"""
    info = {"onnxruntime": None, "anbieter": [], "mediapipe": False}
    try:
        import onnxruntime as ort
        info["onnxruntime"] = ort.__version__
        info["anbieter"] = list(ort.get_available_providers())
    except Exception:
        pass
    try:
        import mediapipe          # noqa: F401
        info["mediapipe"] = True
    except Exception:
        pass
    return info


def main():
    p = argparse.ArgumentParser(description="Video-Tempo dieses Rechners messen")
    p.add_argument("--zeigen", action="store_true",
                   help="gespeicherte Messung ausgeben, nicht neu messen")
    a = p.parse_args()

    if a.zeigen:
        if not ZIEL.exists():
            print("Noch keine Messung vorhanden. Einmal ohne --zeigen laufen lassen.")
            return 1
        print(ZIEL.read_text(encoding="utf-8"))
        return 0

    if not ffmpeg_da():
        print("FEHLER: ffmpeg fehlt. Zuerst: install_tools.py ffmpeg")
        return 1

    print("Messe die Videoleistung dieses Rechners (etwa 30-60 Sekunden) ...")
    ergebnis = {
        "system": platform.system(),
        "maschine": platform.machine(),
        "kerne": os.cpu_count() or 0,
    }
    print("  System: {} / {} / {} Kerne".format(
        ergebnis["system"], ergebnis["maschine"], ergebnis["kerne"]))

    tmp = tempfile.mkdtemp(prefix="scb_tempo_")
    quelle = os.path.join(tmp, "quelle.mp4")
    try:
        if not testvideo(quelle):
            print("FEHLER: Konnte kein Testvideo erzeugen.")
            return 1

        # --- CPU-Referenz -------------------------------------------------
        cpu = messe_encode(quelle,
                           ["-c:v", "libx264", "-preset", "medium", "-crf", "20"],
                           os.path.join(tmp, "cpu.mp4"))
        ergebnis["cpu_sek"] = cpu
        print("  CPU (x264 medium): {} s fuer 6 s Video".format(cpu))

        # --- Hardware-Encoder ---------------------------------------------
        vorhanden = encoder_liste()
        bester, beste_zeit = None, None
        for enc in HW_ENCODER:
            if enc not in vorhanden:
                continue
            args = ["-c:v", enc]
            if enc == "h264_qsv":
                args += ["-global_quality", "20"]
            elif enc == "h264_nvenc":
                args += ["-cq", "20", "-preset", "p5"]
            elif enc == "h264_videotoolbox":
                args += ["-b:v", "8M"]
            t = messe_encode(quelle, args, os.path.join(tmp, "hw.mp4"))
            if t is not None and (beste_zeit is None or t < beste_zeit):
                bester, beste_zeit = enc, t
            print("  {}: {}".format(enc, "{} s".format(t) if t else "nicht nutzbar"))
        ergebnis["hw_encoder"] = bester
        ergebnis["hw_sek"] = beste_zeit
        if bester and cpu and beste_zeit:
            ergebnis["hw_faktor"] = round(cpu / beste_zeit, 2)
            print("  -> Hardware-Encoder {} ist {}x schneller als die CPU"
                  .format(bester, ergebnis["hw_faktor"]))
        else:
            ergebnis["hw_faktor"] = None
            print("  -> Kein nutzbarer Hardware-Encoder, es rechnet die CPU")

        # --- Freistellung --------------------------------------------------
        fs = pruefe_freistellung()
        ergebnis["freistellung"] = fs
        if fs["onnxruntime"]:
            gpu = [x for x in fs["anbieter"] if x != "CPUExecutionProvider"]
            print("  Freistellung: RVM bereit (onnxruntime {}{})".format(
                fs["onnxruntime"],
                ", GPU: " + gpu[0] if gpu else ", nur CPU"))
        elif fs["mediapipe"]:
            print("  Freistellung: nur MediaPipe - flackert bei Grafik "
                  "dahinter. Besser: onnxruntime nachinstallieren.")
        else:
            print("  Freistellung: nicht eingerichtet (nur noetig fuer "
                  "'Text hinter mir').")

        # --- Empfehlungen fuer den Ablauf ----------------------------------
        # Grobe Klasse: wie lange braucht der Rechner fuer 6 s Video?
        mass = beste_zeit or cpu or 99
        if mass <= 2:
            klasse, sek = "schnell", 20
        elif mass <= 6:
            klasse, sek = "mittel", 10
        else:
            klasse, sek = "langsam", 5
        ergebnis["klasse"] = klasse
        ergebnis["freistellung_max_sek"] = sek
        ergebnis["zwischenstufen_hardware"] = bool(bester)

        print("")
        print("EINSTUFUNG: {}".format(klasse))
        print("  Freistellung hoechstens {} Sekunden am Stueck rechnen "
              "(sonst dauert es spuerbar).".format(sek))
        print("  Zwischenstufen: {}".format(
            "Hardware-Encoder nutzen" if bester else "CPU, sparsam bleiben"))

        ZIEL.parent.mkdir(parents=True, exist_ok=True)
        ZIEL.write_text(json.dumps(ergebnis, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        print("")
        print("Gespeichert: {}".format(ZIEL))
        print("Die Video-Skills lesen das ab jetzt selbst.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
