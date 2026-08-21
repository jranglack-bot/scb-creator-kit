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

**Zum Thema Git:** Das Kit braucht im Hintergrund ein Programm namens
Git. **Du musst dich darum nicht kümmern** — fehlt es, installiert Claude
es im nächsten Schritt selbst, in deinen eigenen Benutzerordner: ohne
Adminrechte, ohne Passwort, ohne dass du etwas suchen oder anklicken
musst.

> ⚠️ **Wichtig, falls dir jemand rät, Git von git-scm.com zu holen:**
> Dieser Installer schreibt nach `C:\Program Files` und **braucht
> Adminrechte**. Bist du auf deinem PC kein Administrator (typisch bei
> Firmen- und Familiengeräten), bricht er mit „Zugriff verweigert" ab.
> Der Weg über Claude hat dieses Problem nicht — lass ihn einfach machen.

Auf dem **Mac** ist Git ebenfalls kein eigener Schritt: Fehlt es, öffnet
sich ein Fenster mit einem „Installieren"-Knopf, den du einmal anklickst
(kein Passwort nötig).

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
> **Meldet der Befehl, dass `git` fehlt, installiere es selbst — ohne
> Adminrechte, ohne mich zu fragen:**
> **Windows (PowerShell):**
> **`$a=(irm https://api.github.com/repos/git-for-windows/git/releases/latest).assets|?{$_.name -like 'MinGit*-64-bit.zip'}|select -First 1`**
> **`iwr $a.browser_download_url -OutFile "$env:TEMP\mingit.zip"`**
> **`Expand-Archive "$env:TEMP\mingit.zip" "$env:LOCALAPPDATA\scb-git" -Force`**
> **`$p=[Environment]::GetEnvironmentVariable("Path","User"); [Environment]::SetEnvironmentVariable("Path","$env:LOCALAPPDATA\scb-git\cmd;$p","User"); $env:Path="$env:LOCALAPPDATA\scb-git\cmd;$env:Path"`**
> **(Auf ARM-Windows `MinGit*-arm64.zip` nehmen.) Danach den Befehl aus
> Schritt 2 wiederholen.**
> **Mac: führe `xcode-select --install` aus und bitte mich, im aufgehenden
> Fenster auf „Installieren" zu klicken; danach den Befehl wiederholen.**
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
