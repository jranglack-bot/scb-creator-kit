---
name: untertitel-und-text
description: >
  Brennt Untertitel, Hook-Texte und frei gestaltbare Text-Overlays in
  9:16-Videos ein (Reels, Stories, B-Roll): transkribiert die Tonspur
  wortgenau, erzeugt sprach-synchrone Untertitel, gestaltet Texte nach
  Wunsch (Schriftart, Größe, Farbe, Hintergrund-Box) und platziert alles
  automatisch in der Instagram Safe-Zone. Verwende diesen Skill bei:
  "mach Untertitel drauf", "Untertitel einbrennen", "Captions ins Video",
  "Text ins Reel", "Text auf mein B-Roll", "Hook-Text einfügen",
  "Textfarbe/Schriftart ändern", "Text mit Hintergrund", "subtitles",
  oder nach dem Video-Schnitt, wenn das Video Text bekommen soll.
---

# Untertitel & Text einbrennen (9:16)

Erzeuge sprach-synchrone Untertitel und brenne sie zusammen mit optionalem
Hook-Text in das Video ein. Platzierung IMMER nach den Safe-Zone-Regeln aus
dem Skill `reel-layout` — Reels und Stories unterscheiden sich!

## Schritt 0: Vorklärung

Frage (falls nicht aus dem Kontext klar):
1. **Reel oder Story?** → bestimmt Untertitel-Position und -Größe.
2. **Soll oben ein Hook-Text stehen?** (z. B. die Kernaussage als Text-Overlay)
3. Ist das Video schon fertig geschnitten? Wenn nicht → erst Skill
   `video-schneiden`, DANN untertiteln (Untertitel müssen zur finalen
   Schnittfassung passen — nie Zeitstempel des Rohmaterials recyceln).

Benötigt: ffmpeg + ElevenLabs-API-Key (derselbe wie beim Video-Schneiden,
`~~elevenlabs-api-key`). Fehlt der Key → wie im Skill `video-schneiden`
Schritt 0 beschrieben einrichten.

## Schritt 1: Tonspur extrahieren und transkribieren

```bash
ffmpeg -i "VIDEO" -vn -ac 1 -acodec libmp3lame -q:a 4 "audio_temp.mp3" -y -loglevel error
```

Transkription mit Wort-Zeitstempeln (ElevenLabs Speech-to-Text, wie im Skill
`video-schneiden` Schritt 4 — gleiche .bat-Methode, `timestamps_granularity=word`,
`language_code=de`).

## Schritt 2: Untertitel-Datei (ASS) erzeugen

Baue aus den Wort-Zeitstempeln eine `.ass`-Datei (per Python-Script):

- **Cues: 2–3 Wörter** pro Einblendung — kurz und lesbar.
- **Nur während gesprochen wird** — in Pausen kein Untertitel stehen lassen.
- PlayRes an die Videoauflösung anpassen (Standard 1080×1920).

**Stil REEL** (unteres Drittel, Safe-Zone):
```
Style: Reel,Segoe UI,64,&H00FFFFFF,&H00000000,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,6,2,2,55,165,460,1
```
→ ~64 px, fett, weiß mit schwarzer Kontur, Alignment 2 (unten zentriert),
MarginR 165 (rechte Button-Spalte frei), MarginV 460 (Unterkante ≈ 76 %).

**Stil STORY / Talking-Head** (konstant unter dem Kinn):
```
Style: Story,Segoe UI,92,&H00FFFFFF,&H00000000,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,2,2,55,55,730,1
```
→ GROSS (92 px), Alignment 2, MarginV 730 ≈ Brusthöhe (~62 %) — Position nie
springen lassen.

## Schritt 3: Optionaler Hook-Text (oben)

Hook-Text als eigener ASS-Style mit Alignment 8 (oben zentriert) und
**MarginV ≥ 290** — damit er unterhalb der oberen ~15 % beginnt (dort liegt
Instagrams „Reels"-Überschrift). Kurz halten (1–2 Zeilen), gleicher
Kontrast-Stil. Bei Stories reicht MarginV ≥ 280 (oberhalb liegt der
Fortschrittsbalken-Bereich bis ~14 %).

## Schritt 3b: Text-Overlays für B-Roll-Reels (frei gestaltbar)

Für B-Roll-Content (Stock-/Stimmungs-Video mit Botschaft als Text) ist der
Text das Hauptelement — Gestaltung aktiv mit dem User klären, statt Standard
zu nehmen:

1. **Stil erfragen oder aus Obsidian ziehen:** Liegt im Vault unter
   `00 Kontext/Branding.md` ein definierter Look (Schriftart, Farben)?
   → verwenden. Sonst kurz fragen: „Welcher Stil — cleaner weißer Text,
   Text mit farbiger Box dahinter, oder was Eigenes?"
2. **Frei wählbar sind:**
   - **Schriftart** — jede auf dem System installierte Schrift (z. B.
     Segoe UI, Arial Black, Impact, Georgia; `fc-list`/Fonts-Ordner prüfen)
   - **Größe & Zeilenumbruch** — Botschaft groß (80–110 px), Nebentext kleiner
   - **Schriftfarbe** — beliebiger Hex-Wert (`&H00FFFFFF&`-Schema in ASS:
     Blau-Grün-Rot gedreht!)
   - **Kontur/Schatten** — Stärke und Farbe
   - **Hintergrund** — keine Box, halbtransparente Box (`BorderStyle=3` +
     `BackColour`), oder deckender Balken/Banner (per `drawbox`-Filter
     hinter dem Text)
   - **Position** — überall innerhalb der Safe-Zone (siehe `reel-layout`);
     bei B-Roll bewährt: mittig im oberen Drittel (unterhalb der 15 %-Grenze)
3. **Timing:** Text kann stehen bleiben (ganzes Video), in Phasen wechseln
   (mehrere ASS-Events) oder wort-/zeilenweise erscheinen.
4. **Vorher eine Stil-Vorschau zeigen:** einen Beispiel-Frame mit dem
   gestalteten Text rendern und dem User zur Freigabe zeigen, BEVOR das
   ganze Video gerendert wird.
5. Gewählten Stil in Obsidian (`00 Kontext/Branding.md`) notieren, damit er
   beim nächsten Mal ohne Nachfragen wiederverwendet wird.

## Schritt 4: Einbrennen

```bash
ffmpeg -i "VIDEO" -vf "ass=untertitel.ass" -c:v libx264 -crf 21 -preset medium -c:a copy "VIDEO_untertitelt.mp4" -y
```

**Windows-Stolperstein:** Der `ass=`-Filter verschluckt sich am Doppelpunkt in
`C:\...`-Pfaden. Lösung: ins Arbeitsverzeichnis wechseln und die .ass-Datei
mit **relativem Pfad** angeben.

## Schritt 5: Qualitätskontrolle

1. 2–3 Frames an Sprechstellen extrahieren (`ffmpeg -ss <t> -frames:v 1`) und
   prüfen: Untertitel in der Safe-Zone? Lesbar? Nicht über Gesicht/Buttons?
2. Ein Frame in einer Sprechpause: kein Untertitel sichtbar?
3. Dem User 1–2 Vorschau-Frames zeigen und ein Okay einholen, bevor lange
   Renderläufe gestartet werden.

## Merkregeln

- Reel ≠ Story: unterschiedliche Position UND Größe (64 px vs. 92 px).
- Nach jedem weiteren Schnitt: neu transkribieren, Untertitel neu erzeugen.
- Untertitel-Stil konsistent halten — nicht pro Video neu erfinden.
