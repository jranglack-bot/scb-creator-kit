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
| **pro-look-editing** | Pro-Look-Paket: animierte Wort-für-Wort-Captions (CapCut-Stil), Punch-Ins, Picture-in-Picture mit animiertem Hintergrund, Color-Grade, Filmkorn, SFX — über getestete Templates, minimaler Token-Verbrauch | „Mach das Video professionell" |
| **higgsfield-generate** (+ Soul ID, Photoshoot, Marketplace-Cards) | Eigene Fotos hochladen, Bilder & Videos generieren, Bild-zu-Video, Soul-Charakter für dein Gesicht — alles direkt über deinen Higgsfield-Account | „Generier mir ein Bild/Video" |
| **instagram-audit** | Profil-Audit, Engagement-Rate & echter Wachstums-Check (15-Tage-Verlauf via Social Blade) über Apify (mit Kosten-Check vor jedem Lauf) | „Ist mein Profil gewachsen?" |
| **reel-hooks** | Erprobte Hook-Formeln & Reel-Strukturen (Humor + Sales), fragt nach deinem Funnel-Keyword | „Schreib mir ein Reel" |
| **reel-layout** | Safe-Zones: wo Text in Reels & Stories sitzen darf | läuft automatisch beim Bearbeiten |
| **reel-posting** | Auto-Posting-System mit Airtable + Make bauen | „Richte mein Auto-Posting ein" |
| **obsidian-gehirn** | Claude merkt sich alles über dich in deinem Obsidian-Vault | „Verbinde Obsidian" |

Zusätzlich empfiehlt und installiert der Setup-Assistent auf Wunsch zwei
kostenlose Community-Tools:
- **/watch** ([bradautomates/claude-video](https://github.com/bradautomates/claude-video)) —
  Claude kann Videos „ansehen" und z. B. virale Reels analysieren.
- **RTK** ([rtk-ai/rtk](https://github.com/rtk-ai/rtk)) — komprimiert Claudes
  Terminal-Ausgaben (60–90 % Token-Ersparnis), dein Kontingent hält länger.
  Nach der Installation richtet der Assistent es mit `rtk init -g` direkt ein.

## Installation

### Claude Desktop-App (empfohlen)

1. Lade die Datei **`scb-creator-kit.plugin`** herunter:
   **[⬇️ Direkt-Download (neueste Version)](https://github.com/jranglack-bot/scb-creator-kit/releases/latest/download/scb-creator-kit.plugin)**
2. Ziehe sie in ein Claude-Gespräch und bestätige die Installation.
3. Sag: **„Richte das SCB Kit ein"** — der Assistent übernimmt den Rest.

### Claude Code (Terminal)

```
/plugin marketplace add jranglack-bot/scb-creator-kit
/plugin install scb-creator-kit@scb-creator-kit
```

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

Made with ❤️ für die SCB Community · v0.9.0
