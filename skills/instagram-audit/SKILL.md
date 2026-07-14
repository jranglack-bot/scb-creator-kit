---
name: instagram-audit
description: >
  Instagram-Profil-Audit und Account-Recherche mit Apify: holt Profildaten
  (Bio, Follower, Posts, Engagement) strukturiert und ohne Login über
  Apify-Actors und kombiniert sie mit einem visuellen Eindruck des Profils.
  Verwende diesen Skill bei: "Instagram Audit", "analysiere mein Profil",
  "Profil-Audit", "such starke Accounts in meiner Nische",
  "Konkurrenz-Analyse Instagram", "welche Accounts funktionieren in
  [Nische]", "analysiere diesen Account".
---

# Instagram-Audit & Recherche (Apify)

Analysiere Instagram-Profile mit Apify-Actors — strukturierte Daten ganz ohne
Instagram-Login. Funktioniert für das eigene Profil (Audit) und für fremde
Accounts (Nischen-/Konkurrenz-Recherche).

## Voraussetzung: Apify-Zugang

Prüfe, ob der Apify-Connector verbunden ist (Apify-Tools verfügbar?). Falls
nicht, führe den User hin:

1. Kostenloses Konto auf **https://apify.com** erstellen — der Free-Plan
   enthält monatlich ~5 $ Guthaben, das reicht für hunderte Profil-Abrufe.
2. Verbindung mit Claude: **Apify-Connector** in den Claude-Einstellungen
   verbinden (claude.ai → Einstellungen → Connectoren → Apify suchen).
   Alternativ den API-Token nutzen: console.apify.com → **Settings →
   API & Integrations → Personal API Token** kopieren.
3. Token nie im Chat wiederholen und nie in Cloud-Notizen speichern.

## Budget-Regel (IMMER einhalten)

Apify-Actors kosten Geld pro Lauf. Vor JEDEM Actor-Start:

1. **Günstigsten passenden Actor suchen** (z. B. via Actor-Suche) — nicht den
   erstbesten nehmen. Bewährt für Profildaten:
   `apify/instagram-profile-scraper` (~0,003 $ pro Profil, liefert Bio,
   Follower, Posts, Engagement — ohne Login).
2. **Kostenschätzung nennen:** Preis × geplante Menge, in einfacher Sprache
   („Das kostet ungefähr X Cent").
3. **Auf Bestätigung warten** — erst dann starten. Ziel: im Monats-Guthaben
   des Free-Plans bleiben.

## Ablauf: Eigenes Profil-Audit

1. Der User nennt seinen Handle oder öffnet sein Profil selbst im Browser —
   Claude sucht das Profil nicht auf eigene Faust und loggt sich nirgends ein.
2. **Fakten via Apify:** Profil-Scraper auf den Handle → Bio, Follower,
   Beitragszahl, letzte Posts, Engagement.
3. **Optik separat beurteilen:** Apify liefert keinen visuellen Gesamteindruck.
   Wenn Browser-Zugriff verfügbar ist: Screenshot des Grids machen (Layout,
   Farbwelt, Konsistenz). Sonst den User um einen Screenshot bitten.
4. **Audit erstellen** — strukturiert bewerten:
   - **Bio:** Klar wer/für wen/was? CTA vorhanden? (→ Keyword-Funnel, siehe
     Skill `reel-hooks`)
   - **Grid/Optik:** roter Faden, Farbwelt, erkennbares Thema?
   - **Content-Mix:** Verhältnis Reichweiten- zu Sales-Content (Cluster 1 vs. 2)?
   - **Engagement:** Likes/Kommentare im Verhältnis zur Followerzahl?
   - **Hooks:** Stoppen die ersten Sekunden bzw. Titelzeilen den Daumen?
5. Konkrete, priorisierte Verbesserungen vorschlagen (max. 3–5, umsetzbar).

## Ablauf: Nischen-/Konkurrenz-Recherche

1. Nische und Zielgröße klären („Welche Nische, wie viele Accounts?").
2. Günstigsten Such-/Scraper-Actor wählen, Kosten schätzen, bestätigen lassen.
3. Ergebnisse verdichten: Wer wächst, welche Formate laufen, welche Hooks
   wiederholen sich? (Muster → in Obsidian `03 Hooks` sammeln, Skill
   `obsidian-gehirn`.)
4. Ableitungen für den eigenen Content vorschlagen — Strukturen übernehmen,
   nie Texte 1:1 kopieren.
