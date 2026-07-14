---
name: kling-prompt-builder
description: >
  Erstellt perfekte, fertige Prompts für Kling AI 3.0 — speziell für Anfänger
  der SCB Community, die virale Reels generieren wollen. Verwende diesen Skill
  immer, wenn jemand einen Kling-Prompt haben möchte, ein Kling-Video erstellen
  will, nach einem Video-Prompt fragt, etwas mit Kling 3.0 generieren will, oder
  wenn jemand ein virales Reel, UGC-Ad oder KI-Video produzieren möchte — auch
  wenn die Person "Kling" nicht explizit nennt. Der Skill führt den User
  schrittweise durch alle nötigen Fragen und liefert am Ende einen
  copy-paste-fertigen Prompt auf Englisch (Dialog auf Deutsch), der Credits
  spart und maximale Ausgabequalität liefert.
---

# Kling 3.0 Prompt Builder — SCB Community

## Zweck
Dieser Skill führt Anfänger Schritt für Schritt durch alle relevanten
Entscheidungen und generiert danach einen technisch sauberen, strukturierten
Kling 3.0 Prompt. Ziel: maximale Qualität mit minimalen Credits auf Higgsfield
oder klingai.com.

---

## VORSCHRITT: Character Reference Sheet (optional, aber empfohlen)

Dieser Schritt kommt **vor** dem eigentlichen Kling-Prompt und ist der
wichtigste Hebel gegen Character Drift — das häufigste Problem bei Anfängern.

### Was ist Character Drift?
Ohne Referenzbilder verändert Kling das Aussehen eines Charakters im Laufe
des Videos leicht — das Gesicht deformiert, der Stil ändert sich, besonders
wenn der Charakter sich dreht oder die Kamera schneidet. Mit einem Character
Reference Sheet wird das weitgehend verhindert.

### Wann diesen Schritt empfehlen?
Immer wenn der User einen **wiederkehrenden Charakter** in seinem Video haben
will — also bei UGC-Ads, Storytelling-Reels, Avatar-Content oder wenn der
Charakter sich im Video bewegt und in verschiedene Richtungen dreht.

### Hinweis zu den Tools
Für die Erstellung von Character Reference Sheets funktionieren zwei Tools:
- **GPT Image 2** (OpenAI) — direkt im ChatGPT-Interface nutzbar
- **Nano Banana 2** (Google Imagen) — z.B. über Higgsfield AI nutzbar

Beide liefern vergleichbare Ergebnisse. Der User soll das Tool nutzen,
das er bereits hat oder bevorzugt.

---

### So erstellt man ein Character Reference Sheet

**Ziel:** 8 Shots des Charakters in einem einzigen Bild — 4 Spalten,
jede Spalte zeigt eine andere Blickrichtung.

**Aufbau des Sheets:**
- Spalte 1: Frontansicht (Full Body + Close-up Gesicht)
- Spalte 2: ¾-Ansicht links (Full Body + Close-up Gesicht)
- Spalte 3: Seitenprofil links (Full Body + Close-up Gesicht)
- Spalte 4: Rückansicht (Full Body + Close-up Gesicht)

**Basis-Prompt für das Character Reference Sheet (in GPT Image 2 oder
Nano Banana 2 einfügen):**

```
Create a professional character reference sheet with 4 vertical columns.
Each column shows the same character from a different angle:
Column 1: front view, Column 2: three-quarter view left,
Column 3: side profile left, Column 4: back view.
Each column contains: full body shot on top, close-up face shot below.

Character description: [HIER CHARAKTER BESCHREIBEN — z.B. "young woman,
mid-20s, blonde hair, casual streetwear, confident expression"]

photorealistic, DSLR camera, muted color tones, shot on 35mm film,
high detail, consistent lighting across all columns.
```

**Für eigene bestehende Charaktere** (User hat bereits ein AI-Bild):
Bild als Referenz hochladen und diesen Zusatz verwenden:
```
Create a professional character reference sheet based on the uploaded image.
[Gleiche Spalten-Struktur wie oben]
photorealistic, DSLR camera, muted color tones, shot on 35mm film.
```

### Häufiger Fehler und Fix
Wenn zwei Side-Profile-Shots in dieselbe Richtung schauen (passiert oft),
das fehlerhafte Sheet als Referenz hochladen und schreiben:
```
Change the character reference sheet so that the full body shot in column 3
faces the opposite direction.
```

---

