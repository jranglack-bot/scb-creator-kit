---
name: motion-grafik
description: >
  Aufwendige Bewegtgrafik für Reels, die das Cockpit nicht kann: animierte
  Ringe und Zähler, extrudierte 3D-Schrift, Lower Thirds, Ecken-Klammern —
  gebaut mit Motion Canvas (kostenlos, MIT) und als Alpha-Ebene ins Reel
  gelegt. Dazu der „Text hinter mir"-Effekt: die Person wird per MediaPipe
  freigestellt, sodass Grafik hinter ihr verschwindet. Verwende diesen Skill
  bei: "3D-Effekt", "3D-Schrift", "animierte Grafik", "Motion Graphics",
  "Zahl soll hochzählen", "Ring/Prozentanzeige", "Text soll hinter mir
  schweben", "Text hinter der Person", "Grafik hinter mir", "wie bei den
  großen Accounts", "aufwendigere Effekte als das Cockpit kann".
---

# Motion-Grafik (Motion Canvas / Remotion + Freistellung)

Dieser Skill ist die **Stufe 2 und 3** der Videoproduktion. Stufe 1 ist und
bleibt das Cockpit (`video-projekt`).

## GRUNDREGEL: nie höher einsteigen als nötig

| Stufe | Werkzeug | Wofür | Kosten für den Nutzer |
|---|---|---|---|
| 1 | **Cockpit** (`video-projekt`) | Schnitt, Untertitel, Musik, **einfache Texte und Hooks** | 0 Token, er ändert selbst |
| 2a | **Motion Canvas** | animierte Grafik — schneller gebaut und geändert | jede Änderung = eine Coderunde |
| 2b | **Remotion** | animierte Grafik — mehr möglich, u. a. echtes 3D | mehr Bauzeit je Runde |

**Zwischen 2a und 2b wählt der NUTZER**, nicht du — siehe Pflichtfrage unten.
| 3 | **Freistellung** (`freistellen.py`) | alles, was **hinter** der Person liegt | zusätzlich Rechenzeit |

### 2a oder 2b? — das entscheidet IMMER der Nutzer, nie du

**Sobald animierte Grafik gewünscht ist, MUSST du fragen** — mit
AskUserQuestion, genau einmal, bevor irgendetwas gebaut wird. Nicht
selbst wählen, auch dann nicht, wenn eines der beiden offensichtlich
besser passt.

> **Frage:** „Für die animierte Grafik habe ich zwei Werkzeuge. Womit
> soll ich arbeiten?"
>
> **Antwort A — Motion Canvas (schneller):** Schneller gebaut und
> schneller geändert. Ideal für Text-Einblendungen, Ringe, hochzählende
> Zahlen, Balken und Lower Thirds. Wenn du danach noch etwas ändern
> willst, geht das zügig.
>
> **Antwort B — Remotion (schönere Effekte):** Kann deutlich mehr,
> unter anderem echtes 3D mit Räumen, Kamerafahrten und Beleuchtung.
> Dafür dauert jede Runde länger.

**Antwort merken** und für dieses Projekt beibehalten — nicht bei jeder
Grafik neu fragen.

**Wenn der Nutzer unsicher ist oder zurückfragt**, darfst du beraten —
aber als Empfehlung, nicht als Entscheidung:

| Wunsch | Empfehlung |
|---|---|
| Text, Lower Thirds, Ecken-Klammern | Motion Canvas |
| Ringe, Balken, hochzählende Zahlen, Prozente | Motion Canvas |
| Ein-/Ausblenden, Verschieben, Skalieren in der Fläche | Motion Canvas |
| 3D-Schrift durch Extrusion (versetzte Kopien) | Motion Canvas |
| Echtes 3D: rotierende Körper, Räume, Kamerafahrten, Licht | Remotion |
| Viele gleichzeitig bewegte Elemente mit Tiefenstaffelung | Remotion |
| Ein Motion-Canvas-Versuch ist bereits gescheitert | Remotion |

