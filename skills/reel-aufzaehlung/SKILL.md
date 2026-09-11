---
name: reel-aufzaehlung
description: >
  Baut das Aufzählungs-Reel mit Urteil („Print on Demand — lass es sein.
  KI-Agentur — mach's."): zehn Begriffe, je ein sofortiges Urteil, feste
  Bewertungskästen links und rechts, Logo-Kacheln die zur passenden Seite
  aus dem Bild fliegen. Enthält das Verfahren, eine sauber aufgenommene
  zweite Tonspur über ein Video mit schlechtem Ton zu legen, und zieht die
  Untertitel-Wortzeiten danach automatisch nach. Verwende diesen Skill bei:
  "Aufzählungs-Reel", "Side-Hustle-Reel", "lohnt sich / lohnt sich nicht",
  "mach's / lass es sein", "zehn Begriffe mit Bewertung", "Reel wie
  realaaronchen", "saubere Tonspur über das Video legen", "Untertitel ist
  doppelt zu sehen", "Untertitel läuft dem Ton voraus".
---

# Aufzählungs-Reel mit Urteil

Zehn Begriffe, jeder mit einem sofortigen Urteil. Das eigene Thema kommt
zuletzt und bekommt die stärkste Zusage. Rund 24 Sekunden.

Dieser Skill ist die Zusammenfassung eines kompletten Durchlaufs inklusive
aller Sackgassen. **Was hier steht, ist gemessen, nicht geschätzt.** Wer
sich daran hält, braucht dafür zwei Render statt zwanzig.

Gebaut wird es mit dem `video-projekt`-Skill. Dieser Skill beschreibt nur,
was an diesem Format anders ist.

## 1. Das Format

Vier bis fünf Absagen zuerst, dann die Zusagen, das eigene Thema ganz zum
Schluss. Die Steigerung trägt das Reel:

- **Die Absagen flach und gleich betont.** Erst am Ende hochgehen. Ohne
  diesen Kontrast fällt der Schluss in sich zusammen.
- **Ein Bruch in der Reihe hält die Aufmerksamkeit** — eine Absage mitten
  zwischen den Zusagen.
- **Cold Open.** Kein „Hi", kein Aufwärmen. Erstes Wort ist der erste
  Begriff.
- **Ein roter Faden unter der Auswahl, der nicht ausgesprochen wird.** Im
  Referenzdurchlauf waren vier der fünf Absagen dasselbe Modell (eigene
  Produkte verkaufen), die Zusage am Ende das Gegenteil. Die Erkenntnis
  soll beim Zuschauer entstehen, nicht im Video stehen.

Hook-Formeln und CTA: `reel-hooks`.

## 2. Aufnahme: zwei Takes, nicht einer

1. **Hauptvideo**, 1080×1920 hochkant, alles am Stück: Begriffe, Urteile,
   CTA.
2. **Saubere Tonspur** mit dem guten Mikro: **nur die Begriffe**, im selben
   Rhythmus wie im Hauptvideo.

Der Ton im Hauptvideo ist bei so einem Dreh fast immer schwächer
(Ansteckmikro, Handy in der Tasche). Die Begriffe kommen deshalb aus
Take 2, die Urteile bleiben aus Take 1.

**Take 2 im gleichen Tempo sprechen wie Take 1.** Im Referenzdurchlauf
stimmte die erste Hälfte auf Hundertstel, die zweite lag bis zu 0,94 s
daneben und musste von Hand nachgeschoben werden.

## 3. Die saubere Tonspur über das Video legen

Der Teil, an dem am meisten schiefgeht. Die Reihenfolge ist nicht beliebig.

1. **Einzelne Schnipsel, kein durchgehendes Voiceover.** Je Begriff eine
   eigene WAV im Unterordner `stimme/`, sprechend benannt
   (`01_print_on_demand.wav`). Als Einträge in `effekte.sfx`. Nur einzeln
   kann der Nutzer sie im Cockpit verschieben.

2. **Beim Anlegen gleich `worte` mitschreiben.** Die Zuordnung ist genau
   jetzt bekannt und später nur mühsam zu rekonstruieren:

   ```json
   {"time": 20.90, "file": "stimme/08_amazon_fba.wav",
    "gain": 1.0, "name": "Amazon FBA", "worte": "Amazon FBA"}
   ```

3. **Alle Zeiten sind ROHZEIT**, also Zeit im zusammengefügten Material vor
   den Schnitten — nie in geschnittene Zeit umrechnen. Die Cockpit-Timeline
   läuft in Rohzeit, die Schnitte stehen als rote Balken darin, und
   `render_projekt.py` verschiebt beim Rendern selbst. Steht in
   `video-projekt/SKILL.md` ausführlich.

4. **Wellenform auf die Marker legen.** Ohne sie schiebt der Nutzer blind.
   Umsetzung in `cockpit_custom.js` neben der `projekt.json` (überlebt
   Kit-Updates): SVG-Wellenform je Datei als Base64, im Cockpit als
   `background-image` auf die `.sfx`-Elemente. **Zuordnung über den Text in
   `.slbl`** — die Projektvariable im Cockpit ist `let`-deklariert und über
   `window` nicht erreichbar. Schlüssel ist der auf 18 Zeichen gekürzte
   Name, genau wie der Marker ihn anzeigt.

5. **Hauptspur unter jedem Schnipsel stumm.** Über `volumes` mit
   `track: "main"`, je Schnipsel drei Abschnitte: kurze Rampe auf 0,45,
   dann `gain 0` für die Länge des Schnipsels, dann Rampe zurück. Ohne
   Rampen knackt es. Fenster = `time` bis `time + Länge`, plus 0,04 s Rand.

6. **Der Nutzer schiebt und speichert. Erst danach Schritt 7.** Seine
   Positionen sind die Wahrheit, nicht die gemessenen.

7. **Wortzeiten nachziehen — nie auslassen:**

   ```
   python scripts/stimme_synchronisieren.py <projekt.json>
   ```

   Ohne diesen Schritt läuft der Untertitel dem Ton voraus (gemessen: bis
   0,83 s) und steht an mehreren Stellen doppelt im Bild. Warum, steht
   unten unter „Doppelter Untertitel". Das Script misst den Sprechbeginn in
   jeder Stimmdatei, legt die zugehörigen Wörter darauf und räumt
   anschließend alle Überlappungen weg. Mit `--test` erst zeigen.

### Was nicht funktioniert

Alles hier ausprobiert und verworfen:

- **Kreuzkorrelation der beiden Tonspuren.** Zwei Mikrofone und zwei Takes
  sind sich nicht ähnlich genug. Ergebnis war eine Reihenfolge, in der ein
  Begriff hinter einem lag, der im Video später kommt.
- **Whisper-Wortzeiten als Schnittgrenzen.** An Pausen bis 0,45 s daneben.
  Echte Stimmeinsätze über die Energiehüllkurve messen, 10-ms-Fenster.
- **Ein globaler Versatz für alle Schnipsel.** Funktioniert nur, solange
  der Sprechrhythmus gleich bleibt, und das tut er selten über 24 Sekunden.
- **Pegel- und Frequenzmessung als Argument, die schlechtere Aufnahme sei
  gut genug.** Die Werte waren fast identisch, hörbar war der Unterschied
  trotzdem deutlich. Sagt der Nutzer, eine Aufnahme klingt schlechter,
  dann stimmt das.

## 4. Doppelter Untertitel — Ursache und Riegel

**Symptom:** An einzelnen Stellen stehen zwei Untertitelzeilen übereinander,
Wörter schieben sich ineinander („Werbvoll für'n Arsch Geld"). Sieht aus,
als wäre am Schnitt etwas stehengeblieben.

**Es liegt nicht am Schnitt.** Transkriptionen setzen Wortanfänge
regelmäßig schon in die Stille davor, im Referenzdurchlauf bis 0,83 s zu
früh. Das Wort-**Ende** ist der zuverlässige Wert. Reicht ein Wort dadurch
über den Beginn der nächsten Wortgruppe hinaus, stehen beide Gruppen
gleichzeitig im Bild. Besonders sicher passiert das, wenn Wortzeiten aus
zwei Aufnahmen stammen, also genau bei diesem Format.

Zwei Stellen fangen das ab:

- `stimme_synchronisieren.py` zieht jeden Wortstart hinter das Ende des
  Vorgängers. Die geklemmten Starts lagen danach auf 0,01–0,07 s an den
  gemessenen echten Stimmeinsätzen — die Klemmung rät nicht, sie trifft.
- `pro-look-editing/scripts/animated_captions.py` macht die Wortzeiten vor
  dem Schreiben der `.ass` ohnehin monoton und deckelt die letzte Zeile
  einer Wortgruppe auf den Beginn der nächsten. Gegenprobe mit den
  unkorrigierten Wortzeiten aus dem Referenzdurchlauf: vorher acht
  gleichzeitig sichtbare Zeilen, danach null.

Der Riegel in `animated_captions.py` repariert nur die **Anzeige**. Den
**Versatz** zum Ton behebt er nicht — dafür bleibt Schritt 7 nötig.

Nachsehen, ob eine fertige Untertiteldatei sauber ist: benachbarte
`Dialogue`-Zeilen in der `.ass` dürfen sich zeitlich nie überlappen.

## 5. Die festen Bildelemente

Balken oben, zwei Symbole, zwei Urteilskästen. Sie stehen über die **volle
Länge** (`start` 0 bis `duration`) und bewegen sich nicht. Nur die Kacheln
in der Mitte wechseln.

| Element | Wo | Richtwerte (1080×1920) |
|---|---|---|
| Balken oben | `texts` | x 0.50, y 0.075, 52 px, Box dunkel |
| Symbol links | `texts` | x 0.135, y 0.175, 96 px |
| Urteil links | `texts` | x 0.165, y 0.243, 34 px, Box rot |
| Symbol rechts | `texts` | x 0.865, y 0.175, 96 px |
| Urteil rechts | `texts` | x 0.855, y 0.243, 34 px, Box grün |
| Untertitel | `captions` | y 0.698, Größe 74 |

**Diese Elemente gehören in denselben Durchgang wie der Schnitt**, nicht in
eine zweite Runde. Sie sind Stufe 1 und kosten keinen eigenen Render. Beim
**ersten** Zeigen im Cockpit einmal fragen: „Soll ich die festen Elemente
gleich mit einsetzen — Balken, Symbole, Urteilskästen? Dann rendern wir nur
einmal."

**Welche Seite welche Farbe hat, einmal bestätigen lassen und dann nicht
mehr ändern.** Im Referenzdurchlauf wurden die Seiten dreimal vertauscht,
jedes Mal mit Nachfrage.

### Farbige Emojis brauchen eine Bildebene

**libass rendert keine Farb-Emojis.** Ein Emoji in `texts` oder `captions`
kommt schwarzweiß heraus, ohne Fehlermeldung. Wer farbige Emojis will,
legt Balken und Emojis als eigene Ebene darüber:

1. Die Elemente als PNG mit Transparenz bauen (Browser-Render reicht).
2. **Als Video wandeln, nicht als PNG einbinden** — ein Standbild-Overlay
   zeigt sonst nur einen einzigen Frame:
   `-c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le`, Länge = Länge
   des fertigen Videos.
3. In `effekte.overlays` mit `"alpha": true, "fullframe": true`.

## 6. Kacheln, die aus dem Bild fliegen

Je Begriff eine Kachel mit Logo und Beschriftung, die von unten hochkommt
und zur Seite ihres Urteils wieder hinausfliegt. Das ist Stufe 2, also
animierte Grafik — Werkzeugwahl und Ablauf stehen in `motion-grafik`.
HyperFrames eignet sich gut, weil die Alpha-Ebene ohne Fallstricke
herauskommt.

Vier Fehler, die dort Zeit gekostet haben:

- **GSAP überschreibt das CSS-`transform`.** Ein per CSS zentriertes
  Element (`translate(-50%,-50%)`) hängt nach dem ersten Tween halb im
  Bild. Zentrierung in GSAP selbst setzen: `gsap.set(el, {xPercent: -50,
  yPercent: -50})`.
- **Startposition weit genug außerhalb.** `y: 1000` ragte noch 105 px ins
  Bild. Gemessen prüfen, nicht schätzen.
- **Breite UND Höhe explizit setzen, plus `object-fit: contain`.** Nur mit
  `width` sehen die Kacheln in der Vorschau richtig aus und sind im Render
  vertikal gestreckt.
- **Beschriftung gegenlesen.** Bei zehn Kacheln fehlt sonst genau auf der
  letzten die zweite Zeile.

Dazu der Woosh beim Hinausfliegen: ein kurzer Effekt aus der
SFX-Bibliothek je Kachel, auf `effekte.sfx`, Zeit in Rohzeit.

## 7. Kontrolle vor dem Zeigen

- **Das Cockpit wirklich ansehen, nicht nur rechnen.** Es ist eine lokale
  Datei; eingebettete Browser zeigen `file://` oft nur als Standbild. Im
  Projektordner `python -m http.server 8731 --bind 127.0.0.1` starten,
  `http://127.0.0.1:8731/editor.html` öffnen, Screenshot. Ein Blick darauf
  hätte im Referenzdurchlauf vier Runden erspart.
- **Nach jeder Änderung den ganzen Frame prüfen, nicht nur die geänderte
  Stelle.** Kontaktbogen über die volle Länge:
  `ffmpeg -i final.mp4 -vf fps=1/2,scale=320:-1,tile=4x3 kontrolle.jpg`.
  Alle Fehler, die im Referenzdurchlauf zurückkamen, waren außerhalb der
  zuletzt bearbeiteten Stelle sichtbar.
- **Beurteilt wird an abspielbarem Video**, nicht an Standbildern.

## 8. Zwei Render, nicht zwanzig

1. Schnitt, Ton, Untertitel **und alle festen Bildelemente** → zeigen,
   Freigabe abwarten.
2. Animierte Kacheln dazu → zeigen, Freigabe abwarten, rendern.

Jeder weitere Render entsteht dadurch, dass etwas vergessen wurde.
