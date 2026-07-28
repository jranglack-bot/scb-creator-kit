#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Installiert Basiswerkzeuge plattformuebergreifend - Windows, macOS, Linux.

Claude ruft dieses Script auf, nachdem der User zugestimmt hat.
Der User muss KEIN Terminal oeffnen und nichts abtippen.

    python install_tools.py ffmpeg
    python install_tools.py node yt-dlp gh
    python install_tools.py --pruefen ffmpeg node

Werkzeuge: ffmpeg, node, yt-dlp, gh

Exit 0 = alles da/installiert
Exit 1 = fehlgeschlagen (Grund steht dabei)
Exit 2 = auf macOS fehlt Homebrew (Claude soll das dem User anbieten)
"""
import platform
import shutil
import subprocess
import sys

# Paketnamen je Plattform-Paketmanager
PAKETE = {
    "ffmpeg": {"winget": "Gyan.FFmpeg",          "brew": "ffmpeg",
               "apt": "ffmpeg",                  "dnf": "ffmpeg",
               "pruefbefehl": ["ffmpeg", "-version"]},
    "node":   {"winget": "OpenJS.NodeJS.LTS",    "brew": "node",
               "apt": "nodejs",                  "dnf": "nodejs",
               "pruefbefehl": ["node", "--version"]},
    "yt-dlp": {"winget": "yt-dlp.yt-dlp",        "brew": "yt-dlp",
               "apt": "yt-dlp",                  "dnf": "yt-dlp",
               "pruefbefehl": ["yt-dlp", "--version"]},
    "gh":     {"winget": "GitHub.cli",           "brew": "gh",
               "apt": "gh",                      "dnf": "gh",
               "pruefbefehl": ["gh", "--version"]},
}

BREW_INSTALL = ('/bin/bash -c "$(curl -fsSL '
                'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def vorhanden(werkzeug):
    """True, wenn das Werkzeug aufrufbar ist."""
    if not shutil.which(werkzeug.split()[0]):
        # yt-dlp/ffmpeg heissen im PATH genau so; gh und node auch
        if not shutil.which(PAKETE[werkzeug]["pruefbefehl"][0]):
            return False
    return run(PAKETE[werkzeug]["pruefbefehl"]).returncode == 0


def paketmanager():
    """(name, basisbefehl) des passenden Paketmanagers - oder (None, None)."""
    sys_name = platform.system()
    if sys_name == "Windows":
        if shutil.which("winget"):
            return "winget", ["winget", "install", "--silent",
                              "--accept-package-agreements",
                              "--accept-source-agreements", "-e", "--id"]
        return None, None
    if sys_name == "Darwin":
        if shutil.which("brew"):
            return "brew", ["brew", "install"]
        return "brew-fehlt", None
    # Linux
    for name, basis in (("apt", ["sudo", "apt-get", "install", "-y"]),
                        ("dnf", ["sudo", "dnf", "install", "-y"]),
                        ("pacman", ["sudo", "pacman", "-S", "--noconfirm"])):
        if shutil.which(name if name != "apt" else "apt-get"):
            return name, basis
    return None, None


def main():
    argumente = [a for a in sys.argv[1:] if not a.startswith("--")]
    nur_pruefen = "--pruefen" in sys.argv
    if not argumente:
        print("FEHLER: Kein Werkzeug angegeben. Moeglich:",
              ", ".join(PAKETE))
        return 1
    unbekannt = [a for a in argumente if a not in PAKETE]
    if unbekannt:
        print(f"FEHLER: Unbekannt: {', '.join(unbekannt)}. "
              f"Moeglich: {', '.join(PAKETE)}")
        return 1

    print(f"System: {platform.system()} / {platform.machine()}")

    fehlend = []
    for w in argumente:
        if vorhanden(w):
            print(f"  [da]     {w}")
        else:
            print(f"  [fehlt]  {w}")
            fehlend.append(w)

    if not fehlend:
        print("\nAlles vorhanden, nichts zu tun.")
        return 0
    if nur_pruefen:
        print("\nFehlend:", ", ".join(fehlend))
        return 0

    pm, basis = paketmanager()

    if pm == "brew-fehlt":
        print("\nAuf diesem Mac fehlt Homebrew, der uebliche Weg fuer solche "
              "Programme.")
        print("Einmalig einzurichten mit diesem offiziellen Befehl:")
        print("  " + BREW_INSTALL)
        print("Danach dieses Script erneut aufrufen.")
        return 2

    if not pm:
        print(f"\nFEHLER: Kein unterstuetzter Paketmanager auf "
              f"{platform.system()} gefunden.")
        return 1

    print(f"\nPaketmanager: {pm}")
    fehler = []
    for w in fehlend:
        paket = PAKETE[w].get(pm)
        if not paket:
            fehler.append(f"{w} (kein Paketname fuer {pm})")
            continue
        print(f"Installiere {w} ({paket}) ...")
        r = run(basis + [paket])
        if r.returncode != 0 and not vorhanden(w):
            grund = (r.stderr or r.stdout or "").strip()[:200]
            fehler.append(f"{w}: {grund}")
        else:
            print(f"  OK: {w}")

    if fehler:
        print("\nNICHT INSTALLIERT:")
        for f in fehler:
            print("  -", f)
        return 1

    print("\nFERTIG.")
    if platform.system() == "Windows":
        print("Hinweis: Neu installierte Programme sind erst in einer neuen "
              "Sitzung im Suchpfad.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
