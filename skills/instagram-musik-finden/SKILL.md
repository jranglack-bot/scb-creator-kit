---
name: instagram-musik-finden
description: >
  Identifiziert ein auf Instagram entdecktes Lied und lädt es legal als
  Datei herunter, damit es unter ein eigenes Video gelegt werden kann.
  Verwende diesen Skill bei: "wie heißt das Lied aus dem Reel", "diesen
  Song will ich haben", "Musik von Instagram runterladen", "der Sound
  gefällt mir", "RF-Song laden", "Instagram-Audio identifizieren",
  "Musik aus dem Reel für mein Video".
---

# Song von Instagram finden und legal herunterladen

Der User hat auf Instagram Musik gehört, die ihm gefällt, und will sie als
Datei unter sein eigenes Video legen. Dieser Ablauf ist end-to-end erprobt.

**Wichtig vorab: Apify kann das NICHT.** Die dortigen „Instagram Music/Audio
Downloader" sind reine Metadaten-Scraper. Ihr Feld `musicUrl`/`audio_url`
enthält nur die Instagram-Seiten-URL, keine Audiodatei. Nicht ausprobieren,
das kostet nur Geld. Der Weg unten ist kostenlos und funktioniert.

## Schritt 1 — Audio-URL besorgen (User)

In der Instagram-App im Reel unten auf den **Songnamen tippen** → Audio-Seite
öffnet sich → oben rechts **Teilen → Link kopieren**.
Form: `instagram.com/reels/audio/<zahlen-id>/`

## Schritt 2 — Titel und Künstler auslesen (kostenlos, kein Login)

Instagram legt beides in die Seiten-Metadaten. Die Audio-URL per **WebFetch**
holen und den Seitentitel lesen:

```
Format: "<Künstler> | <Titel> on Instagram"
Beispiel: "Ross Lara | Love Is Like The Wind on Instagram"
```

Kein Apify, kein Login, keine Kosten. Ergebnis dem User nennen.

## Schritt 3 — Speicherort klären (IMMER FRAGEN, nie annehmen)

**Bevor irgendetwas gespeichert wird, den User nach seinem Ordner fragen.**
Niemals eigenmächtig einen Pfad wählen.

1. Erst in `00 Kontext\Branding.md` nachsehen, Zeile `Musik-Bibliothek: <pfad>`.
2. Steht dort nichts: User fragen, wo seine Musik liegen soll, und die Antwort
   als `Musik-Bibliothek: <pfad>` in `Branding.md` eintragen. Ab dann gemerkt.
3. Stimmungs-Unterordner wie im pro-look-editing-Skill: `energetisch/`,
   `ruhig/`, `emotional/`, `episch/`, `froehlich/`.

## Schritt 4 — In der Meta Sound Collection suchen

**facebook.com/sound** (Facebook-Login nötig, der User ist meist schon
angemeldet).

> ⚠️ **Der entscheidende Trick: Künstler UND Titel zusammen in EIN Suchfeld.**
> Nur der Titel liefert bloß Ähnlichkeitstreffer. Nur der Künstler liefert
> eine Liste, die häppchenweise nachlädt und den Song verstecken kann.
> Kombiniert (`Ross Lara Love Is Like The Wind`) erscheint der exakte Treffer
> sofort. Wer das falsch macht, schließt fälschlich, der Track sei nicht da.

Beim allerersten Aufruf verlangt Meta eine einmalige Zustimmung zu den
Nutzungsbedingungen. **Diesen Haken setzt der User selbst, niemals Claude.**

## Schritt 5 — Herunterladen, nach MP3 wandeln, ablegen

Download-Button (Kreis mit Pfeil nach unten) in der Trefferzeile.

Die Datei kommt als **Audio-only-MP4 (AAC)**, das ist kein Fehler. Referenzwerte
aus dem Test: 4:26 Länge, 48 kHz Stereo, ~49 kbps, 1,55 MB. Also der
**vollständige Song**, nicht der kurze App-Ausschnitt.

**Immer automatisch nach MP3 wandeln** (Kit-Konvention, wie bei `sfx-extraktion`):

```
ffmpeg -y -v error -i "<download>.mp4" -vn -c:a libmp3lame -b:a 192k "<ziel>.mp3"
```

192 kbps ist bewusst großzügig gewählt: Die Quelle hat nur ~49 kbps, mit
Reserve geht beim Umkodieren praktisch nichts Hörbares verloren. Danach die
MP4-Datei löschen, damit die Bibliothek sauber bleibt (vorher kurz beim User
rückfragen, wenn er sie behalten will).

Ehrlich sagen, falls der User nachfragt: MP3 ist ein Neu-Kodieren von bereits
komprimiertem Material, also technisch ein kleiner Qualitätsverlust. Als
geducktes Musikbett unter einer Stimme nicht hörbar. Wer verlustfrei arbeiten
will, benennt stattdessen nach `.m4a` um (`-c:a copy`, reiner Container-Wechsel).

Fertige MP3 in den in Schritt 3 geklärten Ordner verschieben, passender
Stimmungs-Unterordner.

## Schritt 6 — Ins Video

```
python scripts/set_music.py projekt.json "<pfad zur datei>" [--gain 0.3]
```
(Script liegt im `video-projekt`-Skill.) Ducking und Loudness laufen wie
gewohnt, siehe pro-look-editing.

## Zwei Grenzen, die du dem User aktiv sagen musst

**1. RF-Kennzeichnung bedeutet nicht automatisch herunterladbar.**
Instagrams RF-Spur (Tracks, die man *innerhalb* von Instagram nutzen darf)
und die Meta Sound Collection (Tracks, die *zusätzlich* als Datei ladbar sind)
sind nicht deckungsgleich. Findest du den Song trotz kombinierter Suche nicht,
ehrlich sagen: dieser Track ist nur in der App verwendbar. Dann als
Alternative **denselben Künstler** durchsuchen, dort liegen meist stilistisch
sehr ähnliche Titel (Beispiel: Ross Lara hat über 35 Tracks in der Collection).

**2. Die Lizenz gilt nur für Meta-Plattformen.**
Im Zustimmungsdialog steht wörtlich „für den Einsatz auf Facebook, Instagram
oder anderen Apps von Meta". Das heißt: **nicht** für TikTok, YouTube oder die
eigene Webseite. Bei Usern, die ihre Reels auch auf TikTok hochladen, unbedingt
ansprechen. Für **Werbeanzeigen** gelten pro Track eigene Bedingungen, die
separat zu prüfen sind.
