#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Oeffnet den Motion-Canvas-Editor im ECHTEN Browser des Nutzers.

Hintergrund (teuer gelernt am 21.08.2026): Claude darf den Editor NIEMALS
in seinem eingebauten Browser oeffnen. Dieser ist fuer den Nutzer nicht
sichtbar - er sieht kein Fenster, weiss nicht, dass auf seinen Klick
gewartet wird, und der Browser drosselt unsichtbare Tabs bis zum
Stillstand (gemessen: 0 Bilder in 30 Sekunden statt 349 in einer Minute).
Ein Nutzer wartete dadurch 20 Minuten auf nichts.

    python editor_oeffnen.py                 # http://localhost:9000
    python editor_oeffnen.py --port 9001
    python editor_oeffnen.py --pruefen       # nur pruefen, nicht oeffnen

Exit 0 = Editor laeuft und wurde im Standardbrowser geoeffnet
Exit 1 = Editor antwortet nicht (npm start vergessen?)
"""
import argparse
import platform
import subprocess
import sys
import urllib.error
import urllib.request


def laeuft(url, timeout=3):
    """True, wenn unter url etwas antwortet."""
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except urllib.error.HTTPError:
        return True          # antwortet, nur nicht mit 200 - reicht
    except Exception:
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
        description="Motion-Canvas-Editor im echten Browser oeffnen")
    p.add_argument("--port", type=int, default=9000)
    p.add_argument("--pruefen", action="store_true",
                   help="nur pruefen, ob der Editor laeuft")
    a = p.parse_args()
    url = "http://localhost:" + str(a.port)

    if not laeuft(url):
        print("FEHLER: Unter " + url + " antwortet nichts.")
        print("Zuerst im Motion-Canvas-Projektordner 'npm start' starten")
        print("(am besten als Hintergrundbefehl), dann dieses Script erneut.")
        return 1

    if a.pruefen:
        print("Editor laeuft: " + url)
        return 0

    if not im_standardbrowser(url):
        return 1

    print("Editor im Standardbrowser geoeffnet: " + url)
    print("")
    print("DEM NUTZER JETZT WOERTLICH SAGEN:")
    print("  'Es hat sich gerade ein Browserfenster geoeffnet -")
    print("   schau bitte in deinen eigenen Browser (Chrome/Edge).")
    print("   Dort siehst du die Vorschau.'")
    print("")
    print("Fuer den Render zusaetzlich: 'Klick dort unten rechts auf")
    print("Render und lass das Fenster sichtbar im Vordergrund -")
    print("minimierte Tabs werden vom Browser eingefroren.'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
