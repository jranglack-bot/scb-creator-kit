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
> 1. **KI-Videos generieren** — Kling 3.0 & Seedance Prompt-Builder + Higgsfield-Anbindung
> 2. **Videos automatisch schneiden + untertiteln** — Versprecher raus, sprach-synchrone Untertitel und Hook-Texte rein
> 3. **Reel-Wissen** — Safe-Zones (wo Text sitzen darf) und erprobte Hook-Formeln
> 4. **Auto-Posting** — Reels über Airtable + Make automatisch auf Instagram posten
> 5. **Instagram-Audit & Recherche** — Profil-Analyse und Nischen-Recherche über Apify
> 6. **Video-Analyse** — Claude kann Videos „ansehen" (virale Reels analysieren, Transkripte ziehen)
> 7. **Obsidian-Gehirn** — Claude merkt sich alles über dich in deinem eigenen Vault
> 8. **Token-Sparer (RTK)** — komprimiert Claudes Terminal-Ausgaben, dein Kontingent hält deutlich länger
>
> Ich richte jetzt mit dir ein, was du davon nutzen willst — du brauchst
> nichts vorzubereiten.

Frage dann (mit AskUserQuestion, multiSelect), welche Bereiche eingerichtet
werden sollen. Richte anschließend NUR die gewählten Bereiche ein, in der
Reihenfolge unten — **das Obsidian-Gedächtnis kommt immer zuerst**, damit
sich Claude ab der ersten Minute alles merken kann.

### Schritt 2: Obsidian-Gehirn ZUERST einrichten

**Warum zuerst:** Alles, was der User ab jetzt erzählt (Zielgruppe, Angebot,
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

### Schritt 3: Basis-Werkzeuge prüfen (immer)

Prüfe still im Hintergrund und berichte das Ergebnis in einfacher Sprache:

```powershell
# Node.js / npm (für Higgsfield-CLI)
node --version; npm --version
# ffmpeg / ffprobe (für Video-Schnitt)
ffmpeg -version; ffprobe -version
```

- Fehlt **Node.js**: nur nötig, wenn Higgsfield gewählt wurde → `winget install OpenJS.NodeJS.LTS`, danach Terminal-Neustart erklären.
- Fehlt **ffmpeg**: nur nötig für Video-Schnitt/Posting → `winget install Gyan.FFmpeg`, danach Terminal-Neustart erklären.
- Führe Installationen erst nach kurzer Rückfrage aus („Darf ich ffmpeg installieren? Ist kostenlos und offiziell.").

### Schritt 4: RTK — Token-Sparer (optional, empfohlen)

Frage: „Willst du RTK installieren? Ein kostenloses Open-Source-Tool, das
Claudes Terminal-Ausgaben filtert und komprimiert, bevor sie deinen Kontext
erreichen — spart laut Projekt 60–90 % Tokens bei typischen Befehlen. Dein
Claude-Kontingent hält damit spürbar länger."

Quelle: **https://github.com/rtk-ai/rtk** (offizielle Releases).

Installation für den User übernehmen (nach kurzer Ankündigung des Downloads):

**Windows:**
1. Offizielles Windows-Paket laden:
   `https://github.com/rtk-ai/rtk/releases/latest/download/rtk-x86_64-pc-windows-msvc.zip`
2. Entpacken und die `rtk.exe` in einen PATH-Ordner legen — bewährt:
   `%LOCALAPPDATA%\Microsoft\WinGet\Links\` (derselbe Ordner wie ffmpeg/yt-dlp).
3. **WICHTIG — direkt nach der Installation ausführen: `rtk init -g`**
   Das installiert den automatischen Rewrite-Hook (Befehle wie `git status`
   werden ab dann transparent zu `rtk git status` umgeschrieben) und legt die
   RTK-Dokumentation an. Ohne diesen Schritt bleibt RTK wirkungslos!
4. Prüfen: `rtk --version` und `rtk gain` (zeigt die Token-Ersparnis).

**macOS/Linux:** `brew install rtk` (oder das Quick-Install-Script von der
Projektseite), danach ebenfalls **`rtk init -g`**.

Hinweis bei Problemen: Schlägt `rtk gain` fehl, ist evtl. ein anderes
Programm namens „rtk" (Rust Type Kit) installiert — Namenskollision prüfen.

### Schritt 5: Higgsfield (KI-Bilder & -Videos)

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

### Schritt 6: Video-Schneiden & Untertitel

Benötigt: ffmpeg (Schritt 3) + einen **ElevenLabs-API-Key** (kostenloses
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

### Schritt 8: Instagram-Audit & Recherche (Apify)

Frage: „Willst du Profil-Audits und Nischen-Recherche nutzen? Dafür brauchst
du ein kostenloses Apify-Konto (dein Monats-Freiguthaben reicht für hunderte
Profil-Abrufe)."

1. Konto auf **https://apify.com** erstellen (Free-Plan)
2. Mit Claude verbinden: claude.ai → Einstellungen → **Connectoren** → Apify.
   Alternativ per Token: **console.apify.com** → Settings →
   **API & Integrations** → Personal API Token kopieren.
3. Erkläre die Budget-Regel: Claude nennt vor jedem Apify-Lauf die geschätzten
   Kosten und wartet auf ein Okay — so bleibt es im Freiguthaben.

### Schritt 9: Video-Analyse — /watch (optional, empfohlen)

Frage: „Soll Claude Videos ‚ansehen' können? Damit kannst du z. B. virale
Reels analysieren lassen (was macht der Hook, wie ist das Video aufgebaut)
oder Transkripte ziehen."

Das ist ein **kostenloses Community-Plugin eines Drittanbieters**:
`watch` aus dem GitHub-Repo **bradautomates/claude-video**
(https://github.com/bradautomates/claude-video).

Installation für den User übernehmen — in `~/.claude/settings.json` mergen
(bestehende Einträge erhalten!):

```json
{
  "enabledPlugins": { "watch@claude-video": true },
  "extraKnownMarketplaces": {
    "claude-video": {
      "source": { "source": "github", "repo": "bradautomates/claude-video" }
    }
  }
}
```

Danach die Werkzeuge sicherstellen (Windows):
1. `winget install yt-dlp.yt-dlp` und ffmpeg (Schritt 3). Terminal-Neustart
   nötig, damit der PATH greift.
2. **Bekannte Windows-Falle:** das Plugin braucht `yt-dlp` als echte .exe im
   PATH. Meldet `/watch` später „missing binaries: yt-dlp", die
   `yt-dlp.exe` nach `%LOCALAPPDATA%\Microsoft\WinGet\Links\` kopieren
   (gleicher Ordner wie ffmpeg) — das wirkt sofort.
3. Optional für Videos ohne Untertitel: kostenloser **Groq-API-Key**
   (console.groq.com → API Keys) für die Whisper-Transkription; der
   Setup-Check des Plugins fragt danach.

Test: „/watch <YouTube-Link> Worum geht es?" — kommt eine Antwort, läuft alles.

### Schritt 10: GitHub verbinden (optional, zukunftssicher)

Frage: „Willst du dein Claude Code mit GitHub verbinden? Brauchst du nicht
zwingend — aber dann kann Claude dir künftig weitere Tools und Updates aus
GitHub mit einem Satz installieren."

Wenn ja:
1. Konto (falls noch keins): **https://github.com/signup** — kostenlos,
   2 Minuten. Der User erstellt es selbst im Browser.
2. GitHub-CLI installieren: `winget install GitHub.cli` (danach Terminal-
   Neustart).
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
