# SCB Creator Kit installieren

**Dauer: etwa 1 Minute. Kein Download, kein Terminal — du schickst Claude
eine Nachricht, den Rest macht er selbst.**

---

## Was du vorher brauchst

Die **Claude Desktop-App** auf deinem Rechner. Falls du sie noch nicht hast:
👉 [claude.ai/download](https://claude.ai/download) — kostenlos, für Windows und Mac.

In der App oben auf den Tab **Code** klicken und einen beliebigen Ordner
wählen (z. B. deinen Dokumente-Ordner). Beim allerersten Mal richtet die App
sich kurz selbst ein — einfach durchklicken.

---

## Schritt 1: Diese Nachricht an Claude schicken

Kopier den folgenden Text **komplett** und schick ihn Claude im Code-Tab —
genau dort, wo du ihm auch „Hallo" schreiben würdest:

> **Installiere bitte das SCB Creator Kit. Führe dazu nacheinander diese
> zwei Befehle aus:**
> **`claude plugin marketplace add jranglack-bot/scb-creator-kit`**
> **`claude plugin install scb-creator-kit@scb-creator-kit`**

Claude führt die Befehle selbst aus — das ist der offizielle
Installationsweg über Claudes eigene Plugin-Verwaltung. Falls eine
Berechtigungsabfrage erscheint („Darf ich diesen Befehl ausführen?"),
einfach bestätigen.

Wenn Claude **„Successfully installed"** (oder „erfolgreich installiert")
meldet, weiter mit Schritt 2.

---

## Schritt 2: Claude neu starten

Claude **einmal komplett schließen und wieder öffnen.**
Neue Plugins werden erst beim Start geladen — ohne Neustart passiert nichts.

---

## Schritt 3: Loslegen

Schreib Claude einfach:

> **Richte das SCB Kit ein**

Startet der Setup-Assistent mit einer Bereichsauswahl → alles gut.
Ab hier führt er dich durch alles. Er fragt nur, was du wirklich nutzen
willst, und richtet den Rest selbst ein.

---

## Wenn etwas nicht klappt

**Claude meldet: „`claude` — Befehl nicht gefunden."**
Sehr selten. Dann einmal selbst ins Terminal:

- **Mac:** `Cmd + Leertaste` drücken, „Terminal" tippen, Enter.
- **Windows:** Startmenü, „PowerShell" tippen, Enter.

Dort diese zwei Zeilen nacheinander einfügen (Enter nach jeder):

```
claude plugin marketplace add jranglack-bot/scb-creator-kit
claude plugin install scb-creator-kit@scb-creator-kit
```

Danach weiter mit Schritt 2 (Neustart).

**Du nutzt Claude Code im Terminal statt der Desktop-App?**
Dann funktioniert alles genauso — Nachricht aus Schritt 1 in die
Claude-Eingabe. Oder du tippst diese zwei Zeilen direkt in die
Chat-Eingabe (sie beginnen mit `/` und sind Chat-Befehle, keine
Shell-Befehle):

```
/plugin marketplace add jranglack-bot/scb-creator-kit
/plugin install scb-creator-kit@scb-creator-kit
```

**Der Setup-Assistent startet nach dem Neustart nicht?**
Schick Claude die Nachricht aus Schritt 1 einfach noch einmal und starte
danach erneut neu. Klemmt es weiter, schick deinem SCB-Ansprechpartner
einen Screenshot von Claudes Antwort.

---

## Update auf eine neue Version

Genauso einfach — schick Claude:

> **Aktualisiere bitte das SCB Creator Kit:**
> **`claude plugin update scb-creator-kit@scb-creator-kit`**

Danach Claude einmal neu starten.

---

## Was danach passiert

Der Setup-Assistent geht mit dir durch:

1. **Python** — wird bei Bedarf automatisch mitinstalliert, du merkst davon nichts
2. **Dein Gedächtnis** — Claude merkt sich in einem eigenen Ordner, wer du bist
3. **Video-Werkzeuge** — Schnitt, Untertitel, Cockpit
4. **Was du sonst willst** — Instagram-Analyse, Auto-Posting, KI-Videos

Alles ist freiwillig. Was du nicht willst, wird übersprungen, und du kannst
den Assistenten jederzeit erneut starten.
