# ðŸŽ¬ SCB Creator Kit

Das Creator-Toolkit der SCB Community fÃ¼r Claude: KI-Reels erstellen,
Videos automatisch schneiden, mit erprobten Hook-Formeln texten und
Instagram-Posting automatisieren â€” alles in einem Plugin, gefÃ¼hrt von
einem Setup-Assistenten.

## Was steckt drin?

| Skill | Was er kann | So startest du ihn |
|---|---|---|
| **scb-setup** | Setup-Assistent: fragt ab, was du hast (Higgsfield, Make, Airtable, Obsidian â€¦) und richtet alles ein | â€žRichte das SCB Kit ein" |
| **kling-prompt-builder** | FÃ¼hrt dich zu einem perfekten Kling-3.0-Prompt (spart Credits) | â€žBau mir einen Kling-Prompt" |
| **seedance-prompt-builder** | Shot-fÃ¼r-Shot-Prompts fÃ¼r Seedance 2.0 | â€žSchreib mir einen Seedance-Prompt" |
| **video-model-prompting** | Verifizierte Prompt-Regeln pro Videomodell (Seedance 2.0, Kling 3.0, Veo 3.1, Gemini Omni Flash) â€” Modell-Eigenheiten, Kamera-Vokabular, bekannte Fallen | lÃ¤uft automatisch beim Prompt-Schreiben |
| **video-schneiden** | Schneidet Versprecher, Ã„hs und Pausen automatisch raus â€” token-optimiert (Scripts Ã¼bernehmen die Mechanik, das KI-Modell nur das Verstehen) | â€žSchneide mein Video" |
| **untertitel-und-text** | Untertitel, Hook-Texte & B-Roll-Overlays einbrennen â€” mit persÃ¶nlichem Stil-Profil: einmal einrichten (auch per Screenshot-Vorlage â€žso will ich das"), gilt fÃ¼r immer | â€žMach Untertitel drauf" / Screenshot zeigen |
| **pro-look-editing** | Pro-Look-Paket: animierte Wort-fÃ¼r-Wort-Captions (CapCut-Stil), Punch-Ins & weicher Zoom, Wisch-ÃœbergÃ¤nge mit gekoppeltem Sound, B-Roll-Einblendungen, animierte Motion-Overlays (Pfeile/Buttons/Konfetti per Green-Screen), Picture-in-Picture, Hook-Cover, Fortschrittsbalken, Color-Grade, Filmkorn, Typewriter- & Akzent-SFX â€” plus Audio-Suite: Musikbett mit Auto-Ducking, Stimm-Mastering und Loudness auf Instagram-Standard (alle Extras immer nur auf Nachfrage) | â€žMach das Video professionell" |
| **higgsfield-generate** (+ Soul ID, Photoshoot, Marketplace-Cards) | Eigene Fotos hochladen, Bilder & Videos generieren, Bild-zu-Video, Soul-Charakter fÃ¼r dein Gesicht â€” alles direkt Ã¼ber deinen Higgsfield-Account | â€žGenerier mir ein Bild/Video" |
| **instagram-audit** | Profil-Audit, Engagement-Rate & echter Wachstums-Check (15-Tage-Verlauf via Social Blade) Ã¼ber Apify (mit Kosten-Check vor jedem Lauf) | â€žIst mein Profil gewachsen?" |
| **reel-hooks** | Erprobte Hook-Formeln & Reel-Strukturen (Humor + Sales), fragt nach deinem Funnel-Keyword | â€žSchreib mir ein Reel" |
| **reel-layout** | Safe-Zones: wo Text in Reels & Stories sitzen darf | lÃ¤uft automatisch beim Bearbeiten |
| **reel-posting** | Auto-Posting-System mit Airtable + Make bauen | â€žRichte mein Auto-Posting ein" |
| **sfx-extraktion** | Soundeffekte aus Reels/Videos herausschneiden â€” automatische Erkennung in SFX-Compilation-Reels, Ablage als MP3 in deiner Bibliothek | â€žHol mir den Sound aus dem Reel" |
| **karussell-posts** | Komplette Instagram-Karussells (1080Ã—1350): Texte nach Hook-Formel, gebrandete Folien aus Templates (gerendert vom vorinstallierten Browser â€” nichts zu installieren), Kontrolle Ã¼ber einen Kontaktbogen | â€žMach mir ein Karussell zu [Thema]" |
| **obsidian-gehirn** | Claude merkt sich alles Ã¼ber dich in deinem Obsidian-Vault | â€žVerbinde Obsidian" |

ZusÃ¤tzlich empfiehlt und installiert der Setup-Assistent auf Wunsch zwei
kostenlose Community-Tools:
- **/watch** ([bradautomates/claude-video](https://github.com/bradautomates/claude-video)) â€”
  Claude kann Videos â€žansehen" und z. B. virale Reels analysieren.
- **RTK** ([rtk-ai/rtk](https://github.com/rtk-ai/rtk)) â€” komprimiert Claudes
  Terminal-Ausgaben (60â€“90 % Token-Ersparnis), dein Kontingent hÃ¤lt lÃ¤nger.
  Nach der Installation richtet der Assistent es mit `rtk init -g` direkt ein.

## Installation

### Claude Desktop-App (empfohlen)

1. Lade die Datei **`scb-creator-kit.plugin`** herunter:
   **[â¬‡ï¸ Direkt-Download (neueste Version)](https://github.com/jranglack-bot/scb-creator-kit/releases/latest/download/scb-creator-kit.plugin)**
2. Ziehe sie in ein Claude-GesprÃ¤ch und bestÃ¤tige die Installation.
3. Sag: **â€žRichte das SCB Kit ein"** â€” der Assistent Ã¼bernimmt den Rest.

### Claude Code (Terminal)

```
/plugin marketplace add jranglack-bot/scb-creator-kit
/plugin install scb-creator-kit@scb-creator-kit
```

## Was du brauchst (je nach Funktion)

- **KI-Videos:** Higgsfield-Account (higgsfield.ai) â€” Free-Plan zum Testen
- **Video-Schnitt & Untertitel:** kostenloser ElevenLabs-API-Key + ffmpeg (installiert der Assistent)
- **Auto-Posting:** Airtable- + Make.com-Account, Instagram Business-/Creator-Konto
- **Audit & Recherche:** kostenloses Apify-Konto (apify.com)
- **Obsidian-Gehirn:** Obsidian (kostenlos, obsidian.md)

Nichts davon ist Pflicht â€” der Setup-Assistent richtet nur ein, was du nutzen willst.

## Sicherheit

- Das Plugin enthÃ¤lt **keine** Zugangsdaten. Jeder verbindet seine eigenen Konten.
- API-Keys werden nur lokal gespeichert, nie in Cloud-Notizen oder im Chat.
- Logins (Higgsfield, Airtable, Make) machst du immer selbst im Browser â€”
  Claude fragt nie nach PasswÃ¶rtern.

---

Made with â¤ï¸ fÃ¼r die SCB Community Â· v0.17.1

