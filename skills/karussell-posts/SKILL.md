---
name: karussell-posts
description: >
  Erstellt komplette Instagram-Karussell-Posts (1080×1350): Folientexte nach
  Hook-Formel, gebrandete Folien aus HTML-Templates per vorinstalliertem
  Edge/Chrome gerendert, Qualitätskontrolle über einen einzigen
  Kontaktbogen. Verwende diesen Skill bei: "mach mir ein Karussell",
  "Carousel-Post erstellen", "Slides für Instagram", "Karussell zu [Thema]",
  "mach aus dem Reel ein Karussell", "Infografik-Post".
---

# Instagram-Karussells (Template-basiert)

Baue komplette Karussells mit minimalem Token-Verbrauch: Die HTML-Templates
sind fertig und getestet — **pro Karussell entsteht nur ein kleines
Config-JSON**, das Script rendert alle Folien und einen Kontaktbogen.

## EISERNE TOKEN-REGELN

1. **NIEMALS HTML schreiben oder ändern.** Die Templates in `templates/`
   (hook/content/cta) sind fix. Design-Wünsche = nur `brand`-Werte im JSON
   (Farben, Schrift, Account). Nur wenn der User ausdrücklich ein ANDERES
   Layout will: Template einmal anpassen, zurückspeichern — nie pro Post.
2. **NIEMALS Einzelfolien ansehen.** Qualitätskontrolle ausschließlich über
   `kontaktbogen.jpg` (alle Folien in einem Bild = eine Bild-Ansicht).
3. **Korrekturen nur im JSON** (Texte/Farben ändern → neu rendern →
   neuer Kontaktbogen). Kein Zwischenschritt braucht weitere Bilder.

## Workflow

### 1. Inhalt schreiben (das ist die eigentliche Claude-Arbeit)

- Aufbau: **Hook-Folie** (Formeln aus `reel-hooks` / der 1000-Hooks-
  Datenbank, Kategorie meist EDUCATIONAL) → **3–7 Inhalts-Folien** (eine
  Idee pro Folie, kurze Sätze, Kernbegriffe in `<b>`/`<em>` für die
  Akzentfarbe) → **CTA-Folie** mit dem Funnel-Keyword des Users (Regeln in
  `reel-hooks`: Keyword IMMER erfragen/aus dem Profil nehmen, nie erfinden;
  bei Sales-Inhalt Disclaimer-Regeln beachten).
- Texte dem User kurz als Liste zeigen, Freigabe, dann rendern.

### 2. Branding (einmal einrichten, immer nutzen)

`karussell-profil` aus Obsidian `00 Kontext/Branding.md` lesen (Codeblock
mit bg1/bg2/accent/text/font/account). Fehlt es: aus dem Untertitel-Profil
ableiten (Akzentfarbe übernehmen) oder 2–3 kurze Fragen bzw.
Screenshot-Vorlage — dann als Block speichern, nie wieder fragen.

### 3. Rendern & prüfen

```
python scripts/build_carousel.py config.json
```

(Config-Schema steht im Script-Kopf. Rendert per vorinstalliertem
Edge/Chrome — keine Installation, kein Account.) Danach NUR den
`kontaktbogen.jpg` ansehen: Texte korrekt? Nichts abgeschnitten
(lange Titel → Schriftgröße wirkt automatisch, aber prüfen)? Branding
stimmig? Dann dem User den Kontaktbogen zeigen und Freigabe holen.

### 4. Übergabe & Posten

- Fertige Folien: `slide01.png … slideNN.png` (1080×1350) — Reihenfolge =
  Dateiname. Dem User den Ordner nennen.
- Posten: manuell in der Instagram-App (Musik dort hinzufügen = lizenzfrei
  fürs Karussell irrelevant) oder automatisiert über Make („Create a
  Carousel Post"-Modul) via `reel-posting`-Strecke.

## Creator-Fotos als Sticker (automatisch verteilt)

Will der User seine eigenen Fotos auf den Folien haben („hier sind 4
Bilder von mir, pack auf jede Folie ein anderes"), genügt **eine Zeile**
in der Config:

```json
"accent_images": ["foto1.jpg", "foto2.jpg", "foto3.jpg", "foto4.jpg"]
```

Das Script verteilt die Fotos automatisch reihum auf die Folien — als
runde „Sticker" mit weißem Rahmen, Schatten und leichter Drehung, an
wechselnden, **layout-sicheren** Positionen (weichen Nummern, Titeln und
Footer aus; unten-links ist bewusst gesperrt, weil dort Text ausläuft).
Pro Folie übersteuern geht mit `"accent_image"` / `"accent_pos"`
(`tl`/`tr`/`bl`/`br`). Auf `image`-Folien gibt es keine Sticker
(Foto auf Foto wirkt unruhig). Im Kontaktbogen prüfen: kein Foto
verdeckt Text.

## Folien mit Bildern

Zwei weitere Slide-Typen für gemischte Karussells (gleiche Config, nur
`"image": "<pfad>"` dazu):

- **`image`** — Bild füllt die ganze Folie; unten dunkler Verlauf, damit
  der optionale `title` immer lesbar bleibt (funktioniert mit jedem Foto).
- **`content-image`** — Text-Folie mit abgerundeter Bildkarte oben,
  Titel + Body darunter.

Bild-Quellen: eigene Fotos/Screenshots des Users, oder KI-Bilder per
`higgsfield-generate` (Nano Banana; Vorschlags- und Kosten-Regeln von dort
beachten). Beste Qualität ab ~1080 px Breite; das Template schneidet
automatisch passend zu (object-fit cover).

## Grenzen

Für vollständig frei gestaltete Einzel-Layouts (Poster-Design pro Folie)
ist Canva die bessere Wahl — die Templates hier sind bewusst ein festes,
konsistentes System. Template-Änderungen nur auf ausdrücklichen
User-Wunsch, einmalig, nie pro Post.
