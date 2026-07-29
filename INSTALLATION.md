# SCB Creator Kit installieren

**Dauer: etwa 1 Minute. Du musst nichts können, nichts eintippen, nichts einrichten.**

---

## Was du vorher brauchst

Die **Claude Desktop-App** auf deinem Rechner. Falls du sie noch nicht hast:
👉 [claude.ai/download](https://claude.ai/download) — kostenlos, für Windows und Mac.

---

## Schritt 1: Datei herunterladen

Klick auf diesen Link:

**[⬇️ scb-creator-kit.plugin herunterladen](https://github.com/jranglack-bot/scb-creator-kit/releases/latest/download/scb-creator-kit.plugin)**

Die Datei landet in deinem **Downloads-Ordner** und heißt `scb-creator-kit.plugin`.

---

## Schritt 2: Datei in Claude ziehen

1. Öffne die Claude Desktop-App
2. Starte ein neues Gespräch
3. Zieh die heruntergeladene Datei mit der Maus **in das Chatfenster**
4. Claude fragt, ob du das Plugin installieren willst → **bestätigen**

Das war der ganze technische Teil.

---

## Schritt 3: Loslegen

Schreib Claude einfach:

> **Richte das SCB Kit ein**

Ab hier führt dich der Assistent durch alles. Er fragt nur, was du wirklich
nutzen willst, und richtet den Rest selbst ein.

---

## Wenn etwas nicht klappt

**„Claude sagt, er kann das Plugin nicht installieren."**
Das passiert, wenn du Claude *bittest*, das Plugin zu installieren, oder ihm
den GitHub-Link schickst. So funktioniert es bei niemandem — Claude installiert
keine Plugins. **Du ziehst die Datei selbst ins Fenster**, siehe Schritt 2.

**„Ich finde die Datei nicht."**
Sie liegt im Downloads-Ordner: `scb-creator-kit.plugin`. Falls dein Browser
gefragt hat, wo er sie speichern soll, dort nachsehen.

**„Mein Browser warnt, die Datei sei ungewöhnlich."**
Das sagen Browser bei allen Dateiendungen, die sie nicht kennen. Auf
„Behalten" beziehungsweise „Trotzdem herunterladen" klicken.

**„Ich nutze Claude Code im Terminal, nicht die App."**
Dann tipp diese zwei Zeilen nacheinander dorthin, wo du sonst mit Claude
schreibst:

```
/plugin marketplace add jranglack-bot/scb-creator-kit
/plugin install scb-creator-kit@scb-creator-kit
```

---

## Was danach passiert

Der Setup-Assistent geht mit dir durch:

1. **Python** — wird bei Bedarf automatisch mitinstalliert, du merkst davon nichts
2. **Dein Gedächtnis** — Claude merkt sich in einem eigenen Ordner, wer du bist
3. **Video-Werkzeuge** — Schnitt, Untertitel, Cockpit
4. **Was du sonst willst** — Instagram-Analyse, Auto-Posting, KI-Videos

Alles ist freiwillig. Was du nicht willst, wird übersprungen, und du kannst
den Assistenten jederzeit erneut starten.
