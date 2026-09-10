# Kinetischer Untertitel — Bauanleitung

Beobachtet an einem Reel von @jenya_kork (Shortcode `DdCPjPvT1ZI`,
analysiert am 09.09.2026), von Julian als Ziel benannt. Das ist eine
**Spezifikation zum Nachbauen**, kein fertiges Werkzeug — der Zustand des
Cockpits am Ende dieser Datei sagt, was davon heute schon geht.

Der Kern: **es ist kein Untertitelband.** Ein gleichförmiger Streifen am
selben Ort, in derselben Größe, in derselben Farbe wirkt wie ein
Barrierefreiheits-Untertitel. Dieser hier ist ein gestaltetes Element, das
sich in vier Richtungen vom Standard löst.

## 1. Zwei Zeilen mit stark unterschiedlichem Gewicht

Jede Einblendung besteht aus zwei Zeilen:

| | Inhalt | Größe | Schnitt | Farbe |
|---|---|---|---|---|
| oben | die Wörter davor, Zusammenhang | klein, rund 40 % der unteren | normal | weiß |
| unten | das **Schlüsselwort**, ein bis zwei Wörter | groß | fett | siehe Punkt 3 |

Beispiele aus dem Reel: „geschnitten und heute ist" klein, darunter
**„der Tag"** groß. „als ich meine Videos in" klein, darunter **„Claude"**
groß. „Code bearbeite und dir" klein, darunter **„zeig"** groß.

Die obere Zeile ist also nicht der vorherige Untertitel, sondern der
**Anlauf auf das betonte Wort**. Der Satz wird beim Sprechen in Häppchen
zerlegt, und immer nur das jeweils betonte Wort kommt groß.

## 2. Die Position wechselt

Der Block sitzt nicht immer an derselben Höhe. Im Reel wandert er
zwischen etwa 0,25 und 0,60 der Bildhöhe, je nachdem, wo im Bild gerade
Platz ist — über dem Kopf, wenn die Person tief sitzt; auf Brusthöhe,
wenn oben Grafik läuft. Ein fester Wert für das ganze Video wäre der
sichtbarste Unterschied zum Vorbild.

Im Kit gibt es dafür bereits `captions.y_regions` in der `projekt.json`
(Liste aus `{von, bis, y}`) — die Fähigkeit ist da, sie wird nur bisher
kaum genutzt.

## 3. Die Füllung des Schlüsselworts

Drei Varianten wechseln sich ab:

- **Volltonfarbe** — weiß, oder Julians Blau `597fd9`.
- **Farbverlauf** — violett nach blau über das Wort hinweg.
- **Negativ des Videos** — das Wort hat keine eigene Farbe, sondern zeigt
  das invertierte Bild dahinter. Erkennbar daran, dass die Schrift über
  Hautton **cyan** wird und die Streifen im Buchstaben den Falten des
  Stoffs dahinter folgen. Es ist kein reines Negativ: über dem dunklen
  Sofa bleibt ein violetter Grundton, es liegt also noch eine Farbebene
  darin (`difference` oder `exclusion` gegen eine getönte Fläche, nicht
  gegen Weiß).

Umsetzung: im Browser eine Zeile (`mix-blend-mode: difference`), in
ffmpeg `blend=all_mode=difference` zwischen Textebene und Videobild.
**Der ffmpeg-Weg ist der wichtige** — nur so bleibt der Text im Cockpit
änderbar, statt bei jeder Korrektur eine Coderunde zu kosten.

## 4. Das Wort liegt HINTER der Person

Die Schrift wird von Haaren, Schulter und Hand sauber verdeckt. Das ist
die Loch-Stanze aus `motion-grafik` (Stufe 3): Personenmaske stanzt ein
Loch in die Textebene, darunter das Originalvideo. Die Person existiert
dabei nur einmal im Bild.

**Hier liegt die eine echte Lücke im Kit:** `render_projekt.py` hängt den
Freisteller als OBERSTE Ebene an, `prolook.py` brennt die Untertitel aber
erst danach ein (`post.append('ass=...')` nach der Overlay-Kette). Grafik
liegt damit hinter der Person, Untertitel aber davor. Für diesen Effekt
muss die Untertitel-`ass` **vor** dem Freisteller-Overlay in die Kette,
nicht danach.

## Womit es gebaut wird — nichts davon neu schreiben

Die Untertitel entstehen heute in
`skills/pro-look-editing/scripts/animated_captions.py`. Das Script liest ein
Transkript mit Wortzeiten und schreibt eine ASS-Datei: Gruppen aus zwei bis
drei Wörtern, Pop beim Erscheinen, farbige Hervorhebung auf dem gerade
gesprochenen Wort, Safe-Zone-Werte für Reel und Story. Es kennt **eine**
Schriftgröße und **eine** Hervorhebungsfarbe.

Genau dort setzt der kinetische Untertitel an: es ist eine Erweiterung
dieses Scripts, kein zweites Werkzeug. Eingebrannt wird weiter über
`prolook.py` (`captions`), gesteuert weiter über die `projekt.json`.

## Was fehlt dem Cockpit dafür

Reihenfolge nach Nutzen je Aufwand:

1. **Untertitel hinter die Person** — Reihenfolge in `prolook.py` (s. o.).
   Kleinster Eingriff, größte Wirkung, macht den Effekt überhaupt möglich.
2. **Zwei Größen je Einblendung** — heute kennt das Cockpit eine Schrift-
   größe plus ein hervorgehobenes Wort. Gebraucht wird: kleine Anlaufzeile
   und großes Schlüsselwort als zwei Stile in derselben Einblendung.
3. **Position je Abschnitt im Cockpit klickbar** — `y_regions` gibt es
   schon in der `projekt.json`, aber keinen Regler dafür.
4. **Füllung des Schlüsselworts wählbar** — Vollton / Verlauf / Negativ.
   Verlauf und Negativ kann das ASS-Format nicht; die brauchen einen
   eigenen Renderdurchgang mit `blend`.

## Vorgehen beim Nachbauen

Nie eine Variante nach der anderen als Einzelclip zeigen. Zwei bis drei
Rechenarten auf denselben zwei Problembildern als **einen Kontaktbogen**
(CLAUDE.md §7b), Julian zeigt auf die richtige, danach wird genau eine
gebaut.
