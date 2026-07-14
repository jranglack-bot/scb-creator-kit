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

**Was KEINE Wiederholung 