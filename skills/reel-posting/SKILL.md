---
name: reel-posting
description: >
  Baut ein automatisches Instagram-Posting-System mit Airtable + Make.com:
  Reels liegen in einer Airtable-Base, ein Make-Szenario postet sie geplant
  (z. B. 2× täglich) oder auf Zuruf ("Sofort Posten") auf Instagram.
  Verwende diesen Skill bei: "Auto-Posting einrichten", "Reels automatisch
  posten", "Posting-Automatisierung", "Airtable Make Instagram", "poste mein
  Reel", "Sofort Posten einrichten", "Content-Pipeline bauen".
---

# Auto-Posting: Airtable + Make + Instagram

Baue mit dem User ein Posting-System nach dem in der SCB Community erprobten
Muster. Zwei Betriebsarten aus derselben Architektur:

- **Tagesposts:** Make-Szenario läuft nach Zeitplan (z. B. 8 & 18 Uhr) und
  postet das nächste „offene" Reel.
- **Sofort Posten:** separates On-Demand-Szenario + eigene Base — ein Reel auf
  Zuruf live bringen, ohne die Tagesposts zu stören.

## Voraussetzungen (prüfen, ggf. an scb-setup verweisen)

1. **Airtable-Account** (Free reicht für den Start)
2. **Make.com-Account** (Free: 1.000 Ops/Monat reichen für 2 Posts/Tag)
3. **Instagram Business- oder Creator-Konto**, verknüpft mit einer
   Facebook-Seite (Voraussetzung der Instagram-API — im Zweifel zuerst prüfen)
4. Optional: Airtable- und Make-Connectoren in Claude verbunden (dann kann
   Claude die Base direkt lesen/schreiben und Szenarien starten)

## Schritt 1: Airtable-Base anlegen

Eine Base (z. B. „Reels") mit einer Tabelle, vier Felder:

| Feld | Typ | Zweck |
|---|---|---|
| `ID` | Text (Primary) | Sortierschlüssel: `01`, `02`, … — bestimmt die Post-Reihenfolge |
| `Status` | Single Select: `offen` / `gepostet` | Steuert, was noch gepostet wird |
| `Caption` | Long Text | Der Instagram-Begleittext (Emojis ok) |
| `Videos` | Attachment | Die Reel-Videodatei |

Für „Sofort Posten" zusätzlich eine **zweite, eigene Base** mit identischer
Struktur — so kollidieren On-Demand-Posts nie mit den Tagesposts.

## Schritt 2: Videos hochladen

**Wichtig: Airtable-Attachments haben ~5 MB Upload-Limit** (Content-API).
Reels vorher komprimieren:

```
ffmpeg -y -i IN.mp4 -vf "scale='min(1080,iw)':-2" \
  -c:v libx264 -preset medium -b:v 5500k -maxrate 6500k -bufsize 9000k \
  -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart OUT.mp4
```

Upload-Wege:
- **Von Hand:** Datei in Airtable ins Attachment-Feld ziehen (einfachster Weg).
- **Per Script/API:** Airtable Content-API
  `POST https://content.airtable.com/v0/{baseId}/{recordId}/{fieldId}/uploadAttachment`
  mit Base64-Datei. Dafür braucht der User einen **Personal Access Token (PAT)**
  von https://airtable.com/create/tokens mit Scopes `data.records:read` +
  `data.records:write`, **nur für diese Base** (least privilege).

### Stolpersteine (alle in der Praxis aufgetreten)
- PAT ohne `data.records:write` → **403** beim Anlegen/Hochladen.
- Captions mit Emojis immer als **UTF-8-Datei** übergeben, nie inline — sonst Zeichensalat.
- Beim Verifizieren per API `?returnFieldsByFieldId=true` anhängen, sonst
  wirken Felder fälschlich leer.
- PAT **niemals** in Notizen/Vault/Chat ablegen — nur in eine lokale `.env`.

## Schritt 3: Make-Szenario bauen

Modul-Kette (der User baut sie in Make zusammen; Schritt für Schritt begleiten):

1. **Airtable → Search Records:** Formel `{Status}='offen'`, Sortierung `ID`
   aufsteigend, Limit 1 → zieht genau das nächste Reel.
2. **Instagram for Business → Create a Reel Post:** Video = Attachment-URL aus
   Schritt 1, Caption = Feld `Caption`.
3. *(Optional)* **Instagram → Create a Comment:** fester Funnel-Kommentar unter
   den eigenen Post (z. B. Keyword-CTA — siehe Skill `reel-hooks`).
4. **Airtable → Update Record:** `Status` → `gepostet`.

Trigger:
- **Tagesposts:** Szenario-Schedule in Make (z. B. täglich 08:00 & 18:00).
- **Sofort Posten:** Szenario auf „on demand"; Start per Klick in Make oder —
  wenn der Make-Connector verbunden ist — durch Claude auf Zuruf.

**Hinweis:** Das Szenario muss in Make **aktiv** geschaltet sein, sonst
schlagen API-Starts fehl. Aktivieren macht der User selbst — ein On-Demand-
Szenario postet auch aktiv nichts von allein.

## Schritt 4: Testlauf

1. Einen Datensatz mit Test-Reel + Caption anlegen, `Status` = `offen`.
2. Szenario einmal manuell laufen lassen.
3. Prüfen: Post live? Status auf `gepostet` gesprungen? Kommentar da?
4. Beim „Sofort Posten"-Muster danach aufräumen: Felder des Datensatzes leeren
   (Caption `""`, Videos `[]`, Status leer), damit er fürs nächste Reel bereit ist.

## Betrieb mit Claude (wenn Connectoren verbunden)

- „Poste dieses Reel sofort" → Claude legt den Datensatz an, lädt das Video
  hoch (lokales Script/PAT), startet das Szenario, räumt auf.
- „Was ist noch offen?" → Claude liest die Base und zeigt die Warteschlange.
- Live-Posting-Aktionen kündigt Claude immer an und holt ein Okay ein.
