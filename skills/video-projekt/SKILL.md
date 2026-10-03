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

## Tempo dieses Rechners kennen (vor dem ERSTEN Video)

Lies `~/.scb-creator-kit/tempo.json`. Fehlt die Datei, einmal
`<python> ../scb-setup/scripts/tempo_check.py` laufen lassen (30–60 s)
— danach nie wieder. Die Datei sagt dir:

| Feld | Bedeutung fürs Vorgehen |
|---|---|
| `klasse` | `schnell` / `mittel` / `langsam` |
| `freistellung_max_sek` | So viele Sekunden Freistellung am Stück höchstens rechnen |
| `hw_encoder`, `hw_faktor` | Welcher Hardware-Encoder greift und wie viel er bringt |
| `freistellung.onnxruntime` | Fehlt der Wert, läuft die Freistellung auf MediaPipe und flackert unter Grafik |

**Danach handeln, nicht nur wissen:** Bei `langsam` die Freistellung
strikt auf den angesagten Abschnitt begrenzen und dem User vorher
sagen, wie lange es dauert. Fehlt `onnxruntime` und es soll etwas
*hinter* der Person liegen: erst `install_tools.py` bzw. den
Freistellungs-Bereich des Setups anbieten, sonst wird das Ergebnis
sichtbar schlechter.

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
`format` / `einpassen` / `ausschnitt` (Bildformat, siehe 2b-Format),
`music`, `voiceover`, `zooms`, `texts`, `filter` (Filter- und Look-Abschnitte inkl.
Sin City, siehe 2b-Filter), `spuren_zu` (im Cockpit zugeklappte Spuren, z. B.
`["sfx","music"]`), `sfx_library` (optionaler Pfad zur
Soundeffekt-Library), `render` (crf/preset/output),
`freistellung` (`{von, bis}` in Output-Zeit — render_projekt.py stellt die
Person selbst frei (gecacht, `freisteller.mkv/.webm`) und legt sie als
OBERSTE Ebene über alle Grafik-overlays) und
`effekte` (prolook-Durchreiche; `effekte.sfx` = Soundeffekt-Spur, siehe
2b-Sfx). **Bild-im-Bild wurde entfernt** — ein Reel,
ein Video (bzw. mehrere Clips hintereinander). Schnitte gelten über die
zusammengefügte Timeline.

## Workflow

### 0. EINGANGSFRAGE — einmal stellen, Antwort merken

Bevor irgendetwas gebaut wird, EINMAL fragen, wie weit es gehen soll. Nicht
raten, und nicht in jeder Runde neu fragen:

> „Bevor ich loslege: Reicht dir Schnitt und Untertitel? Sollen einfache
> Texte drüber — die machst du danach im Cockpit selbst? Brauchst du
> animierte Grafik, also Ringe, hochzählende Zahlen oder 3D-Schrift? Und soll
> etwas **hinter** dir liegen, sodass du davor stehst?"

Daraus ergibt sich die Stufe. **Nie höher einsteigen als nötig:**

| Stufe | Werkzeug | Kosten für den Nutzer |
|---|---|---|
| 1 | dieser Skill (Cockpit): Schnitt, Untertitel, Musik, **einfache Texte** | 0 Token, er ändert selbst |
| 2 | `motion-grafik`: animierte Grafik, die das Cockpit nicht kann | jede Änderung = eine Coderunde |
| 3 | `motion-grafik`: Freistellung für „hinter mir" | zusätzlich Rechenzeit |

Ein Text, den die `texts`-Kachel im Cockpit kann, gehört ins Cockpit — auch
wenn er in Motion Canvas hübscher würde. Der Nutzer justiert ihn dort selbst
und ohne Token.

Die Stufen danach **einzeln nacheinander** abarbeiten, mit Freigabe
dazwischen — nicht alles auf einmal.

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

**Öffnen — immer über das Script, auf allen Systemen:**
`<python> scripts/cockpit_oeffnen.py <projektordner>`. Es nimmt Chrome,
Edge, Brave, Arc, Opera oder Vivaldi, falls installiert — nur die können
direkt in Ordner speichern. Safari und Firefox können das nicht (dort wird
jedes Speichern ein Download); meldet das Script „Kein Chrome/Edge
gefunden", dem Nutzer einmal empfehlen, Chrome zu installieren.

**Start & Wiedergabe (server-frei, kinderleicht):** Claude öffnet
`editor.html` EINMAL. Kein Helfer, kein Server, keine .bat
zum Starten, keine Verbindung. Das eine Video spielt; beim Abspielen werden
aktive Schnitte LIVE übersprungen (Button „✂ Schnitte überspringen" an =
Standard = zeigt das geschnittene Ergebnis; aus = Rohmaterial). Mehrere
Clips (`videos`) laufen im Cockpit nacheinander (Playlist). Timeline =
Roh-Zeitachse mit roten Schnitt-Balken, weißer Läufer, ↩/Strg+Z, KACHELN.
Alles ohne Token. (Es gibt KEINE Vorschau-Dateien/kein cockpit_server mehr.)

