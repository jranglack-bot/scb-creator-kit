---
name: video-projekt
description: >
  Projekt-Modus für Video-Editing: verwaltet jedes Video als Projekt-Datei
  (Schnitte, Untertitel, Effekte), rendert in Stufen (Korrekturen ohne
  Komplett-Neuanalyse) und bietet das Video-Cockpit — einen lokalen
  Browser-Editor, in dem der Nutzer Schnitte auf der Timeline verschieben,
  Untertitel ziehen und Bild-im-Bild skalieren kann, bevor gerendert wird.
  Verwende diesen Skill bei: "schneide mein Video" (als Ober-Workflow),
  "ich will die Schnitte selbst prüfen", "öffne das Cockpit", "mach es
  editierbar", "für Canva exportieren", "Schnitt anpassen", "Untertitel
  verschieben", oder wenn nach einem Render Korrekturen kommen.
---

# Video-Projekt-Modus (Cockpit + Stufen-Rendering)

Jedes Video ist ein **Projekt**: ein Ordner mit dem Original, einer
`projekt.json` (die einzige Wahrheit über Schnitte, Untertitel, Effekte)
und optional dem Cockpit. Korrekturen ändern NUR die projekt.json — nie
wird neu analysiert, nie Code neu geschrieben.

## Projekt-Struktur

```
<videoname>-projekt/
  original.mp4        (unangetastet)
  projekt.json        (Schnitte + Wortliste + alle Einstellungen)
  schnittliste.md     (lesbar: Zeit, Zitat, Grund je Schnitt)
  editor.html         (Cockpit, per build_editor.py erzeugt)
  01_schnitt.mp4      (Stufe 1: nur geschnitten — wird wiederverwendet!)
  final.mp4           (Stufe 2: mit allen Effekten)
```

`projekt.json`-Kern: `video`, `duration`, `cuts` (start/end/reason/active),
`words` (Transkript der Original-Timeline), `captions` (enabled/size/y/
primary/highlight/group), `pip` (enabled/x/y/scale) — plus alle
prolook-Configs (music, transition, broll …).

## Workflow

### 1. Analyse (einmalig pro Video)
Wie in `video-schneiden` (Transkript, kompakter Fließtext, Schnitt-Analyse)
— aber die Cuts landen mit Textzitat + Grund in `projekt.json` UND als
lesbare `schnittliste.md`. Bei Material OHNE Sprache: den Nutzer fragen
(eigene Zeitstempel / automatische Szenenwechsel-Vorschläge via
`ffmpeg select=gt(scene,0.3)` / feste Taktung) — Vorschläge ebenfalls in
die Schnittliste.

### 2. Kontrolle — den Nutzer WÄHLEN lassen (einmal fragen, Antwort merken)
> „Willst du die Schnitte selbst prüfen? Ich kann dir (a) die Schnittliste
> zum Lesen zeigen, (b) das Cockpit öffnen — ein Editor im Browser, wo du
> Schnitte verschieben, Untertitel ziehen und Bild-im-Bild anpassen kannst
> — oder (c) du vertraust mir und ich rendere direkt."

Cockpit-Weg — **EIN-TAB-PRINZIP (wichtig!):**
`python scripts/build_editor.py <projekt.json>` erzeugt `editor.html`
(statisch) + `projekt_data.js` (die Daten). Das offene Cockpit lädt die
Daten-Datei alle 2,5 s selbst nach — **Änderungen von Claude erscheinen im
offenen Tab von allein.** Deshalb: `Start-Process editor.html` NUR beim
allerersten Erstellen des Cockpits. Bei jeder späteren Änderung NUR
`build_editor.py` ausführen und dem User sagen „schau in deinen offenen
Tab" — NIEMALS erneut öffnen (das erzeugt verwirrende Doppel-Tabs). Hat
der User ungespeicherte Änderungen, zeigt das Cockpit einen
Übernehmen/Behalten-Banner statt sie zu überschreiben.

Der Nutzer arbeitet dort OHNE Token-Verbrauch:
Timeline unten zeigt das GANZE Video, Schnitte rot, Kanten ziehbar,
Doppelklick = Schnitt an/aus, „Vorschau: Schnitte überspringen" spielt das
Video wie geschnitten. Bei aktivem Bild-im-Bild gibt es ZWEI Videospuren
(Aufziehen auf einer Spur schneidet nur dieses Video); „Tonspur anzeigen"
blendet die Waveform ein — die Daten (`waveform_data.js`) erzeugt
`build_editor.py` automatisch und gecacht (braucht ffmpeg). Untertitel: Live-Vorschau mit Wort-Highlight, per
Maus vertikal ziehbar, Größe/Farben rechts, Safe-Zones einblendbar.
Bild-im-Bild: Rahmen ziehen + an der Ecke skalieren.

**Speichern legt `projekt.json` in den Downloads-Ordner** (Browser können
lokal nicht direkt zurückschreiben). Wenn der Nutzer „fertig" sagt: neueste
`projekt.json` aus `%USERPROFILE%\Downloads` in den Projektordner
verschieben (alte ersetzen), dann rendern.

### 2b. Schnitte pro Videospur (`track` je Schnitt aus dem Cockpit)

