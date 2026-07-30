#!/bin/bash
# mirror-memory-to-obsidian.sh  (Template — Platzhalter werden vom Setup ersetzt)
# PostToolUse-Hook (Matcher Write|Edit) fuer macOS und Linux — Gegenstueck zur
# .ps1-Variante fuer Windows. Wenn Claude eine Memory-.md-Datei schreibt oder
# bearbeitet, wird sie 1:1 in den Obsidian-Vault gespiegelt.
# Blockiert nie: Exit-Code ist immer 0.
#
# Nach dem Kopieren ausfuehrbar machen:  chmod +x <pfad>/mirror-memory-to-obsidian.sh

MEM_DIR='__MEMORY_DIR__'
VAULT='__VAULT_DIR__'

# Das Hook-JSON kommt auf stdin. jq ist auf macOS NICHT vorinstalliert,
# deshalb uebernimmt python3 das Auswerten und Kopieren — Python ist fuer
# das Kit ohnehin Voraussetzung.
python3 -c '
import json, os, shutil, sys

mem, vault = sys.argv[1].rstrip("/"), sys.argv[2]
try:
    daten = json.load(sys.stdin)
except Exception:
    sys.exit(0)

pfad = (daten.get("tool_input") or {}).get("file_path") or ""
if not pfad.endswith(".md") or not os.path.isfile(pfad):
    sys.exit(0)

# nur Dateien AUS dem Memory-Verzeichnis spiegeln
echt = os.path.realpath(pfad)
if not echt.startswith(os.path.realpath(mem) + os.sep):
    sys.exit(0)

os.makedirs(vault, exist_ok=True)
name = os.path.basename(echt)
shutil.copyfile(echt, os.path.join(vault, name))
sys.stdout.write(json.dumps({
    "systemMessage": "Memory -> Obsidian gespiegelt: " + name,
    "suppressOutput": True}))
' "$MEM_DIR" "$VAULT" 2>/dev/null

exit 0
