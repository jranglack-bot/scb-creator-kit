---
name: obsidian-gehirn
description: >
  Richtet ein Obsidian-Vault als "zweites Gehirn" für Claude ein: legt die
  SCB-Ordnerstruktur an (Kontext, Inbox, Claude Memory, Hooks) und
  installiert auf Wunsch einen Hook, der Claudes Memory-Notizen automatisch
  in den Vault spiegelt. Verwende diesen Skill bei: "verbinde Obsidian",
  "richte mein Obsidian ein", "Claude Gehirn einrichten", "Memory in
  Obsidian speichern", "zweites Gehirn", oder wenn der Setup-Assistent
  (scb-setup) den Bereich Obsidian einrichtet.
---

# Obsidian-Gehirn einrichten

Verbinde Claude mit dem Obsidian-Vault des Users: Ordnerstruktur anlegen und
optional die automatische Memory-Spiegelung installieren. Alles auf Deutsch
erklären, der User ist kein Techniker.

## Schritt 1: Vault finden oder anlegen

Frage nach dem Vault-Pfad oder suche danach (Ordner, die einen
`.obsidian`-Unterordner enthalten):

```powershell
foreach ($r in @("$env:USERPROFILE\OneDrive","$env:USERPROFILE\Documents","$env:USERPROFILE\Desktop")) {
  if (Test-Path $r) { Get-ChildItem -Path $r -Directory -Filter ".obsidian" -Recurse -Depth 4 -ErrorAction SilentlyContinue | ForEach-Object { $_.Parent.FullName } }
}
```

Gefundene Vaults dem User zeigen und bestätigen lassen. Hat er noch keinen:
Obsidian von https://obsidian.md installieren lassen und einen neuen Vault
anlegen (empfohlener Name: „Claude Gehirn").

## Schritt 2: Ordnerstruktur anlegen

Lege im Vault diese Ordner an (vorhandene nicht anfassen):

```
00 Kontext/        ← wer der User ist: Schreibstil, Branding, ICP, Angebote, Über Mich
01 Inbox/          ← schnelle Notizen, Brain Dumps
02 Claude Memory/  ← hierhin spiegelt Claude seine Memory-Notizen
03 Hooks/          ← Instagram-Hooks & Reel-Formeln, die sich bewähren
```

Lege in `00 Kontext/` leere Start-Notizen an: `Schreibstil.md`, `Branding.md`,
`ICP.md`, `Angebote.md`, `Über Mich.md` — nur falls sie fehlen. Erkläre dem
User: „Diese Notizen füllt Claude nach und nach, wenn du ihm etwas über dich
erzählst — du kannst sie auch selbst pflegen."

## Schritt 3: Automatische Memory-Spiegelung (optional, empfohlen)

Frage: „Soll Claude alles, was er sich über dich merkt, automatisch als Notiz
in deinen Vault spiegeln? Dann hast du sein Gedächtnis immer im Blick."

Wenn ja:

1. Ermittle das Memory-Verzeichnis des aktuellen Projekts:
   `~/.claude/projects/<projekt-ordner>/memory/` (der Projekt-Ordnername ist
   der aktuelle Arbeitsordner mit `-` statt `\` und `:`). Existiert noch kein
   Memory-Ordner, erkläre, dass die Spiegelung greift, sobald sich Claude das
   erste Mal etwas merkt.
2. Kopiere das Script `scripts/mirror-memory-to-obsidian.template.ps1` (liegt
   in diesem Skill-Ordner) nach `~/.claude/hooks/mirror-memory-to-obsidian.ps1`
   und ersetze darin die Platzhalter `__MEMORY_DIR__` (Memory-Verzeichnis) und
   `__VAULT_DIR__` (Vault-Ordner `02 Claude Memory`).
3. Trage in `~/.claude/settings.json` einen PostToolUse-Hook ein — **bestehende
   Einträge dabei erhalten, nur mergen**:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "powershell",
            "args": ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", "<PFAD>\\mirror-memory-to-obsidian.ps1"],
            "statusMessage": "Spiegle Memory nach Obsidian...",
            "timeout": 20
          }
        ]
      }
    ]
  }
}
```

4. Teste: schreibe eine Wegwerf-Datei `_mirror-test.md` ins Memory-Verzeichnis
   (per Write-Tool, damit der Hook feuert), prüfe, dass die Kopie im Vault
   liegt, und lösche beide Testdateien wieder.

## Schritt 4: Merk-Regel erklären

Erkläre dem User zum Abschluss:

> Ab jetzt gilt: Sag einfach **„Merk dir: …"** — Claude speichert es auf
> Deutsch, es erscheint automatisch in `02 Claude Memory`, und Wissen über
> dich (Schreibstil, Branding, Zielgruppe, Angebote) pflegt Claude zusätzlich
> in die passende Notiz unter `00 Kontext` ein. Gute Instagram-Hooks sammelt
> er in `03 Hooks`.

Diese Einsortier-Regel dann auch selbst befolgen (als Memory speichern, damit
sie in allen Sessions gilt).

## Wichtige Regeln

- Vault-Notizen des Users nie überschreiben — nur ergänzen oder neue anlegen.
- Keine API-Keys oder Tokens in den Vault schreiben (liegt oft in OneDrive/Cloud!).
- Liegt der Vault in OneDrive, darauf hinweisen, dass er automatisch in die
  Cloud synchronisiert wird.
