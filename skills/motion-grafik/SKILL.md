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

# Motion-Grafik (Motion Canvas + Freistellung)

Dieser Skill ist die **Stufe 2 und 3** der Videoproduktion. Stufe 1 ist und
bleibt das Cockpit (`video-projekt`).

## GRUNDREGEL: nie höher einsteigen als nötig

| Stufe | Werkzeug | Wofür | Kosten für den Nutzer |
|---|---|---|---|
| 1 | **Cockpit** (`video-projekt`) | Schnitt, Untertitel, Musik, **einfache Texte und Hooks** | 0 Token, er ändert selbst |
| 2 | **Motion Canvas** | animierte Grafik, die das Cockpit nicht kann | jede Änderung = eine Coderunde |
| 3 | **Freistellung** (`freistellen.py`) | alles, was **hinter** der Person liegt | zusätzlich Rechenzeit |

**Ein Text, den das Cockpit als `texts`-Overlay kann, gehört ins Cockpit** —
auch wenn er in Motion Canvas hübscher würde. Grund ist nicht Bequemlichkeit,
sondern Geld: Im Cockpit justiert der Nutzer selbst und ohne Token; jede
Motion-Canvas-Änderung kostet eine Runde über Claude.

Stufe 3 nur einschalten, wenn wirklich etwas hinter der Person liegen soll.
Die Freistellung kostet rund **1,5 Minuten Rechenzeit je 12 Sekunden**
Material.

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

## Stufe 2: Motion Canvas

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

**Erst nach seinem Okay** `PREVIEW = false` setzen und im Editor auf *Render*
klicken. Ergebnis: eine PNG-Sequenz mit Alphakanal unter `output/<projekt>/`.

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
<python> -m pip install mediapipe opencv-python numpy
```

Das Modell (`models/selfie_segmenter.tflite`, 244 KB, Apache 2.0) liegt im
Kit. Kein Download, kein Konto, kein Netzzugriff zur Laufzeit.

```bash
<python> freistellen.py <geschnittenes_video> <zielbasis>
```

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

- **Kein echtes 3D.** Keine Beleuchtung, keine Kamera, keine Reflexionen.
  Wer einen frei im Raum rotierenden Körper will, braucht Blender.
- **Die Freistellung wird an Haaren nicht perfekt.** Bei ruhigem Hintergrund
  und gutem Licht sitzt sie gut; bei schnellen Handbewegungen reißt sie.
- **Motion Canvas rendert im Browser**, per Klick — kein CLI-Befehl.
- **VP9-WebM trägt seinen Alphakanal nur im Browser.** Wer es ffmpeg
  vorwirft, bekommt eine deckende Ebene und wundert sich. Dafür ist die
  `.mkv` da.

## Token-Regeln

- Zuerst prüfen, ob das Cockpit den Wunsch schon erfüllt. Wenn ja: dort.
- Der Nutzer klickt *Render* selbst. Claude soll den Editor nicht fernsteuern
  — das kostet pro Runde ein Vielfaches der eigentlichen Codeänderung.
- Beurteilt wird in der Vorschau auf localhost:9000, nicht an Einzelbildern.
  Nach einem fertigen Render höchstens ein Kontrollbild.
- Effekte, die schon gebaut wurden, wiederverwenden statt neu schreiben.
