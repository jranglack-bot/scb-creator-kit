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
Exit 2 = auf macOS fehlt Homebrew UND es blieb ein Werkzeug uebrig, das
         nur Homebrew installieren kann (node, gh). ffmpeg/ffprobe und
         yt-dlp brauchen KEIN Homebrew mehr - die laedt das Script als
         fertige Programme direkt herunter (ohne Passwort, ohne Terminal).
"""
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

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

# macOS ohne Homebrew: fertige Einzelprogramme, kein sudo, kein Passwort.
# ffmpeg/ffprobe von ffmpeg.martin-riedl.de (offiziell verlinkte statische
# Builds, arm64 UND Intel - evermeet.cx waere nur Intel). Je nach
# Architektur liegt der aktuelle Build mal unter "release", mal unter
# "snapshot", darum werden beide probiert.
FFMPEG_REDIRECT = ("https://ffmpeg.martin-riedl.de/redirect/latest/"
                   "macos/{arch}/{kanal}/{name}.zip")
YTDLP_MACOS = ("https://github.com/yt-dlp/yt-dlp/releases/latest/"
               "download/yt-dlp_macos")
BIN_DIR = Path.home() / ".local" / "bin"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def _befehl_mit_pfad(befehl):
    """Prueft auch ~/.local/bin, falls es (noch) nicht im PATH steht."""
    gefunden = shutil.which(befehl[0])
    if not gefunden:
        kandidat = BIN_DIR / befehl[0]
        if kandidat.is_file() and os.access(kandidat, os.X_OK):
            gefunden = str(kandidat)
    if not gefunden:
        return None
    return [gefunden] + list(befehl[1:])


def vorhanden(werkzeug):
    """True, wenn das Werkzeug aufrufbar ist (PATH oder ~/.local/bin)."""
    befehl = _befehl_mit_pfad(PAKETE[werkzeug]["pruefbefehl"])
    if not befehl:
        return False
    # returncode-Pruefung faengt auch kaputte Binaries ab, z. B. ein
    # Intel-ffmpeg auf einem M-Mac ohne Rosetta ("bad CPU type")
    return run(befehl).returncode == 0


def _lade(url, ziel):
    """Laedt url nach ziel. True bei Erfolg."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "scb-setup"})
        with urllib.request.urlopen(req, timeout=120) as antwort, \
                open(ziel, "wb") as f:
            shutil.copyfileobj(antwort, f)
        return True
    except Exception as e:
        print(f"  Download fehlgeschlagen ({url}): {e}")
        return False


def _entpacke_binary(zip_pfad, name):
    """Holt die Datei <name> aus dem ZIP nach BIN_DIR und macht sie ausfuehrbar."""
    with zipfile.ZipFile(zip_pfad) as z:
        eintrag = next((m for m in z.namelist()
                        if Path(m).name == name and not m.endswith("/")), None)
        if not eintrag:
            print(f"  FEHLER: {name} nicht im Archiv gefunden.")
            return False
        ziel = BIN_DIR / name
        with z.open(eintrag) as quelle, open(ziel, "wb") as f:
            shutil.copyfileobj(quelle, f)
    os.chmod(ziel, 0o755)
    return True


def statisch_ffmpeg():
    """ffmpeg + ffprobe als fertige Programme nach ~/.local/bin (macOS).

    Per Python geladene Dateien bekommen KEIN Quarantaene-Attribut -
    Gatekeeper blockt nichts, xattr ist nicht noetig.
    """
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    arch = "arm64" if platform.machine() == "arm64" else "amd64"
    for name in ("ffmpeg", "ffprobe"):
        zip_pfad = BIN_DIR / f"{name}.zip"
        ok = False
        for kanal in ("release", "snapshot"):
            url = FFMPEG_REDIRECT.format(arch=arch, kanal=kanal, name=name)
            if _lade(url, zip_pfad):
                ok = _entpacke_binary(zip_pfad, name)
                if ok:
                    break
        zip_pfad.unlink(missing_ok=True)
        if not ok:
            return False
    return True


def statisch_ytdlp():
    """yt-dlp als fertiges Programm nach ~/.local/bin (macOS, universal)."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    ziel = BIN_DIR / "yt-dlp"
    if not _lade(YTDLP_MACOS, ziel):
        return False
    os.chmod(ziel, 0o755)
    return True

STATISCH = {"ffmpeg": statisch_ffmpeg, "yt-dlp": statisch_ytdlp}


def pfad_eintragen():
    """~/.local/bin dauerhaft in den PATH haengen (zsh + bash)."""
    if str(BIN_DIR) in os.environ.get("PATH", ""):
        return
    zeile = 'export PATH="$HOME/.local/bin:$PATH"'
    for rc in (Path.home() / ".zshrc", Path.home() / ".bashrc"):
        try:
            inhalt = rc.read_text(encoding="utf-8") if rc.exists() else ""
            if zeile not in inhalt:
                with open(rc, "a", encoding="utf-8") as f:
                    f.write(f"\n# SCB Creator Kit: Werkzeuge in ~/.local/bin\n"
                            f"{zeile}\n")
        except OSError:
            pass
    print(f"  Hinweis: {BIN_DIR} wurde in den Suchpfad eingetragen "
          "(gilt ab dem naechsten Terminal/Neustart; Scripts des Kits "
          "finden die Programme auch so).")


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
        # Mac ohne Homebrew: was ohne Homebrew geht, direkt erledigen
        statisch = [w for w in fehlend if w in STATISCH]
        fehler = []
        for w in statisch:
            print(f"Lade {w} als fertiges Programm (kein Homebrew noetig) ...")
            if STATISCH[w]() and vorhanden(w):
                print(f"  OK: {w}")
            else:
                fehler.append(f"{w}: Direkt-Download fehlgeschlagen")
        if len(fehler) < len(statisch):        # mindestens eins hat geklappt
            pfad_eintragen()
        rest = [w for w in fehlend if w not in STATISCH]

        if fehler:
            print("\nNICHT INSTALLIERT:")
            for f in fehler:
                print("  -", f)
            return 1
        if not rest:
            print("\nFERTIG - ganz ohne Homebrew.")
            return 0

        print(f"\nFuer {', '.join(rest)} fehlt auf diesem Mac Homebrew - "
              "der uebliche Weg, solche Programme zu installieren.")
        print("Infos dazu: https://brew.sh")
        print("")
        print("WICHTIG: Diesen Befehl bitte SELBST im Terminal einfuegen -")
        print("er fragt nach dem Mac-Passwort, und das kann Claude nicht "
              "eingeben.")
        print("(Terminal oeffnen: Cmd+Leertaste, 'Terminal' tippen, Enter)")
        print("")
        print("  " + BREW_INSTALL)
        print("")
        print("Das dauert ein paar Minuten und ist EINMALIG pro Mac noetig.")
        print("Danach Bescheid sagen - Claude macht dann allein weiter.")
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
