#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Richtet die Grafik-Werkzeuge ein: Motion Canvas und/oder Remotion.

Beide landen an EINEM festen Ort, den alle Videoprojekte mitbenutzen:

    ~/.scb-creator-kit/grafik/motion-canvas
    ~/.scb-creator-kit/grafik/remotion

Damit muss nicht je Video ein neues Projekt entstehen, und ein Update des
Kits kann eine neu dazugekommene Faehigkeit wirklich nachliefern.

    python grafik_einrichten.py                 # was fehlt, einrichten
    python grafik_einrichten.py --nur remotion  # gezielt eines
    python grafik_einrichten.py --pruefen       # nur nachsehen

Bereits vorhandene Projekte des Nutzers (z. B. unter D:) werden erkannt
und NICHT ein zweites Mal angelegt.

Exit 0 = alles da, Exit 1 = etwas fehlgeschlagen, Exit 2 = Node.js fehlt
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

BASIS = Path.home() / ".scb-creator-kit" / "grafik"

# Wo der Nutzer schon eigene Projekte haben koennte
EIGENE_ORTE = [Path.home(), Path("D:/Instagram Content"), Path("C:/Instagram Content")]

WERKZEUGE = {
    "motion-canvas": {
        "titel": "Motion Canvas",
        "hinweis": "kostenlos (MIT), schneller fuer einfache Grafik",
        "befehl": ["npm", "create", "@motion-canvas@latest", "--", "--name",
                   "scb", "--path", "{ziel}", "--language", "ts",
                   "--plugins", "ffmpeg"],
    },
    "remotion": {
        "titel": "Remotion",
        "hinweis": ("kostenlos fuer Einzelpersonen und Firmen bis 3 "
                    "Mitarbeiter, darueber kostenpflichtig; kann echtes 3D"),
        "befehl": ["npx", "--yes", "create-video@latest", "{ziel}",
                   "--blank", "--yes", "--no-tailwind"],
    },
}


def run(cmd, minuten=15, **kw):
    """Befehl ausfuehren - mit geschlossener Eingabe und Zeitlimit.

    Beides ist Pflicht: 'create-video' fragt sonst interaktiv nach
    TailwindCSS und wartet endlos (gemessen: haengt bis zum Abbruch).
    Ohne Zeitlimit blockiert das den ganzen Ablauf.
    """
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              stdin=subprocess.DEVNULL,
                              timeout=minuten * 60, **kw)
    except subprocess.TimeoutExpired:
        class R:
            returncode = 1
            stdout = ""
            stderr = ("Zeitlimit ueberschritten - der Befehl wartete "
                      "vermutlich auf eine Eingabe.")
        return R()


def npm_befehl(name):
    """Auf Windows heissen npm/npx .cmd - sonst findet Python sie nicht."""
    kandidaten = ([name + ".cmd", name] if platform.system() == "Windows"
                  else [name])
    for k in kandidaten:
        p = shutil.which(k)
        if p:
            return p
    return None


def vorhanden(schluessel):
    """Pfad eines bereits eingerichteten Projekts - oder None."""
    eigenes = BASIS / schluessel
    if (eigenes / "package.json").exists():
        return eigenes
    for ort in EIGENE_ORTE:
        try:
            kandidat = ort / schluessel
            if (kandidat / "package.json").exists():
                return kandidat
        except Exception:
            pass
    return None


def einrichten(schluessel):
    """Projekt anlegen und Abhaengigkeiten installieren."""
    info = WERKZEUGE[schluessel]
    ziel = BASIS / schluessel
    BASIS.mkdir(parents=True, exist_ok=True)
    print("Richte {} ein ({}) ...".format(info["titel"], info["hinweis"]))
    print("  Ziel: {}".format(ziel))
    print("  Das laedt einige hundert MB und dauert ein paar Minuten.")

    befehl = [t.replace("{ziel}", str(ziel)) for t in info["befehl"]]
    programm = npm_befehl(befehl[0])
    if not programm:
        print("  FEHLER: {} nicht gefunden.".format(befehl[0]))
        return False
    r = run([programm] + befehl[1:], cwd=str(BASIS))
    if not (ziel / "package.json").exists():
        print("  FEHLER beim Anlegen: "
              + ((r.stderr or r.stdout or "")[:250]))
        return False

    npm = npm_befehl("npm")
    if npm:
        print("  Installiere Abhaengigkeiten ...")
        r2 = run([npm, "install"], cwd=str(ziel))
        if r2.returncode != 0 and not (ziel / "node_modules").exists():
            print("  WARNUNG: 'npm install' hat nicht sauber durchlaufen.")
            print("  " + ((r2.stderr or "")[:200]))
            return False
    print("  OK: {} steht.".format(info["titel"]))
    return True


def main():
    p = argparse.ArgumentParser(description="Grafik-Werkzeuge einrichten")
    p.add_argument("--nur", choices=sorted(WERKZEUGE),
                   help="nur dieses eine Werkzeug")
    p.add_argument("--pruefen", action="store_true",
                   help="nur nachsehen, nichts anlegen")
    a = p.parse_args()

    if not npm_befehl("node"):
        print("FEHLER: Node.js fehlt. Zuerst: install_tools.py node")
        return 2

    gewuenscht = [a.nur] if a.nur else list(WERKZEUGE)
    fehlend = []
    for s in gewuenscht:
        pfad = vorhanden(s)
        if pfad:
            print("[da]    {:<15} {}".format(WERKZEUGE[s]["titel"], pfad))
        else:
            print("[fehlt] {:<15} {}".format(WERKZEUGE[s]["titel"],
                                             WERKZEUGE[s]["hinweis"]))
            fehlend.append(s)

    if a.pruefen or not fehlend:
        if not fehlend:
            print("")
            print("Alles vorhanden.")
        return 0

    print("")
    fehler = [s for s in fehlend if not einrichten(s)]
    print("")
    if fehler:
        print("NICHT eingerichtet: "
              + ", ".join(WERKZEUGE[s]["titel"] for s in fehler))
        return 1
    print("FERTIG. Die Grafik-Werkzeuge liegen unter " + str(BASIS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
