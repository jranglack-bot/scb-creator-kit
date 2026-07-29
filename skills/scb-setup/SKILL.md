---
name: scb-setup
description: >
  Setup-Assistent für das SCB Creator Kit. Führt neue Community-Mitglieder
  Schritt für Schritt durch die Einrichtung: prüft welche Tools und Accounts
  vorhanden sind (Higgsfield, Make, Airtable, Obsidian, ffmpeg, Node.js) und
  richtet nur das ein, was gewünscht ist. Verwende diesen Skill, wenn jemand
  sagt: "richte das SCB Kit ein", "Setup starten", "SCB Setup", "hilf mir bei
  der Einrichtung", "was brauche ich für das Creator Kit", oder direkt nach
  der Installation des Plugins.
---

# SCB Creator Kit — Setup-Assistent

Führe den User freundlich und auf Deutsch durch die Einrichtung. Er ist
wahrscheinlich **kein Techniker** — erkläre alles einfach, ein Schritt nach
dem anderen, und führe technische Befehle selbst aus, statt sie dem User
zuzumuten. Frage nur, was nötig ist.

## Ablauf

### Schritt 1: Begrüßung und Überblick

Begrüße den User und zeige kurz, was das Kit kann:

> Willkommen beim SCB Creator Kit! 🎬 Das steckt drin:
>
> 1. **Obsidian-Gehirn** — Claude merkt sich alles über dich in deinem eigenen Vault
> 2. **Video-Editor** — Videos automatisch schneiden, Untertitel, Musik, Voiceover, Texte — mit Browser-Cockpit und Ein-Klick-Render
> 3. **Content-Recherche** — Profil-Audits und Nischen-Recherche über Apify
> 4. **Auto-Posting** — Reels über Airtable + Make automatisch auf Instagram posten
> 5. **KI-Videos generieren** — Kling 3.0 & Seedance Prompt-Builder + Higgsfield-Anbindung
> 6. **Reel-Wissen** — Safe-Zones und erprobte Hook-Formeln (immer dabei, kein Setup nötig)
>
> Ich richte jetzt mit dir ein, was du davon nutzen willst — du brauchst
> nichts vorzubereiten.

Frage dann (mit AskUserQuestion, multiSelect), welche Bereiche eingerichtet
werden sollen. Richte anschließend NUR die gewählten Bereiche ein, in der
Reihenfolge unten — **das Obsidian-Gedächtnis zuerst**, damit sich Claude ab
der ersten Minute alles merkt.

**Zwei optionale Extras (RTK, /watch) gehören bewusst NICHT ins Setup.**
Sie sind Fremdsoftware, nichts im Kit braucht sie, und sie haben den
Einstieg früher zuverlässig blockiert. Erwähne sie hier nicht. Nur wenn der
User von sich aus danach fragt, siehe den Abschnitt „Optionale Extras" ganz
unten.

### Grundregel für dieses Setup (gilt überall)

> **Die Zielgruppe kann nicht programmieren und will kein Terminal sehen.**
> Wer dieses Kit einrichtet, ist Creator, nicht Entwickler. Jede Antwort, die
> mit „öffne dein Terminal", „führe bitte selbst aus" oder „tippe folgenden
> Befehl" beginnt, ist ein Fehlschlag des Setups.

**Erst erklären, dann fragen, dann selbst ausführen.** Der User trifft genau
eine Entscheidung: ja oder nein. Danach macht Claude die Arbeit.

1. **Vorher erklären**, was konkret passiert — in einfachen Worten: was wird
   geladen, woher, was verändert sich, wie macht man es rückgängig.
2. **Mit AskUserQuestion fragen**, ja oder nein.
3. **Bei Ja: selbst ausführen**, mit dem eigenen Bash/PowerShell-Werkzeug.
   Nicht zurückdelegieren, nicht ein zweites Mal rückversichern. Die
   Berechtigungsabfrage von Claude Code erscheint ohnehin — sie ist die
   Kontrollinstanz, nicht der User als Abtipper.
4. **Bei Nein: sofort weiter.** Kein Nachhaken, kein Überreden.
5. **Nur bei echtem Fehler** (Firewall, Rechte, kein Netz): Grund
   verständlich erklären, später nochmal anbieten, weitermachen.