### Character Reference Sheet in Kling einsetzen (Omni Reference)

**Workflow:**
1. Character Reference Sheet(s) in Kling Omni Reference hochladen
2. Zusätzlich: ein generiertes Szenenbild als Start-Frame hochladen
3. Im Prompt die Bilder über ihre Label ansprechen: Image 1, Image 2, Image 3

**Prompt-Syntax für mehrere Referenzbilder:**
```
The woman from image 3 [= Character Reference Sheet Frau] and
the man from image 2 [= Character Reference Sheet Mann]
walk forward side by side through [location] in image 1 [= Start Frame].
[Action description]
The scene ends with them [SITUATION] inside image 1.
```

**Wichtig — End-Scene-Fix:**
Immer am Ende des Prompts ergänzen:
`"The scene ends with [characters] in [situation] inside image 1."`
Ohne diesen Satz schneidet Kling am Video-Ende zufällig zum
Character Reference Sheet — das zerstört das fertige Video.

**Konsistenz-Warnung:**
- 1 Charakter: sehr gute Konsistenz
- 2 Charaktere: gute Konsistenz, empfohlen als Maximum
- 3+ Charaktere: Konsistenz nimmt deutlich ab, nicht empfohlen für Anfänger

---

## Wichtige Regeln für die Prompt-Generierung

- **Prompts immer auf Englisch** — Kling 3.0 versteht Englisch deutlich besser
- **Ausnahme: Dialog/Sprache im Video immer auf Deutsch** (falls gewünscht)
- **Aspect Ratio Default: 9:16** — optimal für Instagram Reels
- **Negative Prompts immer mitgenerieren** — spart Credits durch weniger
  Fehlgenerierungen
- **Timecodes bei Multi-Shot immer explizit setzen** (z.B. "0–4s: ..., 4–8s: ...")
- **Kein Motion Intensity Slider in der API** — Bewegung nur über Prompt-Sprache
  steuern ("slowly", "rapidly", "gently", "explosive")

### Zeichenlimit — HARTES LIMIT, niemals überschreiten

- **Maximale Prompt-Länge gesamt: 2.500 Zeichen** (inkl. Negative Prompt)
- **Pro Multi-Shot-Segment: maximal 512 Zeichen**
- Vor jeder Ausgabe prüfen ob das Limit eingehalten wird — wenn zu lang: kürzen
- Priorität beim Kürzen: Camera > Action > Lighting > Audio
- Keine Wiederholungen, keine Füllsätze, Adjektive auf das Wesentliche
  reduzieren: statt "slowly, gently, carefully moving" → "slow steady push-in"

---

## Phase 1: Informationen vom User sammeln

Stelle diese Fragen **einzeln nacheinander**, nicht alle auf einmal.
Warte jeweils auf die Antwort bevor du die nächste Frage stellst.

### Frage 1 — Die Grundidee
> „Was soll in deinem Video passieren? Beschreib es kurz und einfach —
> keine technischen Details nötig, einfach was du dir vorstellst."

### Frage 2 — Charakter-Konsistenz
> „Soll ein bestimmter Charakter in deinem Video vorkommen, der konsistent
> aussehen soll — also immer gleich, egal aus welchem Winkel?
> Falls ja: Hast du bereits ein Character Reference Sheet oder ein
> Referenzbild deines Charakters?"

- **Ja, Reference Sheet vorhanden** → Omni Reference Workflow (siehe Vorschritt)
- **Ja, aber kein Sheet** → User auf den Vorschritt hinweisen, Sheet erstellen
  lassen mit GPT Image 2 oder Nano Banana 2
- **Nein / nicht nötig** → direkt zu Frage 3

### Frage 3 — Eingabe-Typ
> „Hast du bereits ein Bild, das als erste Szene dienen soll
> (Image-to-Video), oder soll alles komplett aus Text generiert werden
> (Text-to-Video)?"

- **Image-to-Video**: User hat ein Start-Bild (aus GPT Image 2,
  Nano Banana 2, Midjourney oder Flux). Bild bestimmt Look und Stil.
  → Weiter zu Frage 3b.
- **Text-to-Video**: Kling generiert alles selbst aus dem Prompt.
  → Weiter zu Frage 4.

#### Frage 3b — End Frame (nur bei Image-to-Video)
> „Möchtest du auch ein End-Frame festlegen — also ein Bild vorgeben,
> wie die letzte Szene aussehen soll? (z.B. für Loops oder Transformationen)"

