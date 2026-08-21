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

### Erster Schritt: Hilfsprogramm herunterladen und installieren

Beim ersten Öffnen des **Code**-Tabs sagt Claude dir, dass ihm ein
Hilfsprogramm fehlt. Solange das nicht installiert ist, kannst du dort
**keine Nachricht abschicken** — auf beiden Systemen.

Das ist eine **richtige Installation mit Download**, kein schneller
Klick. Plan dafür Zeit ein und lass den Rechner am Strom:

| | Claude verlangt | Download | Dauer |
|---|---|---|---|
| **Windows** | **Git für Windows** | ca. 65 MB | 2–5 Minuten |
| **Mac** | **Xcode Command Line Tools** | ca. 700 MB (belegt danach ~1,2 GB) | 5–15 Minuten, je nach Internet |

**Windows — so geht's:** Auf den Knopf **„Download Git for Windows"**
klicken (oder [git-scm.com/download/win](https://git-scm.com/download/win)),
die heruntergeladene Datei im Downloads-Ordner doppelklicken, dann im
Installer **immer „Next"** und zum Schluss **„Install"**. Nichts
umstellen, die Voreinstellungen passen. Am Ende „Finish".

**Mac — so geht's:** Es erscheint ein Fenster, dort auf **„Installieren"**
klicken und den Lizenzbedingungen zustimmen. Dann lädt macOS im
Hintergrund — das dauert und sieht zwischendurch aus, als würde nichts
passieren. Fenster offen lassen, nicht abbrechen.

**Danach auf beiden Systemen: Claude komplett schließen und neu öffnen.**
Dieser Schritt kommt nie wieder.

**Wenn es hakt:**
- *Windows, „Zugriff verweigert":* Du bist kein Administrator und es ist
  noch ein altes Git registriert. In den Windows-Einstellungen unter
  **Apps** das alte „Git" deinstallieren, dann erneut starten.
- *Mac, es erscheint kein Fenster:* Sag Claude „Führe
  `xcode-select --install` aus" — dann kommt es.

---|---|---|
| **Windows** | „Git Bash is required" / du musst **Git** installieren | Knopf **„Download Git for Windows"** anklicken (oder [git-scm.com/download/win](https://git-scm.com/download/win)), Installer starten, immer **„Next"**, zum Schluss **„Install"** |
| **Mac** | du musst die **Xcode Command Line Tools** installieren | Im aufgehenden Fenster auf **„Installieren"** klicken und warten (einige Minuten). Kein Passwort, keine Webseite |

**Danach Claude einmal komplett schließen und neu öffnen.** Das war's —
dieser Schritt kommt nie wieder.

**Windows-Sonderfall:** Bist du auf deinem PC kein Administrator
(Firmen- oder Familiengerät) und der Installer meldet „Zugriff
verweigert", ist meist noch ein altes Git registriert: in den
Windows-Einstellungen unter **Apps** das alte „Git" deinstallieren, dann
den Installer erneut starten.

**Mac-Sonderfall:** Kommt gar kein Fenster, sag Claude:
„Führe `xcode-select --install` aus" — dann erscheint es.

---

## Schritt 1: Diese Nachricht an Claude schicken

Kopier den folgenden Text **komplett** und schick ihn Claude im Code-Tab —
genau dort, wo du ihm auch „Hallo" schreiben würdest:

> **Installiere bitte das SCB Creator Kit:**
> **1. Prüfe mit `claude --version`, ob der Befehl `claude` existiert.
> Falls nicht, installiere zuerst Claude Code mit dem offiziellen
> Installer — Mac/Linux: `curl -fsSL https://claude.ai/install.sh | bash`
> — Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`.
> Er braucht kein Admin-Passwort. Findet die Shell den Befehl danach
> nicht, nutze den vollen Pfad `~/.local/bin/claude`.**
> **2. `claude plugin marketplace add jranglack-bot/scb-creator-kit`**
> **3. `claude plugin install scb-creator-kit@scb-creator-kit`**
> **4. Verweigert dir der Berechtigungs-Modus das Ausführen der
> claude-plugin-Befehle: Gib mir genau diese Befehle als anklickbare
> Codeblöcke und sag mir, dass ich sie der Reihe nach anklicken soll —
> als mein Klick laufen sie. Auf Windows stelle dabei jedem Befehl
> `cmd /c` voran (`cmd /c claude plugin …`) — das umgeht die
> PowerShell-Skriptsperre, an der eine per npm installierte Claude-CLI
> sonst scheitert. Schlag mir in der Desktop-App NIEMALS
> /plugin-Chat-Befehle vor, die existieren nur im Terminal-Claude.**
> **5. Wichtig: Ich kenne mich mit Terminal und Technik nicht aus. Führe
> alles selbst aus und erkläre mir nur kurz und in einfachen Worten, was
> du gerade tust. Wenn ein Schritt fehlschlägt, lies die Fehlermeldung,
> such die Ursache und behebe sie selbstständig — probiere sinnvolle
> Alternativen, bevor du mich um Hilfe bittest. Nur wenn es wirklich
> ohne mich nicht geht (z. B. eine Passwort-Eingabe oder ein Klick), sag
> mir Klick für Klick, was ich tun soll.**

Claude führt die Befehle selbst aus — das ist der offizielle
Installationsweg über Claudes eigene Plugin-Verwaltung. Falls
Berechtigungsabfragen erscheinen („Darf ich diesen Befehl ausführen?"),
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

**Claude kommt mit „Befehl nicht gefunden" nicht weiter.**
Dann einmal selbst ins Terminal:

- **Mac:** `Cmd + Leertaste` drücken, „Terminal" tippen, Enter.
- **Windows:** Startmenü, „PowerShell" tippen, Enter.

**Mac** — diese drei Zeilen nacheinander einfügen (Enter nach jeder,
die erste dauert 1–2 Minuten):

```
curl -fsSL https://claude.ai/install.sh | bash
claude plugin marketplace add jranglack-bot/scb-creator-kit
claude plugin install scb-creator-kit@scb-creator-kit
```

**Windows (PowerShell)** — diese drei Zeilen (das `cmd /c` davor ist
Absicht — es umgeht die Windows-Skriptsperre, falls Claude Code über
npm installiert wurde):

```
irm https://claude.ai/install.ps1 | iex
cmd /c claude plugin marketplace add jranglack-bot/scb-creator-kit
cmd /c claude plugin install scb-creator-kit@scb-creator-kit
```

Meldet das Terminal nach der ersten Zeile „command not found: claude",
das Terminalfenster einmal schließen, neu öffnen und die letzten zwei
Zeilen wiederholen. Danach weiter mit Schritt 2 (Neustart).

**„git not found" bei `claude plugin marketplace add`?**
In der Desktop-App kann das nicht vorkommen — dort läuft ohne Git gar
nichts. Im **Terminal** aber schon: Dort startet Claude Code auch ohne
Git, und erst der Marketplace-Befehl stolpert darüber. Dann sag Claude:

> Der Befehl meldet, dass git fehlt. Installier es bitte selbst ohne
> Adminrechte — Windows: MinGit-ZIP aus dem neuesten
> git-for-windows-Release nach `%LOCALAPPDATA%\scb-git` entpacken und
> `\cmd` in meinen Benutzer-PATH eintragen. Mac: `xcode-select --install`
> ausführen und mich im Fenster auf „Installieren" klicken lassen.
> Danach den Befehl wiederholen.

**Du nutzt Claude Code im Terminal statt der Desktop-App?**
Dann funktioniert alles genauso — Nachricht aus Schritt 1 in die
Claude-Eingabe. Oder du tippst diese zwei Zeilen direkt in die
Chat-Eingabe (sie beginnen mit `/` und sind Chat-Befehle, keine
Shell-Befehle):

```
/plugin marketplace add jranglack-bot/scb-creator-kit
/plugin install scb-creator-kit@scb-creator-kit
```

**„Muss ich mich im Terminal erst anmelden?"**
Nein. Die Installations-Befehle (`claude plugin …`) funktionieren ohne
Anmeldung, und in der Desktop-App bist du über deinen normalen App-Login
schon angemeldet. Eine Terminal-Anmeldung braucht nur, wer Claude Code
**im Terminal als Chat** benutzen will: dort `claude` eintippen, dann
`/login` — es öffnet sich der Browser, dort mit dem Claude-Konto
anmelden und die Freigabe bestätigen.

**Der Setup-Assistent startet nach dem Neustart nicht?**
Schick Claude diese Nachricht — er prüft und repariert das selbst:

> Das SCB Creator Kit scheint nicht geladen zu sein. Prüfe bitte mit
> `claude plugin list`, ob es installiert ist, finde die Ursache und
> behebe sie selbstständig. Ich kenne mich mit Technik nicht aus —
> erkläre mir nur, was du tust.

Danach Claude noch einmal neu starten. Klemmt es immer noch, schick
deinem SCB-Ansprechpartner einen Screenshot von Claudes Antwort.

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
