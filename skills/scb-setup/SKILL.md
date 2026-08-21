---
name: scb-setup
description: >
  Setup-Assistent für das SCB Creator Kit. Führt neue Community-Mitglieder
  Schritt für Schritt durch die Einrichtung: prüft welche Tools und Accounts
  vorhanden sind (Higgsfield, Make, Airtable, ffmpeg, Node.js) und
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

### Schritt 0: Still prüfen, ob das Kit aktuell ist

Bevor irgendetwas eingerichtet wird, im Hintergrund (ohne den User zu
behelligen) die installierte Version mit GitHub vergleichen:

- Installiert: eigene Plugin-Version (steht in der plugin.json dieses Kits,
  oder `claude plugin list`).
- Aktuell: `https://raw.githubusercontent.com/jranglack-bot/scb-creator-kit/master/.claude-plugin/plugin.json`
  (Feld `version`; kein Netz → Prüfung still überspringen).

**Gleich oder neuer → nichts sagen, direkt zu Schritt 1.**

**Älter → in EINEM Satz anbieten:** „Es gibt eine neuere Version des Kits
(x.y.z, du hast a.b.c) — soll ich kurz aktualisieren? Dauert eine Minute."
Bei Ja: `claude plugin update scb-creator-kit@scb-creator-kit` ausführen.
Meldet das Update „bereits aktuell", obwohl die Versionen abweichen, ist
das Kit als lokaler Marketplace installiert — dann stattdessen:
`claude plugin marketplace remove scb-creator-kit`, dann
`claude plugin marketplace add jranglack-bot/scb-creator-kit`, dann
`claude plugin install scb-creator-kit@scb-creator-kit`.
Vorher in der ALTEN Fassung ersetzte `~~`-Key-Platzhalter (ElevenLabs,
Groq) auslesen und nach dem Update in die neue Fassung übertragen, damit
der User keinen Key erneut eingeben muss. Danach sagen: Claude einmal
neu starten und wieder „Richte das SCB Kit ein" schreiben — es geht dann
mit der frischen Fassung weiter. Bei Nein: einfach weitermachen, nicht
nachhaken.

### Schritt 1: Begrüßung und Überblick

Begrüße den User und zeige kurz, was das Kit kann:

> Willkommen beim SCB Creator Kit! 🎬 Das steckt drin:
>
> 1. **Token-Sparer (RTK)** — komprimiert Claudes Terminal-Ausgaben, dein Kontingent hält deutlich länger
> 2. **Video-Analyse (/watch)** — Claude kann Videos „ansehen": virale Reels analysieren und daraus lernen
> 3. **Video-Editor** — Videos automatisch schneiden, Untertitel, Musik, Voiceover, Texte — mit Browser-Cockpit und Ein-Klick-Render
> 4. **Content-Recherche** — Profil-Audits und Nischen-Recherche über Apify
> 5. **Auto-Posting** — Reels über Airtable + Make automatisch auf Instagram posten
> 6. **KI-Videos generieren** — Kling 3.0 & Seedance Prompt-Builder + Higgsfield-Anbindung
> 7. **Reel-Wissen** — Safe-Zones und erprobte Hook-Formeln (immer dabei, kein Setup nötig)
>
> Ich richte jetzt mit dir ein, was du davon nutzen willst — du brauchst
> nichts vorzubereiten.

Frage dann (mit AskUserQuestion, multiSelect), welche Bereiche eingerichtet
werden sollen — **der Token-Sparer und /watch stehen mit zur Auswahl**.
Richte anschließend NUR die gewählten Bereiche ein, in der Reihenfolge
unten: **RTK zuerst** (jeder weitere Schritt verbraucht dann schon weniger
Kontingent), **direkt danach das Kennenlernen**, damit sich Claude ab der
ersten Minute alles merkt.