**Installationen laufen über die mitgelieferten Scripts in `scripts/`**, nicht
über selbst zusammengebaute Befehlsketten. Das ist im ganzen Kit so (siehe
`pro-look-editing`: die Scripts machen die Arbeit, Claude trifft nur
Entscheidungen). Ein Script ist ein Aufruf, getestet und nachvollziehbar.

Ordner anlegen, `winget install ffmpeg` und Prüfbefehle wie `ffmpeg -version`
brauchen keine eigene Zustimmungsfrage, die laufen einfach mit.

### Schritt 2: Python sicherstellen (Fundament, IMMER zuerst)

**Ohne Python läuft kein einziges Script des Kits** — nicht der Video-Schnitt,
nicht das Cockpit, nicht die Karussells. Deshalb steht das ganz am Anfang und
wird nicht abgefragt, sondern still erledigt.

Dieser eine Schritt darf **nicht** über ein Python-Script laufen (Henne und Ei).
Claude führt die Befehle direkt aus.

**1. Prüfen** — welcher Aufruf funktioniert:

    python --version
    python3 --version

> ⚠️ **Wichtig für den Rest des Setups:** Unter Windows heißt der Befehl
> meist `python`, auf macOS und Linux fast immer `python3`. **Merke dir,
> welcher hier funktioniert hat, und benutze ab dann durchgehend genau
> diesen** für alle Script-Aufrufe des Kits.
>
> Windows-Falle: Wenn `python --version` nichts ausgibt oder den Microsoft
> Store öffnet, ist Python NICHT installiert — das ist nur ein Platzhalter
> von Windows. Dann behandeln wie „fehlt".

