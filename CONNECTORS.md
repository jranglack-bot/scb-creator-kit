# Connectors & Platzhalter

## Wie `~~`-Platzhalter funktionieren

Einige Skills nutzen `~~name` als Platzhalter für persönliche Werte, die bei
der Einrichtung durch deine eigenen Daten ersetzt werden. Das Plugin ist
account-neutral — jedes Community-Mitglied verbindet seine eigenen Konten.

## Platzhalter in diesem Plugin

| Platzhalter | Wofür | Woher |
|---|---|---|
| `~~elevenlabs-api-key` | Transkription beim Video-Schneiden & Untertiteln | elevenlabs.io → Profil → API Keys (Free-Konto reicht) |

## Externe Konten (jeweils dein eigenes)

| Dienst | Wofür | Verbindung |
|---|---|---|
| Higgsfield | KI-Bild-/Video-Generierung | `npm i -g @higgsfield/cli` + `higgsfield auth login` |
| Airtable | Reel-Datenbank fürs Auto-Posting | Claude-Connector + eigener PAT (nur für deine Base) |
| Make.com | Posting-Automatisierung | Claude-Connector + Szenario in deinem Make-Account |
| Apify | Profil-Audit & Nischen-Recherche | Claude-Connector oder Token: console.apify.com → Settings → API & Integrations |
| Instagram | Ziel-Plattform | Business-/Creator-Konto, in Make verbunden |
| Obsidian | Zweites Gehirn / Notizen | lokale App, Vault-Pfad wird beim Setup abgefragt |

## Empfohlenes Zusatz-Plugin (Drittanbieter)

| Plugin | Wofür | Quelle |
|---|---|---|
| `/watch` (watch@claude-video) | Claude kann Videos „ansehen": virale Reels analysieren, Transkripte ziehen | https://github.com/bradautomates/claude-video — der Setup-Assistent installiert es auf Wunsch |

Der Skill `scb-setup` fragt alles der Reihe nach ab — starte einfach mit:
**„Richte das SCB Kit ein."**