**Bei Remotion vor dem Start einmal die Lizenz erwähnen:** kostenlos für
Einzelpersonen, Firmen bis 3 Mitarbeiter und Non-Profits, größere Firmen
brauchen eine kostenpflichtige Lizenz.

## EINGANGSFRAGE (einmal stellen, Antwort merken)

Bevor irgendetwas gebaut wird, den Nutzer EINMAL fragen — nicht raten, und
nicht in jeder Runde neu fragen:

> „Bevor ich loslege: Reicht dir Schnitt und Untertitel? Sollen einfache
> Texte drüber — die macht das Cockpit, die kannst du danach selbst
> verschieben. Brauchst du animierte Grafik, also Ringe, hochzählende Zahlen
> oder 3D-Schrift? Und soll etwas **hinter** dir liegen, sodass du davor
> stehst?"

Danach die Stufen **einzeln nacheinander** abarbeiten, mit Freigabe
dazwischen. Nicht alles auf einmal bauen.

**Sagt er ja zu animierter Grafik, folgt sofort die zweite Pflichtfrage:
Motion Canvas oder Remotion** (siehe oben). Erst danach wird gebaut.

## Stufe 2a: Motion Canvas

Kostenloses Open-Source-Werkzeug (MIT), das Animationen als Code beschreibt.
Kein Konto, keine Lizenz, kein Abo. Braucht **Node.js** — das bringt der
Setup-Assistent bereits mit (Basis-Werkzeuge). Das Projekt-Gerüst unten
entsteht je Videoprojekt in Sekunden.

### Einmalig einrichten

```bash
npm create @motion-canvas@latest -- --name motion --path <projektordner>/motion --language ts --plugins ffmpeg
cd <projektordner>/motion
npm install
```

Danach `src/project.meta` auf Reel-Format setzen (die Datei entsteht beim
ersten Start selbst und steht sonst auf 1920×1080 quer — **häufigste
Fehlerquelle**):

```json
{"version": 1,
 "shared": {"background": null, "size": {"x": 1080, "y": 1920}},
 "preview": {"fps": 30},
 "rendering": {"fps": 30,
   "exporter": {"name": "@motion-canvas/core/image-sequence",
                "options": {"fileType": "image/png", "quality": 100}}}}
```

`"background": null` ist Pflicht — nur so entsteht eine transparente Ebene.
**Jedes Projekt braucht seine eigene `.meta`.**

### Arbeiten damit

`npm start` startet den Editor auf **http://localhost:9000**. Dort spielt der
Nutzer das Ergebnis ab und scrubbt durch die Timeline — das kostet ihn keine
Token.

> ### ⛔ NIEMALS im eingebauten Browser öffnen
>
> `localhost:9000` gehört **ausschließlich in den echten Browser des
> Nutzers**. Öffne den Editor NIE mit deinen eigenen Browser-Werkzeugen
> (`preview_start`, `navigate`, Chrome-MCP) — dieses Fenster sieht der
> Nutzer nicht.
>
> Zwei Schäden entstehen sonst gleichzeitig (real passiert am 21.08.2026,
> Kosten: 20 Minuten Leerlauf):
> 1. Der Nutzer weiß nicht, dass auf seinen Klick gewartet wird, und sitzt
>    vor einem scheinbar hängenden Chat.
> 2. Browser frieren unsichtbare Tabs ein — gemessen **0 Bilder in 30
>    Sekunden** statt 349 in gut einer Minute.
>
> **Immer so öffnen:**
>
>     <python> scripts/editor_oeffnen.py
>
> Das Script prüft, ob der Editor läuft, öffnet ihn im Standardbrowser und
> gibt dir den Wortlaut vor, den du dem Nutzer sagen musst. **Sag danach
> ausdrücklich:** „Es hat sich gerade ein Browserfenster geöffnet — schau
> bitte in deinen eigenen Browser." Wartest du auf einen Klick von ihm,
> sag es in derselben Nachricht, sonst wartet ihr aneinander vorbei.

