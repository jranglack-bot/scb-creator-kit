# Schnittregeln für Instagram-Kursvideos

## Füllwörter (immer entfernen)
- "äh", "ähm" und alle Varianten mit Interpunktion
- Entferne das Füllwort und die umgebenden Pausen (Luft davor + danach)
- Übergang soll natürlich klingen: 0.05–0.1s Überlappung an Schnittkanten

## Lange Pausen (kürzen auf max. 0.3s)
- Pausen > 2.0s zwischen zwei Wörtern: auf 0.3s reduzieren
- Typische Ursachen: Nutzer schaut auf Bildschirm, sucht nach Worten, Aufnahme-Unterbrechung
- Pausen 0.5–2.0s: belassen (natürliche Sprechpausen)

## Versprecher (mit KI-Analyse erkennen)
Versprecher sind Stellen, wo der Sprecher mitten im Satz abbricht und neu ansetzt.

**Erkennungsmuster:**
- Abgebrochene Wörter direkt gefolgt von Neustart desselben Satzes
  → Beispiel: "Das ist quasi ein- also das ist ein Werkzeug, das..."
  → Schnitt: ab dem Abbruch bis kurz vor dem Neustart
- Direkte Wortwiederholungen ("ich ich", "das das", "und und")
  → Schneide eine Instanz komplett raus
- Satzabbruch + inhaltliche Neuformulierung
  → Beispiel: "Du kannst hier... Also, was du machen kannst ist..."
  → Schneide alles bis zum Neustart raus

**KRITISCHE REGEL – Satz-Neustart mit gleichen Anfangswörtern:**
Wenn der Sprecher einen Satz abbricht und mit denselben Wörtern neu ansetzt, entstehen nach dem Schnitt doppelte Wörter, wenn nur die Pause herausgeschnitten wird.

Falscher Schnitt:
→ "Das hier ist jetzt eben [Pause raus] das hier ist jetzt eben mein Hook-Generator."
→ Ergebnis: "Das hier ist jetzt eben das hier ist jetzt eben mein Hook-Generator." ✗

Richtiger Schnitt – zwei Optionen:
1. Den gesamten ersten Anlauf entfernen, nur die vollständige zweite Version behalten:
   → Cut: von Beginn des ersten Anlaufs bis Beginn des zweiten Anlaufs
   → Ergebnis: "...vorheriger Satz. das hier ist jetzt eben mein Hook-Generator." ✓

2. Den ersten Anlauf bis zur letzten gemeinsamen Stelle behalten, dann die Wiederholung im zweiten Anlauf überspringen:
   → Cut: von Ende des ersten Anlaufs bis nach den wiederholten Wörtern im zweiten Anlauf
   → Ergebnis: "Das hier ist jetzt eben mein Hook-Generator." ✓

**Prüfschritt nach jedem Versprecher-Cut:** Lies die Wörter direkt vor und nach dem Schnitt laut durch. Kommen dieselben Wörter doppelt vor? Dann ist der Cut-Punkt falsch — nachjustieren.

**Was KEIN Versprecher ist:**
- Bewusste Wiederholungen zur Betonung ("sehr, sehr gut")
- Umgangssprache ("son bisschen", "halt", "irgendwie") – das gehört zum Stil
- Kurze Denkpausen mit "also" oder "genau" – nur wenn wirklich störend

## Doppelte Erklärungen (mit KI-Analyse erkennen)
Stellen, wo dasselbe Konzept oder dieselbe Information zweimal erklärt wird.

**Erkennungsmuster:**
- Erste Erklärung → kurze Pause oder Überleitung → inhaltlich identische zweite Erklärung
- Typische Überleitungen vor Wiederholung: "also nochmal", "das heißt", "oder anders gesagt", "kurz zusammengefasst" (wenn danach inhaltlich dasselbe kommt)
- Selbe Handlungsanweisung zweimal in leicht abgewandelter Form

**Was KEINE Wiederholung ist:**
- Die bewusste Zusammenfassung am Ende eines Abschnitts – die gehört zur Didaktik
- Ein Beispiel, das eine vorher abstrakt erklärte Sache konkret macht
- Dieselbe Aussage mit einem neuen Detail, das vorher nicht da war
- Der Rückbezug auf etwas Früheres als Überleitung ("weißt du noch, der Hook von eben")

**Welche Version bleibt stehen:**
Die klarere und vollständigere – nicht automatisch die erste. Prüfe:
1. Welche Version nennt alle nötigen Details?
2. Welche ist flüssiger gesprochen, ohne Stocken?
3. Passt der Anschluss an den Satz davor und danach noch?

Im Zweifel die zweite behalten: der Sprecher hat meist deshalb wiederholt,
weil ihm der erste Anlauf nicht gefiel.

## Verbale Fehlersignale (höchste Priorität)
Der Sprecher sagt selbst, dass er sich verhauen hat. Das sind die
eindeutigsten Schnittmarken überhaupt.

**Signalwörter:**
- Flüche und Ausrufe: "fuck", "shit", "mist", "scheiße", "verdammt", "ach Gott"
- Explizite Korrekturen: "nein warte", "moment", "ich mein", "also nochmal",
  "ich hab mich versprochen", "von vorne"
- Abbruch-Signale: "ähm nein", "warte mal", "stopp"

**Wichtig:** Das Signal markiert das ENDE des Fehlers, nicht den Anfang.
Geschnitten wird ab dem Beginn des fehlerhaften Inhalts bis dorthin, wo der
Sprecher sauber neu ansetzt. Das Signalwort selbst fliegt mit raus.

## Anfang und Ende
- **Anfangsstille:** alles vor dem ersten Wort weg, 0.2s Luft davor lassen
- **Endstille:** alles nach dem letzten Wort weg, 0.5s Luft danach lassen
- Beides fast immer vorhanden: Aufnahme läuft vor dem Sprechen an und nach dem
  letzten Satz weiter, bis der Nutzer den Knopf findet

## Grundsätze für jeden Schnitt
1. **Im Zweifel drin lassen.** Ein Schnitt zu viel zerstört den Redefluss,
   ein Füllwort zu viel merkt niemand.
2. **Nie mitten im Wort schneiden.** Cut-Grenzen liegen immer zwischen zwei
   Wörtern, sonst hört man einen abgehackten Laut.
3. **Den Ton entscheiden lassen, nicht das Bild.** Bei Sprechvideos fällt ein
   holpriger Ton sofort auf, ein Sprung im Bild kaum.
4. **Nach dem Schnitt gegenlesen.** Der verbleibende Text muss sich wie ein
   geschriebenes Skript lesen lassen.
5. **Nicht glattbügeln.** Umgangssprache, Tempo und kleine Unregelmäßigkeiten
   sind der Stil. Weg soll nur, was nach Fehler klingt.