**Arbeitsordner (wie bei CapCut) — EIN Ort für alle Projekte:**
`scripts/arbeitsordner.py` merkt ihn in `~/.scb-creator-kit/einstellungen.json`.

```
<Arbeitsordner>/
    Projekte/<name>-projekt/   jedes neue Projekt (projekt_starten.py, Standard)
    Fertig/                    jedes fertige Video: "<name> JJJJ-MM-TT.mp4"
    Startseite.html            alle Projekte, zuletzt bearbeitete vorne
```

- **Vor dem ERSTEN Projekt** `arbeitsordner.py` ausführen. Exit 2 = noch
  keiner gesetzt → einmal per AskUserQuestion fragen (Vorschlag aus
  `--vorschlag`, Warnung bei OneDrive/iCloud wegen großer Videos), dann
  `--setzen "<pfad>"`. Danach nie wieder fragen.
- `projekt_starten.py` legt neue Projekte automatisch unter `Projekte/` an
  (`--ziel` überschreibt das für ein einzelnes Projekt, wenn der Nutzer einen
  anderen Ort will).
- `render_projekt.py` legt jedes fertige Video zusätzlich in `Fertig/` ab
  (gleicher Tag = neueste Fassung ersetzt die alte).
- `build_editor.py` merkt sich jedes Projekt (auch ältere außerhalb des
  Arbeitsordners), macht ein Vorschaubild und baut die Startseite neu.
- „Zeig mir meine Projekte" → `arbeitsordner.py --startseite --oeffnen`.

**Speichern im Cockpit — je Projekt EINMAL gefragt, danach automatisch:**
Beim ersten Klick auf „Speichern" in einem Projekt zeigt das Cockpit, wo
gespeichert wird (der Projektordner) — „Hier speichern" bestätigt. Beim
allerersten Mal öffnet der Browser seinen Ordner-Dialog: dort den
Arbeitsordner wählen; danach reicht in jedem weiteren Projekt der
Bestätigungsklick. Ab dann speichert **jede Änderung von selbst** (~1 s
später) **direkt in die projekt.json des Projekts** — Claude liest genau
diese, kein Abholen nötig. Der Knopf zeigt den Zustand („Gespeichert" mit
Uhrzeit im Tooltip / „Speichert …" / „Speichern", wenn noch kein Ort
feststeht). Nach einem Browser-Neustart erscheint „Weiter, wo du aufgehört
hast" — ein Klick erlaubt das Speichern wieder und lädt den zuletzt
gespeicherten Stand, falls er neuer ist als der von Claude gebaute
(`_gebaut` in projekt_data.js gegen `_gespeichert` in der projekt.json).
Rechtsklick auf den Knopf = Speicherort ändern. „Anderer Ort …" speichert
nach `<Ordner>/<projekt>/projekt.json`; die holt Claude mit
`cockpit_holen.py <ordner>` ab. Ohne Ordnerzugriff (Safari/Firefox):
einzelne Datei wählen bzw. Download.

**Für Claude heißt das:** Vor jeder Änderung die projekt.json im
Projektordner FRISCH lesen (der Nutzer kann seit dem letzten Lesen im
Cockpit weitergearbeitet haben), ändern, sofort `build_editor.py`.

**Wichtig für Änderungen am Polling:** `lastApplied` ist der zuletzt von
Claude gesehene Stand — beim Speichern NICHT auf die eigene Fassung setzen.
Sonst hält das 2,5-s-Polling Claudes unveränderte Datei für neu und spielt
sie zurück; die Änderungen des Nutzers wären weg (Fehler bis 05.08.2026).

**Herkunft in der Datei — so findet Claude das richtige Projekt.** Jede
gespeicherte Fassung trägt drei Zusatzfelder, die das Cockpit selbst setzt:

| Feld | Inhalt |
|---|---|
| `_projekt` | Name des Projekts |
| `_projektpfad` | voller Pfad des Projektordners (auch auf einer anderen Platte) |
| `_gespeichert` | Zeitpunkt in ISO |

Damit ist auch bei zehn Projekten eindeutig, welches zuletzt bearbeitet wurde
und wohin es gehört. Abholen per Script — findet die jüngste Fassung, zeigt
was sich geändert hat und kopiert sie in ihren Projektordner:

```
<python> scripts/cockpit_holen.py <sammelordner>        # einmal, wird gemerkt
<python> scripts/cockpit_holen.py                       # danach ohne Pfad
<python> scripts/cockpit_holen.py --nur-zeigen          # nur anzeigen
```

Warum das bei lokalen Dateien funktioniert: IndexedDB fällt bei `file://`
NICHT pro Ordner auseinander — getestet, in Projekt A geschrieben und in
Projekt B gelesen. Fallback-Kette, falls der Browser den Ordner-Dialog nicht
kann: einzelne Datei wählen (`showSaveFilePicker`), sonst Download.

