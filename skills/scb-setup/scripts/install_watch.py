#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Installiert das /watch-Plugin (bradautomates/claude-video) ueber die
offiziellen claude-plugin-Befehle - derselbe Weg, ueber den auch das
SCB Creator Kit selbst installiert wird.

Claude ruft dieses Script auf, nachdem der User zugestimmt hat.
Der User muss KEIN Terminal oeffnen und keinen Slash-Befehl tippen.

Es wird NICHTS von Hand in Claudes Konfigurationsdateien geschrieben -
die Registrierung erledigt die Claude-CLI selbst.

    python install_watch.py

Rueckgabe: Exit 0 = fertig (Neustart noetig)
           Exit 1 = fehlgeschlagen
           Exit 3 = der Befehl "claude" fehlt auf diesem Rechner.
                    Dann zuerst Claude Code mit dem offiziellen Installer
                    nachziehen (Mac/Linux:
                    curl -fsSL https://claude.ai/install.sh | bash
                    Windows-PowerShell:
                    irm https://claude.ai/install.ps1 | iex
                    - kein Admin-Passwort noetig), danach dieses Script
                    erneut ausfuehren.
"""
import os
import platform
import shutil
import subprocess
import sys

MARKT = "claude-video"
REPO = "bradautomates/claude-video"
PLUGIN = "watch@claude-video"


def claude_cli():
    """Pfad zur claude-CLI - PATH zuerst, dann der Standard-Installationsort."""
    p = shutil.which("claude")
    if p:
        return p
    name = "claude.exe" if platform.system() == "Windows" else "claude"
    kandidat = os.path.join(os.path.expanduser("~"), ".local", "bin", name)
    return kandidat if os.path.exists(kandidat) else None


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def main():
    cli = claude_cli()
    if not cli:
        print("FEHLER: Der Befehl 'claude' wurde nicht gefunden.")
        print("Zuerst Claude Code mit dem offiziellen Installer nachziehen")
        print("(siehe Kopf dieses Scripts), dann dieses Script erneut starten.")
        return 3

    print(f"Registriere Marketplace {REPO} ...")
    r = run([cli, "plugin", "marketplace", "add", REPO])
    ausgabe = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0 and "already" not in ausgabe.lower():
        print("FEHLER beim Marketplace-Hinzufuegen:", ausgabe.strip()[:300])
        return 1
    print("  OK")

    print(f"Installiere {PLUGIN} ...")
    r = run([cli, "plugin", "install", PLUGIN])
    ausgabe = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0 and "already" not in ausgabe.lower():
        print("FEHLER bei der Installation:", ausgabe.strip()[:300])
        return 1
    print("  OK")

    print("")
    print("FERTIG. Claude Code einmal neu starten, danach ist /watch da.")
    print(f"Rueckgaengig: claude plugin uninstall {PLUGIN}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
