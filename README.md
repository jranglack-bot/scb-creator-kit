# 🎬 SCB Creator Kit

Das Creator-Toolkit der SCB Community für Claude: KI-Reels erstellen,
Videos automatisch schneiden, mit erprobten Hook-Formeln texten und
Instagram-Posting automatisieren — alles in einem Plugin, geführt von
einem Setup-Assistenten.

## Was steckt drin?

| Skill | Was er kann | So startest du ihn |
|---|---|---|
| **scb-setup** | Setup-Assistent: fragt ab, was du hast (Higgsfield, Make, Airtable …) und richtet alles ein | „Richte das SCB Kit ein" |
| **kling-prompt-builder** | Führt dich zu einem perfekten Kling-3.0-Prompt (spart Credits) | „Bau mir einen Kling-Prompt" |
| **seedance-prompt-builder** | Shot-für-Shot-Prompts für Seedance 2.0 | „Schreib mir einen Seedance-Prompt" |
| **video-model-prompting** | Verifizierte Prompt-Regeln pro Videomodell (Seedance 2.0, Kling 3.0, Veo 3.1, Gemini Omni Flash) — Modell-Eigenheiten, Kamera-Vokabular, bekannte Fallen | läuft automatisch beim Prompt-Schreiben |
| **video-schneiden** | Schneidet Versprecher, Ähs und Pausen automatisch raus — token-optimiert (Scripts übernehmen die Mechanik, das KI-Modell nur das Verstehen) | „Schneide mein Video" |
| **untertitel-und-text** | Untertitel, Hook-Texte & B-Roll-Overlays einbrennen — mit persönlichem Stil-Profil: einmal einrichten (auch per Screenshot-Vorlage „so will ich das"), gilt für immer | „Mach Untertitel drauf" / Screenshot zeigen |
| **pro-look-editing** | Pro-Look-Paket: animierte Wort-für-Wort-Captions (CapCut-Stil), Punch-Ins & weicher Zoom, Wisch-Übergänge mit gekoppeltem Sound, B-Roll-Einblendungen, animierte Motion-Overlays (Pfeile/Buttons/Konfetti per Green-Screen), Picture-in-Picture, Hook-Cover, Fortschrittsbalken, Color-Grade, Filmkorn, Typewriter- & Akzent-SFX — plus Audio-Suite: Musikbett mit Auto-Ducking, Stimm-Mastering und Loudness auf Instagram-Standard (alle Extras immer nur auf Nachfrage) | „Mach das Video professionell" |
| **higgsfield-generate** (+ Soul ID, Photoshoot, Marketplace-Cards) | Eigene Fotos hochladen, Bilder & Videos generieren, Bild-zu-Video, Soul-Charakter für dein Gesicht — alles direkt über deinen Higgsfield-Account | „Generier mir ein Bild/Video" |
| **instagram-audit** | Profil-Audit, Engagement-Rate & echter Wachstums-Check (15-Tage-Verlauf via Social Blade) über Apify (mit Kosten-Check vor jedem Lauf) | „Ist mein Profil gewachsen?" |
| **reel-hooks** | Erprobte Hook-Formeln & Reel-Strukturen (Humor + Sales), fragt nach deinem Funnel-Keyword | „Schreib mir ein Reel" |
| **reel-layout** | Safe-Zones: wo Text in Reels & Stories sitzen darf | läuft automatisch beim Bearbeiten |
| **reel-posting** | Auto-Posting-System mit Airtable + Make bauen | „Richte mein Auto-Posting ein" |
| **sfx-extraktion** | Soundeffekte aus Reels/Videos herausschneiden — automatische Erkennung in SFX-Compilation-Reels, Ablage als MP3 in deiner Bibliothek | „Hol mir den Sound aus dem Reel" |
| **karussell-posts** | Komplette Instagram-Karussells (1080×1350): Texte nach Hook-Formel, gebrandete Folien aus Templates (gerendert vom vorinstallierten Browser — nichts zu installieren), Kontrolle über einen Kontaktbogen | „Mach mir ein Karussell zu [Thema]" |
| **video-projekt** | Projekt-Modus mit Video-Cockpit: Browser-Editor zum Schnitte-Verschieben (Timeline mit rot markierten Schnitten), Untertitel-Ziehen und Bild-im-Bild-Skalieren — Feinarbeit kostet 0 Tokens; Stufen-Rendering + Editierbar-Export für Canva/CapCut (Master + SRT) | „Ich will die Schnitte selbst prüfen" / „Mach es editierbar" |
| **motion-grafik** | Aufwendige Bewegtgrafik, die das Cockpit nicht kann: animierte Ringe & hochzählende Zahlen, extrudierte 3D-Schrift, Lower Thirds — plus der „Text schwebt hinter mir"-Effekt, bei dem du freigestellt wirst und vor der Grafik stehst | „Ich will einen 3D-Effekt" / „Text soll hinter mir schweben" |

### Optionale Extras (bewusst nicht Teil der Einrichtung)

Zwei kostenlose Programme von anderen Entwicklern. Das Kit braucht sie
**nicht**, deshalb halten sie deinen Einstieg auch nicht auf. Wenn du sie
später haben willst, sag es Claude einfach — er richtet sie dann ein:

- **/watch** ([bradautomates/claude-video](https://github.com/bradautomates/claude-video)) —
  Claude kann Videos „ansehen" und z. B. virale Reels analysieren.
  Sag dann: *„Richte mir /watch ein"*
- **RTK** ([rtk-ai/rtk](https://github.com/rtk-ai/rtk)) — komprimiert Claudes
  Terminal-Ausgaben (60–90 % Token-Ersparnis), dein Kontingent hält länger.
  Sag dann: *„Richte mir RTK ein"*
- **Motion Canvas** ([motion-canvas](https://github.com/motion-canvas/motion-canvas),
  MIT) — für den Skill `motion-grafik`: animierte Ringe, hochzählende Zahlen,
  3D-Schrift. Braucht Node.js. Schnitt und Untertitel laufen auch ohne.
  Sag dann: *„Richte mir Motion Canvas ein"*
- **MediaPipe** (`mediapipe`, `opencv-python`, `numpy` — Apache 2.0) — nur für
  den „Text hinter mir"-Effekt. Das Erkennungsmodell liegt bereits im Kit, zur
  Laufzeit wird nichts nachgeladen. Sag dann: *„Richte mir die Freistellung ein"*

## Empfohlene Reihenfolge & Modellwahl (Kontingent sparen)

Der Setup-Assistent führt dich in dieser Reihenfolge durch — bewusst so
gewählt, damit dein Kontingent von Anfang an geschont wird:

1. **Token-Sparer (RTK)** — zuerst, dann verbraucht alles Weitere schon weniger
2. **Kennenlernen** — Claude merkt sich ab Minute 1 alles über dich
3. **Video-Editor** — Schneiden, Cockpit, Untertitel, Ein-Klick-Render
4. **Content-Recherche** — Apify (Audits, Nischen) + /watch (Reels analysieren)
5. **Auto-Posting** — Airtable + Make
6. **KI-Generierung** — Higgsfield und alles Weitere

**Modellwahl:** Für den Alltag reicht **Sonnet** völlig (Schneiden, Cockpit,
Rendern, Posten — die Intelligenz steckt in den Scripts des Kits) und
verbraucht nur einen Bruchteil des Kontingents. **Opus** lohnt sich punktuell
für kreative Konzept-Arbeit (Hooks, Content-Strategie) oder wenn etwas
Ungewöhnliches klemmt. Faustregel: *Alltag = Sonnet, Konzept & Notfall = Opus.*

## Installation — 3 Schritte, ca. 1 Minute

Kein Download, kein Terminal — Claude installiert das Kit selbst.
Die ausführliche Anleitung mit Bildern steht in
[INSTALLATION.md](INSTALLATION.md), die Kurzfassung:

1. **Claude Desktop-App öffnen**, oben den Tab **Code** wählen
   (App kostenlos hier: [claude.ai/download](https://claude.ai/download))
2. **Diese Nachricht an Claude schicken** (komplett kopieren):

   > Installiere bitte das SCB Creator Kit:
   > 1. Prüfe mit `claude --version`, ob der Befehl `claude` existiert.
   > Falls nicht, installiere zuerst Claude Code mit dem offiziellen
   > Installer — Mac/Linux: `curl -fsSL https://claude.ai/install.sh | bash`
   > — Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`.
   > Er braucht kein Admin-Passwort. Findet die Shell den Befehl danach
   > nicht, nutze den vollen Pfad `~/.local/bin/claude`.
   > 2. `claude plugin marketplace add jranglack-bot/scb-creator-kit`
   > Meldet der Befehl, dass `git` fehlt (typisch auf einem neuen Mac):
   > führe `xcode-select --install` aus und bitte mich, im aufgehenden
   > Fenster auf „Installieren" zu klicken; danach den Befehl wiederholen.
   > Alternativ: das Repo als .tar.gz laden (`curl -L`, GitHub-Archiv von
   > master), entpacken und den Ordner als lokalen Marketplace registrieren.
   > 3. `claude plugin install scb-creator-kit@scb-creator-kit`
   > 4. Wichtig: Ich kenne mich mit Terminal und Technik nicht aus. Führe
   > alles selbst aus und erkläre mir nur kurz, was du tust. Schlägt ein
   > Schritt fehl, such die Ursache und behebe sie selbstständig. Nur wenn
   > es ohne mich nicht geht, sag mir Klick für Klick, was ich tun soll.

   Claude führt die Befehle selbst aus — kommen Berechtigungsabfragen,
   einfach bestätigen.
3. **Claude komplett schließen und neu öffnen**, dann schreiben:
   „Richte das SCB Kit ein"

Fertig. Der Assistent führt dich durch alles Weitere.

---

### Wenn es nicht klappt

**Claude kommt mit „Befehl nicht gefunden" nicht weiter**
Dann einmal selbst: Terminal öffnen (Mac: `Cmd+Leertaste` → „Terminal" /
Windows: Startmenü → „PowerShell") und die drei Befehle aus der Nachricht
in Schritt 2 dort nacheinander einfügen (Installer zuerst). Danach Claude
neu starten.

**Du nutzt Claude Code im Terminal statt der Desktop-App?**
Gleiche Nachricht, gleiche Wirkung. Oder direkt in die Chat-Eingabe
(das sind Chat-Befehle, keine Shell-Befehle):

```
/plugin marketplace add jranglack-bot/scb-creator-kit
/plugin install scb-creator-kit@scb-creator-kit
```

**Update auf eine neue Version:** Claude schicken:
„Aktualisiere das SCB Creator Kit: `claude plugin update scb-creator-kit@scb-creator-kit`",
danach neu starten.

## Was du brauchst (je nach Funktion)

- **KI-Videos:** Higgsfield-Account (higgsfield.ai) — Free-Plan zum Testen
- **Video-Schnitt & Untertitel:** kostenloser ElevenLabs-API-Key + ffmpeg (installiert der Assistent)
- **Auto-Posting:** Airtable- + Make.com-Account, Instagram Business-/Creator-Konto
- **Audit & Recherche:** kostenloses Apify-Konto (apify.com)

Nichts davon ist Pflicht — der Setup-Assistent richtet nur ein, was du nutzen willst.

## Sicherheit

- Das Plugin enthält **keine** Zugangsdaten. Jeder verbindet seine eigenen Konten.
- API-Keys werden nur lokal gespeichert, nie in Cloud-Notizen oder im Chat.
- Logins (Higgsfield, Airtable, Make) machst du immer selbst im Browser —
  Claude fragt nie nach Passwörtern.

---

Made with ❤️ für die SCB Community · v0.18.0
