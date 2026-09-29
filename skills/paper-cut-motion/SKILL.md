---
name: paper-cut-motion
description: >
  Paper-Cut-Clip für Reels: Eine Idee oder ein eigenes Bild wird zur Szene
  aus gerissenem Papier, die sich in Stop-Motion Stück für Stück selbst
  zusammensetzt, mit leisen Papiergeräuschen. Drei Aufträge über die
  Higgsfield-CLI (Papierbild, Storyboard mit neun Feldern, 10-Sekunden-Video
  mit Kling 3.0 oder Seedance 2.0), getestete Prompts, gemessene Preise ab
  24,5 Credits und ein Skript, das das Kling-Startbild aus dem Storyboard
  schneidet. Verwende diesen Skill bei: "Paper-Cut", "Paper Cut Motion",
  "Papier-Collage", "Papier-Animation", "Stop-Motion aus Papier", "Szene baut
  sich aus Papier auf", "torn paper", "Bild in Papier verwandeln",
  "Collage-Look animieren". Nicht für Erklärvideos mit Sprecher und nicht für
  Clips mit lesbarem Text im Bild.
---

# Paper-Cut Motion

Ergebnis: ein 10-Sekunden-Clip, in dem sich eine Szene aus flachen, gerissenen
Papierstücken selbst zusammensetzt. Hintergrund zuerst, Hauptmotiv zuletzt,
jedes Stück mit hartem Schatten, dazu leise Papiergeräusche. Taugt als Einstieg
oder Einspieler im Reel.

Am 17.09.2026 über Higgsfield gebaut und getestet, Preise am 21.09.2026
nachgemessen. Was nicht getestet ist, steht ausdrücklich dabei.

## Ablauf und Preise

| Schritt | Modell und Einstellung | Eingabe | Credits |
|---|---|---|---|
| 1 Papierbild | `gpt_image_2`, 1k, high | Idee als Text, auf Wunsch eigenes Bild | 3,5 |
| 2 Storyboard | `gpt_image_2`, 1k, high | Papierbild als Referenz | 3,5 |
| 3a Video mit Kling | `kling3_0`, std, 10 s, Ton an | Feld 1 als Startbild, Papierbild als Endbild | 17,5 |
| 3b Video mit Seedance | `seedance_2_0`, std, 720p, 10 s | nur das Storyboard als Referenz | 45 |

Zusammen 24,5 Credits mit Kling oder 52 mit Seedance. Kling ohne Ton kostet
12,5. Preise ändern sich; vor jedem Auftrag zählt der Wert aus
`higgsfield generate cost`.

## Acht Regeln, die Credits sparen

1. **Erst Preis, dann Freigabe, dann Auftrag.** `higgsfield generate cost` mit
   genau den Flags des späteren Auftrags kostet nichts. Vor dem ersten Credit
   den Auftrag in eigenen Worten wiederholen: Motiv, Format, Videoweg, Ton,
   was ausdrücklich nicht dazugehört, Summe. Erst nach dem Okay starten.
2. **GPT Image 2 immer mit `--resolution 1k --quality high`.** Ohne Angabe
   rechnet das Modell mit 2k und kostet 6,5 statt 3,5. Als Vorlage für ein
   720p-Video reicht 1k.
3. **Seedance bekommt nur das Storyboard.** Am 17.09.2026 blockte Seedance 2.0
   zweimal mit Status `nsfw`, sobald das Papierbild als zweite Referenz neben
   dem Storyboard mitging, auch mit entschärften Wörtern. Mit dem Storyboard
   allein lief derselbe Prompt durch. Ob es an der Zahl der Referenzen lag oder
   an diesem Bild, ist offen. Das Ende stimmt trotzdem, weil Feld 9 die fertige
   Szene zeigt. Blockierte Läufe werden erstattet und kosten nur Wartezeit.
4. **Kling nimmt kein Referenzbild,** nur Start- und Endbild. Das ganze
   Storyboard als Startbild bringt das Raster ins Video. Deshalb geht nur Feld 1
   hinein, ausgeschnitten mit `scripts/feld_ausschneiden.py`.
5. **Kein lesbarer Text im Bild.** Kein Videomodell hält Schrift sauber. Texte
   kommen danach als Overlay ins Cockpit (`video-projekt`), in die Zonen aus
   `reel-layout`.
