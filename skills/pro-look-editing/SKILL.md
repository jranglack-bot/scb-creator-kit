---
name: pro-look-editing
description: >
  Pro-Look-Paket für Reels: animierte Wort-für-Wort-Untertitel (Pop-Effekt +
  Wort-Highlight im CapCut-Stil), Punch-Ins auf Schnitte, Picture-in-Picture
  (Nutzer klein über animiertem Hintergrund), Color-Grade, Filmkorn und
  SFX-Akzente — alles über fertige, getestete Template-Scripts mit minimalem
  Token-Verbrauch. Verwende diesen Skill bei: "mach das Video professionell",
  "Pro-Look", "animierte Untertitel", "CapCut-Style Captions", "Punch-In",
  "mach mich klein mit Animation im Hintergrund", "Picture-in-Picture",
  "mach das Reel hochwertiger", "Editing wie ein Profi".
---

# Pro-Look-Editing (Template-basiert)

Verwandle ein geschnittenes Video in ein professionell editiertes Reel.
**Architektur-Prinzip: Die Scripts machen die Arbeit, Claude trifft nur die
kreativen Entscheidungen.** Niemals Effekt-Code improvisieren — die
Templates in `scripts/` sind getestet; nur Parameter setzen und ausführen.

## Die zwei Template-Scripts (liegen in diesem Skill-Ordner)

1. **`scripts/animated_captions.py`** — erzeugt animierte
   Wort-für-Wort-Untertitel als .ass: 2–3-Wort-Gruppen, Pop-Animation beim
   Erscheinen, farbiges Highlight auf dem gesprochenen Wort, nur während
   Sprache. Safe-Zones für Reel/Story eingebaut.
   ```
   python animated_captions.py transkript.json untertitel.ass --mode reel
       [--font "Segoe UI"] [--highlight FFD400] [--group 3]
   ```
2. **`scripts/prolook.py`** — rendert alles in EINEM ffmpeg-Lauf:
   Picture-in-Picture, Punch-Ins, Grade, Grain, Captions, SFX. Gesteuert
   über eine kleine config.json (Schema steht im Script-Kopf).
   ```
   python prolook.py config.json
   ```

## Workflow

### 1. Voraussetzungen klären
- Video ist geschnitten (sonst zuerst Skill `video-schneiden`) und das
  Transkript-JSON der GESCHNITTENEN Fassung liegt vor (nach dem Schnitt neu
  transkribieren!).
- Stil aus dem **Untertitel-Profil** in Obsidian `00 Kontext/Branding.md`
  ziehen (`untertitel-profil`-Codeblock — Format und Einrichtung inkl.
  Screenshot-Vorlage siehe Skill `untertitel-und-text`). Die Profilwerte
  (font/size/highlight/outline) direkt als Flags an
  `animated_captions.py` durchreichen. Existiert noch kein Profil: dort
  einmalig einrichten, dann weiter. Nie pro Video neu fragen.

### 2. Effekte wählen (kurz fragen, nicht alles ungefragt aktivieren)
- **Captions animiert** (fast immer ja)
- **Punch-Ins**: Schnittzeiten aus dem Schneide-Schritt als `cuts` übergeben
- **Picture-in-Picture**: nur wenn ein Hintergrund-Video da ist — z. B. mit
  Higgsfield/Kling generierter Loop (Skill `higgsfield-generate`; passend
  zum Thema, subtil, ohne eigenen Bildfokus) oder eigenes B-Roll
- **Grade + Grain**: dezenter Standard-Look (contrast 1.06, saturation 1.12,
  grain 6) — nicht übertreiben
- **Wisch-Übergänge**: `transition` in der Config (Typ z. B. `wipeleft`,
  `slideleft`, `fade`; nutzt dieselben `cuts` wie Punch-In). WICHTIG: Bei
  aktiven Übergängen die Captions mit `--transition-cuts "<cuts>"
  --transition-duration <d>` erzeugen, sonst laufen sie asynchron
  (Übergänge verkürzen die Timeline)!
- **Sound-Effekte**: siehe eigener Abschnitt unten — NIEMALS ungefragt

## Sound-Effekte — EISERNE REGEL: nur auf Nachfrage

**Baue NIEMALS automatisch Soundeffekte ein.** Nicht auf Cuts, nicht auf
Captions, nicht auf Übergänge — auch dann nicht, wenn es „gut passen
würde". Stattdessen: Wenn ein Video fertig geschnitten/gebaut ist, einmal
kurz ANBIETEN:

> „Möchtest du Soundeffekte an den passenden Stellen — z. B. ein Wisch-Sound
> auf den Übergängen oder Tipp-Geräusche auf den Untertiteln?"

Erst nach einem klaren Ja einbauen — und nur das, was gewählt wurde.
Gleiches gilt für Übergänge und jeden anderen Effekt: anbieten, nicht
aufdrängen.

### Mitgelieferte Basis-Sounds (lizenzfrei, im Kit enthalten)

In `scripts/sfx/` liegen sechs selbst erzeugte, frei nutzbare Sounds:
`whoosh` (Wisch), `swish` (kurzer heller Wisch), `click` (Tastatur/Typing),
`pop`, `ding`, `riser` (Spannungsaufbau). Pegel aufeinander abgestimmt.