**Referenzebene:** In der Szene einen Schalter vorsehen, der das geschnittene
Video unter die Grafik legt:

```tsx
const PREVIEW = true;   // true = Video liegt zur Beurteilung darunter
                        // false = Export, nur die Grafik als Alpha-Ebene
if (PREVIEW) {
  view.add(<Video src={'/ref.mp4'} play width={1080} height={1920} />);
}
```

Das Video muss im `public/`-Ordner liegen. **Ohne Referenzebene kann der
Nutzer das Zusammenspiel nicht beurteilen** — sie gehört immer eingeschaltet,
solange er schaut.

**Ein-Tab-Prinzip wie beim Cockpit:** Motion Canvas lädt Codeänderungen selbst
nach. Den Tab einmal öffnen, danach nur noch sagen „schau in deinen offenen
Tab". Nie ein zweites Mal öffnen.

**Erst nach seinem Okay** `PREVIEW = false` setzen. Den Render startet der
Nutzer im Editor per Klick auf *Render* — **in seinem eigenen, sichtbaren
Browserfenster**. Ergebnis: eine PNG-Sequenz mit Alphakanal unter
`output/<projekt>/`.

Ihm dabei zwei Dinge sagen: **wo** er klickt (unten rechts im gerade
geöffneten Fenster) und dass das Fenster **sichtbar im Vordergrund bleiben
muss** — minimiert oder im Hintergrund drosselt der Browser den Render bis
zum Stillstand. Richtwert zur Einordnung: rund 350 Bilder brauchen im
sichtbaren Fenster gut eine Minute. Läuft es spürbar langsamer, ist das
Fenster verdeckt.

### Was sich bewährt hat

- **Pseudo-3D durch Extrusion:** Motion Canvas kann kein echtes 3D. Tiefe
  entsteht durch 12–14 gestapelte Kopien eines Elements, von dunkel nach
  hell versetzt. Bei Reel-Größe liest sich das als 3D.
- **Schrift extrudieren:** Versatz nach unten rechts (Licht von oben links),
  weiße Wörter in kühles Grau extrudieren, goldene in dunkles Gold — Weiß
  nach Braun sieht schmutzig aus.
- **Hereindrehen statt einblenden:** `scale.x` von 0 auf 1 ist die
  2D-Projektion einer Drehung um die Hochachse. Mit Überschwingen
  (`easeOutBack`) bekommt es Masse.
- **Beschriftung nicht mitkippen** — sonst wird sie unlesbar.
- Ein einziges Signal für Bogen, Tiefenschichten und Zähler, sonst laufen
  sie auseinander.

## Stufe 2b: Remotion

React-basiert, sehr aktiv gepflegt (Stand 22.08.2026: Release v4.0.515 vom
Vortag; Motion Canvas hatte seit Dezember 2024 keines mehr). Kann alles,
was Motion Canvas kann, **plus echtes 3D** über Three.js.

**Lizenz — vorher sagen, nicht verschweigen:** Remotion ist nicht MIT.
Kostenlos für Einzelpersonen, Firmen **bis 3 Mitarbeiter** und
Non-Profits; größere Firmen brauchen eine kostenpflichtige Lizenz. Für
Creator ist das unkritisch, aber der Nutzer muss es einmal gehört haben.

### PFLICHT: erst das Studio, dann der Render

**Das Remotion Studio ist für Stufe 2b das, was das Cockpit für Stufe 1
ist.** Es wird geöffnet, BEVOR irgendetwas gerendert wird — nicht danach,
nicht „bei Bedarf":

    <python> skills/motion-grafik/scripts/editor_oeffnen.py --remotion

Das Script findet das Projekt, startet das Studio falls nötig und öffnet
es im **echten** Browser des Nutzers. Danach gilt das Ein-Tab-Prinzip:
einmal öffnen, ab dann nur noch „schau in deinen offenen Tab".

