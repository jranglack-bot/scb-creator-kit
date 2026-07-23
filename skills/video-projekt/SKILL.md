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

Der Nutzer arbeitet dort OHNE Token-Verbrauch. Die Seitenleiste besteht aus
zusammenklappbaren KACHELN (Zustand merkt sich der Browser). Abspielen zeigt
IMMER das geschnittene Ergebnis auf ALLEN Spuren (WYSIWYG); der Schalter
„Rohmaterial zeigen" blendet die herausgeschnittenen Stellen wieder ein.
Timeline unten zeigt das GANZE Video, Schnitte rot, Kanten ziehbar,
Doppelklick = Schnitt an/aus. Vorschau-Zoom: Mausrad über dem Video =
rein-/rauszoomen (auf den Cursor), bei Zoom Bild per Ziehen verschieben,
−/100%/+ unten links (100% = zurücksetzen) — für Detailkontrolle
(Untertitel-Sitz usw.) ohne Token. Kachel „Audio hinzufügen": eigenes Lied
wählen, Voiceover-Datei wählen oder Voiceover direkt mit dem Mikro
aufnehmen (Video läuft stumm mit, Aufnahme ab Reel-Start) — neue Dateien
legt das Cockpit automatisch in Downloads (beim „fertig"-Roundtrip wie die
projekt.json in den Projektordner verschieben, dann `build_editor.py`). Bei aktivem Bild-im-Bild gibt es ZWEI Videospuren
(Aufziehen auf einer Spur schneidet nur dieses Video), mit Musik zusätzlich
eine ♪-Spur; „Tonspur anzeigen" blendet die Waveforms ein — die Daten
(`waveform_data.js`) erzeugt `build_editor.py` automatisch und gecacht
(braucht ffmpeg). Werkzeug-Button oben: ✂ Aufziehen = Schnitt, 🔊 Aufziehen
= Lautstärke-Abschnitt (zeitweise lauter/leiser, blau). Seitenleiste:
Lautstärke-Regler pro Tonspur (großes/kleines Video, Musik). Musik: unter
der Timeline liegt die SONG-ÜBERSICHT (ganzes Lied als Waveform, lila
Fenster = Reel-Ausschnitt — ziehen wählt die Stelle im Lied; Feinjustage
über „Start im Lied"). Untertitel: Live-Vorschau mit Wort-Highlight, per
Maus vertikal ziehbar, Größe/Farben rechts, Safe-Zones einblendbar — und
der TEXT ist direkt editierbar („Untertitel-Text"-Liste; Doppelklick auf
den Untertitel im Video springt zur Zeile). Kachel „Texte": freie
Text-Overlays (Hook/Titel) mit eigener 📝-Spur, Position per Ziehen,
Stil + Einflug-Animation je Text (siehe 2b-Texte). Bild-im-Bild: Rahmen ziehen +
Ecke skalieren + Videodatei per Dropdown wechselbar (Liste `_dateien`
liefert build_editor.py; PiP aus = auch sein Ton aus). Spur-Farben überall
gleich: großes Video blau, kleines grün, beide orange, Musik lila.

**Eigene Cockpit-Erweiterungen NIEMALS in editor.html/das Template bauen**
(Kit-Updates überschreiben es), sondern IMMER in `cockpit_custom.js` im
Projektordner — die lädt das Cockpit automatisch als letztes Script, alle
Funktionen/Variablen sind global und dort ergänz- oder ersetzbar (danach
ggf. `renderTL()` aufrufen). Die Datei überlebt jedes Update. Soll eine
Erweiterung in allen Projekten gelten: zusätzlich unter
`%USERPROFILE%\.scb-creator-kit\cockpit_custom.js` ablegen —
`build_editor.py` kopiert sie in jedes neue Projekt. Wünsche, die für die
ganze Community taugen, dem Kit-Autor (Julian) melden statt lokal bauen.

**Speichern legt `projekt.json` in den Downloads-Ordner** (Browser können
lokal nicht direkt zurückschreiben). Wenn der Nutzer „fertig" sagt: neueste
`projekt.json` aus `%USERPROFILE%\Downloads` in den Projektordner
verschieben (alte ersetzen), dann rendern.

### 2a-Render. Rendern = EIN Befehl (niemals Pipeline improvisieren)

```
python scripts/render_projekt.py <projekt.json>
```

Das Script macht ALLES selbst (Schnittlisten pro Spur, Dateien schneiden,
Lautstärke-Abschnitte, Musik/Voiceover-Vorbereitung, Untertitel- und
Text-ASS, prolook, QC-Kontaktbogen `qc_final.png`). Danach nur den
Kontaktbogen ansehen (1 Bild) und dem User zeigen. `build_editor.py` legt
zusätzlich `video_rendern.bat` in den Projektordner — der User kann per
DOPPELKLICK selbst neu rendern (0 Tokens). Qualitätswünsche („bessere
Qualität") = in projekt.json `"render": {"crf": 18}` setzen (Standard 20,
kleiner = besser; optional `"preset"`, `"output"`). Die Abschnitte 2b ff.
beschreiben das Mapping, das render_projekt.py implementiert — nur lesen,
wenn das Script mal nicht reicht.

### 2b. Schnitte pro Videospur (`track` je Schnitt aus dem Cockpit)

Bei aktivem Bild-im-Bild zeigt das Cockpit ZWEI Videospuren (oben großes,
unten kleines Video). Jeder Schnitt trägt `track`: `both` | `main` | `pip` —
gesetzt beim Aufziehen auf einer Spur bzw. per „Gilt für"-Dropdown in der
Schnittliste. Altbestand ohne `track`: das alte globale `cuts_apply` gilt
als Default (das Cockpit stempelt es beim Laden auf jeden Schnitt).

Beim Rendern ZWEI Schnittlisten bilden (nur aktive Schnitte):
- **Großes Video:** alle Schnitte mit `track` `main` oder `both`
- **Kleines Video:** alle Schnitte mit `track` `pip` oder `both`

WICHTIG: Die Listen sind ZEITLEISTEN-Zeiten. Vor dem Schneiden je Spur in
Quellzeit umrechnen (Aufrück-Formel, macht render_projekt.py automatisch):
Quell-Schnitt_i = [start_i + vorher, end_i + vorher], `vorher` = Summe der
Längen früherer Schnitte derselben Spur — denn nach jedem übersprungenen
Schnitt läuft das Material versetzt weiter; spätere Schnitte treffen
späteres Material. Ohne diese Umrechnung wird der Spur zu viel Material
abgeschnitten (Standbild am Ende). Jede Quelldatei mit ihrer umgerechneten
Liste schneiden (leere Liste = Originaldatei unverändert verwenden).
Danach wie gehabt: Datei laut Ton-Quelle als prolook-`input`, die andere als
`pip.background`; ist das große Video (Background) am Ende kürzer als das
kleine → `pip.background_end: "freeze"`.

Untertitel-Wortzeiten dabei passend wählen: Sie folgen dem TON — also der
Datei, die als `input` läuft (ungeschnittene Datei = Original-Zeiten
unverändert!).

### 2b-Audio. Lautstärke, Abschnitte und Musik (aus dem Cockpit)

**Basis-Lautstärke (`gains` = `{main, pip}`, 0–1.5):** Das Cockpit leitet
daraus `audio_from` weiter ab (beide > 0 → `both`). Beim Rendern: Die Datei
mit dem führenden Ton als prolook-`input` (ihr Gain → prolook
`audio_gain`), die andere als `pip.background` (ihr Gain →
`pip.audio_gain`); sind beide hörbar zusätzlich `pip.mix_audio: true`.
Gain 0 = Spur stumm (dann kein mix_audio nötig). Das Layout — wer
groß/klein ist — steuern `pip.x/y/scale` unabhängig davon. Die
Cockpit-Vorschau klingt wie der Render.

**Lautstärke-Abschnitte (`volumes` = `[{track, start, end, gain}]`,
track `main`|`pip`|`music`):** zeitweise lauter/leiser. Hat eine Spur
Abschnitte, ihre KOMPLETTE Lautstärke (Basis + Abschnitte) VOR dem
Schneiden in die Quelldatei einrechnen (Zeiten = Quellzeiten):
`ffmpeg -i quelle.mp4 -af "volume='if(between(t,S1,E1),G1,BASIS)':eval=frame" -c:v copy quelle_vol.mp4`
(mehrere Abschnitte = verschachtelte `if`) — und den zugehörigen
prolook-Gain für diese Spur auf 1.0 lassen. Ohne Abschnitte reicht der
prolook-Gain.

**Musik (`music` = `{file, offset, gain}` + Schnitte/volumes mit track
`music`):** Musikquellen siehe pro-look-editing-Skill (pixabay, mixkit …);
Datei in den Projektordner, `music` in projekt.json setzen, `build_editor.py`
erzeugt die Musik-Waveform mit. Beim Rendern `musik_schnitt.mp3` bauen:
Song ab `offset`; jeder Musik-Schnitt entfernt in SONG-Zeit das Stück
`[offset + start + vorher, offset + end + vorher]` (`vorher` = Summe der
Längen früherer Musik-Schnitte); `volumes`-Abschnitte der Musikspur mit
Timeline-Zeiten einrechnen (= Dateizeiten der vorbereiteten Datei). Dann
prolook `music: {enabled: true, file: musik_schnitt.mp3, gain: <gain>}` —
Kürzen auf Reel-Länge, Loop falls kürzer, Fade-Out und Auto-Ducking macht
prolook (Ducking hört die Vorschau nicht, der Render schon).

**Voiceover (`voiceover` = `{file, gain}` + Schnitte/volumes mit track
`voice`):** klebt an der Timeline des großen Videos (startet bei 0).
Vorbereitung fürs Rendern: Datei mit DERSELBEN Schnittliste schneiden wie
die Ton-/Zeit-Master-Datei (Voiceover-Material an Videoschnitten fällt mit
weg); `voice`-Schnitte sind STUMM-Stellen (kein Aufrücken!) — als
0%-Volume-Abschnitte einrechnen, zusammen mit `volumes`-Abschnitten der
voice-Spur (gleicher volume-Ausdruck wie oben). Dann prolook
`voiceover: {file: <vorbereitete datei>, gain: <gain>}` — wird vor
Mastering/Musik gemischt, das Musik-Ducking reagiert also auch auf das
Voiceover. Aufnahmen aus dem Cockpit heißen `voiceover.webm` (liegt nach
der Aufnahme in Downloads).

### 2b-Texte. Freie Text-Overlays (Hook & Titel, B-Roll)

Cockpit-Kachel „Texte": beliebig viele Overlays, je
`{text, start, end, x, y, font, size, color, bold, box, box_color,
box_alpha, box_style, anim, width, lines}` in `P.texts` (`box_style`:
`line` = schmiegt sich pro Zeile an, `block` = EIN symmetrisches Viereck).
Text bricht NIE automatisch um: `width` 0 = eine Zeile pro Enter;
`width` > 0 (Anteil von 1080, per Anfasser am Text gezogen) = Text-Fläche,
das Cockpit vermisst die Umbrüche mit der echten Schrift und speichert sie
als `lines` — `text_overlays.py` rendert exakt diese Zeilen (`lines` hat
Vorrang vor `text`; nach manuellen texts-Änderungen per Hand `lines`
löschen oder neu setzen). Timing auf der 📝-Spur (Aufziehen = neuer
Text), Position per Ziehen im Video (x/y = Zentrum als Anteil), Hintergrund
schmiegt sich pro Zeile um die Wörter, `anim`: `fade|left|right|up|pop|none`.
Beim Rendern: `python text_overlays.py projekt.json texte.ass` (liest die
texts direkt, macht ASS mit \\move/\\fad/\\t-Animationen) und in der
prolook-Config `"text_overlays": "texte.ass"` setzen (wird nach den
Untertiteln eingebrannt). ACHTUNG: `start/end` sind Timeline-Zeiten des
UNGESCHNITTENEN Materials — bei Schnitten vor dem Rendern die Zeiten wie
Untertitel-Wortzeiten verschieben (Summe der vorher entfernten
Schnittlängen abziehen), sonst sitzen die Texte falsch.

### 2c. Claude arbeitet im Projekt mit (Roundtrip)

Sagt der User z. B. „setz noch einen Schnitt bei 20–22" oder „ändere die
Schriftfarbe": ERST prüfen, ob er im Cockpit ungespeicherte Änderungen hat
(„Hast du im Cockpit gespeichert? Sonst geht deine Maus-Arbeit verloren") —
ggf. neueste projekt.json aus Downloads einspielen. Dann projekt.json
ändern, `build_editor.py` neu ausführen, User drückt F5. Kosten: eine
JSON-Änderung.

Untertitel-Stil aus dem Cockpit an `animated_captions.py` durchreichen:
`captions.font` → `--font`, `size` → `--size`, `primary` → `--primary`,
`group` → `--group`, `bold: false` → `--no-bold`,
`highlight_on: false` → `--highlight` = gleicher Wert wie `--primary`
(= Highlight unsichtbar), sonst `highlight` → `--highlight`,
`box: true` → `--box --box-color <box_color> --box-alpha <box_alpha>
--box-style <box_style>` (`line` = pro Zeile um die Wörter, `block` = EIN
symmetrisches Viereck um den ganzen Text).
Wörter dabei IMMER aus `projekt.json` nehmen (Cockpit-Textkorrekturen!),
nie neu transkribieren.

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
  mehrfach Stil-/Positions-/Text-/Musikwünsche äußert (Untertitel-Text,
  Song-Stelle, Lautstärken: alles im Cockpit selbst machbar).
- **Untertitel anlegen NUR per Script:**
  `python scripts/transkript_untertitel.py projekt.json <video>` —
  schreibt die Wörter direkt in die projekt.json; die Wortliste NIEMALS in
  den Kontext laden oder ausgeben (auch nicht „zur Kontrolle").
- **Musik anlegen NUR per Script:**
  `python scripts/set_music.py projekt.json <datei-oder-url> [--gain]` —
  holt die Datei, setzt music, baut das Cockpit inkl. Waveform.
- projekt.json nie im Ganzen ausgeben/anzeigen — Scripts melden Zählwerte.
- QC im Cockpit-Workflow macht der NUTZER im offenen Tab (er sieht alles
  live); Claude prüft nur auf ausdrücklichen Wunsch, dann 1 Frame/
  Screenshot, nie mehrere pro Runde. Nach finalem Render: 1–2 Frames.
- Alle Effekt-Extras bleiben Frag-zuerst (siehe `pro-look-editing`).
