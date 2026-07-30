---
name: video-projekt
description: >
  Projekt-Modus für Video-Editing: verwaltet jedes Video als Projekt-Datei
  (Schnitte, Untertitel, Effekte), rendert in Stufen (Korrekturen ohne
  Komplett-Neuanalyse) und bietet das Video-Cockpit — einen lokalen
  Browser-Editor, in dem der Nutzer Schnitte auf der Timeline verschieben,
  Untertitel/Texte anpassen und Musik/Voiceover einstellen kann, bevor
  gerendert wird. Mehrere Clips laufen nacheinander (zusammengefügt).
  Verwende diesen Skill bei: "schneide mein Video" (als Ober-Workflow),
  "füge die Videos zusammen", "mehrere Videos nacheinander",
  "ich will die Schnitte selbst prüfen", "öffne das Cockpit", "mach es
  editierbar", "für Canva exportieren", "Schnitt anpassen", "Untertitel
  verschieben", "Musik ins Video", "Voiceover drüberlegen", "Text/Hook
  ins Video", "Zoom auf …", "Lautstärke ändern", "render das Video",
  oder wenn nach einem Render Korrekturen kommen.
---

# Video-Projekt-Modus (Cockpit + Stufen-Rendering)

Jedes Video ist ein **Projekt**: ein Ordner mit dem Original, einer
`projekt.json` (die einzige Wahrheit über Schnitte, Untertitel, Effekte)
und optional dem Cockpit. Korrekturen ändern NUR die projekt.json — nie
wird neu analysiert, nie Code neu geschrieben.

## GRUNDREGEL: Windows UND Mac — immer beide

**Jede Neuerung an diesem Kit muss auf Windows und auf macOS funktionieren
— mitgedacht beim Bauen, nicht nachgereicht.** Die Community arbeitet auf
beiden Systemen; ein Feature, das nur auf einem läuft, ist nicht fertig.

Konkret heißt das:

- **Keine `.bat` ohne `.command`.** Startdateien immer über eine
  Plattform-Weiche (`platform.system() == 'Windows'`) erzeugen, die
  Mac/Linux-Variante mit `#!/bin/bash` und `os.chmod(pfad, 0o755)`.
- **Pfade** nur über `os.path.join` / `pathlib` — nie `C:\…`, nie
  Backslashes fest verdrahtet.
- **Python heißt `python` unter Windows und `python3` unter Mac/Linux.**
  In diesem Skill steht deshalb überall `<python>` — dafür immer den Befehl
  einsetzen, der auf dem System des Users tatsächlich funktioniert. Nie den
  nackten Aufruf `python …` in eine Anleitung schreiben.
- **Öffnen** je nach System: `Start-Process` / `open` / `xdg-open`.
- **Textdateien** in UTF-8 mit `\n`; `cp1252` und `\r\n` nur in `.bat`.
- **Nutzerordner** als `~` bzw. `os.path.expanduser('~')`, nicht
  `%USERPROFILE%`.
- **ffmpeg-Filter** sind plattformgleich — aber die Hardware-Encoder nicht:
  Windows kennt `h264_qsv`/`h264_nvenc`/`h264_amf`, Mac `h264_videotoolbox`.
  Immer erkennen statt annehmen, und auf `libx264` zurückfallen.

Wird eine Stelle gefunden, die nur ein System bedient: reparieren, nicht
dokumentieren. Ein Hinweis „unter Windows zusätzlich …" ist eine Lücke,
keine Lösung.

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

`projekt.json`-Kern: `videos` (Liste von Clips, laufen NACHEINANDER =
zusammengefügt; Altbestand `video` = ein Clip), `duration`, `cuts`
(start/end/reason/active, `track` `both`/`music`/`voice`), `words`
(Transkript), `captions` (Stil inkl. box/box_style/group/highlight_on/bold),
`gains` (`{main}` = Video-Lautstärke), `volumes` (Lautstärke-Abschnitte),
`music`, `voiceover`, `zooms`, `texts`, `render` (crf/preset/output) und
`effekte` (prolook-Durchreiche). **Bild-im-Bild wurde entfernt** — ein Reel,
ein Video (bzw. mehrere Clips hintereinander). Schnitte gelten über die
zusammengefügte Timeline.

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
> Schnitte, Untertitel, Texte und Musik selbst feinjustieren kannst
> — oder (c) du vertraust mir und ich rendere direkt."

