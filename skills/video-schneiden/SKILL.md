---
description: >
  Schneidet Instagram-Kursvideos vollautomatisch: erkennt Versprecher, verbale Fehlersignale,
  doppelte Erklärungen, Füllwörter (äh, ähm) und lange Pausen – mit tiefer KI-Transkriptanalyse.
  Trigger: "schneide das Video", "Video schneiden", "schneide mein Instagram Video",
  "schneide mein Kursvideo", "Versprecher rausschneiden", "Video für den Kurs schneiden",
  "cut the video", "Video bearbeiten".
---

# KI-Video-Cutter für Instagram-Content

Führe den folgenden Workflow Schritt für Schritt aus. Warte nach jedem Schritt auf Bestätigung oder Benutzereingabe, bevor du weitermachst.

---

## Schritt 0: API-Keys prüfen (Groq bevorzugt, ElevenLabs als Rückfallebene)

Die Transkription läuft **bevorzugt über Groq** (schnell, kostenlos).
ElevenLabs ist die Rückfallebene — der Key lohnt sich trotzdem, weil
ElevenLabs auch Musik und Soundeffekte erzeugen kann. Es reicht EINER
der beiden Keys, ideal sind beide.

Prüfe, ob `~~groq-api-key` und `~~elevenlabs-api-key` noch unersetzte
Platzhalter sind (d. h. der Nutzer hat sie noch nicht konfiguriert).

**Fehlen beide**, weise den Nutzer freundlich darauf hin:

> "Bevor wir starten: Für die automatische Transkription brauchst du
> einen kostenlosen **Groq**-API-Key. So bekommst du ihn:
> 1. Gehe auf **console.groq.com** und erstelle ein kostenloses Konto
> 2. Links auf **API Keys** → **Create API Key** → Key kopieren
>
> Empfehlenswert ist zusätzlich ein **ElevenLabs**-Key — als
> Rückfallebene für die Transkription, und weil ElevenLabs Musik und
> Soundeffekte erzeugen kann:
> 1. Auf **elevenlabs.io** ein kostenloses Konto erstellen
> 2. Oben rechts aufs Profilbild → **API Keys** → Key erstellen und kopieren
>
> Gib mir einen oder beide Keys und ich speichere sie einmalig in
> deinem Plugin. Du wirst nie wieder danach gefragt."

**Fehlt nur einer**, arbeite ohne Rückfrage weiter — erwähne nur in
einem Satz, dass der fehlende Key sich lohnt (Groq: schnellere und
kostenlose Transkription; ElevenLabs: Rückfallebene + Musik/Soundeffekte),
und biete an, ihn jederzeit nachzutragen.

Erhaltene Keys als `~~groq-api-key` bzw. `~~elevenlabs-api-key` für
diesen und alle zukünftigen Durchläufe speichern.

Sind die Keys bereits konfiguriert: direkt zu Schritt 1 weitergehen,
ohne den Nutzer zu fragen.

---

## Schritt 1: Video finden und Modus wählen

Suche im Workspace-Ordner nach Videodateien (.mp4, .mkv, .mov, .avi, .m4v). Zeige dem Nutzer die Dateien. Wenn mehrere vorhanden, frage welches geschnitten werden soll.

Frage dann:

> "Wie soll ich vorgehen?
> **A)** Du gibst mir eigene Zeitstempel vor (z.B. 1:23–1:45) – ich schneide genau diese Stellen raus.
> **B)** Ich analysiere das komplette Video anhand des Transkripts und schneide automatisch alles raus, was nicht perfekt klingt."

**Modus A – Eigene Timestamps:**
Nimm die Zeitstempel des Nutzers entgegen. Akzeptiere alle Formate: mm:ss, m:ss, Sekunden als Zahl. Wandle alles in Sekunden um. Speichere die Cuts. Springe direkt zu Schritt 2 und dann zu Schritt 7 (Transkription und KI-Analyse entfallen).

**Modus B – Vollanalyse:**
Führe alle Schritte 2–11 aus.

---

## Schritt 2: Videoinfos prüfen

```bash
ffprobe -v quiet -print_format json -show_format -show_streams "PFAD_ZUM_VIDEO"
```

Extrahiere und teile mit: Dauer, Auflösung, Codec, Dateigröße. Speichere Gesamtdauer für spätere Berechnungen.

---

## Schritt 3: Audio extrahieren (nur Modus B)

```bash
ffmpeg -i "EINGABE" -vn -acodec libmp3lame -q:a 4 "WORKSPACE/audio_temp.mp3" -y -loglevel error
```

---

## Schritt 4: Transkription starten (nur Modus B)

Claude führt das mitgelieferte Script selbst aus — läuft auf Windows, macOS
und Linux gleichermaßen. Es gibt **keine .bat-Datei mehr**, die war
Windows-only und auf dem Mac nicht lauffähig.

    <python> scripts/transkribieren.py "<workspace>/audio_temp.mp3" "~~elevenlabs-api-key" --groq-key "~~groq-api-key" -o "<workspace>/transkript.json"