6. **Die Higgsfield-CLI nie aus Python heraus starten.** Auf Windows zerschneidet
   der `.cmd`-Starter lange Argumente ohne Fehlermeldung: Der Prompt kommt
   gekürzt an, alle Flags danach fehlen. Aufrufe direkt in der Shell, den Prompt
   aus einer Datei in eine Variable, ein Absatz ohne Zeilenumbruch.
7. **Nach dem ersten Auftrag zurücklesen,** was wirklich ankam, bevor der
   nächste startet (Befehl unten). Stimmt ein Wert nicht, stoppen.
8. **`generate create` liefert manchmal eine Meldung statt einer Job-ID**, zum
   Beispiel `grace_daily_limit_reached`. Abgezogen wird dann nichts, aber mit
   dem Text darf nicht weitergearbeitet werden. Das Konto prüft der Nutzer
   selbst auf higgsfield.ai.

## Schritt 0: Klären und Auftrag wiederholen

Was fehlt, in einer Runde als Auswahl abfragen (AskUserQuestion, höchstens vier
Fragen). Was der Nutzer schon gesagt hat, nicht noch einmal fragen.

| Frage | Optionen |
|---|---|
| Motiv | eigene Idee / eigenes Bild / Vorschlag passend zum Reel-Thema |
| Videoweg | Kling, 17,5 Credits / Seedance, 45 Credits (Vergleich unten) |
| Ton | Papiergeräusche an / aus (bei Kling 12,5 statt 17,5) |
| Format | 9:16 für Reels / 1:1 / 16:9 |

