---
name: sfx-extraktion
description: >
  Extrahiert Soundeffekte aus Reels und Videos in die eigene SFX-Bibliothek:
  Video laden (lokale Datei oder Reel-Link), Sounds automatisch oder per
  Zeitangabe herausschneiden, als MP3 benennen und in der Bibliothek
  ablegen. Verwende diesen Skill bei: "extrahier den Soundeffekt",
  "schneide den Sound raus", "hol mir den Sound aus dem Reel",
  "Soundeffekt aus Video schneiden", "SFX extrahieren", "in dem Reel sind
  Soundeffekte, die will ich haben".
---

# SFX aus Reels & Videos extrahieren

Schneide Soundeffekte aus Videos heraus und lege sie in die persönliche
SFX-Bibliothek — komplett per Script, keine Audiodaten im Kontext.

**Fairness-Hinweis (dem User einmal sagen):** Nur für den eigenen Gebrauch
in eigenen Videos. SFX-Compilation-Reels werden genau zum Teilen solcher
Sounds gepostet — dafür ist das gedacht. Keine Musik oder geschützte
Audio-Inhalte extrahieren und nirgends weiterverteilen.

## Schritt 1: Quelle beschaffen

- **Lokale Datei:** direkt verwenden.
- **Reel-Link:** mit `yt-dlp "<url>" -o reel.mp4` laden (yt-dlp ist über
  den /watch-Setup-Schritt installiert; fehlt es → scb-setup Schritt 9).
  Klappt der Download nicht (privates Reel), den User bitten, das Video
  z. B. per Screen-Recording bereitzustellen.

## Schritt 2: Sounds finden — zwei Wege

**Weg A — User nennt die Stelle:** „Bei 0:12 kommt ein Whoosh" → direkt zu
Schritt 3 mit dieser Zeit (großzügig ±0,3 s greifen, dann exakt trimmen).

**Weg B — automatische Erkennung (für SFX-Compilation-Reels):**
SFX-Reels haben Stille zwischen den Sounds — das nutzt die Erkennung:

```
ffmpeg -i reel.mp4 -af "silencedetect=noise=-35dB:d=0.25" -f null NUL
```

Die Sound-Segmente liegen jeweils zwischen `silence_end` und dem nächsten
`silence_start` (plus ~0,05 s Puffer vorn/hinten). Dem User die gefundene
Liste zeigen („Sound 1: 0.0–0.5s, Sound 2: 1.75–1.87s …") und fragen,
welche er behalten will — oder auf Wunsch alle.

## Schritt 3: Schneiden — IMMER als MP3

```
ffmpeg -y -ss <start> -to <ende> -i reel.mp4 -vn -c:a libmp3lame -b:a 320k <name>.mp3
```

- **Immer MP3** (320 kbit/s), niemals WAV abliefern.
- **Sprechende Dateinamen** vergeben: `whoosh-tief.mp3`, `klick-hell.mp3`,
  `impact-bass.mp3` — nicht `sound1.mp3`. Im Zweifel kurz reinhören lassen
  und den User benennen lassen.

## Schritt 4: In die SFX-Bibliothek einsortieren

1. Bibliothekspfad aus Obsidian `00 Kontext/Branding.md` lesen (Zeile
   `SFX-Bibliothek: <pfad>`).
2. Existiert noch keine: Ordner anlegen (z. B. `Dokumente\SFX`), Zeile in
   Branding.md eintragen — einmalig, danach automatisch.
3. MP3s dorthin verschieben, kurz zusammenfassen was jetzt in der
   Bibliothek liegt.

Ab dann stehen die Sounds in `pro-look-editing` automatisch zur Verfügung
(eigene Bibliothek vor Basis-Sounds — aber wie immer: **Sounds nur
einbauen, wenn der User gefragt wurde und Ja gesagt hat**).

## Token-Regeln

- Audio nie in den Kontext laden — nur silencedetect-Zeiten lesen.
- ffmpeg-Ausgaben nicht spiegeln, nur Erfolg + Segmentliste berichten.