Hinweis für den User: End-Frame ist sinnvoll für Loops (gleiches Bild wie
Start = nahtloser Loop), Outfit-Wechsel, oder Tag-zu-Nacht-Übergänge.

### Frage 4 — Videolänge und Schnitte
> „Wie lang soll dein Video sein und willst du mehrere Szenen/Cuts darin
> haben — oder soll es eine einzige durchgehende Aufnahme sein?"

Optionen erklären:
- **1 Szene, 3–8 Sekunden**: Einfachste Option, beste Qualität, wenigste
  Credits. Ideal für Produkt-Shots, Charakter-Momente, kurze Hooks.
- **Mehrere Szenen (Multi-Shot), bis 15 Sekunden**: Mehrere Cuts in einem
  Video (bis zu 6 Shots). Ideal für UGC-Ads, Storytelling, Reels.
  Kling hält Charakter-Konsistenz über die Cuts — besonders stark mit
  Reference Sheet.

### Frage 5 — Audio und Dialog
> „Soll jemand im Video sprechen oder soll es Musik/Soundeffekte geben?
> Wichtiger Hinweis: Audio kostet auf Higgsfield doppelte Credits —
> lohnt sich aber für Talking-Head-Content und UGC-Ads sehr."

Optionen:
- **Kein Audio** — rein visuell, günstigste Option
- **Soundeffekte (SFX)** — z.B. Wind, Explosionen, Kaffee-Geräusche
- **Hintergrundmusik** — Kling generiert passende Musik automatisch
- **Dialog/Sprache** — Charakter spricht (Kling generiert Lip-Sync)
  → Wenn Ja: „Was soll die Person sagen?" (auf Deutsch, Kling übernimmt
  die Vertonung)
- **Kombination** — z.B. Dialog + Musik + SFX

### Frage 6 — Elemente und Details
> „Gibt es bestimmte Dinge, die unbedingt im Video vorkommen müssen?
> Z.B. ein bestimmtes Produkt, ein Logo, eine bestimmte Stimmung,
> ein besonderer Kamera-Effekt — oder hast du noch Wünsche?"

### Frage 7 — Output-Format
> „In welchem Format willst du den fertigen Prompt?
> Option A: Nur der fertige Prompt als Copy-Paste-Block — direkt
>           in Higgsfield/Kling einfügen, fertig.
> Option B: Prompt + kurze Erklärung, was welcher Teil bewirkt —
>           gut zum Lernen und für spätere eigene Anpassungen."

---

## Phase 2: Prompt generieren

Sobald alle Fragen beantwortet sind, generiere den Prompt nach dieser Struktur.

### Die SCALE-Struktur (für jeden Shot)

```
[CAMERA]     Kamerabewegung + Framing
[CHARACTER]  Subjekt mit konkreten visuellen Merkmalen
[ACTION]     Was passiert — bei Multi-Shot mit Timecodes
[LIGHTING]   Licht, Ort, Atmosphäre, Farbpalette
[EXTRA]      Audio (SFX, Musik, Dialog) + Negative Prompt
```

### Kamera-Vokabular (immer englisch, immer konkret)

**Bewegung:**
slow dolly in / dolly out / tracking shot / orbit / crane up / crane down /
pan left / pan right / tilt up / tilt down / FPV drone shot / whip pan /
snap zoom / handheld with subtle drift / static tripod / reverse push /
fast lateral pass left to right / crash push into face / speed ramp

**Framing:**
wide establishing shot / medium shot / close-up / macro close-up /
extreme close-up / over-the-shoulder / two-shot / profile shot /
low-angle / high-angle / Dutch angle / shallow depth of field

**Spezial-Effekte (neu in Kling 3.0):**
motion blur / rack focus from [A] to [B] / speed ramp from 40% to 100% /
robotic arm camera control / bokeh effect / lens flare / film grain

**Für mehrere Cuts:**
„jump cut to [next scene]" oder separate Shot-Paragraphen mit Timecodes

### Dialog-Format (Sprache im Video = immer Deutsch)

```
[Character: Rolle, Stimm-Tonalität]: "Deutscher Text hier."
```

Beispiel:
```
[Young woman, warm and excited voice]: "Das ist mein neues Lieblingsparfüm —
ich trage es jeden Tag."
```

### SFX-Format

```
SFX: [genaue Beschreibung des Sounds]
```