Bei aktivem Bild-im-Bild zeigt das Cockpit ZWEI Videospuren (oben großes,
unten kleines Video). Jeder Schnitt trägt `track`: `both` | `main` | `pip` —
gesetzt beim Aufziehen auf einer Spur bzw. per „Gilt für"-Dropdown in der
Schnittliste. Altbestand ohne `track`: das alte globale `cuts_apply` gilt
als Default (das Cockpit stempelt es beim Laden auf jeden Schnitt).

Beim Rendern ZWEI Schnittlisten bilden (nur aktive Schnitte):
- **Großes Video:** alle Schnitte mit `track` `main` oder `both`
- **Kleines Video:** alle Schnitte mit `track` `pip` oder `both`

Jede Quelldatei mit IHRER Liste schneiden (z. B. `01_schnitt_main.mp4`,
`01_schnitt_pip.mp4`; leere Liste = Originaldatei unverändert verwenden).
Danach wie gehabt: Datei laut Ton-Quelle als prolook-`input`, die andere als
`pip.background`; ist das große Video (Background) am Ende kürzer als das
kleine → `pip.background_end: "freeze"`.

Untertitel-Wortzeiten dabei passend wählen: Sie folgen dem TON — also der
Datei, die als `input` läuft (ungeschnittene Datei = Original-Zeiten
unverändert!).

**Ton-Quelle (`audio_from` aus dem Cockpit):** `main`, `pip` oder `both` —
beim Rendern gilt: Der Ton kommt aus der prolook-`input`-Datei. Also bei
`main`/`pip` die Datei mit dem gewünschten Ton als `input` setzen und die
andere als `pip.background` (das Layout — wer groß/klein ist — steuern
`pip.x/y/scale` unabhängig davon). Bei `both` als `input` die Ton-/Zeit-führende Datei
nehmen und zusätzlich `"mix_audio": true` in die
`pip`-Config setzen — prolook mischt dann den Ton des `pip.background`
dazu (Lautstärke-Balance optional via `pip.audio_gain`, Standard 1.0). Die
Cockpit-Vorschau schaltet exakt so stumm wie der Render (bei `both` spielen
beide).

### 2c. Claude arbeitet im Projekt mit (Roundtrip)

Sagt der User z. B. „setz noch einen Schnitt bei 20–22" oder „ändere die
Schriftfarbe": ERST prüfen, ob er im Cockpit ungespeicherte Änderungen hat
(„Hast du im Cockpit gespeichert? Sonst geht deine Maus-Arbeit verloren") —
ggf. neueste projekt.json aus Downloads einspielen. Dann projekt.json
ändern, `build_editor.py` neu ausführen, User drückt F5. Kosten: eine
JSON-Änderung.

Die Untertitel-`font` aus dem Cockpit (Windows-Systemschriften-Dropdown)
als `--font` an `animated_captions.py` durchreichen.

### 3. Stufen-Rendering (Zeit sparen, nichts doppelt tun)
- **Stufe 1 — Schnitt:** nur wenn sich `cuts` geändert haben (oder noch
  kein `01_schnitt.mp4` existiert): Keep-Segmente aus den aktiven Cuts
  berechnen → select/aselect-Render wie in `video-schneiden` Schritt 7.
- **Stufe 2 — Look:** `prolook.py` auf `01_schnitt.mp4` mit den Werten aus
  projekt.json. Untertitel: `animated_captions.py` mit angepassten Flags —
  `--size` aus captions.size, MarginV = `int(1920 * (1 - captions.y))`,
  Farben aus primary/highlight. WICHTIG: Wortzeiten gelten für die
  ORIGINAL-Timeline → vor der ASS-Erzeugung auf die geschnittene Timeline
  umrechnen (je Wort: neue Zeit = alte Zeit − Summe aller aktiven
  Cut-Längen davor; Wörter innerhalb von Cuts entfallen). Kleines
  Python-Snippet, deterministisch.
- **Nur Untertitel/Stil geändert?** → Stufe 1 überspringen, nur Stufe 2
  (Sekunden statt Minuten).

### 4. Export-Ziele (Frag-zuerst, Wahl im Profil merken)
| Ziel | Ergebnis |
|---|---|
| **Fertig-Reel** | final.mp4 mit allem Gewählten (Captions, Effekte, Audio-Suite) |
| **Cockpit** | Nutzer justiert selbst, dann Fertig-Reel |
| **Editierbar (Canva/CapCut)** | `01_schnitt.mp4` (+ Stimm-Mastering/Loudness, OHNE eingebrannte Elemente) + `untertitel.srt` aus den umgerechneten Wortzeiten. Hinweis: Canva importiert kein SRT — dort eigene Auto-Captions nutzen; CapCut/Premiere/DaVinci können SRT. Bild-im-Video baut Canva selbst (zwei Spuren). |

## Token-Regeln

- Korrektur = projekt.json-Feld ändern + Stufen-Render. NIE neu
  transkribieren, NIE Cuts neu analysieren, NIE Effekt-Code schreiben.
- Cockpit-Feinarbeit kostet 0 Tokens — dorthin lenken, wenn der Nutzer
  mehrfach Stil-/Positionswünsche äußert.
- QC wie gewohnt: 1–2 Frames nach finalem Render, nicht pro Zwischenschritt.
- Alle Effekt-Extras bleiben Frag-zuerst (siehe `pro-look-editing`).
