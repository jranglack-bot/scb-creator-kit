#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sorgt dafuer, dass Videobearbeitung ab der Installation schnell ist.

Anlass (21.08.2026): Auf einem frisch eingerichteten Rechner dauerte das
erste Video ewig. Ursache war NICHT die Hardware, sondern eine fehlende
Laufzeit: ohne onnxruntime faellt die Freistellung still auf MediaPipe
zurueck - langsamer UND sichtbar schlechter, sobald Grafik dahinter liegt.
Das Setup installierte bis dahin nur mediapipe/opencv/numpy.

Dieses Script richtet die schnellen Wege ein und WEIST NACH, dass sie
greifen - statt sie nur zu installieren:

  1. onnxruntime in der fuer das System passenden Fassung
     Windows -> onnxruntime-directml (rechnet auf der Grafikeinheit)
     macOS   -> onnxruntime          (CoreML ist eingebaut)
     Linux   -> onnxruntime
  2. Nachweis, welcher Rechenweg tatsaechlich zur Verfuegung steht
  3. Kontrolle, dass das RVM-Modell vorhanden ist
  4. Tempo-Messung, damit die Video-Skills den Ablauf anpassen koennen

    python beschleunigen.py            # einrichten und nachweisen
    python beschleunigen.py --pruefen  # nur nachsehen

Exit 0 = schnelle Wege stehen, Exit 1 = etwas fehlt (Grund steht dabei)
"""
import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
MODELL = (HIER.parent.parent / "pro-look-editing" / "scripts" / "models"
          / "rvm_mobilenetv3_fp32.onnx")


def run(cmd, minuten=10):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              stdin=subprocess.DEVNULL,
                              timeout=minuten * 60)
    except Exception as e:
        class R:
            returncode = 1
            stdout = ""
            stderr = str(e)
        return R()


def paketname():
    """Die fuer dieses System schnellste onnxruntime-Fassung."""
    if platform.system() == "Windows":
        return "onnxruntime-directml"
    return "onnxruntime"


def laufzeit_status():
    """(vorhanden, anbieterliste) - in einem eigenen Prozess geprueft,
    damit eine frische Installation sofort sichtbar ist."""
    code = ("import json, onnxruntime as ort;"
            "print(json.dumps({'v': ort.__version__,"
            "'p': list(ort.get_available_providers())}))")
    r = run([sys.executable, "-c", code], minuten=2)
    if r.returncode != 0:
        return (False, None, None)
    try:
        import json
        d = json.loads((r.stdout or "").strip().splitlines()[-1])
        return (True, d["v"], d["p"])
    except Exception:
        return (False, None, None)


def schneller_anbieter(anbieter):
    """Der erste Anbieter, der nicht die reine CPU ist."""
    for a in anbieter or []:
        if a != "CPUExecutionProvider":
            return a
    return None


def main():
    p = argparse.ArgumentParser(
        description="Videobearbeitung von Anfang an schnell machen")
    p.add_argument("--pruefen", action="store_true",
                   help="nur nachsehen, nichts installieren")
    a = p.parse_args()

    print("Beschleunigung der Videobearbeitung")
    print("=" * 52)
    print("System: {} / {}".format(platform.system(), platform.machine()))

    fehlt = []

    # --- 1. Laufzeit fuer die Freistellung ------------------------------
    da, version, anbieter = laufzeit_status()
    if not da and not a.pruefen:
        paket = paketname()
        print("")
        print("Installiere {} - ohne das ist die Freistellung".format(paket))
        print("deutlich langsamer und sichtbar schlechter.")
        r = run([sys.executable, "-m", "pip", "install", "--quiet", paket])
        if r.returncode != 0:
            print("  FEHLER: " + ((r.stderr or "")[:250]))
        da, version, anbieter = laufzeit_status()

    if da:
        schnell = schneller_anbieter(anbieter)
        print("")
        print("  [ok]     Freistellungs-Laufzeit  onnxruntime " + version)
        if schnell:
            print("  [ok]     Rechenweg               " + schnell
                  + " (Grafikeinheit)")
        else:
            print("  [!]      Rechenweg               nur CPU - laeuft, "
                  "aber langsamer")
    else:
        print("  [fehlt]  Freistellungs-Laufzeit  onnxruntime")
        fehlt.append("onnxruntime")

    # --- 2. Modell ------------------------------------------------------
    if MODELL.exists():
        mb = MODELL.stat().st_size / 1e6
        print("  [ok]     RVM-Modell              {:.1f} MB".format(mb))
    else:
        print("  [fehlt]  RVM-Modell              " + str(MODELL))
        fehlt.append("RVM-Modell")

    # --- 3. Tempo messen, damit die Skills sich anpassen ----------------
    profil = Path.home() / ".scb-creator-kit" / "tempo.json"
    if not profil.exists() and not a.pruefen:
        print("")
        print("Messe einmalig die Videoleistung (30-60 Sekunden) ...")
        r = run([sys.executable, str(HIER / "tempo_check.py")], minuten=10)
        for zeile in (r.stdout or "").splitlines():
            if zeile.startswith("EINSTUFUNG") or "Hardware-Encoder" in zeile:
                print("  " + zeile.strip())
    if profil.exists():
        print("  [ok]     Tempo-Profil            " + str(profil))
    else:
        print("  [!]      Tempo-Profil            noch nicht gemessen")

    print("")
    print("=" * 52)
    if fehlt:
        print("Fehlt noch: " + ", ".join(fehlt))
        return 1
    print("Die schnellen Wege stehen. Beim Videoschneiden ist ab jetzt")
    print("nichts mehr von Hand nachzujustieren.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