Im Studio kostet jede Änderung NULL Rechenzeit — Text, Farbe, Timing,
Reihenfolge ändern und der Nutzer sieht es sofort. Erst wenn er sagt „so
ist es gut", wird EIN einziges Mal gerendert.

> **Teuer gelernt am 23.08.2026: 25 Minuten für 15 Sekunden Grafik.**
> Das Studio blieb zu. Stattdessen wurde die Grafik „blind" über
> einzelne CLI-Aufrufe geprüft — ein Testrender und zwei Kontrollbilder.
> Jeder `npx remotion`-Aufruf baut das Projekt komplett neu (rund 40 s),
> und die ersten schleppten zusätzlich 78 MB Videomaterial mit. Der
> Nutzer sah die Grafik zum ersten Mal im fertigen Video — da konnte er
> nichts mehr ändern. Sein Satz dazu: „Und jetzt kann ich sie nicht
> bearbeiten." Mit offenem Studio: 0 Sekunden, 0 Fragen.

Daraus drei harte Regeln:

1. **Nie `remotion still` für Kontrollbilder.** Dafür ist das Studio da.
   Beurteilt wird an der laufenden Vorschau, nie an Standbildern.
2. **Nie ein Testrender „nur zum Schauen".** Pro Grafik gibt es genau
   EINEN Render, nach der Freigabe.
3. **Nie Videomaterial nach `public/` legen.** Jeder Bundle kopiert den
   Ordner mit, bei jedem einzelnen Aufruf. Die Grafik wird MIT ALPHA
   gerendert und erst per ffmpeg über das Video gelegt. Braucht die Szene
   das Video wirklich als Hintergrund, gehört ein kurzer, kleiner
   Ausschnitt hinein — nie das ganze Material.

### Render — nach der Freigabe, ein Befehl

Remotion rendert über die Kommandozeile — **kein sichtbares Fenster, kein
Render-Knopf, kein eingefrorener Tab**:

    npx remotion render <Komposition> out/<name>.mp4

Damit entfällt der ganze Ärger aus Stufe 2a (siehe Warnkasten dort). Claude
startet den Render selbst und wartet auf das Ergebnis.

Für eine Ebene MIT Alphakanal (Grafik über dem Video) — der Regelfall:

    npx remotion render <Komposition> out/<name>.mkv --codec=prores --prores-profile=4444

**Die gültigen Befehle** — geprüft an `@remotion/cli 4.0.507`, nicht aus
dem Gedächtnis schreiben:

| Befehl | Zweck |
|---|---|
| `remotion studio` | Vorschau. **`remotion preview` gibt es nicht mehr.** |
| `remotion render <comp> <datei>` | rendern |
| `remotion compositions` | zeigt, welche Kompositionen registriert sind |
| `remotion still <comp> <datei.png>` | Standbild — im Videoablauf **nicht** benutzen |

Bei Unsicherheit `npx remotion help` fragen. Das kostet zwei Sekunden;
ein Fehlversuch mit einem umbenannten Befehl kostet drei Minuten Render,
die niemand zurückbekommt.

### Einrichten

Braucht Node.js (bringt der Setup-Assistent mit). Neues Projekt:

    npx create-video@latest --blank

Existiert beim Nutzer bereits ein Remotion-Projekt, dieses verwenden statt
ein zweites anzulegen. Kompositionen werden in `src/Root.tsx` registriert —
ohne Eintrag dort ist eine Szene unsichtbar (dasselbe Prinzip wie
`vite.config.ts` bei Motion Canvas).

**Alte Kompositionen sind Vorlagen, kein Altlast.** Sie bleiben als Code im
Projekt liegen und sind im Studio alle nebeneinander abrufbar. Vor jedem
neuen Grafikauftrag deshalb erst `npx remotion compositions` bzw. das
offene Studio ansehen: taugt eine bestehende als Ausgangspunkt, sind es
Texte und Zeiten ändern statt neu bauen. Eine bestehende Komposition
ändern kostet eine Coderunde plus einen Render.

