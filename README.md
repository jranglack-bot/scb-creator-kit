# 🎬 SCB Creator Kit

Das Creator-Toolkit der SCB Community für Claude: KI-Reels erstellen,
Videos automatisch schneiden, mit erprobten Hook-Formeln texten und
Instagram-Posting automatisieren — alles in einem Plugin, geführt von
einem Setup-Assistenten.

## Was steckt drin?

| Skill | Was er kann | So startest du ihn |
|---|---|---|
| **scb-setup** | Setup-Assistent: fragt ab, was du hast (Higgsfield, Make, Airtable, Obsidian …) und richtet alles ein | „Richte das SCB Kit ein" |
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
| **obsidian-gehirn** | Claude merkt sich alles über dich in deinem Obsidian-Vault | „Verbinde Obsidian" |

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
2. **Obsidian-Gehirn** — Claude merkt sich ab Minute 1 alles über dich
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

**[⬇️ HIER KLICKEN: scb-creator-kit.plugin herunterladen](https://github.com/jranglack-bot/scb-creator-kit/releases/latest/download/scb-creator-kit.plugin)**

1. **Datei herunterladen** — auf den Link oben klicken
2. **Datei in Claude ziehen** — die heruntergeladene Datei mit der Maus in ein
   Claude-Gespräch ziehen und die Rückfrage bestätigen
3. **Schreiben:** „Richte das SCB Kit ein"

Fertig. Der Assistent führt dich durch alles Weitere.

> 💡 Du brauchst die **Claude Desktop-App**. Kostenlos hier:
> [claude.ai/download](https://claude.ai/download)

---

### Wenn es nicht klappt

**„Claude sagt, er kann das nicht installieren"**
Du hast Claude vermutlich gebeten, das Plugin zu installieren, oder ihm die
GitHub-Adresse geschickt. Das funktioniert nicht, und zwar bei niemandem.
Claude installiert keine Plugins. **Du ziehst die Datei selbst ins Fenster** —
Schritt 2 oben. Das ist alles.

**„Ich finde die heruntergeladene Datei nicht"**
Sie liegt in deinem Downloads-Ordner und heißt `scb-creator-kit.plugin`.

<details>
<summary><b>Für Fortgeschrittene: Installation im Terminal (Claude Code)</b></summary>

Diese zwei Zeilen nacheinander in die Claude-Eingabe tippen (nicht ins
Betriebssystem-Terminal, sondern dorthin, wo du sonst mit Claude schreibst):

```
/plugin marketplace add jranglack-bot/scb-creator-kit
/plugin install scb-creator-kit@scb-creator-kit
```

Danach: „Richte das SCB Kit ein"
</details>

## Was du brauchst (je nach Funktion)

- **KI-Videos:** Higgsfield-Account (higgsfield.ai) — Free-Plan zum Testen
- **Video-Schnitt & Untertitel:** kostenloser ElevenLabs-API-Key + ffmpeg (installiert der Assistent)
- **Auto-Posting:** Airtable- + Make.com-Account, Instagram Business-/Creator-Konto
- **Audit & Recherche:** kostenloses Apify-Konto (apify.com)
- **Obsidian-Gehirn:** Obsidian (kostenlos, obsidian.md)

Nichts davon ist Pflicht — der Setup-Assistent richtet nur ein, was du nutzen willst.

## Sicherheit

- Das Plugin enthält **keine** Zugangsdaten. Jeder verbindet seine eigenen Konten.
- API-Keys werden nur lokal gespeichert, nie in Cloud-Notizen oder im Chat.
- Logins (Higgsfield, Airtable, Make) machst du immer selbst im Browser —
  Claude fragt nie nach Passwörtern.

---

Made with ❤️ für die SCB Community · v0.18.0