(`<python>` = `python` unter Windows, meist `python3` auf macOS/Linux.)

Das Script nimmt **Groq zuerst** und weicht bei Fehlern automatisch auf
ElevenLabs aus; unersetzte `~~`-Platzhalter erkennt es selbst als „nicht
gesetzt". Die Ausgabe hat bei beiden Diensten dasselbe Format — für alle
weiteren Schritte ist der Dienst egal.

Optionen: `--sprache de` (Standard), `--modell scribe_v1` (nur für die
ElevenLabs-Rückfallebene). Die Keys können alternativ über die
Umgebungsvariablen `GROQ_API_KEY` / `ELEVENLABS_API_KEY` kommen.

Das Script schreibt direkt ans Ziel, meldet die Anzahl der Wortmarken und
erklärt Fehler verständlich (abgelehnter Key, aufgebrauchtes Guthaben, keine
Verbindung). Kommen **0 Wortmarken**, ist der Schnitt nicht möglich — dann
prüfen, ob die Tonspur überhaupt Sprache enthält.

Der User muss dabei nichts tun und nichts anklicken — Claude startet das
Script und wartet auf die Rückmeldung.

---

## Schritt 5: Transkript prüfen (nur Modus B)

```bash
python3 -c "import json; d=json.load(open('PFAD/transkript.json')); print('OK', len(d.get('words',[])), 'Woerter')"
```

Falls die Datei fehlt oder ungültig ist: Nutzer bitten das Skript erneut auszuführen.
Falls das JSON abgeschnitten ist (häufig bei langen Videos): Das letzte vollständige Wort-Objekt finden und das JSON reparieren:

```python
with open('PFAD/transkript.json') as f:
    raw = f.read()
last = raw.rfind('},{"text"')
if last > 0:
    raw = raw[:last+1] + ']}'
import json
data = json.loads(raw)
```

---

## Schritt 6a: Regelbasierte Schnittanalyse (nur Modus B)

```python
import json

with open('PFAD/transkript.json') as f:
    data = json.load(f)

words = data.get('words', [])
cuts = []

# Füllwörter
filler = {'äh', 'ähm', 'äh,', 'ähm,', 'äh.', 'ähm.', 'äh?', 'ähm?'}
for i, w in enumerate(words):
    if w.get('type') == 'word' and w.get('text', '').lower().strip('.,!?') in filler:
        prev_end = words[i-1].get('end', w['start']) if i > 0 else w['start']
        next_start = words[i+1].get('start', w['end']) if i < len(words)-1 else w['end']
        cuts.append((prev_end, next_start, 'Füllwort: ' + w['text']))

# Lange Pausen > 2s
for i in range(len(words)-1):
    w1, w2 = words[i], words[i+1]
    if w1.get('type') == 'word' and w2.get('type') == 'word':
        gap = w2.get('start', 0) - w1.get('end', 0)
        if gap > 2.0:
            cuts.append((w1.get('end', 0) + 0.3, w2.get('start', 0) - 0.2, f'Pause {gap:.1f}s'))

# Anfangsstille
real_words = [w for w in words if w.get('type') == 'word']
if real_words and real_words[0].get('start', 0) > 0.5:
    cuts.append((0, real_words[0]['start'] - 0.2, 'Anfangsstille'))

# Endstille
if real_words:
    cuts.append((real_words[-1].get('end', 0) + 0.5, 9999, 'Endstille'))

cuts.sort()
print(json.dumps(cuts))
```

---

## Schritt 6b: Tiefe KI-Analyse (nur Modus B)

Dies ist der wichtigste Schritt. Lies das **gesamte** Transkript und analysiere
es mit vollem Sprachverständnis. Kein regelbasiertes Denken – verstehe, was der
Sprecher sagen wollte, und erkenne wo das Video nicht perfekt klingt.

**Token-Spar-Architektur (Qualität bleibt identisch):** Du liest weiterhin
jedes gesprochene Wort — aber als kompakten Fließtext mit sparsamen
Zeit-Ankern, NICHT als Wort-für-Wort-Liste mit Timestamps (die kostet ~5×
mehr Tokens, ohne Informationsgewinn fürs Verstehen). Die exakten
Schnitt-Zeitstempel liefert danach ein Script per Wort-Lookup.

Erstelle den kompakten Fließtext (ein Zeit-Anker ca. alle 15 Wörter):

```bash
python3 -c "
import json
with open('PFAD/transkript.json') as f:
    data = json.load(f)
words = [w for w in data.get('words', []) if w.get('type') == 'word']
out, line = [], []
for i, w in enumerate(words):
    if i % 15 == 0:
        out.append(' '.join(line)); line = []
        line.append(f'[{w[\"start\"]:.0f}s]')
    line.append(w['text'])
out.append(' '.join(line))
print('\n'.join(out).strip())
"
```

Lies die komplette Ausgabe. Analysiere dann auf folgende Muster:

### 1. Verbale Fehlersignale — höchste Priorität