### Vorschau

Siehe oben: `editor_oeffnen.py --remotion`. Es gilt dieselbe Regel wie bei
Motion Canvas — **nur im echten Browser des Nutzers öffnen**, nie im
eingebauten. Und die Vorschau wird nicht seltener gebraucht als dort,
sondern genauso: sie ist die einzige Stelle, an der der Nutzer die Grafik
sieht, solange Änderungen noch nichts kosten.

## Stufe 3: Freistellung („Text hinter mir")

`scripts/freistellen.py` erkennt die Person in jedem Bild und legt sie als
eigene Ebene mit Alphakanal ab. Damit lässt sich Grafik **zwischen** Video und
Person schieben.

**Voraussetzung:** Die Pakete `mediapipe`, `opencv-python` und `numpy`
werden **bereits vom Setup-Assistenten mitinstalliert** (Schritt
Video-Editor — ausdrücklicher Wunsch von Julian: die Werkzeuge sollen von
Anfang an auf dem Rechner sein). Fehlen sie doch (Setup übersprungen oder
pip schlug damals fehl), jetzt nachholen:

```bash
<python> -m pip install mediapipe opencv-python numpy onnxruntime
```

Unter **Windows** stattdessen `onnxruntime-directml` installieren: rechnet auf
der Grafikkarte (auch Intel-Onboard), gemessen ~2× schneller bei identischer
Alphamaske. Das Script erkennt das selbst und fällt sonst auf die CPU zurück —
auf macOS bleibt es beim normalen `onnxruntime`.

Beide Modelle liegen im Kit unter `models/`: `selfie_segmenter.tflite`
(244 KB, Apache 2.0) und `rvm_mobilenetv3_fp32.onnx` (14 MB, Robust Video
Matting). Kein Download, kein Konto, kein Netzzugriff zur Laufzeit.

```bash
<python> freistellen.py <geschnittenes_video> <zielbasis> [von_sek] [bis_sek]
```

### Zwei Verfahren — und wann welches

| | `rvm` (Standard) | `mediapipe` |
|---|---|---|
| Art | Matting-Netz, echter Alphakanal | Segmentierer, 256×256-Maske hochgezogen |
| Zeitbezug | rekurrent, kennt das vorherige Bild | keiner, jedes Bild einzeln |
| Kanten | weich, inkl. Haaransatz | hart, treppig, flackernd |
| Tempo | ~1 Bild/s (CPU) | ~6 Bilder/s |

**Liegt Grafik HINTER der Person, immer `rvm`.** Der Selfie-Segmenter flackert,
und das einzige Gegenmittel — die zeitliche Glättung — lässt die Maske bei
schnellen Bewegungen nachziehen. Das erzeugt eine halbdurchsichtige
Geisterkopie der vorherigen Position. Solange unter der Person derselbe
Hintergrund liegt, sieht man das nicht; mit Grafik darunter fliegt es sofort
auf. `mediapipe` reicht, wenn der Freisteller nur weichgezeichnet oder
eingefärbt wird.

### Nur den nötigen Abschnitt rechnen

Bei rund einer Sekunde pro Bild lohnt sich `von`/`bis` erheblich: liegt die
Grafik nur vier Sekunden hinter der Person, sind das 130 statt 600 Bilder —
zwei Minuten statt einer Viertelstunde. Die Ausgabe beginnt dann bei `von_sek`,
im `overlays`-Eintrag entsprechend `"start"` setzen. Dieselbe Logik wie bei
Google Omni: nur rechnen, was sich wirklich ändert.

Optionen: `--modell rvm|mediapipe`, `--glaettung` (nur mediapipe),
`--erosion` (Standard: rvm 0, mediapipe 2), `--weich`, `--farbe original|fgr`
und `--lowcut` (beide nur rvm).