Claude-Änderungen erscheinen weiter live im Tab (projekt_data.js-Polling).
Wenn Claude Schnitte/Felder ändert: nur `build_editor.py` ausführen.
**Claude liest die gespeicherte Fassung direkt aus dem Projektordner**
(`projekt.json`). Nur wenn der Nutzer „Anderer Ort" gewählt hat oder ein
Altprojekt noch in einen Sammelordner speichert: `cockpit_holen.py`; als
letzter Notfall der Downloads-Ordner.

**Was der Nutzer im Cockpit kann (alles ohne Token):**
- **Timeline:** ganzes Video, Schnitte rot. Klick in die Zeitskala oben oder
  in eine freie Spurfläche = Läufer dorthin (Ziehen in der Skala = spulen).
  Kanten ziehen = trimmen, Mitte ziehen = verschieben, freie Fläche aufziehen
  (ab 5 Bildpunkten) = neuer Schnitt, Doppelklick
  = an/aus. Feld „Aufziehen =" oben: Schnitt / Lautstärke / Zoom (Tasten
  1–3). Kanten rasten an Wortanfang/-ende ein (Alt/⌥ = frei ziehen).
  Klick auf ein Element = markieren (rechts springt die passende Karte auf,
  Entf löscht). Tasten: ← → ein Bild, Umschalt+← → eine Sekunde, I/O =
  Schnitt-Anfang/-Ende an der Läuferstelle, Strg+Z/Strg+Y (Mac ⌘Z/⌘⇧Z).
  Seitenleiste in Reitern: Schnitt · Text · Ton · Bild (Karten aus
  `cockpit_custom.js` landen unter „Bild").
  Spuren: Video (blau), Musik (lila), Voiceover (rosa), Texte (gelb),
  Filter (pink), Effekte (grün).
- **Timeline-Zoom** (🔍 −/+ links unter der Zeitleiste, oder Mausrad über
  ihr): zoomt zum Läufer bzw. zur Stelle unter der Maus. Beim Abspielen
  fährt die Ansicht mit. Klick auf die Prozentzahl = wieder ganze Zeitleiste.
  Lineal schaltet dabei auf feinere Schritte bis 0,1 s. Gebraucht wird das,
  um Soundeffekte und Schnitte exakt zu setzen.
  „Tonspur anzeigen" blendet Waveforms ein (`waveform_data.js`, erzeugt
  build_editor.py gecacht, braucht ffmpeg).
- **Videos-Kachel:** mehrere Clips nacheinander, Reihenfolge ändern (▲),
  entfernen (🗑), weitere aus dem Projektordner anhängen (`_dateien`).
