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
> 1. **Token-Sparer (RTK)** — komprimiert Claudes Terminal-Ausgaben, dein Kontingent hält deutlich länger
> 2. **Obsidian-Gehirn** — Claude merkt sich alles über dich in deinem eigenen Vault
> 3. **Video-Editor** — Videos automatisch schneiden, Untertitel, Musik, Voiceover, Texte — mit Browser-Cockpit und Ein-Klick-Render
> 4. **Content-Recherche** — Profil-Audits und Nischen-Recherche über Apify + virale Reels „ansehen" (/watch)
> 5. **Auto-Posting** — Reels über Airtable + Make automatisch auf Instagram posten
> 6. **KI-Videos generieren** — Kling 3.0 & Seedance Prompt-Builder + Higgsfield-Anbindung
> 7. **Reel-Wissen** — Safe-Zones und erprobte Hook-Formeln (immer dabei, kein Setup nötig)
>
> Ich richte jetzt mit dir ein, was du davon nutzen willst — du brauchst
> nichts vorzubereiten.

Frage dann (mit AskUserQuestion, multiSelect), welche Bereiche eingerichtet
werden sollen. Richte anschließend NUR die gewählten Bereiche ein, in der
Reihenfolge unten — **der Token-Sparer sinnvollerweise zuerst** (jeder weitere
Schritt verbraucht dann schon weniger Kontingent), **direkt danach das
Obsidian-Gedächtnis**, damit sich Claude ab der ersten Minute alles merkt.

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

### Schritt 2: RTK — Token-Sparer (optional, aber sinnvoll zuerst)

**Warum als allererstes:** Ab der Installation verbrauchen alle weiteren
Setup-Schritte und jeder künftige Auftrag spürbar weniger Kontingent.

Frage: „Willst du RTK installieren? Ein kostenloses Open-Source-Tool, das
Claudes Terminal-Ausgaben filtert und komprimiert, bevor sie deinen Kontext
erreichen — spart laut Projekt 60–90 % Tokens bei typischen Befehlen. Dein
Claude-Kontingent hält damit spürbar länger."

Quelle: **https://github.com/rtk-ai/rtk** (offizielle Releases).

**Ablauf: erklären, fragen, selbst ausführen.**

Sage dem User VOR der Frage in schlichten Worten, was passieren wird:

> Ich würde dafür ein kleines Programm von der offiziellen Projektseite
> herunterladen, es in deinen Suchpfad legen und einen Hook einrichten.
> Der schreibt Befehle wie `git status` im Hintergrund zu `rtk git status`
> um, damit die Ausgabe gefiltert bei mir ankommt. Rückgängig machst du das
> jederzeit mit `rtk init -g --uninstall`. Ich erledige das komplett, du
> musst nichts eintippen.

Dann mit **AskUserQuestion** fragen: **installieren — ja oder nein?**

**Bei Ja: Claude führt dieses Script mit dem eigenen Bash/PowerShell-Werkzeug
aus** (Pfad relativ zu diesem Skill-Ordner):

    python scripts/install_rtk.py

Das Script erledigt alles: Download vom offiziellen Release, Entpacken,
Ablage im Suchpfad, `rtk init -g` und die Prüfung. Es erkennt auch, wenn RTK
schon installiert ist. Melde dem User anschließend nur das Ergebnis in einem
Satz.

> ⚠️ **Der User öffnet KEIN Terminal und tippt NICHTS ab.** Das ist der
> ganze Sinn dieses Kits: Die Zielgruppe hat mit Coding nichts am Hut.
> Claude führt den Befehl selbst aus. Die Berechtigungsabfrage von Claude
> Code erscheint dabei ganz normal, das genügt als Kontrolle. Niemals
> antworten mit „öffne dein Terminal" oder „führe bitte selbst aus".

**Bei Nein: sofort weiter.** Kein Nachhaken. RTK ist Komfort, für nichts im
Kit Voraussetzung.

**Nur wenn das Script mit Fehler abbricht** (Firewall, keine Rechte, kein
Netz): den gemeldeten Grund verständlich weitergeben, anbieten es später
nochmal zu versuchen, und mit dem nächsten Schritt weitermachen.

**Wenn der User ablehnt oder es nicht klappt: einfach weitermachen.** RTK ist
komfortabel, aber für nichts im Kit Voraussetzung. Niemals drängen und den
Setup-Ablauf nicht daran aufhängen.

Hinweis bei Problemen: Schlägt `rtk gain` fehl, ist evtl. ein anderes
Programm namens „rtk" (Rust Type Kit) installiert — Namenskollision prüfen.

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

    python scripts/install_tools.py ffmpeg node

- **Node.js** nur nötig, wenn Higgsfield gewählt wurde
- **ffmpeg** nur nötig für Video-Schnitt und Posting
- Prüfen ohne zu installieren: `python scripts/install_tools.py --pruefen ffmpeg node`

Endet das Script mit **Exit 2**, fehlt auf einem Mac Homebrew. Dann dem User
erklären, dass das der übliche Weg für solche Programme auf dem Mac ist, den
vom Script ausgegebenen offiziellen Befehl anbieten, nach seinem Ja selbst
ausführen und das Script danach erneut aufrufen.

Nach Installationen unter Windows: neue Sitzung nötig, damit der Suchpfad greift.

### Schritt 5: Video-Editor — Schneiden, Cockpit & Untertitel