**2. Fehlt Python**, kurz erklären („Für die Video- und Bildfunktionen brauche
ich Python. Kostenlos und offiziell, ich installiere es eben.") und selbst
installieren:

- Windows: `winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements`
- macOS: `brew install python` — fehlt Homebrew, stattdessen `xcode-select --install` anbieten (bringt python3 mit)
- Linux: `sudo apt-get install -y python3` bzw. `sudo dnf install -y python3`

**3. Danach erneut prüfen.** Unter Windows greift der Suchpfad oft erst in
einer neuen Sitzung — falls der Aufruf noch fehlschlägt, dem User sagen, dass
er Claude Code einmal neu startet, und dort weitermachen.

Erst wenn Python läuft, mit dem nächsten Schritt fortfahren.

### Schritt 3: Obsidian-Gehirn (direkt danach)

**Warum so früh:** Alles, was der User ab jetzt erzählt (Zielgruppe, Angebot,
Keyword, Schreibstil), wird sofort dauerhaft gespeichert — und jeder spätere
Setup-Schritt und jeder künftige Auftrag baut darauf auf.

Sag: „Bevor wir Technik installieren, richten wir Claudes Gedächtnis ein —
so merke ich mir ab sofort alles über dich und deinen Content. Nutzt du
schon Obsidian (kostenlose Notiz-App)?"

- **Nein, kenne ich nicht** → Kurz erklären: kostenlos von
  https://obsidian.md herunterladen, installieren, beim ersten Start einen
  neuen Vault (= Ordner) anlegen, empfohlener Name: „Claude Gehirn". Warten,
  bis das erledigt ist.
- **Ja** → Nach dem Vault-Pfad fragen (oder auf der Platte nach `.obsidian`-
  Ordnern suchen und den Fund bestätigen lassen).

Übergib dann an den Skill `obsidian-gehirn`: Ordnerstruktur anlegen
(00 Kontext / 01 Inbox / 02 Claude Memory / 03 Hooks) und die automatische
Memory-Spiegelung einrichten.

**Kennenlern-Interview (direkt im Anschluss):** Stelle vier kurze Fragen,
eine nach der anderen, und lege jede Antwort sofort in die passende Notiz
unter `00 Kontext/` ab (zusätzlich als Memory merken):

1. „Wer ist deine Zielgruppe — für wen machst du Content?" → `ICP.md`
2. „Was bietest du an bzw. wohin willst du deine Follower führen?" → `Angebote.md`
3. „Hast du schon ein Kommentar-Keyword für deinen DM-Funnel (das Wort, das
   Leute unter deine Reels schreiben)?" → `Angebote.md` — falls nein, das
   klärt später der Skill `reel-hooks` beim ersten Sales-Reel.
4. „Beschreib deinen Schreibstil in 2–3 Sätzen — oder schick mir 1–2
   Beispieltexte von dir (Captions, Posts)." → `Schreibstil.md`

Kann der User etwas noch nicht beantworten: überspringen und sagen, dass
Claude die Notiz später beim Arbeiten von selbst füllt. Will der User KEIN
Obsidian: weiter ohne — alles funktioniert, nur ohne sichtbares Gedächtnis;
das Interview trotzdem anbieten und die Antworten als normale Memories sichern.

### Schritt 4: Basis-Werkzeuge prüfen (immer)

Prüfe still im Hintergrund und berichte das Ergebnis in einfacher Sprache:

```powershell
# Node.js / npm (für Higgsfield-CLI)
node --version; npm --version
# ffmpeg / ffprobe (für Video-Schnitt)
ffmpeg -version; ffprobe -version
```

Fehlt etwas, kurz fragen („Darf ich ffmpeg installieren? Kostenlos und
offiziell.") und dann **selbst** installieren — das Script kennt Windows,
macOS und Linux:

    <python> scripts/install_tools.py ffmpeg node

(`<python>` = der Aufruf, der in Schritt 2 funktioniert hat.)

- **Node.js** nur nötig, wenn Higgsfield gewählt wurde
- **ffmpeg** nur nötig für Video-Schnitt und Posting
- Prüfen ohne zu installieren: `<python> scripts/install_tools.py --pruefen ffmpeg node`

Endet das Script mit **Exit 2**, fehlt auf einem Mac Homebrew. Dann dem User
erklären, dass das der übliche Weg für solche Programme auf dem Mac ist, den
vom Script ausgegebenen offiziellen Befehl anbieten, nach seinem Ja selbst
ausführen und das Script danach erneut aufrufen.

Nach Installationen unter Windows: neue Sitzung nötig, damit der Suchpfad greift.

### Schritt 5: Video-Editor — Schneiden, Cockpit & Untertitel

Das Herzstück des Kits: automatischer Schnitt, das Browser-Cockpit
(Timeline, Untertitel, Musik, Voiceover, Texte, Zoom — alles ohne
Token-Verbrauch) und der Ein-Klick-Render (unter Windows als Doppelklick-
Datei, auf macOS und Linux auf Zuruf durch Claude). Das
Cockpit öffnet Claude auf Zuruf; es spielt das Video und überspringt
Schnitte live. Kein Server, kein Umschalten. Gespeichert wird direkt in die
projekt.json (Datei beim ersten Speichern einmal wählen).

Benötigt: ffmpeg (Schritt 4) + einen **ElevenLabs-API-Key** (kostenloses
Konto reicht) für die Transkription. So bekommt ihn der User — Schritt für
Schritt hinführen:

1. **https://elevenlabs.io** öffnen → kostenloses Konto erstellen
2. Oben rechts aufs **Profilbild** klicken → **API Keys**
3. **Create Key** → Key kopieren und Claude im Chat geben

Der Key wird beim ersten Aufruf des Skills `video-schneiden` gespeichert und
gilt danach auch für `untertitel-und-text` (Untertitel + Hook-Texte). Nie den
Key im Chat wiederholen oder in Notizen ablegen.

**Sound-Effekte (optional erwähnen):** Das Kit bringt sechs lizenzfreie
Basis-Sounds mit (Whoosh, Klick, Pop …). Wer hochwertigere will: kostenlos
bei **pixabay.com/sound-effects** oder **mixkit.co/free-sound-effects**
Favoriten laden, in einen Ordner legen und den Pfad in Obsidian
`00 Kontext/Branding.md` als `SFX-Bibliothek: <pfad>` notieren. Wichtig
erklären: Claude baut Sounds NIE automatisch ein — es fragt immer erst.

**Hintergrundmusik (optional erwähnen):** Für Musikbetten mit Auto-Ducking
eine **Musik-Bibliothek** anlegen: Ordner mit Stimmungs-Unterordnern
(`energetisch/`, `ruhig/`, `emotional/`, `episch/`, `froehlich/`),
kostenlose Tracks von **pixabay.com/music** (keine Namensnennung nötig,
Stimmungs-Suche) hineinsortieren, Pfad in Branding.md als
`Musik-Bibliothek: <pfad>` notieren. Claude schlägt dann je nach
Reel-Stimmung passende Musik vor — aber baut sie nie ungefragt ein.
Chart-/Trend-Musik dagegen nie einbrennen, sondern beim Posten in der
Instagram-App hinzufügen (nur dort lizenziert); bei Verkaufs-/Werbe-Reels
warnt Claude automatisch und empfiehlt lizenzfreie Musik.

**Animierte Overlays (optional erwähnen):** Für Motion-Elemente (animierte
Pfeile, Follow-Buttons, Konfetti) eine **Overlay-Bibliothek** anlegen:
Green-Screen-Clips kostenlos und ohne Account von **pixabay.com/videos**
(Suche „green screen arrow/subscribe/confetti") laden, Ordnerpfad in
Branding.md als `Overlay-Bibliothek: <pfad>` notieren — Claude legt sie
per Chromakey übers Video, aber nie ungefragt.

### Schritt 6: Instagram-Audit & Recherche (Apify)

Frage: „Willst du Profil-Audits und Nischen-Recherche nutzen? Dafür brauchst
du ein kostenloses Apify-Konto (dein Monats-Freiguthaben reicht für hunderte
Profil-Abrufe)."

1. Konto auf **https://apify.com** erstellen (Free-Plan)
2. Mit Claude verbinden: claude.ai → Einstellungen → **Connectoren** → Apify.
   Alternativ per Token: **console.apify.com** → Settings →
   **API & Integrations** → Personal API Token kopieren.
3. Erkläre die Budget-Regel: Claude nennt vor jedem Apify-Lauf die geschätzten
   Kosten und wartet auf ein Okay — so bleibt es im Freiguthaben.

### Schritt 7: Auto-Posting (Make + Airtable)

Frage: „Willst du Reels automatisch auf Instagram posten lassen? Dafür
brauchst du drei kostenlose/günstige Accounts: **Airtable** (Datenbank),
**Make.com** (Automatisierung) und ein **Instagram Business-/Creator-Konto**."

Gehe die drei Konten einzeln durch und führe jeweils hin:

**Airtable:**
1. Konto auf **https://airtable.com** erstellen (Free reicht)
2. Mit Claude verbinden: claude.ai → Einstellungen → **Connectoren** →
   Airtable → anmelden (macht der User selbst im Browser)
3. Für Video-Uploads per Script zusätzlich einen **Personal Access Token**:
   **https://airtable.com/create/tokens** → Token erstellen mit den Scopes
   `data.records:read` + `data.records:write`, **nur für die Reel-Base**
   freigeben. Erklären: Token = Schlüssel, gehört in eine lokale Datei,
   niemals in Notizen oder den Chat.

**Make.com:**
1. Konto auf **https://www.make.com** erstellen (Free: 1.000 Operationen/Monat
   — reicht für 2 Posts am Tag)
2. Mit Claude verbinden: claude.ai → Einstellungen → **Connectoren** → Make
3. In Make selbst wird später das Posting-Szenario gebaut — das übernimmt der
   Skill `reel-posting` Schritt für Schritt (inkl. Instagram-Verbindung).

**Instagram:** Business- oder Creator-Konto nötig (in der Instagram-App:
Einstellungen → Konto → auf professionelles Konto wechseln) und mit einer
Facebook-Seite verknüpft — das verlangt die Instagram-API.

### Schritt 8: Higgsfield (KI-Bilder & -Videos)

Frage zuerst: „Hast du einen Higgsfield-Account? (higgsfield.ai — dort laufen
die KI-Video-Generierungen)"

- **Nein** → Erkläre: Account auf https://higgsfield.ai erstellen (es gibt
  einen Free-Plan zum Testen). Warte, bis der User bereit ist.
- **Ja** → Installiere die CLI und verbinde den Account:

```powershell
npm install -g @higgsfield/cli
higgsfield auth login
```

`higgsfield auth login` öffnet den Browser — der User loggt sich dort selbst
ein (niemals nach Passwort fragen!). Prüfe danach mit `higgsfield auth status`.

Erkläre zum Abschluss die zwei wichtigsten Regeln aus der Community-Praxis:
- **Nano Banana Pro** (`nano_banana_2`) für Bilder nutzen — auf vielen Plänen
  unlimited, spart Credits.
- Vor jeder Generierung zeigt Claude **Idee + Prompt + Modell** und wartet auf
  ein Okay — jede Generierung kostet Credits.

### Schritt 9: GitHub verbinden (optional, zukunftssicher)

Frage: „Willst du dein Claude Code mit GitHub verbinden? Brauchst du nicht
zwingend — aber dann kann Claude dir künftig weitere Tools und Updates aus
GitHub mit einem Satz installieren."

Wenn ja:
1. Konto (falls noch keins): **https://github.com/signup** — kostenlos,
   2 Minuten. Der User erstellt es selbst im Browser.
2. GitHub-CLI installieren — Claude führt das selbst aus:
   `<python> scripts/install_tools.py gh` (danach neue Sitzung nötig).
3. Verbinden: Öffne für den User ein sichtbares Terminal-Fenster mit
   `gh auth login` — er wählt „GitHub.com" → „HTTPS" → „Login with a web
   browser" und loggt sich selbst im Browser ein. Claude gibt niemals
   Passwörter oder Tokens ein.
4. Prüfen: `gh auth status` → „Logged in" = fertig.

### Schritt 10: Abschluss

Fasse zusammen, was eingerichtet wurde und was der User jetzt sagen kann:

> Fertig! 🎉 So nutzt du dein Kit — sag einfach:
> - „Bau mir einen Kling-Prompt" → Prompt-Builder startet
> - „Schneide mein Video" → automatischer Schnitt
> - „Mach Untertitel drauf" → sprach-synchrone Untertitel in der Safe-Zone
> - „Schreib mir ein Reel" → Hook-Formeln & Reel-Struktur (fragt nach deinem Keyword)
> - „Mach ein Audit von meinem Profil" → Apify-Analyse + Verbesserungen
> - „Richte mein Auto-Posting ein" → Airtable + Make Aufbau
> - „Merk dir: …" → landet in deinem Obsidian-Gehirn

Wenn etwas übersprungen wurde: erwähnen, dass `scb-setup` jederzeit erneut
gestartet werden kann.

## Optionale Extras (NICHT im Setup anbieten)

Zwei Fremdprogramme, die das Kit **nicht** braucht. Sie waren früher Teil des
Setups und haben dort den Einstieg blockiert. Deshalb: **von sich aus nie
vorschlagen.** Nur einrichten, wenn der User ausdrücklich danach fragt.

Wenn er fragt, gilt der übliche Ablauf: erklären, mit AskUserQuestion fragen,
bei Ja selbst ausführen, bei Nein sofort weiter.

**RTK (Token-Sparer)** — Quelle: https://github.com/rtk-ai/rtk
Vorher erklären: Ein kleines Programm wird von der offiziellen Projektseite
geladen und ein Hook eingerichtet, der Befehle wie `git status` im
Hintergrund zu `rtk git status` umschreibt, damit die Ausgabe gefiltert
ankommt. Rückgängig mit `rtk init -g --uninstall`.
Bei Ja: `<python> scripts/install_rtk.py` (Windows, macOS und Linux; erkennt
eine vorhandene Installation).

**/watch (Video-Analyse)** — Fremd-Plugin: https://github.com/bradautomates/claude-video
Vorher erklären: Stammt nicht aus dem SCB Kit, sondern von einem anderen
Entwickler. Es wird ein Eintrag in der Claude-Konfiguration ergänzt.
Bei Ja: `<python> scripts/install_watch.py` (legt vorher eine Sicherung an).
Danach: `<python> scripts/install_tools.py yt-dlp ffmpeg`, und Claude Code
einmal neu starten.
Windows-Falle: Meldet `/watch` später „missing binaries: yt-dlp", die
`yt-dlp.exe` nach `%LOCALAPPDATA%\Microsoft\WinGet\Links\` kopieren.
Optional für Videos ohne Untertitel: kostenloser Groq-API-Key
(console.groq.com → API Keys).

`<python>` = der Aufruf, der in Schritt 2 funktioniert hat.

## Wichtige Regeln

- **Script-Aufrufe immer mit dem in Schritt 2 ermittelten Python-Befehl**
  (`python` unter Windows, meist `python3` auf macOS/Linux). Nie raten.
- Niemals nach Passwörtern fragen; Logins macht der User immer selbst im Browser.
- API-Keys nie im Chat wiederholen oder in Cloud-synchronisierte Notizen schreiben.
- Installationen immer kurz ankündigen und bestätigen lassen.
- Bei Fehlern: Fehlermeldung in einfacher Sprache erklären und Lösung anbieten,
  nicht den rohen Log zumuten.
