#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Oeffnet die Grafik-Vorschau im ECHTEN Browser des Nutzers.

    python editor_oeffnen.py                  # Motion Canvas, localhost:9000
    python editor_oeffnen.py --remotion       # Remotion Studio, localhost:3000
    python editor_oeffnen.py --pruefen        # nur pruefen, nicht oeffnen

Hintergrund 1 (teuer gelernt am 21.08.2026): Claude darf die Vorschau
NIEMALS in seinem eingebauten Browser oeffnen. Dieser ist fuer den Nutzer
nicht sichtbar - er sieht kein Fenster, weiss nicht, dass auf seinen Klick
gewartet wird, und der Browser drosselt unsichtbare Tabs bis zum
Stillstand (gemessen: 0 Bilder in 30 Sekunden statt 349 in einer Minute).
Ein Nutzer wartete dadurch 20 Minuten auf nichts.

Hintergrund 2 (teuer gelernt am 23.08.2026): 25 Minuten fuer eine
15-Sekunden-Grafik, weil das Remotion Studio NICHT geoeffnet wurde. Claude
prueft die Grafik dann ueber einzelne CLI-Aufrufe - Testrender,
Kontrollbilder -, und jeder einzelne baut das Projekt neu (rund 40 s). Der
Nutzer sieht die Grafik erst im fertigen Video, wo er nichts mehr aendern
kann. Darum startet dieses Script das Studio bei Bedarf SELBST.