Der Sprecher signalisiert selbst, dass er einen Fehler gemacht hat. Das sind die eindeutigsten Schnittmarken überhaupt.

Erkenne Signalwörter und -sätze wie:
- Flüche/Ausrufe: "fuck", "shit", "mist", "scheiße", "verdammt", "ach Gott"
- Explizite Korrekturen: "nein warte", "moment", "ich mein", "also nochmal", "ich hab mich versprochen", "von vorne"
- Abbruch-Signale: "ähm nein", "warte mal", "stopp"

**Was zu schneiden ist:** Nicht nur das Signalwort selbst, sondern alles ab dem Beginn des fehlerhaften Inhalts, der das Signal ausgelöst hat – bis zum Punkt, wo der Sprecher sauber neu ansetzt. Das Signal selbst fliegt mit raus.

Beispiel: "...ich hätte jetzt gerne ach fuck, jetzt habe ich mich versprochen, also nochmal: ich möchte dir zeigen..."
→ Finde den Beginn von "ich hätte jetzt gerne" (das ist der Fehler-Satz)
→ Schneide von dort bis nach "also nochmal:" 
→ Ergebnis: "...ich möchte dir zeigen..."

### 2. Versprecher ohne verbales Signal

Der Sprecher macht einen Fehler, signalisiert ihn aber nicht explizit.

Erkenne:
- Satzabbruch mitten im Gedanken, dann Neustart
- Falsches Wort, direkt korrigiert ("das ist ein- also das ist eine App")
- Direkte Wortwiederholungen ("ich ich", "das das")

**PFLICHTPRÜFUNG nach jedem Versprecher-Cut:** Die 5 Wörter vor und nach dem Schnitt laut durchlesen. Kommen dieselben Wörter doppelt vor? → Cut-Ende verschieben, bis die Doppelung weg ist.

Beispiel Fehler: Satz bricht nach "Das hier ist jetzt eben" ab, Neustart: "das hier ist jetzt eben mein Hook-Generator."
- Falscher Cut: endet vor "das" → Ergebnis: "Das hier ist jetzt eben das hier ist jetzt eben mein Hook-Generator." ✗
- Richtiger Cut: endet nach "eben" im zweiten Anlauf → Ergebnis: "Das hier ist jetzt eben mein Hook-Generator." ✓

### 3. Doppelte Erklärungen

Dieselbe Information wird zweimal erklärt, auch wenn die Formulierung unterschiedlich ist. Behalte die klarere, vollständigere Version. Schneide die schwächere.

Typische Signale vor der Wiederholung: "also nochmal", "das heißt", "oder anders gesagt", "kurz zusammengefasst".

Nicht schneiden: bewusste Zusammenfassungen am Ende eines Abschnitts, Beispiele die eine Erklärung vertiefen.

### 4. Fließtext-Prüfung am Ende

Nachdem alle Cuts identifiziert sind: Lies den verbleibenden Text durch, als wäre es ein geschriebenes Skript. Klingt es flüssig und professionell? Gibt es noch Stellen die holprig wirken, die du noch nicht markiert hast? Wenn ja, diese ebenfalls als Cut hinzufügen.

### 5. Cuts in exakte Zeitstempel übersetzen (per Script, nicht schätzen!)

Markiere jeden Cut als **exaktes Wort-Zitat**: erste 3–5 Wörter des zu
schneidenden Abschnitts + erste 3–5 Wörter des sauberen Neuanfangs. Übersetze
die Zitate dann per Script in präzise Zeiten — NIEMALS Zeiten aus den
[Ns]-Ankern schätzen:

```bash
python3 -c "
import json, sys
with open('PFAD/transkript.json') as f:
    data = json.load(f)
words = [w for w in data.get('words', []) if w.get('type') == 'word']
texts = [w['text'].lower().strip('.,!?') for w in words]
def find(seq, start_idx=0):
    seq = [s.lower().strip('.,!?') for s in seq]
    for i in range(start_idx, len(texts) - len(seq) + 1):
        if texts[i:i+len(seq)] == seq:
            return i
    return -1
# Beispiel: Cut von Beginn 'ich hätte jetzt gerne' bis vor 'ich möchte dir'
a = find(['ich','hätte','jetzt','gerne'])
b = find(['ich','möchte','dir'], a+1)
print('Cut:', words[a]['start'], '->', words[b]['start'])
"
```

So bleibt die Präzision auf Wort-Ebene (wie zuvor mit der vollen Liste),
aber der Kontext wurde nur mit dem kompakten Fließtext belastet.

---

**Zeige dem Nutzer vor dem Schnitt eine klare Zusammenfassung** aller geplanten Cuts:
- Kategorie (Fehlersignal / Versprecher / Wiederholung / Füllwort / Pause)
- Kurzes Textzitat der betroffenen Stelle (3-5 Wörter)
- Timestamp

Frage ob er einzelne Cuts ablehnen möchte. Passe die Liste an.

---

## Schritt 7: Segmente berechnen

Kombiniere alle Cuts (M