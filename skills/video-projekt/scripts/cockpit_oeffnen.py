#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Oeffnet das Cockpit (oder die Startseite) in einem Browser, der direkt
in Ordner speichern kann.

    <python> cockpit_oeffnen.py <projektordner | editor.html | Startseite.html>

Warum nicht einfach der Standardbrowser: Automatisches Speichern ins Projekt
braucht die Ordner-Freigabe des Browsers (File System Access). Die koennen
nur Chrome, Edge, Brave, Arc, Opera und Vivaldi — Safari und Firefox nicht;
dort waere jedes Speichern ein Download. Deshalb wird ein solcher Browser
bevorzugt, wenn er installiert ist, sonst der Standardbrowser (mit Hinweis).

Windows UND Mac (und Linux) — siehe SKILL.md, Grundregel.
"""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

MAC_APPS = ['Google Chrome', 'Microsoft Edge', 'Brave Browser', 'Arc',
            'Vivaldi', 'Opera', 'Chromium']
LINUX_BEFEHLE = ['google-chrome', 'google-chrome-stable', 'microsoft-edge',
                 'brave-browser', 'chromium', 'chromium-browser', 'vivaldi']


def _windows_browser():
    kandidaten = []
    for basis in (os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'),
                  os.environ.get('LOCALAPPDATA')):
        if not basis:
            continue
        kandidaten += [os.path.join(basis, 'Google', 'Chrome', 'Application', 'chrome.exe'),
                       os.path.join(basis, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
                       os.path.join(basis, 'BraveSoftware', 'Brave-Browser',
                                    'Application', 'brave.exe')]
    return next((k for k in kandidaten if os.path.isfile(k)), None)


def _mac_app():
    for app in MAC_APPS:
        for basis in ('/Applications', os.path.expanduser('~/Applications')):
            if os.path.isdir(os.path.join(basis, app + '.app')):
                return app
    return None


def oeffnen(ziel):
    """Oeffnet ziel; gibt True zurueck, wenn ein speicherfaehiger Browser lief."""
    ziel = os.path.abspath(ziel)
    if os.path.isdir(ziel):
        ziel = os.path.join(ziel, 'editor.html')
    if not os.path.isfile(ziel):
        print('FEHLER: nicht gefunden: ' + ziel)
        return False
    uri = Path(ziel).as_uri()
    system = platform.system()
    if system == 'Windows':
        exe = _windows_browser()
        if exe:
            subprocess.Popen([exe, uri])
            print('Geoeffnet in ' + os.path.basename(exe) + ': ' + ziel)
            return True
        os.startfile(ziel)                      # noqa: Windows-only
    elif system == 'Darwin':
        app = _mac_app()
        if app:
            subprocess.Popen(['open', '-a', app, ziel])
            print('Geoeffnet in ' + app + ': ' + ziel)
            return True
        subprocess.Popen(['open', ziel])
    else:
        befehl = next((b for b in LINUX_BEFEHLE if shutil.which(b)), None)
        if befehl:
            subprocess.Popen([befehl, uri])
            print('Geoeffnet in ' + befehl + ': ' + ziel)
            return True
        subprocess.Popen(['xdg-open', ziel])
    print('Geoeffnet im Standardbrowser: ' + ziel)
    print('HINWEIS: Kein Chrome/Edge gefunden. Im Standardbrowser (z. B. Safari')
    print('oder Firefox) kann das Cockpit nicht automatisch speichern - jedes')
    print('Speichern wird ein Download. Empfehlung an den Nutzer: Chrome')
    print('installieren (kostenlos), dann speichert es von selbst ins Projekt.')
    return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    oeffnen(sys.argv[1])
    sys.exit(0)