Beispiel:
```
SFX: a massive power-up sound effect like a turbine spinning at max speed
that cuts the silence of the final frame
```

### Musik-Format

```
Background music: [Stil + Stimmung + Instrumente]
```

Beispiel:
```
Background music: soft upbeat acoustic guitar, warm and cozy, lo-fi feel
```

---

## Template A — Single Shot (Text-to-Video, 3–8s)

```
[Camera movement + duration] through/around [environment].
[Character: age, clothing, 2–3 visual details] [primary action].
[Time-coded beat if needed: 0–3s: ... 3–5s: ...]
[Lighting source + quality]. [Color palette + atmosphere].
Shot on [film style], [depth of field], [texture/grain].
[Audio line if applicable]
Negative prompt: blur, distortion, low quality, warping fingers,
deformed hands, plastic skin, identity drift, flickering, morphing.
```

## Template B — Multi-Shot (bis 15s, mehrere Cuts)

```
Master scene: [overall mood, character description, location, color palette]

Shot 1 ([Xs]): [camera] — [character entry/establishing] — [action beat]
Shot 2 ([Xs]): [camera change] — [emotional/dialogue beat]
Shot 3 ([Xs]): [close-up/hero shot] — [product/climax beat]
Shot 4 ([Xs]): [wide/resolution shot] — [closing beat]

Continuity: same character face, same outfit, same lighting, same location.
[Audio if applicable]
Negative prompt: identity drift, character merge, frozen lips,
jittery eyes, morphing outfit, background shifting.
```

## Template C — Image-to-Video (Start Frame, ohne Reference Sheet)

```
[Camera movement] around/through [subject from start frame].
[Time-coded micro-motion]: 0–[X]s: [subtle motion]. [X]–[Y]s: [motion change].
[Lighting description]. Preserve all details from source image. No morphing.
[Audio if applicable]
Negative prompt: logo distortion, face warping, background shift,
low quality, blur, morphing.
```

## Template D — Dialog/UGC-Ad (Talking Head, 10–15s, Image-to-Video)

```
Start frame: [image description/upload].

Shot 1 (0–[X]s): [establishing shot — medium, handheld subtle drift].
[Character: role, voice tone]: "[Deutscher Dialog-Text.]"

Shot 2 ([X]–[Y]s): [close-up — slow push in].
[Product/detail action: e.g., holds up product, looks at camera]
[Character, warmer tone]: "[Zweiter Satz auf Deutsch.]"

Shot 3 ([Y]–15s): [wide or hero shot — slow dolly out].
Background music: [style]. SFX: [if needed].
Negative prompt: frozen lips, jittery eyes, identity drift,
character merge, morphing hands, background shift.
```

## Template E — Omni Reference (mit Character Reference Sheet)

```
The [character description] from image [N] [= Character Reference Sheet]
[action] in image 1 [= Start Frame / Szenenreferenz].

[Detailed action + camera description]
[Dialog if applicable]
[Camera cuts with timecodes if multi-shot]

The scene ends with [character(s)] [final situation] inside image 1.

Continuity: preserve character face, outfit, and proportions from reference.
Negative prompt: identity drift, character merge, reference sheet visible,
frozen lips, jittery eyes, morphing, low quality.
```

---

## Konkrete Beispiele (als Orientierung)

### Einfacher Produkt-Shot (Single Shot, Image-to-Video)
```
Slow macro dolly push-in around a glass perfume bottle on a marble surface.
0–2s: bottle rotates slightly, golden liquid catches warm light.
2–4s: fine mist sprays upward in slow motion, droplets catch the light.
4–5s: camera holds on bottle. Studio key light at 45°, soft warm backlight.
Shallow depth of field, blurred cream-colored background.
No morphing. Preserve all label text. Shot on 35mm film, subtle grain.
Negative prompt: logo distortion, text warping, surface scratches,
blur, low quality.
```

### Charakter-Performance (Single Shot, Image-to-Video, mit Dialog)
```
Medium shot, slow handheld push-in. Young woman, mid-20s, light summer dress,
natural makeup, warm bedroom background.
0–4s: looks into camera, picks up perfume bottle, sprays onto wrist.
4–8s: holds bottle toward camera, smiles naturally.
[Young woman, warm and enthusiastic voice]: "Ich musste euch das zeigen —
dieses Parfüm ist einfach unglaublich."
Background music: soft upbeat acoustic guitar, warm lo-fi feel.
Negative prompt: frozen lips, jittery eyes, plastic skin, morphing hands,
identity drift, low quality.
```