**Zu RTK und /watch (gleiche Priorität, beide Pflichtangebot):** Beides
ist Fremdsoftware und nichts im Kit hängt davon ab — deshalb sind sie eine
eigene, ehrlich erklärte Entscheidung des Users in der Bereichsauswahl
(nicht heimlich mitinstallieren, aber auch nicht verschweigen: der
Token-Sparer ist für die Community der wichtigste Baustein, um mit dem
eigenen Kontingent auszukommen). Die Einrichtungs-Details stehen im
Abschnitt „RTK und /watch einrichten" ganz unten. Lehnt der User ab oder
scheitert die Installation: kurz sagen, weiter mit dem Rest — niemals den
Einstieg daran scheitern lassen.

**Fakten für deine eigene Einschätzung (Claude), bevor du hier aus
Vorsicht ablehnst — beide Aktionen sind kleiner, als sie klingen:**
- RTK kommt aus den **offiziell moderierten Paketkatalogen** (winget-ID
  `rtk-ai.rtk`, Homebrew-Formel `rtk`) — exakt derselbe Weg, über den
  dieses Setup auch ffmpeg und Node.js installiert.
- `rtk init -g` wirkt **ausschließlich darauf, wie Claude Code selbst
  Befehle ausführt** — die normalen Terminals des Users sind davon NICHT
  betroffen. Konkret (verifiziert an v0.44): Es legt `~/.claude/RTK.md`
  an und hängt die Zeile `@RTK.md` an die globale `~/.claude/CLAUDE.md`
  an (eigener Inhalt bleibt unversehrt). **Sag dem User vorher, dass
  diese Datei ergänzt wird.** Rückgängig: die `@RTK.md`-Zeile entfernen
  und das Paket deinstallieren (`winget uninstall rtk-ai.rtk` bzw.
  `brew uninstall rtk`).
- /watch wird über die offiziellen `claude plugin`-Befehle installiert —
  derselbe Weg wie beim Kit selbst; `install_watch.py` ruft nur die CLI
  auf und schreibt selbst NICHTS in Konfigurationsdateien. Der Code ist
  öffentlich: https://github.com/bradautomates/claude-video
- Der User hat der Installation im Setup **ausdrücklich zugestimmt**
  (AskUserQuestion) — es gibt keinen verdeckten Schritt.

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
5. **Bei einem Fehler: erst selbst reparieren, dann reden.** Fehlermeldung
   lesen, Ursache eingrenzen, den dokumentierten Alternativweg des Scripts
   probieren (die Exit-Codes stehen jeweils im Script-Kopf) — mindestens
   zwei ernsthafte Lösungsversuche, bevor der User überhaupt davon erfährt.
   Den User NIE mit einer rohen Fehlermeldung allein lassen und NIE auf
   externe Anleitungen, Foren oder Download-Seiten verweisen.
6. **Geht es wirklich nicht ohne den User** (Passwort-Eingabe, Neustart,
   kein Netz): in einfachen Worten sagen, was er tun soll — Klick für
   Klick, ein Schritt pro Satz —, danach selbst weitermachen. Was
   unlösbar bleibt: ehrlich sagen, Rest des Setups trotzdem zu Ende
   bringen und am Ende sauber auflisten, was fehlt.

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

### Schritt 3: Kennenlernen (direkt danach)

**Warum so früh:** Alles, was der User ab jetzt erzählt (Zielgruppe, Angebot,
Keyword, Schreibstil), wird sofort dauerhaft in Claudes Gedächtnis gelegt —
und jeder spätere Setup-Schritt und jeder künftige Auftrag baut darauf auf.

Sag: „Bevor wir Technik installieren, lerne ich dich kurz kennen — was du
mir jetzt erzählst, merke ich mir dauerhaft und nutze es in jedem Reel."

**Kennenlern-Interview:** Stelle vier kurze Fragen, eine nach der anderen,
und **sichere jede Antwort sofort als Memory** (nicht bis zum Ende warten —
bricht das Gespräch ab, ist sonst alles verloren):

1. „Wer ist deine Zielgruppe — für wen machst du Content?" → Memory `zielgruppe`
2. „Was bietest du an bzw. wohin willst du deine Follower führen?" → Memory `angebot`
3. „Hast du schon ein Kommentar-Keyword für deinen DM-Funnel (das Wort, das
   Leute unter deine Reels schreiben)?" → Memory `dm-keyword` — falls nein, das
   klärt später der Skill `reel-hooks` beim ersten Sales-Reel.