Cockpit-Weg — **EIN-TAB-PRINZIP (wichtig!):**
`<python> scripts/build_editor.py <projekt.json>` erzeugt `editor.html`
(statisch) + `projekt_data.js` (die Daten). Das offene Cockpit lädt die
Daten-Datei alle 2,5 s selbst nach — **Änderungen von Claude erscheinen im
offenen Tab von allein.** Deshalb das Cockpit NUR beim allerersten Erstellen
öffnen. Bei jeder späteren Änderung NUR
`build_editor.py` ausführen und dem User sagen „schau in deinen offenen
Tab" — NIEMALS erneut öffnen (das erzeugt verwirrende Doppel-Tabs). Hat
der User ungespeicherte Änderungen, zeigt das Cockpit einen
Übernehmen/Behalten-Banner statt sie zu überschreiben.

**Öffnen je nach System** (Claude wählt das passende, nicht raten):
- Windows: `Start-Process editor.html`
- macOS: `open editor.html`
- Linux: `xdg-open editor.html`

**Start & Wiedergabe (server-frei, kinderleicht):** Claude öffnet
`editor.html` EINMAL. Kein Helfer, kein Server, keine .bat
zum Starten, keine Verbindung. Das eine Video spielt; beim Abspielen werden
aktive Schnitte LIVE übersprungen (Button „✂ Schnitte überspringen" an =
Standard = zeigt das geschnittene Ergebnis; aus = Rohmaterial). Mehrere
Clips (`videos`) laufen im Cockpit nacheinander (Playlist). Timeline =
Roh-Zeitachse mit roten Schnitt-Balken, weißer Läufer, ↩/Strg+Z, KACHELN.
Alles ohne Token. (Es gibt KEINE Vorschau-Dateien/kein cockpit_server mehr.)

**Speichern:** Button „💾 Speichern" → beim ersten Mal wählt der User einmal
die `projekt.json` (moderner Datei-Dialog), danach speichert das Cockpit
direkt dorthin (auto beim Bearbeiten) — kein Downloads-Umweg. Kann der
Browser das nicht (`showSaveFilePicker`), lädt es als Notfall nach Downloads.
Claude-Änderungen erscheinen weiter live im Tab (projekt_data.js-Polling).
Wenn Claude Schnitte/Felder ändert: nur `build_editor.py` ausführen.

**Was der Nutzer im Cockpit kann (alles ohne Token):**
- **Timeline:** ganzes Video, Schnitte rot, Kanten ziehen = trimmen, Mitte
  ziehen = verschieben, freie Fläche aufziehen = neuer Schnitt, Doppelklick
  = an/aus. Werkzeug-Button: ✂ Schnitt / 🔊 Lautstärke-Abschnitt / 🔍 Zoom.
  Spuren: Video (blau), ♪ Musik (lila), 🎙 Voiceover (rosa), 📝 Texte (gelb).
  „Tonspur anzeigen" blendet Waveforms ein (`waveform_data.js`, erzeugt
  build_editor.py gecacht, braucht ffmpeg).
- **Videos-Kachel:** mehrere Clips nacheinander, Reihenfolge ändern (▲),
  entfernen (🗑), weitere aus dem Projektordner anhängen (`_dateien`).