- **Untertitel:** Live-Vorschau mit Wort-Highlight, per Maus ziehbar,
  Schrift/Größe/Farben/Box, und der TEXT ist direkt editierbar
  („Untertitel-Text"; Doppelklick im Video springt zur Zeile).
- **Texte-Kachel:** freie Overlays (Hook/Titel) auf der 📝-Spur, Position
  per Ziehen, Stil + Einflug-Animation je Text (siehe 2b-Texte).
- **Soundeffekte-Kachel:** eigene Datei wählen ODER Library verbinden, dann
  Doppelklick auf die 🔊-Spur = gesetzt, Marker ziehen = verschieben, linke Kante
  = Stille am Anfang wegschneiden, rechte Kante = Länge, Regler =
  Lautstärke. Vorlauf, Länge und Pegel gleicht das Cockpit selbst aus; die
  Vorschau spielt die Effekte mit (siehe 2b-Sfx).
- **Audio-Kachel:** eigenes Lied oder Voiceover-Datei wählen, Voiceover mit
  dem Mikro aufnehmen. Neue Dateien landen in Downloads — beim „fertig"
  in den Projektordner verschieben, dann `build_editor.py`.
  Musik: SONG-ÜBERSICHT unter der Timeline (ganzes Lied, lila Fenster
  ziehen = Stelle im Lied) + „Start im Lied".
- **Vorschau-Zoom:** Mausrad = rein/raus (auf den Cursor), Ziehen =
  verschieben, −/100%/+ unten links.
- **Ebenen (Karte oben):** Grafik-overlays und der Freisteller laufen in der
  Vorschau mit, je Ebene zuschaltbar (kommt aus `cockpit_custom.js`, global
  unter `~/.scb-creator-kit/`). Braucht je Ebene eine `.webm`-Schwesterdatei
  (`freistellen.py` erzeugt sie mit; für PNG-Sequenzen `<ordner>.webm`
  daneben legen). Beim Abspielen minimal versetzt möglich — framegenau ist
  Anhalten/Scrubben; der Render setzt exakt zusammen.

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
#  jeden Clip auf die Groesse des ERSTEN Clips/30fps bringen, dann concat)
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

### 1a-Start. Projekt anlegen = EIN Aufruf, nicht sechs

```
<python> scripts/projekt_starten.py <clip1> [clip2 ...] [--name reel-42]
```

Das erledigt in einem Durchgang: Ordner anlegen (im Arbeitsordner unter
`Projekte/`, siehe „Arbeitsordner" — ist keiner gesetzt, VORHER einmal
fragen und setzen), Clips zusammenfügen, `projekt.json` schreiben,
transkribieren, Pausen messen, Cockpit bauen. Geöffnet wird danach mit
`cockpit_oeffnen.py <projektordner>`.
Am Ende steht eine Bilanz, welcher Abschnitt wie lange gebraucht hat, und
die Schnittvorschläge stehen da. Danach geht es bei 1b Punkt 3 weiter
(Inhalt prüfen) — die Punkte 1 und 2 sind erledigt.

> **Warum das Pflicht ist (gemessen am 23.08.2026):** Derselbe Ablauf aus
> Einzelschritten brauchte **sieben Minuten** — davon rund **drei Minuten,
> in denen der Rechner nichts tat**, weil zwischen sechs bis acht
> Script-Aufrufen jeweils neu nachgedacht wurde. Die Rechenzeit war nie
> das Problem, die Anzahl der Runden war es.

Nur wenn der Nutzer schon „mach fertig" gesagt hat, zusätzlich `--setzen`:
dann werden die Vorschläge direkt als Schnitte gesetzt und es geht sofort
zu `pruef_text.py`. Ohne dieses ausdrückliche Okay **nicht** verwenden —
sonst fällt die inhaltliche Prüfung aus.

### 1b. Schnitt-Analyse — PFLICHTABLAUF (Reihenfolge einhalten!)

Punkt 1 und 2 macht `projekt_starten.py` bereits mit. Einzeln nur nötig,
wenn nachträglich etwas wiederholt werden muss.

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
render_projekt/vorschau fügen sie zusammen (ffmpeg concat, bei
unterschiedlichen Clips alle auf die Größe des ERSTEN Clips gebracht; das
Zielformat setzt erst der Render, siehe 2b-Format) → EIN Quellvideo. Verlustfrei aneinandergehängt
wird nur, wenn alle Clips in ALLEN Stream-Eigenschaften gleich sind (auch
Farbkennung); sonst wird neu kodiert und die Farbkennung vereinheitlicht —
sonst ging am Clipwechsel Bild verloren. Im Cockpit hängt der Nutzer Clips
über „Weiteres anhängen" (Dateien im Projektordner) oder „📁 Video von
woanders" an. Steht in `videos` ein Name, den es im Projektordner nicht
gibt, hat der Nutzer ihn von woanders angehängt: nach dem Ort fragen (oder
suchen), Datei in den Projektordner kopieren, build_editor laufen lassen —
erst dann rendern. Darauf wirken die `cuts` (nur
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

### 2b-Sfx. Soundeffekte (Cockpit-Spur „🔊 Effekte")

`P.effekte.sfx` = `[{time, file, gain, trim?, len?, fade?, level?, peak?,
name?}]` — beliebig viele Events auf einer eigenen Timeline-Spur.
**`time` ist ROHZEIT** (Zeit im zusammengefügten Quellmaterial, VOR den
Schnitten) — genau wie bei Texten und Zooms. Die Cockpit-Timeline läuft
über die volle Rohlänge und zeigt die Schnitte als rote Balken darin.
**Niemals die Dauer der Schnitte herausrechnen** — `render_projekt.py`
verschiebt die Zeiten selbst um die Schnitte und wirft Effekte weg, die IN
einem Schnitt liegen. (Die übrigen `effekte`-Schlüssel bleiben Output-Zeit.)

**Sprach-Schnipsel einer zweiten Aufnahme** (saubere Tonspur über ein Video
mit schwachem Ton) gehören ebenfalls hierher — je gesprochene Einheit ein
eigener Event, damit der Nutzer sie einzeln schieben kann. Sobald er
geschoben hat, stimmen die Untertitel-Wortzeiten nicht mehr: der Untertitel
läuft dem Ton voraus und steht stellenweise doppelt im Bild. Danach immer
`reel-aufzaehlung/scripts/stimme_synchronisieren.py <projekt.json>` laufen
lassen. Das ganze Verfahren steht im Skill `reel-aufzaehlung`.

**Länge:** ohne `len` läuft der Effekt so lang, wie die Datei ist —
build_editor.py misst dafür jede verwendete Datei (auch Pfade außerhalb der
Library, Ergebnis in `_sfxlib.dauer`), das Cockpit zeigt und spielt die
volle Länge. `len` nur setzen, wenn er bewusst KÜRZER sein soll.

Bedienung: Kategorie + Effekt in der Kachel wählen, dann **Doppelklick
auf die 🔊-Spur** = Effekt an dieser Stelle (ein einfacher Klick setzt dort
wie überall nur den Läufer); **aufziehen** = Effekt mit
dieser Länge; **Marker ziehen** = verschieben; **rechte Kante** = Länge.
Je Event ein Lautstärke-Regler (0–100 %). Die Vorschau spielt die Effekte
mit — Platzierung ist ohne Render beurteilbar. „Tonspur anzeigen" zeigt auf
der 🔊-Spur die **Effekt**-Wellenformen, nicht den Videoton.

**Marker-Kanten = trimmen wie ein Clip.** Linke Kante ziehen schneidet vorne
weg, was in der Datei noch still ist: `time` und `trim` wandern gemeinsam,
die rechte Kante bleibt stehen (`len` schrumpft mit) — der Ton unter dem
Marker verrutscht also nicht. Rechte Kante = Länge. **Das ist der Weg für
Dateien, die mit langer Stille anfangen**, wenn keine Messwerte vorliegen.
Zusammen mit dem Timeline-Zoom (unten) geht das millisekundengenau.

**Ohne Library — zwei Knöpfe in der Kachel:**
- **🎧 Eigene Sound-Datei wählen** — wie „Lied auswählen". Die Datei wird im
  Browser vermessen (Dauer, Spitze, Vorlauf, Wellenform), ist sofort hörbar
  und landet unter „Eigene Dateien". Sie muss danach in den Projektordner
  (Hinweis kommt automatisch, wie bei Musik/Voiceover) — sonst fehlt sie beim
  Rendern. Danach steht sie dauerhaft unter „Projekt", vermessen und
  normalisiert. Solche Dateien tragen **kein** `peak`: ohne ffmpeg kann das
  Cockpit sie nicht auf ein einheitliches Niveau bringen, der Regler heißt
  dann schlicht „Anteil dieser Datei" (`gain` = `level`).
- **📂 Sound-Library verbinden** — Ordnerpfad eintragen; landet als
  `sfx_library` in der projekt.json. Beim nächsten `build_editor.py` wird die
  ganze Library vermessen und in `~/.scb-creator-kit/soundlibrary.txt`
  gemerkt, gilt ab dann für **alle** Projekte. (Ein Browser kann keinen
  Ordner von sich aus lesen und kennt keine echten Pfade — deshalb einmal
  eintragen statt Ordner-Dialog.)

Drei Dinge nimmt das Cockpit dem Nutzer ab (alle drei kosten sonst je
einen Render):

- **Vorlauf.** Viele Rohdateien fangen mit Stille an (`Mouse-Click.mp3`
  1,02 s, `Keyboard-Typing.mp3` 2,36 s). `trim` überspringt sie, damit
  `time` der **hörbare** Einsatz ist.
- **Länge.** Alles über 4 s hörbare Länge wird beim Einfügen auf 2,5 s
  mit 0,2 s Ausblende gesetzt (`len`/`fade`), sonst tippt eine 19-s-Datei
  bis zum Reel-Ende durch. Jederzeit über die rechte Kante änderbar.
- **Pegel.** Die Rohdateien liegen bis zu 14 dB auseinander. `build_editor.py`
  legt beim Scan normalisierte Fassungen (−1,5 dBFS, FLAC) in
  `~/.scb-creator-kit/sound-cache/` und die Events zeigen dorthin. Deshalb
  bedeutet der Regler bei jedem Effekt dasselbe — und `gain` bleibt ≤ 1,0.
  **Das ist Absicht:** ein Browser kann nicht lauter als 1,0 abspielen;
  müsste der Render einen leisen Effekt erst hochziehen, wäre die Vorschau
  leiser als das fertige Video und jede Beurteilung wertlos. FLAC statt mp3,
  weil ein mp3-Encoder vorne ~26 ms Stille anhängt — genau die Falle, die
  `trim` gerade zumacht.

**Woher die Effekte kommen:** `build_editor.py` sucht die Library in dieser
Reihenfolge — `sfx_library` in der projekt.json (Pfad oder Liste),
`$SCB_SOUNDS`, `~/.scb-creator-kit/soundlibrary.txt`, dann Raten
(`../Soundeffekte`, `../../Soundeffekte`, `~/Soundeffekte`, `<kit>/sounds`);
der Treffer wird gemerkt. Jeder Unterordner wird eine Kategorie, der
Projektordner `sfx/` heißt „Projekt". Messwerte liegen in
`~/.scb-creator-kit/sound-index.json` (Schlüssel: Pfad + mtime + Größe) —
der erste Scan von ~150 Dateien dauert gut eine Minute, jeder weitere unter
einer Sekunde. Jeder Eintrag trägt **beide** Pfade — `f` (die Datei, die
klingt: normalisiert, falls vorhanden) und `q` (das Original) — plus `pk0`,
den Pegel des Originals. Zeigt ein Effekt noch auf die Originaldatei (ältere
Projekte, von Hand geschriebene Einträge), findet er darüber trotzdem seine
Wellenform und Messwerte; ohne das bleibt die 🔊-Spur an diesen Stellen leer
und der Marker bekommt die falsche Breite. `.mp4` in der Library wird als **Audio** gelesen (die
Essentials-Kategorie liegt so vor). Alles über 30 s gilt nicht als Effekt
(sortiert Lied und Voiceover aus). Die Wellenformen der Effekte fallen beim
Vermessen mit ab und landen in `waveform_data.js` — **nicht** in
`projekt_data.js`, das alle 2,5 s neu geladen wird.

**Sagt jemand „ich hab die Library jetzt":** Pfad in die projekt.json
(`"sfx_library": "<pfad>"`) oder er trägt ihn selbst über den Knopf ein, dann
einmal `build_editor.py` — fertig, ab da automatisch in jedem Projekt.

prolook mischt jedes Event mit
`atrim=start=trim[:end=trim+len],asetpts,afade,volume,adelay`. Bei sehr
vielen gleichartigen Events (z. B. ein Klick auf JEDER Untertitel-
Einblendung) stattdessen `build_sfx_track.py` benutzen: baut EINE WAV, die
als ein einziger sfx-Eintrag eingemischt wird.

### 2b-Zoom. Zoom-Abschnitte mit Zielpunkt

`P.zooms` = `[{start, end, zoom, x, y, mode, ramp}]` — Timeline-Zeiten,
`zoom` 1.05–2.0, `x/y` = Zielpunkt als Anteil, `mode` `fahrt` (sanft
reinziehen, per zoompan subpixel-flüssig) oder `fest` (harter Punch-In).
`ramp` = Sekunden bis voller Zoom (Geschwindigkeit; ohne Angabe = ganze
Abschnittslänge, danach hält der Zoom). „Zoom langsamer/schneller" vom
User = nur `ramp` ändern. Cockpit: „Aufziehen = Zoom", Abschnitt auf einer
Videospur aufziehen, ⌖-Punkt im Video auf das Ziel ziehen — Live-Vorschau
zoomt Video + PiP (Untertitel/Texte bleiben ungezoomt, exakt wie der
Render). render_projekt.py reicht sie (Zeiten verschoben) als
prolook-`zooms` durch. **„Zoom auf mein Gesicht" per Zuruf:** 1 Frame an
der Stelle ziehen (`ffmpeg -ss <t> -frames:v 1`), ansehen, Gesichtszentrum
als x/y schätzen (Anteile!), zooms-Eintrag in projekt.json setzen,
build_editor — der User sieht den ⌖ im Cockpit und kann nachjustieren.

### 2b-Filter. Filter & Looks (Cockpit-Spur „🎨 Filter")

`P.filter` = `[{start, end, preset, staerke, farben?, toleranz?}]` —
Timeline-Zeiten wie Texte (Rohzeit, render_projekt.py verschiebt sie um die
Schnitte), `staerke` 0.1–1. Überlappen zwei Abschnitte, gewinnt der später
beginnende — im Cockpit wie im Render. Per Zuruf IMMER über
`cockpit_befehl.py --filter …` (siehe 2c).

| Gruppe | `preset` | Technik |
|---|---|---|
| Farbe & Licht | `sw` `noir` `sepia` `retro` `warm` `kalt` `kraeftig` `matt` `heller` `dunkler` | Farbfaktoren: Vorschau per CSS-Filter, Render per colorchannelmixer |
| Looks | `kino` (Teal & Orange) `film` (verblasst) `golden` (Golden Hour) `moody` `bleach` (Bleach Bypass) | 3D-Farbtabelle (LUT, 33³) |
| Spezial | `farbe` = Farbe behalten (Sin City): `farben` = Liste #rrggbb (bis 4), `toleranz` in Grad (Standard 25) | 3D-Farbtabelle, je Abschnitt berechnet |

**Eine Quelle:** `scripts/filter_presets.py`. Looks und „Farbe behalten"
laufen über eine 3D-LUT — der Render schreibt sie als `r_filter_<n>.cube`
und nimmt `lut3d=…:interp=trilinear`; das Cockpit wendet dieselbe Tabelle
Pixel für Pixel auf einem Canvas an (Looks aus `filter_luts.js`, das
build_editor.py ins Projekt legt; „Farbe behalten" rechnet das Cockpit mit
derselben Formel). Gemessen 01.10.2026 mit identischen Pixeln: Cockpit vs
ffmpeg höchstens 2/255. WebGL wäre schneller, ist bei lokal geöffneten
Dateien aber gesperrt — Canvas 2D funktioniert. Beim Abspielen rechnet die
Vorschau in 360 px Breite, im Stand in 720 px.

**Sin City:** Haut liegt im Farbton mitten im Rot (103–138°). Getrennt wird
über die Sättigung: jede Zielfarbe verlangt mindestens die halbe Sättigung
der gewählten Farbe — ein knallrotes Shirt bleibt rot, Gesicht und Hände
werden grau. Bei matten Farben deshalb im Cockpit **„Aus dem Video"**
(Pipette) nehmen: das trifft Farbton und Sättigung des echten Kleidungsstücks;
`toleranz` größer = mehr Nachbartöne bleiben farbig. Named colors im Befehl:
rot, blau, gelb, gruen, orange, pink, lila, tuerkis.

Ein neuer Look = nur `look_rgb()` + `LOOKS` in filter_presets.py ergänzen
(build_editor erzeugt filter_luts.js dann neu). Ein neuer einfacher Filter =
nur `PRESETS` (Schritte sat/con/mul/sepia/tint).

### 2b-Format. Bildformat (9:16, 16:9, 1:1, 4:5)

```
"format":     "9:16" | "16:9" | "1:1" | "4:5"
"einpassen":  "fuellen" (zuschneiden) | "unscharf" (unscharfer Hintergrund) | "balken"
"ausschnitt": {"x": 0.5, "y": 0.5}     nur bei "fuellen": 0 = links/oben, 1 = rechts/unten
```

- **Neue Projekte** bekommen das Format automatisch aus dem ersten Clip
  (`projekt_starten.py`, auch bei Handyvideos mit Drehungs-Markierung):
  Querformat → 16:9, Hochkant → 9:16 oder 4:5, fast quadratisch → 1:1.
- **Altprojekte ohne `format`** bleiben exakt wie bisher: 9:16 mit schwarzen
  Rändern (gemessen 03.10.2026: Bild für Bild identisch zum alten Render).
- Fehlt `einpassen`, gilt bei gesetztem Format „unscharf".
- Der Nutzer stellt im Cockpit unter **Bild → Format** um (Bühne, Untertitel-
  und Text-Maßstab, Instagram-Zonen nur bei 9:16 — alles passt sich an);
  „Füllen" zeigt Regler für den Ausschnitt, und zwar nur in der Richtung, in
  der wirklich etwas abgeschnitten wird. Per Zuruf:
  `cockpit_befehl.py <projekt> --format 9:16 --einpassen fuellen --ausschnitt 0.3`.
- Render: `bildformat.py` ist die eine Quelle (Größen, Regeln); prolook
  bringt das Bild per „fuellen" (scale+crop, Ausschnitt wie CSS
  object-position), „unscharf" (klein gerechnet, gblur σ 6, Faktor 0,88 —
  das Cockpit rechnet denselben Rand im Canvas) oder „balken" ins Format.
  **Vollbild-Ebenen** (Freisteller, `fullframe: true`) bekommen denselben
  Zuschnitt, wenn ihre Größe vom Ziel abweicht — sonst säße die Person
  versetzt. Ebenen, die schon in Zielgröße vorliegen (Motion-Canvas-Grafik),
  bleiben unverändert. **Grafik für ein Projekt immer im Zielformat bauen**
  (`render.width/height` = Format-Größe, siehe bildformat.FORMATE).