Das Herzstück des Kits: automatischer Schnitt, das Browser-Cockpit
(Timeline, Untertitel, Musik, Voiceover, Texte, Zoom — alles ohne
Token-Verbrauch) und der Ein-Klick-Render (`video_rendern.bat`). Das
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

### Schritt 7: Video-Analyse — /watch (optional, empfohlen)

Frage: „Soll Claude Videos ‚ansehen' können? Damit kannst du z. B. virale
Reels analysieren lassen (was macht der Hook, wie ist das Video aufgebaut)
oder Transkripte ziehen."

Das ist ein **kostenloses Community-Plugin eines Drittanbieters**:
`watch` aus dem GitHub-Repo **bradautomates/claude-video**
(https://github.com/bradautomates/claude-video).

**Ablauf: erklären, fragen, selbst ausführen.**

Sag vor der Frage offen dazu, dass das Plugin **nicht** aus dem SCB Kit
stammt, sondern von einem anderen Entwickler, und dass du dafür einen
Eintrag in seiner Claude-Konfiguration ergänzen würdest. Wer will, kann sich
das Repo vorher ansehen. Dann mit **AskUserQuestion** fragen: ja oder nein?

**Bei Ja: Claude führt dieses Script mit dem eigenen Werkzeug aus:**

    python scripts/install_watch.py

Das Script legt vorher eine Sicherung an, merged nur die beiden nötigen
Schlüssel in `~/.claude/settings.json` und lässt alles andere unangetastet.
Danach dem User sagen, dass er Claude Code einmal neu starten muss, damit
`/watch` erscheint.

> ⚠️ **Auch hier: kein Terminal, kein Abtippen, kein Slash-Befehl für den
> User.** Claude erledigt es. Nur wenn das Script mit Fehler abbricht (z. B.
> defektes JSON in der settings.json), den Grund verständlich weitergeben.

**Bei Nein: weiter, ohne Nachhaken.**

Danach die Werkzeuge sicherstellen — Claude führt das selbst aus:

    python scripts/install_tools.py yt-dlp ffmpeg

1. Unter Windows danach eine neue Sitzung nötig, damit der Suchpfad greift.
2. **Bekannte Windows-Falle:** das Plugin braucht `yt-dlp` als echte .exe im
   PATH. Meldet `/watch` später „missing binaries: yt-dlp", die
   `yt-dlp.exe` nach `%LOCALAPPDATA%\Microsoft\WinGet\Links\` kopieren
   (gleicher Ordner wie ffmpeg) — das wirkt sofort. Auf macOS und Linux
   tritt das nicht auf.
3. Optional für Videos ohne Untertitel: kostenloser **Groq-API-Key**
   (console.groq.com → API Keys) für die Whisper-Transkription; der
   Setup-Check des Plugins fragt danach.

Test: „/watch <YouTube-Link> Worum geht es?" — kommt eine Antwort, läuft alles.

### Schritt 8: Auto-Posting (Make + Airtable)

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

### Schritt 9: Higgsfield (KI-Bilder & -Videos)

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

### Schritt 10: GitHub verbinden (optional, zukunftssicher)

Frage: „Willst du dein Claude Code mit GitHub verbinden? Brauchst du nicht
zwingend — aber dann kann Claude dir künftig weitere Tools und Updates aus
GitHub mit einem Satz installieren."

Wenn ja:
1. Konto (falls noch keins): **https://github.com/signup** — kostenlos,
   2 Minuten. Der User erstellt es selbst im Browser.
2. GitHub-CLI installieren — Claude führt das selbst aus:
   `python scripts/install_tools.py gh` (danach neue Sitzung nötig).
3. Verbinden: Öffne für den User ein sichtbares Terminal-Fenster mit
   `gh auth login` — er wählt „GitHub.com" → „HTTPS" → „Login with a web
   browser" und loggt sich selbst im Browser ein. Claude gibt niemals
   Passwörter oder Tokens ein.
4. Prüfen: `gh auth status` → „Logged in" = fertig.

### Schritt 11: Abschluss

Fasse zusammen, was eingerichtet wurde und was der User jetzt sagen kann:

> Fertig! 🎉 So nutzt du dein Kit — sag einfach:
> - „Bau mir einen Kling-Prompt" → Prompt-Builder startet
> - „Schneide mein Video" → automatischer Schnitt
> - „Mach Untertitel drauf" → sprach-synchrone Untertitel in der Safe-Zone
> - „Schreib mir ein Reel" → Hook-Formeln & Reel-Struktur (fragt nach deinem Keyword)
> - „Mach ein Audit von meinem Profil" → Apify-Analyse + Verbesserungen
> - „/watch <Link> — warum ist das Reel viral?" → Video-Analyse
> - „Richte mein Auto-Posting ein" → Airtable + Make Aufbau
> - „Merk dir: …" → landet in deinem Obsidian-Gehirn
> - „Wie viel hat RTK gespart?" → Claude zeigt deine Token-Ersparnis (`rtk gain`)

Wenn etwas übersprungen wurde: erwähnen, dass `scb-setup` jederzeit erneut
gestartet werden kann.

## Wichtige Regeln

- Niemals nach Passwörtern fragen; Logins macht der User immer selbst im Browser.
- API-Keys nie im Chat wiederholen oder in Cloud-synchronisierte Notizen schreiben.
- Installationen (npm, winget) immer kurz ankündigen und bestätigen lassen.
- Bei Fehlern: Fehlermeldung in einfacher Sprache erklären und Lösung anbieten,
  nicht den rohen Log zumuten.
