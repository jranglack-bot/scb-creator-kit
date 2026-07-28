#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Installiert RTK (Token-Sparer) vollautomatisch.

Claude ruft dieses Script auf, nachdem der User zugestimmt hat.
Der User muss KEIN Terminal oeffnen und nichts abtippen.

    python install_rtk.py

Rueckgabe: Exit 0 = fertig, Exit 1 = fehlgeschlagen (Grund steht dabei).
"""
import io
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

REL = "https://github.com/rtk-ai/rtk/releases/latest/download"
WIN_ZIP = f"{REL}/rtk-x86_64-pc-windows-msvc.zip"


def run(cmd, **kw):
    # encoding/errors explizit: manche Tools geben UTF-8 aus, die Windows-
    # Standardkodierung (cp1252) wuerde daran mit UnicodeDecodeError sterben.
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def text(r, *felder):
    """Erste nicht-leere Ausgabe aus den genannten Feldern (nie None)."""
    for f in felder:
        wert = getattr(r, f, None)
        if wert and wert.strip():
            return wert.strip()
    return ""


def bereits_da():
    p = shutil.which("rtk")
    if not p:
        return None
    r = run([p, "--version"])
    return p if r.returncode == 0 else None


def install_windows():
    ziel = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                        "Microsoft", "WinGet", "Links")
    os.makedirs(ziel, exist_ok=True)
    print(f"Lade RTK von {WIN_ZIP} ...")
    with urllib.request.urlopen(WIN_ZIP, timeout=120) as resp:
        daten = resp.read()
    print(f"Geladen ({len(daten)//1024} KB), entpacke ...")
    with zipfile.ZipFile(io.BytesIO(daten)) as z:
        tmp = tempfile.mkdtemp(prefix="rtk_")
        z.extractall(tmp)
    exe = None
    for wurzel, _, dateien in os.walk(tmp):
        if "rtk.exe" in dateien:
            exe = os.path.join(wurzel, "rtk.exe")
            break
    if not exe:
        print("FEHLER: rtk.exe im Archiv nicht gefunden.")
        return None
    zielexe = os.path.join(ziel, "rtk.exe")
    shutil.copyfile(exe, zielexe)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Installiert nach: {zielexe}")
    return zielexe


def install_unix():
    if shutil.which("brew"):
        print("Installiere ueber Homebrew ...")
        r = run(["brew", "install", "rtk"])
        if r.returncode == 0:
            return shutil.which("rtk")
        print("Homebrew fehlgeschlagen:", (r.stderr or "").strip()[:300])
    print("FEHLER: Kein Homebrew gefunden. Bitte das Quick-Install-Script "
          "von https://github.com/rtk-ai/rtk verwenden.")
    return None


def main():
    vorhanden = bereits_da()
    if vorhanden:
        print(f"RTK ist bereits installiert: {vorhanden}")
        exe = vorhanden
    else:
        exe = (install_windows() if platform.system() == "Windows"
               else install_unix())
        if not exe:
            return 1

    # Der Hook ist der eigentliche Wirkmechanismus - ohne ihn passiert nichts.
    print("Richte den Rewrite-Hook ein (rtk init -g) ...")
    r = run([exe, "init", "-g"])
    if r.returncode != 0:
        print("FEHLER bei 'rtk init -g':", text(r, "stderr", "stdout")[:400])
        return 1
    print("Hook eingerichtet.")

    v = run([exe, "--version"])
    print("Version:", text(v, "stdout", "stderr") or "(keine Ausgabe)")
    g = run([exe, "gain"])
    if g.returncode == 0:
        print("Ersparnis-Anzeige funktioniert.")
    else:
        print("Hinweis: 'rtk gain' laeuft nicht - evtl. Namenskollision mit "
              "einem anderen Programm namens rtk (Rust Type Kit).")

    print("")
    print("FERTIG. RTK ist aktiv. Neue Terminals/Sessions nutzen es sofort.")
    print("Rueckgaengig machen: rtk init -g --uninstall")
    return 0


if __name__ == "__main__":
    sys.exit(main())