### Cinematic Mood Shot (Multi-Shot, Text-to-Video)
```
Master: moody cinematic atmosphere, blue-hour lighting, urban street at night,
neon reflections on wet pavement, deep teal and amber palette.

Shot 1 (4s): wide establishing — slow drone push forward down empty street —
neon signs blur into bokeh in background.
Shot 2 (4s): medium tracking shot — follows figure in dark jacket
walking toward camera — coat catches wind.
Shot 3 (4s): extreme close-up — slow rack focus from eyes to raindrops
on jacket collar — shallow depth of field.
Shot 4 (3s): crane up — wide bird's eye — figure continues walking,
city lights below.

Shot on 35mm anamorphic, film grain, no motion blur artifacts.
Background music: slow cinematic score, low bass drones.
Negative prompt: identity drift, background shifting, warping, morphing,
flickering, plastic skin, low quality.
```

### Omni Reference Beispiel (zwei Charaktere, mit Reference Sheets)
```
The woman from image 3 and the man from image 2 walk forward side by side
through a dark forest in image 1. They move steadily along the path.
The woman scans the trees to her left while the man keeps his gaze forward,
leaves shift slightly in the wind.
Cut to a side profile shot of the two characters continuing through the forest.
The scene ends with both characters walking deeper into the forest inside image 1.

Continuity: preserve both characters' faces, outfits, and proportions
from their reference sheets.
Negative prompt: identity drift, character merge, reference sheet visible,
morphing faces, background shifting, low quality.
```

---

## Credit-Spar-Regeln (für Higgsfield/Klingai)

1. **Draft/Standard Mode zuerst** — erst wenn der Prompt funktioniert, Pro Mode nutzen
2. **Audio nur wenn nötig** — kostet doppelte Credits
3. **Negative Prompt immer dabei** — verhindert Fehlgenerierungen
4. **Weniger ist mehr bei Multi-Shot** — 3–4 Shots sind stabiler als 6
5. **Klare Timecodes setzen** — reduziert Halluzinationen und Artefakte
6. **Hände beschäftigen** — Charakter hält immer ein Objekt, nie freie Hände
   in der Luft (reduziert Hand-Glitches erheblich)
7. **Image-to-Video stabiler als Text-to-Video** — für Charakter-Konsistenz
   immer mit Start-Frame arbeiten wenn möglich
8. **Character Reference Sheet einmalig erstellen** — danach in allen folgenden
   Videos wiederverwendbar, spart langfristig viele Credits durch weniger
   Fehlgenerierungen durch Character Drift

---

## Bekannte Schwächen von Kling 3.0 (User proaktiv warnen)

- **Körperkontakt** (Umarmungen, Handschütteln) → oft "Melting"-Artefakte
  → Workaround: Charaktere nicht direkt berühren lassen
- **Lip-Sync über 5–8 Sekunden** → wird instabil bei langen Dialogzeilen
  → Workaround: Dialog in kürzere Sätze aufteilen, max. 1–2 Sätze pro Shot
- **Freie Hände** → führt zu Glitches → immer Objekt in der Hand
- **Animierter Text** → instabil → statische Logos/Texte funktionieren gut
- **Kausallogik über Shots** → Kling kann nicht garantieren dass
  Shot 2 logisch auf Shot 1 aufbaut → für Erzähllogik lieber separat
  generieren und in CapCut/Premiere schneiden
- **Omni Reference ohne End-Scene-Fix** → Kling schneidet am Video-Ende
  zufällig zum Reference Sheet → immer "The scene ends with..." ergänzen

---

## Ausgabe-Verhalten

**Bei Option A (nur Prompt):**
Gib einen sauberen, einzigen Copy-Paste-Block aus. Keine Erklärungen darunter.
Füge am Ende hinzu: „Aspect Ratio: 9:16 | Duration: [X]s | Mode: Standard"

**Bei Option B (Prompt + Erklärung):**
Gib zuerst den vollständigen Prompt-Block aus, dann darunter eine kurze
Erklärung jeder Zeile — max. 1 Satz pro Element. Keine langen Ausführungen.

**Nach der Ausgabe immer fragen:**
„Soll ich irgendetwas anpassen — z.B. andere Kamerabewegung, andere Stimmung,
kürzere Dialoge, oder ein Element hinzufügen?"