**Wichtig bei rvm:** Standard ist `--farbe original` — der Freisteller trägt
die Originalpixel des Videos. Liegt er (wie im Kit üblich) über demselben
Video plus Grafik, mischen halbtransparente Kanten echten Inhalt mit der
Grafik — das sieht aus wie natürliche Bewegungsunschärfe. Die RVM-Farb-
schätzung (`fgr`) erzeugt dort Geisterkanten auf dunklen Flächen; sie ist
nur richtig, wenn die Person vor einen KOMPLETT anderen Hintergrund gesetzt
wird. `--lowcut 0.12` verwirft nachziehende Maskenreste bei schnellen
Bewegungen.

Erzeugt zwei Dateien, weil **kein Format beides kann**:

| Datei | liest ffmpeg | liest der Browser | wofür |
|---|---|---|---|
| `<basis>.mkv` (ffv1) | **ja** | nein | Render über prolook |
| `<basis>.webm` (VP9) | **nein** | **ja** | Vorschau in Motion Canvas |

**Wichtig:** Die Freistellung muss auf dem **bereits geschnittenen** Video
laufen. Sonst passen Maske und Bild nicht zusammen. Die Reihenfolge Cockpit →
Freistellung → Effekte ist nicht bequem, sondern zwingend.

**Feinjustierung** (oben in `freistellen.py`): `GLAETTUNG` gegen
Kantenflimmern, `EROSION` gegen Hintergrundsäume, `WEICHZEICHNEN` für die
Kantenhärte.

## Zusammenbauen: alles über die projekt.json

Beide Ebenen wandern als `overlays` in die `effekte` der `projekt.json` und
werden von `render_projekt.py` in **einem** Durchgang gerendert — kein
zweiter Export, kein Qualitätsverlust:

```json
"effekte": {
  "overlays": [
    {"file": "<abs>/motion/output/effekt", "alpha": true, "fullframe": true, "fps": 30},
    {"file": "<abs>/cutout.mkv", "alpha": true, "fullframe": true}
  ]
}
```

**Die Reihenfolge in der Liste ist die Stapelreihenfolge.** Effekt vor Person
= Grafik hinter der Person. Steht die Person nicht in der Liste, liegt die
Grafik vor ihr (der Normalfall für Ringe und Headlines).

Details zu `alpha` und `fullframe`: siehe `pro-look-editing`.

## Grenzen — ehrlich bleiben

- **Motion Canvas kann kein echtes 3D.** Keine Beleuchtung, keine Kamera,
  keine Reflexionen. Genau dafür gibt es Stufe 2b (Remotion mit Three.js) —
  Blender braucht es dafür nicht mehr.
- **Die Freistellung wird an Haaren nicht perfekt.** Bei ruhigem Hintergrund
  und gutem Licht sitzt sie gut; bei schnellen Handbewegungen reißt sie.
- **Motion Canvas rendert im Browser**, per Klick — kein CLI-Befehl.
- **VP9-WebM trägt seinen Alphakanal nur im Browser.** Wer es ffmpeg
  vorwirft, bekommt eine deckende Ebene und wundert sich. Dafür ist die
  `.mkv` da.

## Token-Regeln

- Zuerst prüfen, ob das Cockpit den Wunsch schon erfüllt. Wenn ja: dort.
- Der Nutzer klickt *Render* selbst, in SEINEM Browser. Claude soll den
  Editor nicht fernsteuern — das kostet pro Runde ein Vielfaches der
  eigentlichen Codeänderung, und im eingebauten Browser steht der Render
  ohnehin still (siehe Warnkasten oben).
- Beurteilt wird in der Vorschau auf localhost:9000, nicht an Einzelbildern.
  Nach einem fertigen Render höchstens ein Kontrollbild.
- Effekte, die schon gebaut wurden, wiederverwenden statt neu schreiben.
