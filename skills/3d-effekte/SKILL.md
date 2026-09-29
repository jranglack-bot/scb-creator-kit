---
name: 3d-effekte
description: >
  Echte 3D-Effekte für Reels OHNE KI-Video und ohne Credits: 3D-Schrift aus
  jeder Schriftart, eigenes Logo als 3D-Körper, Logo kommt hinter der Person
  hervor und wird in die Kamera geworfen (Glas springt), schwebende
  3D-Bildschirme mit Kamerafahrt, Gegenstand zerlegt sich in Einzelteile
  (Explosionsansicht), Szene teilt sich in drei Ebenen (Wand, 3D-Objekt,
  Person) und schiebt sich wieder zusammen. Gebaut mit Three.js, gerendert mit
  Remotion oder HyperFrames, alles lokal auf dem eigenen Rechner. Verwende
  diesen Skill bei: "3D-Effekt ohne Higgsfield", "3D ohne KI", "echtes 3D",
  "3D-Logo", "Logo in 3D", "wirf das Logo in die Kamera", "Glas zerspringt",
  "3D-Schrift", "Text in 3D", "schwebende Bildschirme", "meine Reels hinter
  mir in 3D", "Explosionsansicht", "zerleg das in seine Teile", "Ebenen",
  "teil die Szene in Ebenen", "Wand, ich und Text", "Layer-Effekt", "wie in
  dem Claude-Code-Video", "3D ohne Credits".
---

# 3D-Effekte ohne KI-Video (Three.js)

Kein KI-Video, keine Credits, kein Upload. Claude schreibt die 3D-Szene als
Code (Three.js, kostenlos), und Remotion oder HyperFrames rechnet sie Bild
für Bild über das echte Video. Gemessen am 29.09.2026: ein 27-Sekunden-Clip
mit fünf 3D-Effekten in knapp drei Minuten auf einem 8-GB-Laptop.

Dieser Skill gehört zu Stufe 2b/2c aus `motion-grafik`. Alle Regeln dort
gelten weiter: Eingangsfrage, Red Zones, erst Vorschau zeigen, dann rendern.

## Was es fertig gibt

| Szene (`name`) | Was passiert | Braucht |
|---|---|---|
| `schrift` | Zwei Zeilen echte 3D-Schrift fliegen ein, Lichtkante wandert darüber | zwei Texte |
| `bildschirme` | Bis zu 5 Bilder als leuchtende 3D-Bildschirme, Kamera fliegt hindurch, das letzte bleibt groß stehen | 1 bis 5 Bilder (Hochformat) |
| `explosion` | Ein Handy zerlegt sich in Glas, Display, Platine, Akku, Rückseite, Kamera, mit Schildern, und setzt sich wieder zusammen | nichts |
| `ebenen` | Wand, 3D-Schrift und Person fächern sich im Raum auf, am Ende steht die Schrift HINTER der Person | Video-Freisteller, Bild der leeren Wand, ein Text |
| `logo` | Logo taucht hinter dem Kopf auf, schwebt vor der Person, wird in die Kamera geworfen, das Glas springt, das Bild wackelt | Video, Freisteller, optional eigenes Logo (SVG) |