Exit 0 = Vorschau laeuft und wurde im Standardbrowser geoeffnet
Exit 1 = Vorschau antwortet nicht / liess sich nicht starten
"""
import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Wo ein Remotion-Projekt liegen kann - Reihenfolge = Suchreihenfolge
ORTE = [
    Path.home() / ".scb-creator-kit" / "grafik" / "remotion",
    Path("D:/Instagram Content/remotion"),
    Path("C:/Instagram Content/remotion"),
    Path.home() / "remotion",
]


def laeuft(url, timeout=3):
    """True, wenn unter url etwas antwortet."""
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True          # antwortet, nur nicht mit 200 - reicht
    except Exception:
        return False


def npm_befehl(name):
    """Auf Windows heissen npm/npx .cmd - sonst findet Python sie nicht."""
    kandidaten = ([name + ".cmd", name] if platform.system() == "Windows"
                  else [name])
    for k in kandidaten:
        p = shutil.which(k)
        if p:
            return p
    return None


def remotion_projekt(vorgabe=None):
    """Findet den Remotion-Projektordner. None, wenn keiner da ist."""
    kandidaten = [Path(vorgabe)] if vorgabe else list(ORTE)
    for ordner in kandidaten:
        pkg = ordner / "package.json"
        if not pkg.exists():
            continue
        try:
            daten = json.loads(pkg.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        alle = {}
        alle.update(daten.get("dependencies") or {})
        alle.update(daten.get("devDependencies") or {})
        if any(k == "remotion" or k.startswith("@remotion/") for k in alle):
            return ordner
    return None


def studio_starten(ordner, port):
    """Startet 'remotion studio' im Hintergrund, wartet bis es antwortet.

    Der Befehl heisst 'studio'. 'remotion preview' gibt es seit Remotion 4
    NICHT mehr - geprueft an @remotion/cli 4.0.507. Im Zweifel
    'npx remotion help' fragen: das kostet zwei Sekunden, ein Fehlversuch
    kostet drei Minuten.
    """
    npx = npm_befehl("npx")
    if not npx:
        print("FEHLER: npx nicht gefunden - Node.js fehlt.")
        print("Setup-Assistent nachziehen: alles_pruefen.py --update")
        return False

    log = ordner / "studio.log"
    print("Studio wird gestartet ...")
    print("Das dauert etwa eine Minute (gemessen 23.08.2026: 71 s auf einem")
    print("mittleren Windows-Rechner). Beim allerersten Mal laenger.")
    try:
        with open(log, "w", encoding="utf-8") as f:
            kw = {}
            if platform.system() == "Windows":
                kw["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                                       | 0x00000008)   # DETACHED_PROCESS
            else:
                kw["start_new_session"] = True
            subprocess.Popen(
                [npx, "--yes", "remotion", "studio", "--port", str(port)],
                cwd=str(ordner), stdout=f, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, **kw)
    except Exception as e:
        print("Konnte das Studio nicht starten: " + str(e))
        return False

    url = "http://localhost:" + str(port)
    # 180 s, nicht 90: gemessen wurden 71 s: ein knappes Limit laesst den
    # Start scheitern, obwohl das Studio gleich danach da waere.
    for _ in range(180):
        time.sleep(1)
        if laeuft(url, timeout=2):
            return True

    print("FEHLER: Das Studio antwortet nach 3 Minuten nicht.")
    print("Was es sagt, steht in: " + str(log))
    return False


def im_standardbrowser(url):
    """Oeffnet url im Standardbrowser des Nutzers - sichtbares Fenster."""
    system = platform.system()
    try:
        if system == "Windows":
            # start ueber cmd: nimmt den eingestellten Standardbrowser
            subprocess.run(["cmd", "/c", "start", "", url], check=True)
        elif system == "Darwin":
            subprocess.run(["open", url], check=True)
        else:
            subprocess.run(["xdg-open", url], check=True)
        return True
    except Exception as e:
        print("Konnte den Browser nicht starten: " + str(e))
        return False


def main():
    p = argparse.ArgumentParser(
        description="Grafik-Vorschau im echten Browser oeffnen")
    p.add_argument("--remotion", action="store_true",
                   help="Remotion Studio statt Motion Canvas (Port 3000)")
    p.add_argument("--projekt", help="Projektordner (nur mit --remotion)")
    p.add_argument("--port", type=int,
                   help="Standard: 9000 (Motion Canvas), 3000 (Remotion)")
    p.add_argument("--pruefen", action="store_true",
                   help="nur pruefen, ob die Vorschau laeuft")
    a = p.parse_args()

    port = a.port or (3000 if a.remotion else 9000)
    url = "http://localhost:" + str(port)
    titel = "Remotion Studio" if a.remotion else "Motion-Canvas-Editor"

    if not laeuft(url):
        if not a.remotion:
            print("FEHLER: Unter " + url + " antwortet nichts.")
            print("Zuerst im Motion-Canvas-Projektordner 'npm start' starten")
            print("(am besten als Hintergrundbefehl), dann dieses Script "
                  "erneut.")
            return 1
        if a.pruefen:
            print("Studio laeuft nicht: " + url)
            return 1
        ordner = remotion_projekt(a.projekt)
        if not ordner:
            print("FEHLER: Kein Remotion-Projekt gefunden. Gesucht in:")
            for o in ORTE:
                print("  " + str(o))
            print("Anlegen mit: grafik_einrichten.py --nur remotion")
            return 1
        print("Remotion-Projekt: " + str(ordner))
        if not studio_starten(ordner, port):
            return 1

    if a.pruefen:
        print(titel + " laeuft: " + url)
        return 0

    if not im_standardbrowser(url):
        return 1

    print(titel + " im Standardbrowser geoeffnet: " + url)
    print("")
    print("DEM NUTZER JETZT WOERTLICH SAGEN:")
    print("  'Es hat sich gerade ein Browserfenster geoeffnet -")
    print("   schau bitte in deinen eigenen Browser (Chrome/Edge).")
    print("   Dort siehst du die Vorschau.'")
    print("")
    if a.remotion:
        print("AB JETZT GILT: nicht rendern, bevor er die Grafik im Studio")
        print("gesehen und freigegeben hat. Aenderungen an Text, Farbe,")
        print("Timing und Reihenfolge kosten im Studio NICHTS - er sieht sie")
        print("sofort. Keine Testrenders, keine Kontrollbilder.")
    else:
        print("Fuer den Render zusaetzlich: 'Klick dort unten rechts auf")
        print("Render und lass das Fenster sichtbar im Vordergrund -")
        print("minimierte Tabs werden vom Browser eingefroren.'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
