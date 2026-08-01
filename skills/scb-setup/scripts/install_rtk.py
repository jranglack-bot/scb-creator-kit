#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Installiert RTK (Token-Sparer) vollautomatisch - Windows, macOS, Linux.

Claude ruft dieses Script auf, nachdem der User zugestimmt hat.
Der User muss KEIN Terminal oeffnen und nichts abtippen.

    Windows:   python  install_rtk.py
    Mac/Linux: python3 install_rtk.py

Rueckgabe: Exit 0 = fertig, Exit 1 = fehlgeschlagen (Grund steht dabei).

Bevorzugter Weg sind die MODERIERTEN Paketkataloge - derselbe Weg, ueber
den das Kit auch ffmpeg und Node installiert:

    Windows: winget install rtk-ai.rtk   (offizieller winget-Katalog)
    macOS:   brew install rtk            (Homebrew-Formel, homebrew-core)

Nur wenn kein Paketmanager da ist, laedt das Script das passende Paket
direkt aus dem offiziellen GitHub-Release (rtk-ai/rtk).
"""
import io
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

REL = "https://github.com/rtk-ai/rtk/releases/latest/download"

# Asset-Namen wie im offiziellen Release (geprueft an v0.44.0)
ASSETS = {
    ("Windows", "x86_64"): "rtk-x86_64-pc-windows-msvc.zip",
    ("Darwin",  "arm64"):  "rtk-aarch64-apple-darwin.tar.gz",
    ("Darwin",  "x86_64"): "rtk-x86_64-apple-darwin.tar.gz",
    ("Linux",   "arm64"):  "rtk-aarch64-unknown-linux-gnu.tar.gz",
    ("Linux",   "x86_64"): "rtk-x86_64-unknown-linux-musl.tar.gz",
}


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


def arch():
    m = platform.machine().lower()
    if m in ("arm64", "aarch64"):
        return "arm64"
    if m in ("x86_64", "amd64", "x64"):
        return "x86_64"
    return m


def zielordner():
    """Ordner im Suchpfad, der ohne Adminrechte beschreibbar ist."""
    if platform.system() == "Windows":
        return os.path.join(os.environ.get("LOCALAPPDATA", ""),
                            "Microsoft", "WinGet", "Links")
    return os.path.join(os.path.expanduser("~"), ".local", "bin")


def bereits_da():
    p = shutil.which("rtk")
    if not p:
        # Auch am Standard-Zielort nachsehen, falls PATH noch nicht greift
        kand = os.path.join(zielordner(),
                            "rtk.exe" if platform.system() == "Windows" else "rtk")
        p = kand if os.path.exists(kand) else None
    if not p:
        return None
    return p if run([p, "--version"]).returncode == 0 else None


def hole_und_entpacke(url, tmp):
    print(f"Lade RTK von {url} ...")
    with urllib.request.urlopen(url, timeout=180) as resp:
        daten = resp.read()
    print(f"Geladen ({len(daten)//1024} KB), entpacke ...")
    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(daten)) as z:
            z.extractall(tmp)
    else:
        with tarfile.open(fileobj=io.BytesIO(daten), mode="r:gz") as t:
            t.extractall(tmp)


def finde_binary(wurzelpfad, name):
    for wurzel, _, dateien in os.walk(wurzelpfad):
        if name in dateien:
            return os.path.join(wurzel, name)
    return None


def pfad_dauerhaft_ergaenzen(ordner):
    """~/.local/bin in die Shell-Konfig eintragen, falls noch nicht im PATH."""
    if ordner in os.environ.get("PATH", "").split(os.pathsep):
        return True
    shell = os.environ.get("SHELL", "")
    datei = "~/.zshrc" if "zsh" in shell else "~/.bashrc"
    ziel = os.path.expanduser(datei)
    zeile = f'\n# von SCB Creator Kit ergaenzt\nexport PATH="{ordner}:$PATH"\n'
    try:
        vorhanden = ""
        if os.path.exists(ziel):
            with open(ziel, encoding="utf-8", errors="replace") as f:
                vorhanden = f.read()
        if ordner not in vorhanden:
            with open(ziel, "a", encoding="utf-8") as f:
                f.write(zeile)
            print(f"Suchpfad dauerhaft ergaenzt in {datei}")
        return True
    except OSError as e:
        print(f"Hinweis: Konnte {datei} nicht ergaenzen ({e}).")
        return False


def installiere_via_paketmanager():
    """winget (Windows) bzw. brew (macOS) - moderierte Kataloge, denen
    auch vorsichtige Claude-Instanzen vertrauen. None = kein Paketmanager
    da oder Installation fehlgeschlagen -> Direkt-Download versuchen."""
    sys_name = platform.system()
    if sys_name == "Windows" and shutil.which("winget"):
        print("Installiere RTK aus dem offiziellen winget-Katalog "
              "(rtk-ai.rtk) ...")
        r = run(["winget", "install", "--silent",
                 "--accept-package-agreements", "--accept-source-agreements",
                 "-e", "--id", "rtk-ai.rtk"])
        if r.returncode == 0:
            return bereits_da()
        print("winget hat nicht geklappt:",
              text(r, "stderr", "stdout")[:200])
    elif sys_name == "Darwin" and shutil.which("brew"):
        print("Installiere RTK ueber Homebrew (brew install rtk) ...")
        r = run(["brew", "install", "rtk"])
        if r.returncode == 0:
            return bereits_da() or shutil.which("rtk")
        print("brew hat nicht geklappt:", text(r, "stderr", "stdout")[:200])
    return None


def installiere():
    schluessel = (platform.system(), arch())
    asset = ASSETS.get(schluessel)
    if not asset:
        print(f"FEHLER: Keine Version fuer {schluessel[0]}/{schluessel[1]} "
              f"verfuegbar. Unterstuetzt: {sorted(set(k[0] for k in ASSETS))}.")
        return None

    ist_windows = platform.system() == "Windows"
    binname = "rtk.exe" if ist_windows else "rtk"
    ziel = zielordner()
    os.makedirs(ziel, exist_ok=True)

    tmp = tempfile.mkdtemp(prefix="rtk_")
    try:
        hole_und_entpacke(f"{REL}/{asset}", tmp)
        quelle = finde_binary(tmp, binname)
        if not quelle:
            print(f"FEHLER: {binname} im Archiv nicht gefunden.")
            return None
        zielbin = os.path.join(ziel, binname)
        shutil.copyfile(quelle, zielbin)
        if not ist_windows:
            os.chmod(zielbin, os.stat(zielbin).st_mode |
                     stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            pfad_dauerhaft_ergaenzen(ziel)
        print(f"Installiert nach: {zielbin}")
        return zielbin
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print(f"System: {platform.system()} / {arch()}")

    exe = bereits_da()
    if exe:
        print(f"RTK ist bereits installiert: {exe}")
    else:
        exe = installiere_via_paketmanager()
        if not exe:
            print("Kein Paketmanager verfuegbar - lade direkt vom "
                  "offiziellen Release.")
            exe = installiere()
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
    if run([exe, "gain"]).returncode == 0:
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
