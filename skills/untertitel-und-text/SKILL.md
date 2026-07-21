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

## Stil-Profil: einmal einrichten, für immer nutzen

Bevor irgendetwas gefragt wird: Prüfe, ob in Obsidian
`00 Kontext/Branding.md` ein **Untertitel-Profil** existiert (Codeblock mit
der Sprachmarkierung `untertitel-profil`). Wenn ja → still verwenden, KEINE
Stilfragen stellen. Format:

```untertitel-profil
{
  "font": "Segoe UI",
  "size": 64,
  "primary": "FFFFFF",
  "highlight": "FFD400",
  "outline_px": 6,
  "box": false,
  "mode": "reel",
  "position": "unteres Drittel (Standard-Safe-Zone)"
}
```

**Profil neu einrichten — zwei Wege:**

**Weg A — per Screenshot-Vorlage (der einfachste für den User):**
Der User zeigt einen Screenshot eines Reels, dessen Untertitel-Stil ihm
gefällt ("so will ich das"). Dann:
1. Screenshot EINMAL ansehen und den Stil in Parameter übersetzen:
   Schriftcharakter (rund/eckig, fett?), Textfarbe und Highlight-Farbe als
   Hex, Kontur oder Box dahinter, Position im Frame, relative Größe.
2. Als Schriftart die **nächstliegende installierte Systemschrift** wählen
   (Fonts-Ordner prüfen; z. B. rundlich-fett → "Arial Rounded MT Bold" oder
   "Segoe UI Black"). Ehrlich sagen, dass es die nächstliegende Schrift ist —
   die Original-Schrift aus fremden Apps ist oft nicht frei verfügbar; wenn
   der User die exakte Schrift besitzt, kann er sie installieren.
3. **EINEN Vorschau-Frame rendern** (Beispieltext im neuen Stil auf einem
   Frame des User-Videos oder neutralem 1080×1920-Hintergrund) und zeigen.
4. Nach dem Okay (max. 1–2 Korrekturrunden) das Profil als
   `untertitel-profil`-Block in `00 Kontext/Branding.md` speichern.
5. Ab jetzt liest jeder Lauf das Profil — der Screenshot wird nie wieder
   analysiert, es wird nie wieder gefragt.

**Weg B — per kurzen Fragen:** Falls kein Screenshot da ist: maximal 3
Fragen (Schrift-Stil grob, Highlight-Farbe, Box ja/nein), Vorschau-Frame,
speichern wie oben.

**Änderungswunsch später** („mach die Untertitel ab jetzt größer/blau"):
Profil in Branding.md anpassen, kurz bestätigen mit einem Vorschau-Frame,
fertig — gilt ab dann überall (auch im Skill `pro-look-editing`).

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

Baue aus den Wort-Zeitstempeln eine `.ass`-Datei — **vollständig per
Python-Script**, das die Transkript-JSON direkt liest und die Cues
deterministisch erzeugt. Die Wort-für-Wort-Liste dabei NICHT in den Kontext
laden (Token-Verschwendung ohne Qualitätsgewinn — die Cue-Bildung ist reine
Mechanik, das Script macht sie fehlerfrei):

- **Cues: 2–3 Wörter** pro Einblendung — kurz und lesbar (Script gruppiert).
- **Nur während gesprochen wird** — Script beendet jede Cue am Wort-Ende und
  überspringt Lücken > 0,5 s automatisch.
- PlayRes an die Videoauflösung anpassen (Standard 1080×1920).
- Qualitätskontrolle danach über die **Vorschau-Frames** (Schritt 5), nicht
  durch Lesen der Rohdaten.

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