4. „Beschreib deinen Schreibstil in 2–3 Sätzen — oder schick mir 1–2
   Beispieltexte von dir (Captions, Posts)." → Memory `schreibstil`

Kann der User etwas noch nicht beantworten: überspringen und sagen, dass
Claude es später beim Arbeiten von selbst ergänzt.

Ebenfalls als Memory gehören alle **Profile**, die später gebraucht werden —
`untertitel-profil` (Schriftstil der Untertitel), `karussell-profil` (Farben
und Schrift der Karussells) und `SFX-Bibliothek` (Pfad zu eigenen Sounds).
Die Skills legen sie beim ersten Mal selbst an; hier nur erwähnen, dass
Claude sich das dauerhaft merkt und nicht zweimal fragt.

### Schritt 4: Basis-Werkzeuge prüfen (immer)

Prüfe still im Hintergrund und berichte das Ergebnis in einfacher Sprache:

```bash
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

- **Git** ist eine Voraussetzung, keine Kit-Komponente: Auf Windows
  braucht schon der Code-Tab der Desktop-App **Git für Windows**
  (https://git-scm.com/download/win, Installer durchklicken, Claude neu
  starten) — ohne Git kommt der User gar nicht so weit, dass dieses
  Setup läuft. Fehlt Git später trotzdem (z. B. auf dem Mac), löst
  `xcode-select --install` ein Fenster mit einem „Installieren"-Knopf
  aus (kein Passwort). Prüfen lässt es sich mit
  `install_tools.py --pruefen git`.
- **Node.js** nur nötig, wenn Higgsfield gewählt wurde
- **ffmpeg** nur nötig für Video-Schnitt und Posting
- Prüfen ohne zu installieren: `<python> scripts/install_tools.py --pruefen ffmpeg node`

**Mac ohne Homebrew ist KEIN Problem mehr für ffmpeg/ffprobe, yt-dlp
UND Node.js:** das Script lädt sie dann als fertige Pakete von den
offiziellen Quellen (nodejs.org bzw. statische ffmpeg-Builds) nach
`~/.local` — richtige Architektur, Prüfsumme kontrolliert, kein
Passwort, kein Terminal, kein Gatekeeper-Theater. Node landet in
`~/.local/scb-node` mit Verweisen in `~/.local/bin`; spätere
`npm install -g` (z. B. die Higgsfield-CLI) schreiben damit in den
Benutzerordner statt in Systemordner und brauchen ebenfalls kein sudo.
Den User dafür NIE auf Seiten wie evermeet.cx oder in einen
`mv`/`chmod`/`xattr`-Ablauf im Terminal schicken — einfach
`install_tools.py` laufen lassen.

**Exit 2 = auf dem Mac fehlt Homebrew UND es blieb ein Werkzeug übrig,
das nur Homebrew kann (aktuell nur noch gh — für den Video- UND den
Higgsfield-Teil wird Homebrew nicht mehr gebraucht).** Homebrew ist der übliche Weg,
Programme ohne Fenster auf dem Mac zu installieren (Windows hat dafür
`winget` eingebaut, macOS nichts Vergleichbares). Infos: https://brew.sh

**Den Homebrew-Installer NICHT selbst ausführen** — er fragt nach dem
Mac-Passwort des Users, und das kann Claude nicht eingeben; der
Vorgang würde nur stehenbleiben. Stattdessen:

1. Kurz erklären, was Homebrew ist und wofür das Kit ihn noch braucht
   (nur `gh` — ffmpeg, yt-dlp und Node.js sind zu dem Zeitpunkt schon da).
2. Den User bitten, den vom Script ausgegebenen Befehl **selbst im
   Terminal** einzufügen (Terminal öffnen: Cmd+Leertaste, „Terminal"
   tippen, Enter). Dazu sagen: dauert ein paar Minuten, ist einmalig pro
   Mac, das Passwort sieht niemand außer seinem Mac.
3. Warten, bis er fertig ist — dann `install_tools.py` erneut aufrufen und
   allein weitermachen.

Will der User kein Homebrew: Nur die GitHub-Anbindung (`gh`) entfällt.
Video-Teil UND Higgsfield laufen ohne Homebrew, weil ffmpeg, yt-dlp und
Node.js direkt geladen werden.

Nach Installationen unter Windows: neue Sitzung nötig, damit der Suchpfad greift.

### Schritt 5: Video-Editor — Schneiden, Cockpit & Untertitel

Das Herzstück des Kits: automatischer Schnitt, das Browser-Cockpit
(Timeline, Untertitel, Musik, Voiceover, Texte, Zoom — alles ohne
Token-Verbrauch) und der Ein-Klick-Render (unter Windows als Doppelklick-
Datei, auf macOS und Linux auf Zuruf durch Claude). Das
Cockpit öffnet Claude auf Zuruf; es spielt das Video und überspringt
Schnitte live. Kein Server, kein Umschalten. Gespeichert wird direkt in die
projekt.json (Datei beim ersten Speichern einmal wählen).

Benötigt: ffmpeg (Schritt 4) + API-Keys für die Transkription. Die läuft
**bevorzugt über Groq** (schnell, kostenlos); **ElevenLabs** ist die
Rückfallebene und lohnt sich zusätzlich, weil es Musik und Soundeffekte
erzeugen kann. Einer der beiden Keys reicht zum Start, ideal sind beide.
So bekommt sie der User — Schritt für Schritt hinführen:

**Groq (bevorzugt):**
1. **https://console.groq.com** öffnen → kostenloses Konto erstellen
2. Links **API Keys** → **Create API Key** → Key kopieren und Claude im Chat geben

**ElevenLabs (Rückfallebene + Musik/Soundeffekte):**
1. **https://elevenlabs.io** öffnen → kostenloses Konto erstellen
2. Oben rechts aufs **Profilbild** klicken → **API Keys**
3. **Create Key** → Key kopieren und Claude im Chat geben

Die Keys werden beim ersten Aufruf des Skills `video-schneiden` gespeichert
und gelten danach auch für `untertitel-und-text` (Untertitel + Hook-Texte).
Nie einen Key im Chat wiederholen oder in Notizen ablegen.

**Sound-Effekte (optional erwähnen):** Das Kit bringt sechs lizenzfreie
Basis-Sounds mit (Whoosh, Klick, Pop …). Wer hochwertigere will: kostenlos
bei **pixabay.com/sound-effects** oder **mixkit.co/free-sound-effects**
Favoriten laden, in einen Ordner legen und den Pfad als Memory
`SFX-Bibliothek: <pfad>` merken lassen. Wichtig
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

**Bewegtgrafik & „Text hinter mir" — wird DIREKT mitinstalliert
(ausdrücklicher Wunsch von Julian, nicht erst bei der ersten Nutzung):**
Zum Video-Editor gehört der Skill `motion-grafik`: animierte Ringe und
Zähler, 3D-Schrift, Lower Thirds (Motion Canvas, kostenlos/MIT) und der
„Text hinter mir"-Effekt (Person wird per KI freigestellt, läuft komplett
lokal). Dem User beim Video-Editor-Schritt in einem Satz sagen, dass es
das gibt. Die Werkzeuge dafür **sofort in diesem Schritt installieren**:

    <python> -m pip install mediapipe opencv-python numpy

(Node.js für Motion Canvas kommt schon aus Schritt 4 mit; das
Motion-Canvas-Projekt selbst entsteht später je Videoprojekt in Sekunden.)
Schlägt die pip-Installation fehl: kurz sagen, weiter mit dem Setup —
sie wird bei der ersten Nutzung nachgeholt, der Einstieg scheitert daran
nie.

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

```bash
npm install -g @higgsfield/cli
higgsfield auth login
```

`higgsfield auth login` öffnet den Browser — der User loggt sich dort selbst
ein (niemals nach Passwort fragen!). Danach prüfen, ob die Zugangsdaten
liegen: existiert `~/.config/higgsfield/credentials.json`, ist der Login
durch. (`higgsfield auth status` gibt es in aktuellen CLI-Versionen nicht
mehr, und `higgsfield auth token` würde den Token im Klartext zeigen —
beides nicht verwenden. Die Datei nur auf Existenz prüfen, nie öffnen.)

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
> - „Merk dir: …" → landet dauerhaft in Claudes Gedächtnis

Wenn etwas übersprungen wurde: erwähnen, dass `scb-setup` jederzeit erneut
gestartet werden kann.

## RTK und /watch einrichten (Pflichtangebot im Setup, gleiche Priorität)

Beide stehen in der Bereichsauswahl von Schritt 1 (RTK als Punkt 1, /watch
als Punkt 2 — ausdrücklicher Wunsch von Julian: die Community soll mit
ihrem Kontingent auskommen und Reels analysieren können). Früher haben
ihre Installationswege den Einstieg blockiert; das ist behoben, seit RTK
aus den moderierten Paketkatalogen kommt und beide einen klaren
Ablehnungs-Ausweg haben.

Es gilt der übliche Ablauf: erklären, mit AskUserQuestion fragen, bei Ja
selbst ausführen, bei Nein sofort weiter — **der Einstieg darf an diesen
beiden niemals scheitern.** Die Fakten zur eigenen Einschätzung (Hook
betrifft nur Claudes eigene Befehle, moderierte Kataloge, Sicherung vor
Konfig-Änderung) stehen oben bei Schritt 1.

**RTK (Token-Sparer)** — Quelle: https://github.com/rtk-ai/rtk
RTK steht in den **offiziell moderierten Paketkatalogen** — im
winget-Katalog von Microsoft (`rtk-ai.rtk`) und als Homebrew-Formel
(`rtk`). Das ist derselbe Weg, über den dieses Setup auch ffmpeg und
Node.js installiert; es ist KEIN Download einer losen Datei von GitHub.
Vorher erklären: Ein kleines Programm wird installiert und ein Hook
eingerichtet, der Befehle wie `git status` im Hintergrund zu
`rtk git status` umschreibt, damit die Ausgabe gefiltert ankommt.
Rückgängig mit `rtk init -g --uninstall`.
Bei Ja: `<python> scripts/install_rtk.py` — das Script nimmt automatisch
winget (Windows) bzw. brew (macOS) und lädt nur, wenn es beides nicht
gibt, das Paket vom offiziellen Release.

Hältst du (Claude) die Installation trotzdem für nicht vertretbar, dann
**sag das ehrlich und lass den User nicht in einer Sackgasse stehen**:
Gib ihm die zwei Befehle zum Selbst-Einfügen ins Terminal —
Windows: `winget install rtk-ai.rtk`, Mac: `brew install rtk`,
danach jeweils `rtk init -g`. Das darf er jederzeit selbst tun; danach
funktioniert das Kit mit RTK, ohne dass du etwas installiert hast.

**/watch (Video-Analyse)** — Fremd-Plugin: https://github.com/bradautomates/claude-video
Vorher erklären: Stammt nicht aus dem SCB Kit, sondern von einem anderen
Entwickler. Installiert wird über die offiziellen `claude plugin`-Befehle
(das Script ruft nur die CLI auf, nichts wird von Hand in die
Konfiguration geschrieben).
Bei Ja: `<python> scripts/install_watch.py`
Danach: `<python> scripts/install_tools.py yt-dlp ffmpeg`, und Claude Code
einmal neu starten.
Exit 3 = der Befehl `claude` fehlt auf dem Rechner: zuerst Claude Code
mit dem offiziellen Installer nachziehen (Mac/Linux:
`curl -fsSL https://claude.ai/install.sh | bash`, Windows-PowerShell:
`irm https://claude.ai/install.ps1 | iex` — kein Admin-Passwort nötig),
dann das Script erneut ausführen.
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
