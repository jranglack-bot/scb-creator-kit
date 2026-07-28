#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schaltet das /watch-Plugin (bradautomates/claude-video) frei.

Claude ruft dieses Script auf, nachdem der User zugestimmt hat.
Der User muss KEIN Terminal oeffnen und keinen Slash-Befehl tippen.

Das Script merged NUR die noetigen Schluessel in ~/.claude/settings.json
und laesst alles andere unangetastet. Vorher wird eine Sicherung angelegt.

    python install_watch.py

Rueckgabe: Exit 0 = fertig, Exit 1 = fehlgeschlagen.
"""
import json
import os
import shutil
import sys

MARKT = "claude-video"
PLUGIN = "watch@claude-video"
REPO = "bradautomates/claude-video"


def main():
    pfad = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    os.makedirs(os.path.dirname(pfad), exist_ok=True)

    daten = {}
    if os.path.exists(pfad):
        try:
            with open(pfad, encoding="utf-8-sig") as f:
                inhalt = f.read().strip()
            daten = json.loads(inhalt) if inhalt else {}
        except json.JSONDecodeError as e:
            print(f"FEHLER: {pfad} ist kein gueltiges JSON ({e}).")
            print("Nichts veraendert. Bitte die Datei pruefen.")
            return 1
        # Sicherung nur anlegen, wenn es etwas zu sichern gibt
        shutil.copyfile(pfad, pfad + ".backup")
        print(f"Sicherung angelegt: {pfad}.backup")

    if not isinstance(daten, dict):
        print("FEHLER: settings.json enthaelt kein Objekt.")
        return 1

    schon_da = daten.get("enabledPlugins", {}).get(PLUGIN) is True

    # Gezielt mergen - bestehende Eintraege bleiben erhalten
    daten.setdefault("enabledPlugins", {})[PLUGIN] = True
    daten.setdefault("extraKnownMarketplaces", {})[MARKT] = {
        "source": {"source": "github", "repo": REPO}
    }

    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

    if schon_da:
        print("Das Plugin war bereits freigeschaltet - Eintrag aufgefrischt.")
    else:
        print(f"Freigeschaltet: {PLUGIN} (Quelle: {REPO})")
    print(f"Geschrieben: {pfad}")
    print("")
    print("FERTIG. Claude Code einmal neu starten, danach ist /watch da.")
    print(f"Rueckgaengig: in {pfad} den Eintrag {PLUGIN} auf false setzen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