- Mehrere Clips mit unterschiedlichem Format werden beim Zusammenfügen auf
  das Bild des ERSTEN Clips gebracht; das Zielformat setzt erst der Render.
- `render.width/height` überstimmt alles (nur für Sonderfälle).

**Kamera folgt der Person** (`"ausschnitt": {"folgen": true}`, nur bei
„fuellen" und abweichendem Seitenverhältnis, z. B. 16:9-Material als Reel):
`scripts/person_folgen.py` findet den Kopf mit dem Personen-Modell der
Freistellung (kein Download, klappt auch im Profil) — 5 Bilder/s, rund
6× schneller als Echtzeit, gecacht in `r_person.json`. Der „Kameramann":
Totzone (bleibt ruhig, solange der Kopf am Platz ist), weiches Nachziehen,
vorwärts und rückwärts gerechnet (bewegt sich leicht VOR der Person statt
hinterher), springt bei Schnitten hart um, fährt bei längeren Stellen ohne
Person (Titelkarte) in die Bildmitte. Fehlalarme (dunkle Möbel) fallen
weg: nur der größte Bereich zählt, und Bereiche unter 45 % der typischen
Personengröße des Videos gelten nicht. Cockpit und Render rechnen dieselbe
Fahrt (gemessen 03.10.2026: Abweichung 0,00005); der Render verschiebt den
Zuschnitt Bild für Bild per `sendcmd` — auch bei Freisteller-Ebenen.
build_editor.py rechnet die Kopfpunkte, sobald sie gebraucht werden; der
Render rechnet sie notfalls selbst. Per Zuruf:
`cockpit_befehl.py <projekt> --format 9:16 --folgen` (`--nicht-folgen` aus).
Grenze: bei mehreren Personen im Bild folgt sie der größten.

**Hilfe im Cockpit:** Das ?-Symbol oben (oder Taste ?/F1) öffnet Kurz-
anleitung, alle Tastenkürzel und Beispielsätze für Zurufe an Claude.

### 2b-Spuren. Spurenleiste, Ebenen und Nummern im Cockpit

Links neben der Zeitleiste stehen die Spuren wie Ordner: ▾/▸ klappt auf
und zu (gespeichert als `spuren_zu`, das kann Claude auch selbst setzen),
Klick auf den Namen springt zur Spur, ‹ › springt zum vorigen/nächsten
Element dieser Spur. Mausrad über der Leiste (oder Umschalt + Mausrad über
den Spuren) = Spuren hoch/runter; Mausrad über den Spuren = Zoom wie bisher.
Effekte, die sich zeitlich überschneiden, legt das Cockpit selbst auf
eigene Ebenen („↳ Ebene 2" …) — in den Daten ändert sich dadurch nichts.
Alles ist nummeriert, in der Spur und rechts in der Liste gleich:
**Cut 1, 2, 3 …**, Effekte, Texte, Filter und Zooms je ab 1, in
Zeitreihenfolge. Spricht der Nutzer von „Cut 3" oder „Effekt 2", ist das
der dritte Schnitt bzw. zweite Effekt nach Startzeit (alle Schnitte
mitgezählt, auch inaktive).

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

**Zurufe wie „Whoosh beim Wort Brieftaube", „mach 1:10–1:20 schwarz-weiß",
„schneid das Äh raus", „lösch Effekt 3": IMMER `scripts/cockpit_befehl.py`
— NICHT die projekt.json lesen (bei langen Videos 40 KB Wörter = teuer).**
Das Script sucht Wörter selbst, rechnet Zeiten um, setzt den Eintrag genau
so, wie das Cockpit ihn setzen würde (Effekt-Lautstärke angeglichen,
Vorlauf weg), baut das Cockpit neu und meldet EINE Zeile. Der offene Tab
zeigt es nach ~3 s — kein F5, nicht neu öffnen.

```
<python> scripts/cockpit_befehl.py <projekt> --liste            # Überblick mit Nummern
<python> scripts/cockpit_befehl.py <projekt> --suche Brieftaube  # wo kommt das Wort vor
<python> scripts/cockpit_befehl.py <projekt> --sfx-liste [whoosh]
<python> scripts/cockpit_befehl.py <projekt> --effekt whoosh --wort Brieftaube [--nr 2] [--laut 60] [--vor 0.1]
<python> scripts/cockpit_befehl.py <projekt> --effekt pop --bei 0:42 --fertig
<python> scripts/cockpit_befehl.py <projekt> --filter sw --von 1:10 --bis 1:20 [--staerke 70]
<python> scripts/cockpit_befehl.py <projekt> --filter kino --wort Turm --dauer 4
<python> scripts/cockpit_befehl.py <projekt> --filter farbe --farben rot,blau --von 0:10 --bis 0:14
<python> scripts/cockpit_befehl.py <projekt> --text "Hook" --von 0 --bis 3 --fertig
<python> scripts/cockpit_befehl.py <projekt> --zoom 1.2 --wort Turm --dauer 2
<python> scripts/cockpit_befehl.py <projekt> --cut --wort äh --alle
<python> scripts/cockpit_befehl.py <projekt> --loeschen effekt 3
<python> scripts/cockpit_befehl.py <projekt> --format 16:9 [--einpassen fuellen|unscharf|balken] [--ausschnitt 0.3]
<python> scripts/cockpit_befehl.py <projekt> --format 9:16 --folgen        # Kamera folgt der Person
```

**Welche Zeit meint der Nutzer?** Das Cockpit zeigt Rohzeit (ungeschnitten)
— schaut er dabei ins Cockpit, ist das Standard. Meint er das fertige Reel
(„in Sekunde 12 vom Video"), `--fertig` anhängen. Im Zweifel einmal kurz
fragen. Am genauesten sind Wörter (`--wort`) und Nummern (Cut 3, Effekt 2 —
dieselben wie im Cockpit). Wörter in rausgeschnittenen Stellen überspringt
`--wort` von selbst; `--suche` zeigt alle Fundstellen.

Andere Änderungen (Schriftfarbe, Untertitel-Stil …): projekt.json FRISCH
lesen — der Nutzer kann im Cockpit weitergearbeitet haben, es speichert
automatisch —, nur das betroffene Feld ändern, `build_editor.py`. Hat das
Projekt im Cockpit noch keinen Speicherort, stehen seine Klicks nur im
Browser: dann zuerst „einmal auf Speichern klicken" erbitten.

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
  Umgebungsvariable — beim installierten Kit stecken die Nutzer-Keys in
  den Platzhaltern. Groq ist der bevorzugte Transkriptionsdienst,
  ElevenLabs die Rückfallebene — beide setzen, soweit vorhanden
  (unersetzte ~~Platzhalter einfach weglassen), z. B. in PowerShell:
  `$env:GROQ_API_KEY = "~~groq-api-key"` und
  `$env:ELEVENLABS_API_KEY = "~~elevenlabs-api-key"`, dann:
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
- **Bevor ein Visual gesetzt wird, erst die Stelle bestimmen**, an der es
  etwas erklärt, zeigt, vergleicht oder ordnet. Nicht jeder Satz bekommt
  eins, und ein Icon, das nur das gesprochene Wort verdoppelt, ist keins.
  Vorauswahl gemessen statt geraten:
  `<python> skills/pro-look-editing/scripts/aussagen_finden.py <projekt.json>`
  — Begründung und Regeln in `pro-look-editing`, Abschnitt 1b.