Eine eigene Idee, die hier nicht steht, ist eine neue Szene im selben Muster
(siehe „Neue Effekte bauen"). Erst prüfen, ob eine Vorlage mit anderen
Texten, Bildern oder einer anderen Logo-Bahn reicht.

## Ablauf

### 1. Fragen, einmal

Die Eingangsfrage aus `video-projekt`/`motion-grafik` gilt. Dazu EINMAL per
AskUserQuestion das Werkzeug. **Der Nutzer wählt, nicht du:**

> „Für die 3D-Effekte habe ich zwei Werkzeuge, beide rechnen denselben
> 3D-Code. Womit soll ich arbeiten?"
>
> **Remotion:** Farben exakt wie im Originalvideo, Vorschau zeigt alles
> zuverlässig. Braucht bei wenig Arbeitsspeicher einen Zusatzschalter
> (steht unten), sonst bricht der Render ab.
>
> **HyperFrames:** Rund 15 % schneller, lief im Test jedes Mal im ersten
> Anlauf. Bild minimal dunkler (etwa 2 %, nur im direkten Vergleich zu sehen).

Antwort merken. Bei Remotion einmal die Lizenz erwähnen (siehe
`motion-grafik`). HyperFrames muss installiert sein (`npm i -g hyperframes`),
Remotion über den Setup-Assistenten (Bereich Grafik).

### 2. Material vorbereiten

- **Freisteller** (für `ebenen` und `logo`): mit
  `skills/pro-look-editing/scripts/freistellen.py` nur den benötigten
  Abschnitt rechnen. Genommen wird die `.webm` (Browser-Fassung mit Alpha).
- **Leere Wand** (für `ebenen`): am besten vor dem Dreh 2 Sekunden den leeren
  Raum filmen, gleiche Einstellung, Stativ, und davon ein Standbild nehmen.
  Gibt es das nicht:
  `<python> skills/3d-effekte/scripts/leere_wand.py <video> <freisteller.webm> wand.jpg`
  rechnet die Person heraus. Taugt für glatte Wände, nicht für Regale oder
  Fenster hinter der Person.
- **Logo-Bahn messen** (für `logo`): Kopf, Schulter und Hände bewegen sich in
  jedem Clip anders. Einen Kontaktbogen ziehen (ein Bild pro halbe Sekunde)
  und die Punkte der Bahn danach setzen, nie schätzen:
  `ffmpeg -i clip.mp4 -vf "fps=2,scale=216:384,tile=7x2" -frames:v 1 bogen.jpg`
  Wichtig sind drei Dinge: Der Startpunkt liegt hinter dem Kopf (dort
  verdeckt ihn die Person). Beim Wechsel von hinten nach vorn
  (`wechsel`, Standard 1,2 s) steht das Logo neben der Person über der
  Wand, sonst springt es sichtbar. Das Schweben liegt dort, wo die Hände
  gerade sind.
- **Schnitte im Clip meiden:** Die Szene endet vor einem Einstellungswechsel.
  Grobe Bildsprünge findet ein Vergleich aufeinanderfolgender Bilder.

### 3. Plan schreiben (`plan.json`)

Alle Dateinamen relativ zum Ordner des Plans.

```json
{
  "breite": 1080,
  "hoehe": 1920,
  "logo": "logo.svg",
  "szenen": [
    {"name": "schrift", "dauer": 5, "text1": "ECHTES", "text2": "3D"},
    {"name": "bildschirme", "dauer": 5, "bilder": ["a.jpg", "b.jpg", "c.jpg"]},
    {"name": "explosion", "dauer": 5.5},
    {"name": "ebenen", "dauer": 5.9, "text": "DEIN NAME", "wand": "wand.jpg",
     "person": "person.webm", "textLage": [490, 520], "textBreite": 800},
    {"name": "logo", "dauer": 5.9, "video": "clip.mp4", "person": "person.webm",
     "wechsel": 1.2, "aufprall": 4.3,
     "bahn": {"start": [430, 470, -3.0], "auftauchen": [760, 450, -1.2],
              "schulter": [800, 520, -0.3], "bogen": [770, 880, 0.6],
              "schweben": [500, 960, 1.3], "ausholen": [505, 1030, 0.8],
              "einschlag": [545, 880, 9.25]}}
  ]
}
```

- Jede Szene ist optional, Reihenfolge frei, dieselbe Szene darf mehrfach vorkommen.
- `bahn`: x und y in Bildpixeln, dazu die Tiefe z. Negativ heißt weiter weg und
  kleiner, bei 9,25 steht das Logo direkt vor der Linse. Weggelassene Punkte
  behalten den Standardwert.
- `logo` weglassen = eingebautes Strahlenzeichen. Ein eigenes SVG wird Pfad für
  Pfad in seiner Füllfarbe zum 3D-Körper.
- Weitere Felder: `beschriftungen` bei `explosion` (z. B. `{"akku": "Battery"}`),
  `schilder` bei `ebenen` (drei Texte, Standard „Hintergrund", „3D-Objekt", „Du").
- `textLage` und `textBreite` bei `ebenen` so setzen, dass die Schrift hinter
  dem Kopf liegt, aber die Red Zones einhält (rechts bis ca. 890 px).

### 4. Projekt anlegen

```
<python> skills/3d-effekte/scripts/projekt_anlegen.py plan.json --remotion [projektordner]
<python> skills/3d-effekte/scripts/projekt_anlegen.py plan.json --hyperframes <zielordner>
```

Das Script erzeugt die 3D-Schrift aus der Schriftart (Standard Arial Rounded
wie die Untertitel, andere mit `--schrift datei.ttf`), baut das Logo ein,
kopiert Bilder und Videos, installiert bei Remotion `three` nach und trägt
die Komposition `DreiDEffekte` in `src/Root.tsx` ein. Nach jeder Änderung am
Plan einfach erneut laufen lassen.

Bei HyperFrames auf einem externen Laufwerk: `hyperframes init` scheitert
dort, dieses Script braucht es nicht.

### 5. Vorschau zeigen, dann stoppen

- Remotion: `<python> skills/motion-grafik/scripts/editor_oeffnen.py --remotion`
- HyperFrames: `hyperframes lint` und `hyperframes check --no-contrast`, dann
  `hyperframes preview --port 3003 --background` (Port 3000 gehört Remotion).
  `--no-contrast`, weil die Schilder im 3D-Raum liegen und der Kontrasttest
  dort falsch misst: gemeldet 1,9:1, im Bild weißer Text auf dunklem Grund.

Achtung HyperFrames-Vorschau: Sie zeigte das Video in der Logo-Szene einmal
schwarz, im Render war es da. Das vorher sagen, bevor der Nutzer schaut.

Dann Turn beenden und auf das Okay warten (Regel aus `motion-grafik`).

### 6. Rendern (nach der Freigabe)

**Remotion**, immer mit diesen Schaltern:

```
npx remotion render DreiDEffekte out/3d.mp4 --crf=16 --gl=angle --concurrency=2 --offthreadvideo-cache-size-in-bytes=2000000000
```

`--offthreadvideo-cache-size-in-bytes` ist Pflicht, sobald ein Freisteller
drin ist: ohne ihn brach der Render bei unter 1 GB freiem Arbeitsspeicher
dreimal mit „No frame found at position …" ab, jedes Mal an einer anderen
Stelle. Neu kodieren mit mehr Schlüsselbildern allein half nicht.
`--gl=angle` nutzt die Grafikkarte.

**HyperFrames:**

```
hyperframes render . -o renders/3d.mp4 --crf 16 --workers 2
```

Schaltet bei wenig Arbeitsspeicher selbst in einen sparsamen Modus und lief
damit stabil.

### 7. Ins Reel

Die fertige MP4 ist deckend (sie enthält das Video schon). Sie kommt als
Overlay mit `"alpha": true, "fullframe": true` und passendem `start` in die
`projekt.json` und wird mit `render_projekt.py` eingebaut (siehe
`video-projekt`). Remotion schreibt yuvj420p mit BT.601-Farbangabe; der
Kit-Render kodiert das ohnehin Instagram-gerecht neu. Nie eine Remotion-Datei
direkt hochladen.

## Neue Effekte bauen

Alles steckt in `szenen.js` (Vorlage in `skills/3d-effekte/vorlagen/`). Eine
Szene ist eine Funktion, die ein Objekt zurückgibt:

```js
{ bereit: Promise, render(t) { ... }, dispose() { ... } }
```

Der Vertrag, damit beide Werkzeuge dasselbe Bild liefern:

- `render(t)` zeichnet genau das Bild zur Sekunde `t`. Kein
  `requestAnimationFrame`, kein `Date.now()`, keine Zustände aus dem
  vorigen Bild. Zufall nur über `zufall(seed)`.
- Renderer immer über `neuerRenderer()` (Pixelverhältnis 1,
  `preserveDrawingBuffer: true`, sonst ist das abfotografierte Bild leer).
- Bilder und andere Dateien über `pfad(datei)` laden und in `bereit`
  abwarten. Remotion wartet per `delayRender`, HyperFrames über
  `window.__hf.buildReady`.
- Vorhandene Helfer nutzen: `koerperAusPfad` (SVG-Pfad → Körper mit Fase),
  `koerperAusSvg` (ganze SVG-Datei), `textZeile` (Text → einzelne
  3D-Buchstaben), `schild` (Beschriftung), `staub` (schwebende Partikel),
  `umgebung` (Spiegelungen ohne HDRI-Datei), Easing und `feder`.
- Neue Szene in `erstelleSzene` eintragen. Braucht sie Videoebenen (wie
  `logo` oder `ebenen`), in BEIDEN Hüllen ergänzen: `vorlagen/remotion/index.tsx`
  und den HTML-Erzeuger in `projekt_anlegen.py`.

Beschriftungen und Text, die scharf bleiben sollen, liegen besser als flache
Ebene über dem 3D-Bild als in der 3D-Szene.

## Gemessen am 29.09.2026 (819 Bilder, 1080×1920, je 2 Prozesse, CRF 16)

| | Remotion | HyperFrames |
|---|---|---|
| Renderzeit | 194 s | 164 s |
| Bildinhalt | gleich (SSIM über 0,995, Schärfe ±3 %) | gleich |
| Videoebene bildgenau | ja | ja |
| Farbe gegen Originalvideo | ±1 Stufe | ca. 4 Stufen dunkler |
| Ausgabe | yuvj420p, BT.601, Vollbereich | yuv420p, bt709 |
| Erster Anlauf | brach ohne Cache-Schalter ab | lief |

Rechner: Intel Core 3 100U, 7,7 GB RAM, davon beim Test oft unter 1 GB frei.
