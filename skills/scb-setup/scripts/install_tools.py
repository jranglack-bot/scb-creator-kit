#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Installiert Basiswerkzeuge plattformuebergreifend - Windows, macOS, Linux.

Claude ruft dieses Script auf, nachdem der User zugestimmt hat.
Der User muss KEIN Terminal oeffnen und nichts abtippen.

    python install_tools.py ffmpeg
    python install_tools.py node yt-dlp gh
    python install_tools.py --pruefen ffmpeg node

Werkzeuge: ffmpeg, node, yt-dlp, git, gh

Exit 0 = alles da/installiert
Exit 1 = fehlgeschlagen (Grund steht dabei)
Exit 2 = auf macOS fehlt Homebrew UND es blieb ein Werkzeug uebrig, das
         nur Homebrew installieren kann (aktuell nur noch gh).
         ffmpeg/ffprobe, yt-dlp und Node.js brauchen KEIN Homebrew - die
         laedt das Script als fertige Pakete direkt von den offiziellen
         Quellen (ohne Passwort, ohne Terminal, ohne Adminrechte).
"""
import os
import platform
import shutil
import subprocess
import sys
import tempfile
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
    "git":    {"winget": "Git.Git",              "brew": "git",
               "apt": "git",                     "dnf": "git",
               "pruefbefehl": ["git", "--version"]},
    "gh":     {"winget": "GitHub.cli",           "brew": "gh",
               "apt": "gh",                      "dnf": "gh",
               "pruefbefehl": ["gh", "--version"]},
}

BREW_INSTALL = ('/bin/bash -c "$(curl -fsSL '
                'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')

# macOS ohne Homebrew: fertige Einzelprogramme, kein sudo, kein Passwort.
# ffmpeg/ffprobe von ffmpeg.martin-riedl.de (offiziell verlinkte statische
# Builds, arm64 UND Intel - evermeet.cx waere nur Intel).
# Primaer wird die Startseite nach konkreten Build-URLs durchsucht -
# die /redirect/latest/-Endpunkte des Anbieters liefern zeitweise 404
# (live beobachtet am 16.08.2026) und sind nur der Notnagel.
FFMPEG_SEITE = "https://ffmpeg.martin-riedl.de/"
FFMPEG_REDIRECT = ("https://ffmpeg.martin-riedl.de/redirect/latest/"
                   "macos/{arch}/{kanal}/{name}.zip")
YTDLP_MACOS = ("https://github.com/yt-dlp/yt-dlp/releases/latest/"
               "download/yt-dlp_macos")
NODE_INDEX = "https://nodejs.org/dist/index.json"
NODE_TAR = "https://nodejs.org/dist/{ver}/node-{ver}-darwin-{arch}.tar.gz"
NODE_SUMS = "https://nodejs.org/dist/{ver}/SHASUMS256.txt"
BIN_DIR = Path.home() / ".local" / "bin"
NODE_DIR = Path.home() / ".local" / "scb-node"
MINGIT_API = ("https://api.github.com/repos/git-for-windows/git/releases/latest")
GIT_DIR = Path.home() / ".local" / "scb-git"


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


def _text_von(url):
    """Laedt url als Text - oder None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "scb-setup"})
        with urllib.request.urlopen(req, timeout=60) as antwort:
            return antwort.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def _ffmpeg_urls(arch):
    """Konkrete Download-URLs {name: url} vom neuesten Build der Startseite.

    Die Build-Ordner heissen <unix-zeit>_<version>; der juengste gewinnt.
    ffmpeg und ffprobe kommen bewusst aus DEMSELBEN Build. None bei Fehler.
    """
    import re
    html = _text_von(FFMPEG_SEITE)
    if not html:
        return None
    builds = re.findall(
        rf'/download/macos/{arch}/((\d+)[^/"]*)/ffmpeg\.zip', html)
    if not builds:
        return None
    ordner = max(builds, key=lambda b: int(b[1]))[0]
    basis = f"{FFMPEG_SEITE.rstrip('/')}/download/macos/{arch}/{ordner}"
    return {name: f"{basis}/{name}.zip" for name in ("ffmpeg", "ffprobe")}


