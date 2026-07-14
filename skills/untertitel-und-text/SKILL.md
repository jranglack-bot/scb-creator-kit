---
name: untertitel-und-text
description: >
  Brennt Untertitel und Hook-Texte in 9:16-Videos ein (Reels & Stories):
  transkribiert die Tonspur wortgenau, erzeugt sprach-synchrone Untertitel
  im richtigen Stil und platziert alles automatisch in der Instagram
  Safe-Zone. Verwende diesen Skill bei: "mach Untertitel drauf",
  "Untertitel einbrennen", "Captions ins Video", "Text ins Reel", "Hook-Text
  einfügen", "untertitel mein Video", "subtitles", oder nach dem
  Video-Schnitt, wenn das Video Untertitel bekommen soll.
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