### Eigene SFX-Bibliothek (bessere Sounds, einmal einrichten)

Für hochwertigere Sounds legt sich der User eine eigene Bibliothek an:
1. Ordner anlegen (z. B. `Dokumente\SFX`), Lieblings-Sounds als MP3 hinein.
2. Kostenlose Quellen (zur Nutzung frei, nicht weiterverteilen):
   **pixabay.com/sound-effects** und **mixkit.co/free-sound-effects** —
   nach „whoosh", „swoosh", „click", „pop" suchen, Favoriten laden.
   Oder Sounds **direkt mit Claude aus SFX-Reels extrahieren** — es gibt
   Reels, die nur Soundeffekte teilen (Skill `sfx-extraktion`:
   automatische Segment-Erkennung, Schnitt als MP3, Ablage hier).
3. Ordnerpfad in Obsidian `00 Kontext/Branding.md` notieren
   (Zeile: `SFX-Bibliothek: <pfad>`). Ab dann werden bei Sound-Wünschen
   zuerst die eigenen Sounds genutzt, die Basis-Sounds als Fallback.

## Bild-Paket: B-Roll, weicher Zoom, Hook-Cover, Fortschrittsbalken

**NIE Standard — nur anbieten!** Keiner dieser Bausteine wird automatisch
eingesetzt. Nach dem Bau eines Reels EINMAL kompakt hinweisen, was möglich
wäre („Möglich wären außerdem: B-Roll-Einblendungen, weicher Zoom,
Hook-Cover fürs Grid, Fortschrittsbalken — willst du davon etwas?") und nur
das Gewählte umsetzen.

- **B-Roll-Inserts** (`broll`-Liste in der Config: file/start/duration):
  Bildwechsel über dem Talking-Head, Ton läuft weiter — der wichtigste
  Retention-Hebel. Momente aus dem eh gelesenen Transkript wählen (2–4
  Stellen, an denen ein passendes Bild das Gesagte verstärkt). Clips:
  eigenes Material des Users oder per `higgsfield-generate` erzeugen
  (Vorschlags- und Kosten-Regeln von dort beachten!). Captions bleiben
  automatisch über dem B-Roll sichtbar.
- **Weicher Zoom** (`punchin.style: "smooth"`): kontinuierliches
  Reinziehen pro Segment statt Zoom-Sprung — die elegantere Bewegung.
- **Hook-Cover** (`scripts/make_cover.py`): Standbild + großer Hook-Text
  im Untertitel-Profil-Stil als JPG — fürs Cover im Grid. `|` = Zeilenumbruch,
  `*WORT` = Highlight-Farbe. Text-Vorschlag aus dem Hook des Reels ableiten.
- **Fortschrittsbalken** (`progressbar` in der Config): dünner Balken am
  unteren Rand, füllt sich über die Laufzeit — simpler Retention-Trick.

Alle vier sind getestet (inkl. Pixel-Verifikation des Balkens); nur
Parameter setzen, nichts improvisieren.

## Audio-Suite: Musik, Stimm-Mastering, Loudness

### Stimm-Mastering + Loudness (Standard-Empfehlung, einmal kurz anbieten)

Bei jedem Pro-Look-Render anbieten (einmal, nicht aufdrängen): „Soll ich
deine Stimme professionell mastern und die Lautstärke auf den
Instagram-Standard bringen?" Bei Ja in der Config:
`"voice_master": {"enabled": true}` (Trittschall-Filter, Kompressor,
Präsenz-Anhebung) und `"loudnorm": {"enabled": true}` (finaler Pass auf
−14 LUFS — sonst klingt das Reel leiser als der Feed). Getestet: Ergebnis
landet bei ~−14 LUFS.

### Musikbett mit Auto-Ducking — NUR auf Nachfrage (eiserne Regel!)

Niemals ungefragt Musik unterlegen. Nach dem Bau eines Reels EINMAL
anbieten: „Möchtest du Hintergrundmusik? Sie wird automatisch leiser,
sobald du sprichst." Bei Ja:

1. **Stimmung bestimmen — ohne Extra-Kosten:** Das Transkript ist schon
   gelesen → daraus die Stimmung ableiten und vorschlagen („Das Reel ist
   motivierend — ich würde etwas Energetisches nehmen. Passt das?").
2. **Track wählen:** Zuerst in der **Musik-Bibliothek** des Users schauen
   (Pfad in `00 Kontext/Branding.md`, Zeile `Musik-Bibliothek: <pfad>`;
   Stimmungs-Unterordner: `energetisch/`, `ruhig/`, `emotional/`,
   `episch/`, `froehlich/`). Passenden Track nehmen — die Ordner-Konvention
   macht die Wahl zur reinen Dateiabfrage, null Analyse-Token.
3. **Bibliothek leer?** User zu **pixabay.com/music** schicken — kostenlos,
   keine Namensnennung, mit Stimmungs-Suche. Suchbegriffe (DE→EN):
   traurig→`sad`, energetisch→`upbeat`/`energetic`, ruhig→`calm`/`chill`,
   episch→`epic`/`cinematic`, fröhlich→`happy`/`uplifting`. Alternativen:
   mixkit.co/free-stock-music, freebeats.io. Runtergeladene Tracks in den
   passenden Stimmungs-Ordner → für immer verfügbar.

**Chart-/Trend-Musik — der richtige Weg (User aktiv beraten!):**
Trend-Sounds und Chartmusik sind für Instagram-Reels ausdrücklich eine gute
Wahl — aber sie werden **nicht eingebrannt**, sondern **beim Posten in der
Instagram-App hinzugefügt**. Zwei Gründe dem User erklären: (1) Metas
Musik-Lizenz gilt nur für in der App hinzugefügte Musik — eingebrannte
Chartmusik wird vom Rights Manager erkannt und das Reel stummgeschaltet
oder geblockt; (2) In-App-Trend-Audio pusht zusätzlich die Reichweite.
Workflow dann: Reel OHNE Musikbett rendern (Stimme gemastert, SFX, Loudness
— alles wie gewohnt), Musik kommt beim Posten in der App drauf.

**Kommerz-Check (automatisch machen):** Erkennst du am Inhalt, dass das
Reel etwas VERKAUFT oder BEWIRBT (Sales-Aufbau, CTA mit Keyword,
Produkt-Promo), den User aktiv warnen: Für kommerzielle Reels ist
Chartmusik auch in der App nicht lizenziert (Business-Konten sehen nur die
lizenzfreie Sound Collection) — hier lizenzfreies Musikbett einbrennen
(Pixabay/eigene Bibliothek). Gleiches gilt fürs **Auto-Posting** über
Make/API: Dort kann keine In-App-Musik ergänzt werden → immer lizenzfreies
Bett einbrennen oder bewusst ohne Musik posten.
4. **Config:** `"music": {"enabled": true, "file": "<track>", "gain": 0.3}`
   — das Ducking läuft automatisch (Sidechain: Musik senkt sich beim
   Sprechen um ~20 dB und atmet in Pausen wieder auf; getestet).
5. Loudness-Pass (`loudnorm`) bei Musik IMMER mit aktivieren.

### Gekoppelte Effekte (Bild + Ton am selben Zeitpunkt)

- **Wisch mit Sound:** `transition.sfx_file` auf einen Whoosh setzen —
  prolook legt den Sound automatisch exakt auf jeden Übergang.
- **Typewriter-Captions:** Cue-Zeiten beim Captions-Erzeugen mit
  `--emit-times cue_times.json` ausgeben, daraus Klick-Events bauen und mit
  `build_sfx_track.py` zu EINER Tonspur mischen (ein sfx-Eintrag bei
  time 0) — funktioniert auch bei 50+ Klicks ohne Riesen-Kommando.
- Einzelne Akzente (Ding auf eine Zahl, Riser vor der Auflösung): manuell
  als `sfx`-Events an den gewünschten Zeitpunkten.

### 3. Getestete Standard-Kombinationen (nicht neu erfinden)
- **Talking-Head pur:** Captions reel-Mode + Punch-Ins + Grade/Grain
- **PiP-Layout:** `fg_scale: 0.58`, `y_pos: 0.10`, `border_px: 6` — so ist
  das Fenster voll sichtbar (unterhalb der oberen Tabuzone) und die Captions
  haben darunter freien Platz. Bei größerem Fenster (>0.7) kollidieren
  Captions und Fensterunterkante — dann Captions weglassen oder Story-Layout
  prüfen.
- **Story statt Reel:** Captions `--mode story` (größer, unters Kinn),
  PiP unüblich.

### 4. Qualitätskontrolle (PFLICHT, vor dem Okay an den User)
1. Nach dem Render 2–3 Frames ziehen (`ffmpeg -ss <t> -frames:v 1`):
   eine Sprechstelle, ein Punch-In-Segment, eine Pause.
2. Selbst prüfen: Captions in der Safe-Zone? Highlight auf dem richtigen
   Wort? PiP-Fenster komplett sichtbar? Keine Caption über dem Fenster?
3. Dem User die Frames zeigen und Freigabe holen, DANN erst als fertig
   melden. Bei Anpassungswünschen: nur Config ändern, neu rendern.

## Token-Regeln

- Die Scripts NIE inline nachbauen oder umschreiben — sie sind getestet.
  Nur aufrufen. Bei einem Bug: minimalen Fix machen und merken.
- Transkript nur als kompakten Fließtext lesen (wie in `video-schneiden`),
  nie die Wortliste — die Scripts lesen das JSON selbst.
- ffmpeg-Ausgaben nicht in den Chat spiegeln; nur Erfolg/Fehler prüfen.

## Grenzen (ehrlich bleiben)

Dieses Paket liefert den Look eines sehr guten Creator-Editors (animierte
Captions, dynamischer Schnitt, Look, Sound-Akzente). Es ersetzt KEIN
Motion-Design à la After Effects (eigens animierte Grafiken, Tracking,
Compositing). Das dem User gegenüber nie anders darstellen.