def _sha256_ok(datei, url):
    """Vergleicht datei mit der veroeffentlichten <url>.sha256.

    True auch, wenn keine Pruefsumme abrufbar ist (dann kein Urteil) -
    False NUR bei echtem Widerspruch.
    """
    import hashlib
    soll = _text_von(url + ".sha256")
    if not soll:
        return True
    soll = soll.split()[0].strip().lower()
    h = hashlib.sha256()
    with open(datei, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    if h.hexdigest() == soll:
        return True
    print(f"  FEHLER: Pruefsumme falsch fuer {datei.name} - Datei verworfen.")
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


def windows_pfad_eintragen(ordner):
    """Ordner dauerhaft in den Benutzer-PATH schreiben (Windows-Registry).

    Kein Adminrecht noetig: der Environment-Schluessel unter HKEY_CURRENT_USER
    gehoert dem Benutzer selbst.
    """
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                            winreg.KEY_READ | winreg.KEY_WRITE) as k:
            try:
                alt, typ = winreg.QueryValueEx(k, "Path")
            except OSError:
                alt, typ = "", winreg.REG_EXPAND_SZ
            if str(ordner).lower() in (alt or "").lower():
                return
            neu = (str(ordner) + os.pathsep + alt) if alt else str(ordner)
            winreg.SetValueEx(k, "Path", 0, typ or winreg.REG_EXPAND_SZ, neu)
        os.environ["PATH"] = str(ordner) + os.pathsep + os.environ.get("PATH", "")
        print("  Suchpfad ergaenzt: " + str(ordner)
              + " (dauerhaft; neue Fenster sehen es sofort)")
    except Exception as e:
        print("  Hinweis: Suchpfad konnte nicht ergaenzt werden (" + str(e) + ").")


def statisch_git():
    """Git auf Windows ohne Installer und ohne Adminrechte (MinGit-ZIP).

    MinGit ist die offizielle, entpackbare Fassung von Git fuer Windows.
    Kein Setup-Assistent, kein UAC-Fenster, kein Passwort - genau deshalb
    kann Claude das selbst erledigen. Verifiziert: damit laeuft
    "claude plugin marketplace add" (HTTPS-Klon) einwandfrei.
    """
    import json as _json
    m = platform.machine().lower()
    if m in ("arm64", "aarch64"):
        muster = "arm64"
    elif m in ("amd64", "x86_64", "x64"):
        muster = "64-bit"
    else:
        muster = "32-bit"

    roh = _text_von(MINGIT_API)
    if not roh:
        print("  Konnte die Git-Release-Liste nicht laden.")
        return False
    url = None
    try:
        for a in _json.loads(roh).get("assets", []):
            name = a.get("name", "")
            if (name.startswith("MinGit") and muster in name
                    and "busybox" not in name):
                url = a.get("browser_download_url")
                break
    except Exception as e:
        print("  Release-Liste unlesbar (" + str(e) + ").")
        return False
    if not url:
        print("  Keine passende MinGit-Fassung fuer " + muster + " gefunden.")
        return False

    zip_pfad = Path(tempfile.gettempdir()) / "scb_mingit.zip"
    if not _lade(url, zip_pfad):
        return False
    if GIT_DIR.exists():
        shutil.rmtree(GIT_DIR, ignore_errors=True)
    GIT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_pfad) as z:
            z.extractall(GIT_DIR)
    except Exception as e:
        print("  Entpacken fehlgeschlagen (" + str(e) + ").")
        return False
    finally:
        zip_pfad.unlink(missing_ok=True)

    if not (GIT_DIR / "cmd" / "git.exe").exists():
        print("  git.exe im Archiv nicht gefunden.")
        return False
    windows_pfad_eintragen(GIT_DIR / "cmd")
    return True


def statisch_ffmpeg():
    """ffmpeg + ffprobe als fertige Programme nach ~/.local/bin (macOS).

    Per Python geladene Dateien bekommen KEIN Quarantaene-Attribut -
    Gatekeeper blockt nichts, xattr ist nicht noetig.
    """
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    arch = "arm64" if platform.machine() == "arm64" else "amd64"
    urls = _ffmpeg_urls(arch)
    for name in ("ffmpeg", "ffprobe"):
        zip_pfad = BIN_DIR / f"{name}.zip"
        ok = False
        # 1. Wahl: konkreter Build von der Startseite (inkl. Pruefsumme)
        if urls and _lade(urls[name], zip_pfad):
            ok = (_sha256_ok(zip_pfad, urls[name])
                  and _entpacke_binary(zip_pfad, name))
        # Notnagel: redirect/latest (liefert zeitweise 404)
        if not ok:
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