- **Untertitel:** Live-Vorschau mit Wort-Highlight, per Maus ziehbar,
  Schrift/Größe/Farben/Box, und der TEXT ist direkt editierbar
  („Untertitel-Text"; Doppelklick im Video springt zur Zeile).
- **Texte-Kachel:** freie Overlays (Hook/Titel) auf der 📝-Spur, Position
  per Ziehen, Stil + Einflug-Animation je Text (siehe 2b-Texte).
- **Audio-Kachel:** eigenes Lied oder Voiceover-Datei wählen, Voiceover mit
  dem Mikro aufnehmen. Neue Dateien landen in Downloads — beim „fertig"
  in den Projektordner verschieben, dann `build_editor.py`.
  Musik: SONG-ÜBERSICHT unter der Timeline (ganzes Lied, lila Fenster
  ziehen = Stelle im Lied) + „Start im Lied".
- **Vorschau-Zoom:** Mausrad = rein/raus (auf den Cursor), Ziehen =
  verschieben, −/100%/+ unten links.

**Eigene Cockpit-Erweiterungen NIEMALS in editor.html/das Template bauen**
(Kit-Updates überschreiben es), sondern IMMER in `cockpit_custom.js` im
Projektordner — die lädt das Cockpit automatisch als letztes Script, alle
Funktionen/Variablen sind global und dort ergänz- oder ersetzbar (danach
ggf. `renderTL()` aufrufen). Die Datei überlebt jedes Update. Soll eine
Erweiterung in allen Projekten gelten: zusätzlich im Benutzerordner unter
`.scb-creator-kit/cockpit_custom.js` ablegen (Windows `%USERPROFILE%`,
macOS/Linux `~`) — `build_editor.py` kopiert sie in jedes neue Projekt.
Wünsche, die für die ganze Community taugen, dem Kit-Autor (Julian) melden
statt lokal bauen.

Rendern immer per `render_projekt.py`. Nur falls der User über Downloads
gespeichert hat (alter Browser): die projekt.json aus dem Downloads-Ordner
des Benutzers in den Projektordner verschieben.

### 1. MEHRERE CLIPS: EINMAL zusammenfügen, dann EIN Video

Sollen mehrere Aufnahmen hintereinander laufen, werden sie **beim Anlegen
des Projekts einmal zu EINER Datei zusammengefügt** (`gesamt.mp4`), und
`videos` enthält danach nur noch diese eine Datei:

```bash
printf "file 'clip1.mp4'\nfile 'clip2.mp4'\n" > c.txt
ffmpeg -y -v error -f concat -safe 0 -i c.txt -c copy gesamt.mp4
# (schlaegt -c copy fehl, weil die Clips unterschiedliche Formate haben:
#  jeden Clip einzeln auf 1080x1920/30fps normalisieren, dann concat)
```

NICHT mehrere Clips als Playlist im Cockpit lassen — die Wiedergabe über
Dateigrenzen hinweg ist im Browser unzuverlässig (Clip-Längen werden bei
lokalen Dateien oft nicht gemeldet, die Wiedergabe bleibt beim ersten Clip
hängen). Mit einer Datei ist die Zeitachse eindeutig und alles läuft stabil.
Die Videos-Kachel im Cockpit bleibt nur für nachträgliches Anhängen — nach
so einer Änderung erneut zusammenfügen.

### 1a. WARTEZEIT-REGEL (wichtigste Regel für das Nutzererlebnis)

**Der Nutzer wartet NIE auf einen Render, bevor er etwas sehen kann.**
Das Cockpit spielt das Rohmaterial und überspringt Schnitte live — es
braucht KEIN gerendertes Video. Deshalb gilt diese Reihenfolge zwingend:

1. Videos zusammenfügen (Sekunden), transkribieren, analysieren, Schnitte
   setzen, `build_editor.py` → **Cockpit öffnen und den Nutzer schauen
   lassen.** Bis hier: rund eine Minute.
2. **Erst wenn der Nutzer zufrieden ist:** stabilisieren + rendern.

NIEMALS vorab „zur Sicherheit" rendern — jeder Render, der danach noch
korrigiert wird, ist verlorene Wartezeit. Rechenintensives (Stabilisierung,
finaler Render) kommt ans ENDE und läuft im Hintergrund, während der Nutzer
schon im Cockpit arbeitet.

### 1b. Schnitt-Analyse — PFLICHTABLAUF (Reihenfolge einhalten!)

1. **Transkript** per `scripts/transkript_untertitel.py` (Wortliste nie in
   den Kontext laden).
2. **Pausen per LAUTSTÄRKE finden:**
   `<python> scripts/pausen_finden.py projekt.json` — liefert FERTIGE
   Schnittvorschläge mit bereits abgesicherten Grenzen (kein Wort wird
   angeschnitten) plus Sprachkontext je Vorschlag. Diese Werte direkt
   übernehmen — NICHT selbst nachmessen, NICHT die Lautstärke roh ausgeben
   lassen (das kostet ein Vielfaches an Tokens ohne Mehrwert).
   NIEMALS auf die Wortlücken des Transkripts verlassen! Transkriptionen
   dehnen Wörter über Pausen hinweg (ein gemurmeltes „das" läuft dann laut
   Transkript 1,4 s), dadurch bleiben Pausen unsichtbar.
3. **Inhalt lesen** (kompakter Fließtext mit Zeit-Ankern, siehe
   `video-schneiden`): Versprecher, verbale Fehlersignale und vor allem
   DOPPELTE AUSSAGEN suchen. Sagt der Sprecher denselben Gedanken zweimal
   (auch anders formuliert), fliegt der schwächere Anlauf KOMPLETT raus —
   nicht nur der abgebrochene Zwischenteil.
4. **Video muss mit dem ersten gesprochenen Wort beginnen** — Anlauf,
   Räuspern, gemurmelte Wortfetzen und „genervt dastehen" gehören in den
   ersten Schnitt. Prüfen: erster Ton direkt bei 0,00 s.
5. **PFLICHT-Endkontrolle:** `<python> scripts/pruef_text.py projekt.json` —
   den ausgegebenen Text LESEN: vollständig? flüssig? keine zerschnittenen
   Wörter, keine Dopplungen an den Nähten?

6. **DANN FRAGEN — nicht einfach rendern!** Kurz zusammenfassen, was
   geschnitten wurde (1–3 Sätze), und dem Nutzer die Wahl lassen:
   > „Soll ich das Video jetzt fertig rendern, oder willst du vorher im
   > Cockpit drüberschauen und noch etwas anpassen?"
   Antwort merken. Bei „rendern" → `render_projekt.py`, danach EIN
   QC-Kontaktbogen. Bei „Cockpit" → `build_editor.py` + Cockpit öffnen und
   erst nach seinem Okay rendern. Hat der Nutzer vorher schon gesagt „mach
   fertig" / „render direkt", nicht erneut fragen.

### 2a-Render. Rendern = EIN Befehl (niemals Pipeline improvisieren)

```
<python> scripts/render_projekt.py <projekt.json>
```

**Tempo:** Der Render nutzt automatisch den **Hardware-Encoder** der
Grafikkarte (NVIDIA/Intel/AMD), wenn vorhanden — 5–10× schneller als CPU,
gleiche Sichtqualität. Erzwingen von CPU: `"render": {"hardware": false}`.
**Bildstabilisierung** als Projekt-Option: `"stabilisieren": true` (oder
`{"staerke": 10, "glaettung": 60, "randbeschnitt": 6}`) — 2-Pass-vidstab,
Ergebnis wird gecacht (läuft nur neu, wenn sich die Quelle ändert).
**Mehrere Clips** (`videos`) fügt das Script selbst zusammen.

Das Script macht ALLES selbst (Schnittlisten pro Spur, Dateien schneiden,
Lautstärke-Abschnitte, Musik/Voiceover-Vorbereitung, Untertitel- und
Text-ASS, prolook, QC-Kontaktbogen `qc_final.png`). Danach nur den
Kontaktbogen ansehen (1 Bild) und dem User zeigen. `build_editor.py` legt
zusätzlich eine Doppelklick-Startdatei in den Projektordner — dort kann der
User selbst neu rendern (0 Tokens): unter Windows `video_rendern.bat`, unter
macOS/Linux `video_rendern.command` (wird automatisch ausführbar gesetzt).
Qualitätswünsche („bessere
Qualität") = in projekt.json `"render": {"crf": 18}` setzen (Standard 20,
kleiner = besser; optional `"preset"`, `"output"`). Zoom-Wünsche
(„Zoom ab Sekunde 10", „Zoom aufs Gesicht") = `zooms`-Eintrag, siehe
2b-Zoom (hat Cockpit-Anzeige + Live-Vorschau — NICHT punchin verwenden).
Sonstige Effekt-Wünsche (Farb-Look, Übergänge, Filmkorn …) =
`"effekte": {...}` in der projekt.json — die Schlüssel (grade, grain,
transition, progressbar, broll, overlays, sfx, voice_master, loudnorm,
punchin) werden 1:1 in die prolook-Config durchgereicht und überleben
jeden Doppelklick-Render; Zeitangaben in Output-Zeit des fertigen Videos.
Effekte bleiben Frag-zuerst, und die Cockpit-Vorschau zeigt sie NICHT
(nur QC-Frames/Render). Die Abschnitte 2b ff.
beschreiben das Mapping, das render_projekt.py implementiert — nur lesen,
wenn das Script mal nicht reicht.

### 2b. Videos zusammenfügen + Schnitte (macht render_projekt.py)

`videos` = Liste von Clips, die NACHEINANDER laufen (Talking-Head 1, 2, …).
render_projekt/vorschau fügen sie zusammen (ffmpeg concat, alle auf
1080×1920 normalisiert) → EIN Quellvideo. Darauf wirken die `cuts` (nur
aktive; `track` `both` = Video). **Schnitte sind QUELLzeit** (Zeit im
zusammengefügten Video, genau wie auf der Cockpit-Timeline gezogen) — DIREKT
verwenden, KEINE Umrechnung. `music`/`voice`-Schnitte betreffen nur die
jeweilige Tonspur. Untertitel-Wortzeiten folgen der Videozeit; vor der
ASS-Erzeugung um die aktiven Video-Schnitte verschieben (`shift`).

### 2b-Audio. Lautstärke, Abschnitte und Musik (aus dem Cockpit)

**Video-Lautstärke (`gains` = `{main}`, 0–1.5):** → prolook `audio_gain`.

**Lautstärke-Abschnitte (`volumes` = `[{track, start, end, gain}]`,
track `main`|`music`):** zeitweise lauter/leiser. Hat eine Spur
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

### 2b-Zoom. Zoom-Abschnitte mit Zielpunkt

`P.zooms` = `[{start, end, zoom, x, y, mode, ramp}]` — Timeline-Zeiten,
`zoom` 1.05–2.0, `x/y` = Zielpunkt als Anteil, `mode` `fahrt` (sanft
reinziehen, per zoompan subpixel-flüssig) oder `fest` (harter Punch-In).
`ramp` = Sekunden bis voller Zoom (Geschwindigkeit; ohne Angabe = ganze
Abschnittslänge, danach hält der Zoom). „Zoom langsamer/schneller" vom
User = nur `ramp` ändern. Cockpit: Werkzeug 🔍, Abschnitt auf einer
Videospur aufziehen, ⌖-Punkt im Video auf das Ziel ziehen — Live-Vorschau
zoomt Video + PiP (Untertitel/Texte bleiben ungezoomt, exakt wie der
Render). render_projekt.py reicht sie (Zeiten verschoben) als
prolook-`zooms` durch. **„Zoom auf mein Gesicht" per Zuruf:** 1 Frame an
der Stelle ziehen (`ffmpeg -ss <t> -frames:v 1`), ansehen, Gesichtszentrum
als x/y schätzen (Anteile!), zooms-Eintrag in projekt.json setzen,
build_editor — der User sieht den ⌖ im Cockpit und kann nachjustieren.

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
Beim Rendern: `<python> text_overlays.py projekt.json texte.ass` (liest die
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

Hintergrund-Wissen (macht render_projekt.py automatisch — nur für
Sonderfälle): Untertitel-Stil-Mapping an `animated_captions.py`:
`captions.font` → `--font`, `size` → `--size`, `primary` → `--primary`,
`group` → `--group`, `bold: false` → `--no-bold`,
`highlight_on: false` → `--highlight` = gleicher Wert wie `--primary`
(= Highlight unsichtbar), sonst `highlight` → `--highlight`,
`box: true` → `--box --box-color <box_color> --box-alpha <box_alpha>
--box-style <box_style>` (`line` = pro Zeile um die Wörter, `block` = EIN
symmetrisches Viereck um den ganzen Text).
Wörter dabei IMMER aus `projekt.json` nehmen (Cockpit-Textkorrekturen!),
nie neu transkribieren.

### 3. Erneut rendern nach Korrekturen

Immer derselbe EINE Befehl: `<python> scripts/render_projekt.py
<projekt.json>` (alternativ doppelklickt der User die Startdatei im
Projektordner: `video_rendern.bat` unter Windows,
`video_rendern.command` unter macOS/Linux). Das
Script rechnet alle Stufen selbst durch — Schnitt-Umrechnung,
Wortzeiten-Verschiebung, Audio-Vorbereitung, ASS-Dateien, prolook. KEINE
Einzelschritte von Hand nachbauen; die Rechenzeit kostet keine Tokens.

### 4. Export-Ziele (Frag-zuerst, Wahl im Profil merken)
| Ziel | Ergebnis |
|---|---|
| **Fertig-Reel** | final.mp4 mit allem Gewählten (Captions, Effekte, Audio-Suite) |
| **Cockpit** | Nutzer justiert selbst, dann Fertig-Reel |
| **Editierbar (Canva/CapCut)** | die geschnittene Zwischenfassung aus render_projekt (`r_main.mp4`/`r_pip.mp4`, OHNE eingebrannte Elemente) + `untertitel.srt` aus den umgerechneten Wortzeiten. Hinweis: Canva importiert kein SRT — dort eigene Auto-Captions nutzen; CapCut/Premiere/DaVinci können SRT. Bild-im-Video baut Canva selbst (zwei Spuren). |

## Token-Regeln

- Korrektur = projekt.json-Feld ändern + Stufen-Render. NIE neu
  transkribieren, NIE Cuts neu analysieren, NIE Effekt-Code schreiben.
- Cockpit-Feinarbeit kostet 0 Tokens — dorthin lenken, wenn der Nutzer
  mehrfach Stil-/Positions-/Text-/Musikwünsche äußert (Untertitel-Text,
  Song-Stelle, Lautstärken: alles im Cockpit selbst machbar).
- **Untertitel anlegen NUR per Script** (Wortliste NIEMALS in den Kontext
  laden oder ausgeben, auch nicht „zur Kontrolle"). Der API-Key kommt als
  Umgebungsvariable — beim installierten Kit steckt der Nutzer-Key im
  Platzhalter, also z. B. in PowerShell:
  `$env:ELEVENLABS_API_KEY = "~~elevenlabs-api-key"` (bzw. GROQ_API_KEY,
  falls der Nutzer einen Groq-Key nennt), dann:
  `<python> scripts/transkript_untertitel.py projekt.json <video>` —
  schreibt die Wörter direkt in die projekt.json.
- **Musik anlegen NUR per Script:**
  `<python> scripts/set_music.py projekt.json <datei-oder-url> [--gain]` —
  holt die Datei, setzt music, baut das Cockpit inkl. Waveform.
- projekt.json nie im Ganzen ausgeben/anzeigen — Scripts melden Zählwerte.
- **NIEMALS Rohdaten ausgeben lassen** (Lautstärke-Verläufe, Wortlisten mit
  Zeitstempeln, Frame-Tabellen). Das sind schnell 100+ Zeilen, die danach in
  JEDER weiteren Antwort erneut mitlaufen. Die Scripts liefern fertige
  Ergebnisse — diese übernehmen, nicht selbst nachmessen. Braucht man doch
  einen Wert, gezielt EINE Zeile ausgeben (`... | tail -1`).
- Analyse-Schritte bündeln: ein Script-Aufruf statt sich in mehreren
  Teilabfragen vorzutasten.
- QC im Cockpit-Workflow macht der NUTZER im offenen Tab (er sieht alles
  live); Claude prüft nur auf ausdrücklichen Wunsch, dann 1 Frame/
  Screenshot, nie mehrere pro Runde. Nach finalem Render: 1–2 Frames.
- Alle Effekt-Extras bleiben Frag-zuerst (siehe `pro-look-editing`).