Ein aufgeräumtes Motiv mit klarem Hauptelement wird besser als ein unruhiges.
Echte Personen, Marken und Logos nie beim Namen nennen, sondern allgemein
beschreiben („a young man in a blue hoodie"). Ein Schlussmoment nach dem Aufbau
(Auto fährt weg, Konfetti aus Papier) passt nur zum Seedance-Weg, weil bei Kling
das Endbild den letzten Frame festlegt; getestet ist er noch nicht.

Dann den Auftrag wiederholen (Regel 1) und auf das Okay warten.

Arbeitsordner ist der Projektordner des Reels, sonst ein eigener Ordner.
Dateinamen: `1-papier.txt`, `1-papier.png`, `2-storyboard.txt`,
`2-storyboard.png`, `3-start.png`, `3-video.txt`, `3-video.mp4`. Jede Job-ID
kommt in `jobs.txt`.

## Die Grundbefehle

Jeder Auftrag läuft gleich. Den Prompt als Textdatei anlegen (Write-Werkzeug
oder Heredoc mit `<<'EOF'`, dann stören weder Anführungszeichen noch
Apostrophe), dann Preis, Start, Zurücklesen, Warten, Laden. Hier für Schritt 1:

```bash
P="$(cat 1-papier.txt)"
higgsfield generate cost gpt_image_2 --prompt "$P" --aspect_ratio 9:16 --resolution 1k --quality high
JOB=$(higgsfield generate create gpt_image_2 --prompt "$P" --aspect_ratio 9:16 --resolution 1k --quality high)
echo "$JOB" | tee -a jobs.txt     # muss eine Job-ID sein, sonst Regel 8
higgsfield generate get "$JOB" --json | <python> -c "import json,sys; d=json.load(sys.stdin); p=d.get('params',{}); print(d.get('status'), len(p.get('prompt','')), 'Zeichen, Bilder:', [m.get('role') for m in p.get('medias') or []]); print({k:v for k,v in p.items() if k in ('aspect_ratio','resolution','quality','duration','mode','sound','generate_audio')})"
echo "${#P} Zeichen geschickt"
URL=$(higgsfield generate wait "$JOB" --timeout 30m | grep -o 'https://[^ ]*' | tail -1)
curl -sSL -o 1-papier.png "$URL"
```

Beim Zurücklesen muss die Zeichenzahl zur geschickten passen, und die Bilder
müssen stimmen. So sahen die Jobs vom 17.09. aus:

| Auftrag | Bilder | Status |
|---|---|---|
| Papierbild ohne eigenes Bild | `[]` | completed |
| Storyboard | `['image']` | completed |
| Kling | `['start_image', 'end_image']` | completed |
| Seedance mit Storyboard allein | `['image']` | completed |
| Seedance mit Storyboard und Papierbild | `['image', 'image']` | nsfw |

Bei Videos den Warte-Befehl im Hintergrund laufen lassen und nicht in kurzen
Abständen nachfragen; sie brauchen einige Minuten.

## Schritt 1: Papierbild

Der Prompt hat vier Teile, ein Absatz, Englisch:

1. **Szene** von hinten nach vorn: Hintergrund, Boden, Umgebung, Requisiten,
   Hauptmotiv. Konkrete Farben. Mit eigenem Bild beginnt der Absatz mit
   `Recreate the attached image as a torn-paper collage, keeping its subject, pose, layout and colours:`
   und einer kurzen Beschreibung des Bildes.
2. **Bildaufbau**, damit das Hauptmotiv nicht unter Instagrams Beschriftung und
   Knöpfen landet (Zonen aus `reel-layout`):
   `Keep the main subject and every important detail inside the central area of the frame: nothing important in the top seventh, in the bottom fifth or along the right edge.`
3. **Stilblock**, immer wörtlich:
   ```
   Handmade torn-paper collage look. Each element is a separate flat piece of paper, cut or torn by hand, with ragged white-fibred edges and a small hard shadow where it lies on the layer below. Paper grain is visible on every surface. Thin gaps of white paper show between neighbouring pieces. Colours are muted and slightly faded like matte craft paper, lit by soft light from one side. No gradients, no clean vector shapes, no glossy or plastic 3D surfaces.
   ```
4. **Verbot** am Schluss: `No text, no letters, no numbers, no logos anywhere.`

Aufruf wie oben. Mit eigenem Bild zusätzlich `--image <datei>`, der Preis bleibt
bei 3,5.

**Selbst ansehen, bevor es weitergeht:** gerissene Kanten, Schatten und weiße
Spalten sichtbar? Keine Schrift, keine Zahlen? Hauptmotiv mittig, oben und
unten ruhig? Wenn nicht, dem Nutzer zeigen und fragen, ob neu erzeugt wird
(3,5 Credits).

Ein vollständiges Beispiel aus dem Test: `references/beispiel-schreibtisch.md`.

## Schritt 2: Storyboard mit neun Feldern

Vorlage, am 17.09.2026 so auf Anhieb sauber. Eckige Klammern füllen; bei 16:9
`horizontal panels`, bei 1:1 `square panels` statt `vertical panels`:

```
A clean storyboard sheet: a 3x3 grid of 9 sequential vertical panels with thin white borders, read left to right and top to bottom, showing the scene from the reference image assembling itself piece by piece out of torn paper, always with the same fixed framing. Panel 1: a near-empty frame of plain paper, only the first [background] pieces sliding in from the top corners as torn paper. Panel 2: [...]. Panel 3: [...]. Panel 4: [...]. Panel 5: [...]. Panel 6: [...]. Panel 7: [...]. Panel 8: [...]. Panel 9: the complete finished composition exactly matching the reference image. Every panel keeps the same handcrafted paper-cut look: rough torn edges, visible paper grain, hard shadows, rough white negative-space slivers, and the same [palette] palette. Absolutely no text, no labels, no captions, no frame numbers and no writing in any panel.
```

Die Felder bauen von hinten nach vorn auf:

| Feld | Inhalt |
|---|---|
| 1 | fast leere Papierfläche, nur die ersten Stücke der Rückwand |
| 2 und 3 | Hintergrund: Wand, Himmel, Fenster, Horizont |
| 4 | Boden oder Tischfläche, von unten in Streifen |
| 5 und 6 | Umgebung und Requisiten, von links und rechts |
| 7 und 8 | Hauptmotiv Stück für Stück, von unten nach oben |
| 9 | fertige Szene, genau wie das Papierbild |

Aufruf wie oben, zusätzlich `--image 1-papier.png` (3,5 Credits). Das Format ist
das des späteren Videos, dann haben auch die Felder dieses Format.

**Selbst ansehen:** genau neun Felder im Raster? Keine Schrift, keine Nummern?
Feld 1 fast leer, Feld 9 gleich dem Papierbild? Hintergrund vor Hauptmotiv?
Taucht Schrift auf, nach Rückfrage neu erzeugen; der Verbotssatz bleibt am Ende.

**Halt vor dem Video.** Papierbild und Storyboard zeigen, Videoweg und Preis noch
einmal nennen, auf das Okay warten. Das Video kostet das Fünf- bis Dreizehnfache
eines Bildes. Hat der Nutzer beim ersten Okay ausdrücklich „ohne Zwischenstopp"
gesagt, entfällt dieser Halt; die eigene Prüfung der Bilder bleibt.

## Schritt 3a: Video mit Kling 3.0

**Startbild aus Feld 1:**

```bash
<python> scripts/feld_ausschneiden.py 2-storyboard.png 3-start.png
```

Das Skript findet die weißen Trennlinien selbst, auch wenn die Spalten je Zeile
verschoben sind (so war es am 17.09.), und rechnet das Feld auf 720 × 1280 hoch.
Meldet es „Drittel mit Rand genommen", den Ausschnitt ansehen: Am Rand darf
keine weiße Linie stehen. Die Unschärfe vom Hochrechnen fällt auf der fast
leeren Fläche nicht auf.

**Prompt**, am 17.09.2026 so getestet, ein Absatz:

```
Handcrafted stop-motion paper collage animation, the camera stays completely still. Starting from [what panel 1 shows], the scene builds itself piece by piece out of flat torn paper cutouts that slide and drop in from outside the frame in choppy stop-motion steps: first [panels 2 and 3], then [panel 4], then [panels 5 and 6], then [panel 7], and finally [panel 8 and the last details]. Every piece is a rigid flat paper cutout with rough white torn edges, visible paper grain and a crisp drop shadow, arriving one after another with tiny misalignments and staggered timing. No morphing, no cross-fade, no dissolve, no folding, no smooth digital motion. Sound: quiet paper foley only, soft paper slides, taps and drops, no music, no voice.
```

Mit `--sound off` den letzten Satz weglassen.

**Aufruf.** Als Endbild die Job-ID des Papierbilds aus Schritt 1, so getestet:

```bash
higgsfield generate create kling3_0 --prompt "$P" --duration 10 --aspect_ratio 9:16 --mode std --sound on --start-image 3-start.png --end-image <job-id-papierbild>
```

Beobachtet am 17.09.: Die Reihenfolge folgte genau dem Storyboard, das letzte
Bild traf das Papierbild, kein Raster im Bild. Der Anfang ist ruhig: In den
ersten knapp 2 Sekunden ändern sich nur 3 bis 4 % der Bildfläche (gemessen am
21.09. gegen das erste Bild), erst dann kommt das Fenster. Am Ende kamen mehrere
Teile schnell hintereinander. Den ruhigen Anfang im Cockpit kürzen statt neu zu
erzeugen, das kostet nichts.

## Schritt 3b: Video mit Seedance 2.0

**Prompt**, ein Absatz. Der Aufbau nennt jedes Element mit Richtung („slides in
from the left", „drops in from above", „slides up from below in layered torn
strips") und Schatten, das Hauptmotiv kommt zuletzt, Teil für Teil:

```
[Image1] is a 3x3 storyboard sheet: use its nine panels, read left to right and top to bottom, only as the order of the assembly; never show the grid, the borders or several panels at once, the video is one single continuous full-frame shot. Its last panel is the finished scene the video must end on. Static locked-off camera, no camera movement. Handcrafted stop-motion paper collage animation: the scene builds itself piece by piece out of flat torn paper cutouts that slide and drop in from outside the frame in choppy stop-motion steps. The frame starts on plain paper. [Aufbau Feld für Feld.] At the end every piece settles into place with small, slightly uneven nudges. Every piece is a rigid flat paper cutout with rough white torn edges, visible paper grain and a crisp drop shadow, arriving one after another with tiny misalignments and staggered timing. No morphing, no cross-fade, no dissolve, no folding, no smooth digital motion. Sound: quiet paper foley only, soft paper slides, taps and drops, no music, no voice.
```

Die Einleitung bis „no camera movement" und der Aufbau liefen am 17.09. so
durch. Stil-, Verbots- und Tonsätze stammen aus dem Kling-Test vom selben Tag. In
genau dieser Zusammenstellung ist der Seedance-Prompt noch nicht gelaufen, der
erste Lauf ist also der Test.

**Aufruf.** Das Storyboard als Job-ID aus Schritt 2, kein Dateipfad, so getestet.
Nie ein zweites `--image-references` dazu (Regel 3). Ton ist bei Seedance 2.0 von
selbst an.

```bash
higgsfield generate create seedance_2_0 --prompt "$P" --duration 10 --resolution 720p --aspect_ratio 9:16 --mode std --image-references <job-id-storyboard>
```

Beobachtet am 17.09.: Start auf hellem Papier, Aufbau in der Reihenfolge des
Storyboards, kein Raster im Bild, das Ende traf die Szene über Feld 9. Der
Aufbau beginnt nach einer halben Sekunde; nach 1,5 Sekunden hat sich das ganze
Bild verändert (gemessen am 21.09.).

## Kling oder Seedance

| | Kling 3.0 | Seedance 2.0 |
|---|---|---|
| Credits (10 s, 9:16, Ton an) | 17,5 | 45 |
| Vorlage | Feld 1 als Start, Papierbild als Ende | nur das Storyboard |
| Letztes Bild | durch das Endbild festgelegt | über Feld 9, traf im Test |
| Anfang im Test | knapp 2 s fast nur Wand | Aufbau ab 0,5 s |
| Schlussmoment nach dem Aufbau | nicht mit Endbild | möglich, ungetestet |

Empfehlung: Kling zuerst, weil billiger und das Ende sicher; den ruhigen Anfang
im Cockpit kürzen. Seedance, wenn der Clip das Reel eröffnet und sofort etwas
passieren muss, wenn ein Schlussmoment gebraucht wird oder wenn der Rhythmus von
Kling nicht gefällt. Wie flüssig die Bewegung wirkt, beurteilt der Nutzer am
abspielbaren Clip, nicht an Einzelbildern.

## Schritt 4: Prüfen und zeigen

Vor dem Zeigen selbst prüfen, mit einem Kontaktbogen aus acht Bildern und dem
letzten Bild statt vieler Einzelbilder:

```bash
ffmpeg -v error -y -i 3-video.mp4 -vf "fps=0.8,scale=240:-1,tile=4x2" -frames:v 1 3-bogen.jpg
ffmpeg -v error -y -sseof -0.3 -i 3-video.mp4 -frames:v 1 -update 1 3-ende.jpg
```

Prüfen: kein Raster und keine Felder im Bild, die Stücke bleiben flach und
starr, die Reihenfolge stimmt, das letzte Bild zeigt die fertige Szene. Dann dem
Nutzer den Clip abspielbar zeigen. Auffälligkeiten als Beobachtung nennen und
nicht eigenmächtig neu erzeugen; ob etwas stört, entscheidet der Nutzer.

## Schritt 5: Ins Reel

Der Clip ist Material wie jedes andere und läuft über `video-projekt`: als
eigenes Projekt (`projekt_starten.py`) oder als Einspieler (`effekte.broll` in
der projekt.json). Ab dort gilt der Ablauf von `video-projekt`. Nie per Hand mit
ffmpeg schneiden. Den leeren Anfang im Cockpit kürzen, Texte als Overlay setzen.

Danach die Videodatei löschen. Der Job bleibt im Higgsfield-Konto und lässt sich
jederzeit kostenlos neu laden (`higgsfield generate get <job-id>`). Die Job-IDs
aus `jobs.txt` aufheben, nicht die Dateien.

## Wenn etwas schiefgeht

| Was passiert | Was hilft |
|---|---|
| Seedance endet mit Status `nsfw` | Nur das Storyboard mitgeben (Regel 3). Erstattet wird automatisch. |
| Im Video steht das Raster | Das Storyboard ging als Startbild hinein. Seedance: `--image-references`; Kling: nur Feld 1. |
| Schrift oder Nummern im Storyboard | Nach Rückfrage neu erzeugen (3,5 Credits), Verbotssatz am Ende lassen. |
| Stücke verbiegen sich oder blenden über | Verbotssatz wörtlich übernehmen, nicht umformulieren. |
| Startbild hat eine weiße Kante | Meldung von `feld_ausschneiden.py` lesen, Ausschnitt ansehen. |
| `create` gibt Text statt Job-ID | Regel 8: nichts abgezogen, Konto prüfen lassen. |
| Preis weicht von der Tabelle ab | Neuen Preis nennen und neu freigeben lassen. |

## Noch nicht getestet

Vor dem ersten Einsatz einmal messen und hier nachtragen:

- eigenes Foto als Ausgangsbild in Schritt 1 (`--image`)
- Schlussmoment nach dem Aufbau (nur Seedance)
- Kling mit `--mode pro` (1080p, 20 statt 17,5 Credits)
- Seedance mit `--mode fast` (25 Credits) oder 480p (30 Credits)
- Seedance mit dem Papierbild als `--end-image` statt als zweite Referenz
- Seedance 2.5 (bei 720p 65 Credits, Referenzen nur mit `--mode omni_reference`)
- ein volleres Startbild für Kling (`--feld 2`), damit der Clip nicht auf leerer
  Wand beginnt

## Herkunft

Der Dreischritt aus Papierbild, Storyboard und Video stammt aus einem frei
verteilten Prompt-Paket von PYNK Society (September 2026). Die Prompt-Texte hier
sind eigene Formulierungen. Messwerte, Fallen und der Kling-Weg kommen aus dem
eigenen Test vom 17.09.2026.