def statisch_node():
    """Node.js (LTS) als offizielles Paket nach ~/.local/scb-node (macOS).

    Kein Homebrew, kein sudo, kein Passwort - nodejs.org liefert fertige
    Archive. npm landet mit im Paket; spaetere 'npm install -g' schreiben
    dann in den Benutzerordner statt in Systemordner.
    """
    import tarfile
    arch = "arm64" if platform.machine() == "arm64" else "x64"

    # Neueste LTS-Version ermitteln (Fallback: fest verdrahtete Fassung)
    ver = None
    roh = _text_von(NODE_INDEX)
    if roh:
        try:
            ver = next(r["version"] for r in json.loads(roh) if r.get("lts"))
        except Exception:
            ver = None
    if not ver:
        ver = "v24.19.0"

    url = NODE_TAR.format(ver=ver, arch=arch)
    tar_pfad = Path(tempfile.gettempdir()) / f"node-{ver}-{arch}.tar.gz"
    if not _lade(url, tar_pfad):
        return False

    # Pruefsumme gegen die veroeffentlichte SHASUMS256.txt
    sums = _text_von(NODE_SUMS.format(ver=ver))
    if sums:
        dateiname = url.rsplit("/", 1)[-1]
        soll = next((z.split()[0] for z in sums.splitlines()
                     if z.strip().endswith(dateiname)), None)
        if soll:
            import hashlib
            h = hashlib.sha256()
            with open(tar_pfad, "rb") as f:
                for block in iter(lambda: f.read(1 << 20), b""):
                    h.update(block)
            if h.hexdigest() != soll.lower():
                print("  FEHLER: Node-Pruefsumme falsch - Datei verworfen.")
                tar_pfad.unlink(missing_ok=True)
                return False

    ziel_eltern = NODE_DIR.parent
    ziel_eltern.mkdir(parents=True, exist_ok=True)
    if NODE_DIR.exists():
        shutil.rmtree(NODE_DIR, ignore_errors=True)
    try:
        with tarfile.open(tar_pfad, "r:gz") as t:
            wurzel = t.getnames()[0].split("/")[0]
            t.extractall(ziel_eltern)
        (ziel_eltern / wurzel).rename(NODE_DIR)
    except Exception as e:
        print(f"  FEHLER beim Entpacken von Node: {e}")
        return False
    finally:
        tar_pfad.unlink(missing_ok=True)

    # node/npm/npx im Suchpfad verfuegbar machen
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("node", "npm", "npx"):
        quelle = NODE_DIR / "bin" / name
        link = BIN_DIR / name
        if not quelle.exists():
            continue
        if link.exists() or link.is_symlink():
            link.unlink()
        try:
            link.symlink_to(quelle)
        except OSError:
            # Falls Symlinks nicht erlaubt sind: kleiner Starter statt Link
            starter = "#!/bin/sh" + chr(10) + f'exec "{quelle}" "$@"' + chr(10)
            link.write_text(starter, encoding="utf-8")
            os.chmod(link, 0o755)
    return True


STATISCH = {"ffmpeg": statisch_ffmpeg, "yt-dlp": statisch_ytdlp,
            "node": statisch_node}


def pfad_eintragen():
    """~/.local/bin und Nodes bin-Ordner dauerhaft in den PATH haengen.

    Nodes eigener bin-Ordner MUSS mit hinein: "npm install -g <paket>"
    legt Programme wie die Higgsfield-CLI DORT ab, nicht in ~/.local/bin.
    """
    kandidaten = [(BIN_DIR, 'export PATH="$HOME/.local/bin:$PATH"')]
    if NODE_DIR.exists():
        kandidaten.append(
            (NODE_DIR / "bin",
             'export PATH="$HOME/.local/scb-node/bin:$PATH"'))
    pfad = os.environ.get("PATH", "")
    zeilen = [z for ordner, z in kandidaten if str(ordner) not in pfad]
    if not zeilen:
        return
    for rc in (Path.home() / ".zshrc", Path.home() / ".bashrc"):
        try:
            inhalt = rc.read_text(encoding="utf-8") if rc.exists() else ""
            fehlend = [z for z in zeilen if z not in inhalt]
            if fehlend:
                with open(rc, "a", encoding="utf-8") as f:
                    f.write(chr(10))
                    f.write("# SCB Creator Kit: Werkzeuge im Benutzerordner")
                    f.write(chr(10))
                    for z in fehlend:
                        f.write(z + chr(10))
        except OSError:
            pass
    print("  Hinweis: Suchpfad ergaenzt (" + ", ".join(
        str(o) for o, _ in kandidaten) + ") - gilt ab dem naechsten "
        "Terminal/Neustart; Scripts des Kits finden die Programme auch so.")


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

    # Windows: Git ohne Installer und ohne UAC nachziehen. winget wuerde
    # hier ein Adminfenster oeffnen, das Claude nicht bedienen kann.
    if platform.system() == "Windows" and "git" in fehlend:
        print("Lade Git als fertiges Paket "
              "(kein Installer, keine Adminrechte) ...")
        if statisch_git() and vorhanden("git"):
            print("  OK: git")
            fehlend.remove("git")
        else:
            print("  Direkt-Weg fehlgeschlagen - versuche es ueber winget.")
        if not fehlend:
            print("")
            print("FERTIG.")
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
