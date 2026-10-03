"""Fremdes Karussell vermessen: Ordner mit Screenshots rein, Stilwerte raus.

    python vorlage.py <ordner>                      hoechstens zwoelf Zeilen
    python vorlage.py <ordner> --projekt name       Werte in dessen stil schreiben
                                                    und schriftprobe.png bauen
    python vorlage.py <ordner> --projekt name --text "Beispielsatz"

Liest alle Bilder im Ordner samt Unterordnern, saubere Exporte und
Handy-Screenshots mit Instagram-Rahmen. Werte gelten fuer 1080 Breite.
Die Schriftart misst es nicht: schriftprobe.png zeigen, der Mensch waehlt.

Was beim ersten Nachbau Runden gekostet hat und hier abgefangen ist:
- Instagram-Rahmen oben und unten: Postflaeche = Zeilen, in denen der
  Hintergrund ueber 70 % deckt, Median ueber alle Bilder
- Seitenzaehler oben rechts ("9/13"): rechte 20 % fuer Rand und Text aus
- JPEG-Rauschen: Farben vor dem Zaehlen auf 10er-Stufen, genauer Wert danach
  als Median der echten Pixel
- Dateireihenfolge ist nicht Folienreihenfolge: jede Folie fuer sich, Median
- Folien mit Foto nur fuer Farben, nicht fuer Rand und Schrift
- Schriftgroesse ueber den Zeilenabstand, nicht ueber die Hoehe eines Laufs
- 3:4-Vorlage: trotzdem 4:5 vorschlagen, Abstaende umgerechnet
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

import projekt as P

ENDUNGEN = {".jpg", ".jpeg", ".png", ".webp"}
BREITE = 1080
ABSTAND = {"titel": P.STIL_STD["titelAbstand"], "text": P.STIL_STD["textAbstand"]}
FORMATE = [(1.25, "4:5"), (4 / 3, "3:4"), (1.0, "1:1"), (16 / 9, "9:16")]
RECHTS = 0.8          # rechte 20 % sind Seitenzaehler und Oberflaeche
HANDY = 1.45          # hoeher als breit mal das: Screenshot mit Rahmen


# ------------------------------------------------------------------ Farben

def stufen(a):
    """JPEG-Rauschen: auf 10er-Stufen runden, sonst bleiben Flaechen unsichtbar."""
    return (np.round(a / 10.0) * 10).astype(np.int16)


def kodiere(q):
    q = q.astype(np.int32)
    return (q[..., 0] << 16) | (q[..., 1] << 8) | q[..., 2]


def dekodiere(k):
    return np.array([(k >> 16) & 255, (k >> 8) & 255, k & 255], dtype=np.int16)


def zaehlen(pixel, n=40):
    """Haeufigste Stufenfarben einer Pixelliste (N x 3)."""
    if not len(pixel):
        return []
    werte, zahl = np.unique(kodiere(stufen(pixel)), return_counts=True)
    folge = np.argsort(-zahl)[:n]
    return [(dekodiere(int(werte[i])), int(zahl[i])) for i in folge]


def abstand(a, b):
    return np.sqrt(((np.asarray(a, float) - np.asarray(b, float)) ** 2).sum(axis=-1))


def genau(pixel, stufe):
    """Echte Farbe hinter einer Stufe: zweimal Median der nahen Originalpixel
    (robust gegen Kanten), zuletzt der Mittelwert (genauer als ganze Stufen)."""
    mitte = np.asarray(stufe, float)
    for radius in (16, 8, 6):
        nah = pixel[abstand(pixel, mitte) <= radius]
        if not len(nah):
            break
        mitte = np.median(nah, axis=0) if radius > 6 else nah.mean(axis=0)
    return mitte


def hexf(c):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c)


def hell(c):
    c = np.asarray(c, float)
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


# ------------------------------------------------------------- Bilder lesen

def laden(ordner):
    aus, quer = [], 0
    for p in sorted(Path(ordner).rglob("*")):
        if p.suffix.lower() not in ENDUNGEN:
            continue
        try:
            a = np.asarray(Image.open(p).convert("RGB"))
        except Exception:
            continue
        h, w = a.shape[:2]
        if w > h * 1.05:            # quer: Kontaktbogen oder Bildschirmfoto, kein Post
            quer += 1
            continue
        # linke 80 %, jede zweite Spalte, schon gestuft: reicht fuer Zeilenanteile
        aus.append({"pfad": p, "a": a, "q": stufen(a[:, : int(w * RECHTS):2].astype(np.int16)),
                    "handy": h / w > HANDY})
    return aus, quer


def deckt(b, farbe, toleranz=10):
    """Je Zeile: Anteil der linken 80 %, der diese Farbe hat."""
    return (np.abs(b["q"] - np.asarray(farbe)).max(axis=2) <= toleranz).mean(axis=1)


def app_farbe(bilder):
    """Farbe der Instagram-App: oberste und unterste 3 % der Handy-Screenshots
    (Statusleiste, Navigation). Ohne Screenshots None."""
    zaehler = Counter()
    for b in bilder:
        if b["handy"]:
            h = b["a"].shape[0]
            rand = np.concatenate([b["a"][: h * 3 // 100], b["a"][-h * 3 // 100:]]).astype(np.int16)
            for c, n in zaehlen(rand[::2, ::2].reshape(-1, 3), 3):
                zaehler[tuple(c)] += n
    return np.array(zaehler.most_common(1)[0][0]) if zaehler else None


def flaechenfarbe(bilder, app):
    """Haeufigste Farbe, die ganze Zeilen fuellt, ohne die App-Farbe. Nur fuer
    den Rueckfall in postflaeche()."""
    kandidaten = Counter()
    for b in bilder:
        for c, n in zaehlen(b["a"][::3, ::3].reshape(-1, 3).astype(np.int16), 6):
            kandidaten[tuple(c)] += n
    beste, bestzahl = app, 0
    for c, _ in kandidaten.most_common(8):
        if app is not None and abstand(c, app) <= 10:
            continue
        zeilen = sum(int((deckt(b, c) > 0.7).sum()) for b in bilder)
        if zeilen > bestzahl:
            beste, bestzahl = np.array(c), zeilen
    return beste


def plausibel(b):
    if not b.get("post"):
        return False
    o, u = b["post"]
    return 0.95 <= (u - o) / b["a"].shape[1] <= 1.85


def _median_je_groesse(bilder, flaechen):
    gruppen = {}
    for b, f in zip(bilder, flaechen):
        if f:
            gruppen.setdefault(b["a"].shape[:2], []).append(f)
    for b in bilder:
        g = gruppen.get(b["a"].shape[:2])
        b["post"] = (int(np.median([o for o, _ in g])), int(np.median([u for _, u in g]))) if g else None


def postflaeche(bilder, app):
    """Wo im Bild liegt der Post? Saubere Exporte: ganz. Handy-Screenshots: der
    laengste Zeilenblock, in dem die App-Farbe kaum vorkommt. Das haelt auch
    bei Folien mit wechselndem Hintergrund. Rueckfall (weisser Post in weisser
    App u. ae.): Zeilen, in denen der Hintergrund ueber 70 % deckt, oberste und
    unterste. Immer Median ueber alle Bilder gleicher Groesse, nie ein Bild."""
    handy = [b for b in bilder if b["handy"]]
    for b in bilder:
        if not b["handy"]:
            b["post"] = (0, b["a"].shape[0])
    if not handy:
        return
    flaechen = []
    for b in handy:
        bloecke = laeufe(deckt(b, app) < 0.3, int(b["a"].shape[0] * 0.02))
        flaechen.append(max(bloecke, key=lambda x: x[1] - x[0]) if bloecke else None)
    _median_je_groesse(handy, flaechen)
    if all(plausibel(b) for b in handy):
        return
    bg = flaechenfarbe(handy, app)
    flaechen = []
    for b in handy:
        z = np.where(deckt(b, bg) > 0.7)[0]
        flaechen.append((z[0], z[-1] + 1) if len(z) > b["a"].shape[0] * 0.05 else None)
    _median_je_groesse(handy, flaechen)


def randpixel(n):
    """Pixel am Rand einer Folie: oben, links, rechts (ohne Zaehler oben rechts).
    Der Hintergrund umgibt den Inhalt, Karten und Fotos liegen innen."""
    h, w = n.shape[:2]
    d = max(4, w // 25)
    teile = [n[:d, : int(w * RECHTS)], n[:, :d], n[int(h * 0.2):, w - d:]]
    return np.concatenate([t[::2, ::2].reshape(-1, 3) for t in teile])


def normieren(b):
    """Postflaeche ausschneiden und auf 1080 Breite bringen."""
    o, u = b["post"]
    im = Image.fromarray(b["a"][o:u])
    h = round(im.height * BREITE / im.width)
    return np.asarray(im.resize((BREITE, h), Image.BILINEAR), dtype=np.int16)


def ist_foto(n):
    """Flache Grafik: wenige Farben decken fast alles. Foto: viele Toene."""
    z = zaehlen(n[::3, ::3].reshape(-1, 3), 6)
    return sum(c for _, c in z) / n[::3, ::3, 0].size < 0.8


def schriftfarben(posts, bg):
    """Text = kraeftigste Kontrastfarbe unter den haeufigen. Akzent = haeufigste
    Farbe, die keine Mischung aus Hintergrund und Text ist (Kantenglaettung)."""
    pixel = np.concatenate([n[::2, : int(BREITE * RECHTS):2].reshape(-1, 3) for n in posts])
    fremd = pixel[abstand(pixel, bg) > 40]
    z = zaehlen(fremd)
    if not z:
        return None, None, pixel
    oben = z[0][1]
    text = max((c for c, n in z if n >= 0.15 * oben), key=lambda c: abs(hell(c) - hell(bg)))
    richtung = text.astype(float) - bg
    alle = stufen(fremd)

    def gebuendelt(c, n):
        """Designfarbe sitzt auf einer Stufe, Fototoene verlaufen ueber viele."""
        nachbarn = (np.abs(alle - c).max(axis=1) <= 20).sum()
        return n / max(nachbarn, 1) >= 0.4

    akzent = None
    for c, n in z:
        if n < 0.03 * oben or abstand(c, text) < 30 or c.max() - c.min() < 20:
            continue                                   # Akzent hat Farbe, kein Grau
        t = np.clip(np.dot(c - bg, richtung) / np.dot(richtung, richtung), 0, 1)
        if abstand(c, bg + t * richtung) < 12 or not gebuendelt(c, n):
            continue                                   # Kantenglaettung oder Foto
        akzent = c
        break
    return text, akzent, pixel


# ------------------------------------------------------------------ Schrift

def laeufe(an, luecke=0):
    """Zusammenhaengende True-Strecken -> [(von, bis)], kleine Luecken ueberbrueckt."""
    aus, start, leer = [], None, 0
    for i, v in enumerate(an):
        if v:
            if start is None:
                start = i
            leer = 0
        elif start is not None:
            leer += 1
            if leer > luecke:
                aus.append((start, i - leer + 1)); start, leer = None, 0
    if start is not None:
        aus.append((start, len(an) - leer))
    return aus


def zeilen(n, bg, text):
    """Textzeilen einer Folie als Rumpf (ohne Ober- und Unterlaengen). Laeufe,
    die sich beruehren, trennt die Senke zwischen den Ruempfen."""
    breit = int(BREITE * RECHTS)
    kern = abstand(n[:, :breit], text) < 0.3 * abstand(text, bg)
    profil = kern.sum(axis=1)
    aus = []
    for o, u in laeufe(profil >= 2, 1):
        seg = profil[o:u]
        for o2, u2 in laeufe(seg >= 0.3 * seg.max()):
            if u2 - o2 >= 6:
                spalten = np.where(kern[o + o2: o + u2].any(axis=0))[0]
                aus.append({"oben": o + o2, "unten": o + u2, "hoehe": u2 - o2, "tinte": o,
                            "links": int(spalten[0]) if len(spalten) else breit})
    return aus, kern


def zeilenabstaende(z):
    """Abstand Grundlinie zu Grundlinie innerhalb eines Absatzes."""
    aus = []
    for a, b in zip(z, z[1:]):
        h1, h2 = a["hoehe"], b["hoehe"]
        teilung = b["unten"] - a["unten"]
        if 0.6 <= h2 / h1 <= 1.6 and teilung <= 3.2 * max(h1, h2):
            aus.append((teilung, max(h1, h2)))
    return aus


def zwei_gruppen(werte):
    """Titel- und Textzeilen trennen (1D, zwei Mittelwerte)."""
    w = np.sort(np.asarray(werte, float))
    if len(w) < 2:
        return w, np.array([])
    beste, bestfehler = None, None
    for i in range(1, len(w)):
        a, b = w[:i], w[i:]
        f = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
        if bestfehler is None or f < bestfehler:
            beste, bestfehler = i, f
    klein, gross = w[:beste], w[beste:]
    if np.median(gross) / np.median(klein) < 1.3:
        return w, np.array([])
    return klein, gross


# ------------------------------------------------------------------ Ablauf

def format_von(verh):
    for v, name in FORMATE:
        if abs(verh - v) / v < 0.025:
            return v, name
    return verh, "%.2f:1" % verh


def messen(ordner):
    bilder, quer = laden(ordner)
    if not bilder:
        sys.exit("Keine Bilder im Hochformat in %s" % ordner)
    app = app_farbe(bilder)
    postflaeche(bilder, app)
    nutzbar = [b for b in bilder if plausibel(b)]
    if not nutzbar:
        sys.exit("Postflaeche nicht erkennbar (Hintergrund wie die App?)")
    posts = [normieren(b) for b in nutzbar]
    # Hintergrund = Randfarbe, die die meisten Folien haben
    raender = [randpixel(n) for n in posts]
    je = [zaehlen(px, 1)[0][0] for px in raender]
    bg_stufe = np.array(Counter(tuple(c) for c in je).most_common(1)[0][0])
    eigen = [i for i, c in enumerate(je) if abstand(c, bg_stufe) <= 10]
    gleich = [posts[i] for i in eigen]            # Folien im Look der Vorlage
    # genauer Wert aus der ganzen Flaeche, der Bildrand hat Kompressionsraender
    bg = genau(np.concatenate([n[::2, ::2].reshape(-1, 3) for n in gleich]), bg_stufe)
    flach = [n for n in gleich if not ist_foto(n)] or gleich
    text_st, akzent_st, pixel = schriftfarben(gleich, bg)
    text = genau(pixel, text_st) if text_st is not None else None
    akzent = genau(pixel, akzent_st) if akzent_st is not None else None

    hoehe = int(np.median([n.shape[0] for n in posts]))
    verh, fname = format_von(hoehe / BREITE)
    hoehe = round(BREITE * verh)

    r = {"bilder": len(bilder) + quer, "vermessen": len(nutzbar), "foto": len(gleich) - len(flach),
         "anders": len(posts) - len(gleich),
         "handy": sum(b["handy"] for b in nutzbar), "quer": quer,
         "bg": bg, "text": text, "akzent": akzent, "hoehe": hoehe, "format": fname}
    if text is None:
        return r

    raender, kanten, teilungen = [], [], []
    for n in flach:
        z, _ = zeilen(n, bg, text)
        if not z:
            continue
        kanten.append(z[0]["tinte"])         # oberste Tinte, mit Oberlaengen
        links = sorted(x["links"] for x in z)
        raender.append(links[len(links) // 4])
        teilungen += zeilenabstaende(z)
    if raender:
        # Buchstaben beginnen etwas rechts vom Kasten (Vorbreite ~0,05 Schriftgroessen)
        r["randX"] = int(np.median(raender))
    if kanten:
        r["kante"] = int(np.median(kanten))
    if teilungen:
        klein, gross = zwei_gruppen([t for t, _ in teilungen])
        if len(gross):
            r["titelTeilung"], r["textTeilung"] = float(np.median(gross)), float(np.median(klein))
        elif np.median(klein) / ABSTAND["text"] > 55:
            r["titelTeilung"] = float(np.median(klein))
        else:
            r["textTeilung"] = float(np.median(klein))
    if "titelTeilung" in r:
        r["titel"] = round(r["titelTeilung"] / ABSTAND["titel"])
    if "textTeilung" in r:
        r["textgroesse"] = round(r["textTeilung"] / ABSTAND["text"])
    if "randX" in r:
        r["randX"] -= round(0.05 * (r.get("textgroesse") or r.get("titel") or 0))
    if "kante" in r:
        # Der Kasten beginnt ueber der Tinte: Montserrat-Grossbuchstaben
        # setzen bei Zeilenabstand 1,17 etwa 0,24 Schriftgroessen tiefer an.
        erste = r.get("titel") or r.get("textgroesse") or 0
        r["randOben"] = max(0, round(r["kante"] - 0.24 * erste))
    return r


def pct(px, ganz):
    return ("%.1f" % (100.0 * px / ganz)).replace(".", ",")


def ausgeben(r):
    z = ["%d Bilder, %d vermessen%s%s%s%s" % (
        r["bilder"], r["vermessen"],
        ", davon %d Handy-Screenshots" % r["handy"] if r["handy"] else "",
        ", %d mit Foto nur fuer Farben" % r["foto"] if r["foto"] else "",
        ", %d mit anderem Hintergrund nur fuers Format" % r["anders"] if r["anders"] else "",
        ", %d quer uebersprungen" % r["quer"] if r["quer"] else "")]
    z.append("Hintergrund    %s" % hexf(r["bg"]))
    z.append("Textfarbe      %s" % (hexf(r["text"]) if r["text"] is not None else "nicht gefunden"))
    z.append("Akzentfarbe    %s" % (hexf(r["akzent"]) if r["akzent"] is not None else "keine gefunden"))
    z.append("Format         %s (%dx%d)" % (r["format"], BREITE, r["hoehe"]))
    if "randX" in r:
        z.append("Rand links     %s %%  (%d px)" % (pct(r["randX"], BREITE), r["randX"]))
    if "kante" in r:
        z.append("Textoberkante  %s %%  (Tinte ab %d px, Kasten randOben %d)" % (
            pct(r["kante"], r["hoehe"]), r["kante"], r["randOben"]))
    if "titel" in r:
        z.append("Titel          ~%d px  (Zeilenabstand %d px)" % (r["titel"], round(r["titelTeilung"])))
    if "textgroesse" in r:
        z.append("Text           ~%d px  (Zeilenabstand %d px)" % (r["textgroesse"], round(r["textTeilung"])))
    if r["format"] != "4:5":
        v = vorschlag(r)
        z.append("Vorschlag      4:5 fuer automatisches Posten: 1080x1350, randOben %s, randUnten %d"
                 % (v.get("randOben", "-"), v["randUnten"]))
    return z


def vorschlag(r):
    """stil fuer ein neues Projekt, immer 4:5. Breite und Schriftgroessen
    bleiben, Abstaende von oben und unten gehen mit der Hoehe."""
    f = 1350 / r["hoehe"]
    st = {"breite": BREITE, "hoehe": 1350, "bg": hexf(r["bg"]),
          "randUnten": P.STIL_STD["randUnten"],
          "titelAbstand": ABSTAND["titel"], "textAbstand": ABSTAND["text"]}
    if r["text"] is not None:
        st["text"] = hexf(r["text"])
    if r["akzent"] is not None:
        st["akzent"] = hexf(r["akzent"])
    for k in ("randX", "titel", "textgroesse"):
        if k in r:
            st[k] = r[k]
    if "randOben" in r:
        st["randOben"] = round(r["randOben"] * f)
    return st


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    name = P.aus_argv(args)
    probe = None
    if "--text" in args:
        i = args.index("--text")
        probe = args[i + 1] if i + 1 < len(args) else None
    frei = [a for a in args if not a.startswith("--") and a not in (name, probe)]
    if not frei:
        print(__doc__); sys.exit()
    r = messen(frei[0])
    zeilen_aus = ausgeben(r)
    if name:
        neu = not P.gueltig(P.slug(name))
        name = P.neu(name, "45") if neu else P.slug(name)
        d = P.lesen(name)
        d["stil"] = {**P.stil(d), **vorschlag(r)}
        P.schreiben(d, name)
        P.setzen(name)
        import schriftprobe
        bild = schriftprobe.bauen(probe or "Was ist dein unfairer Vorteil", name=name)
        zeilen_aus.append("Projekt %s %s, stil gesetzt, Cockpit zeigt es. Schriftprobe: %s"
                          % (name, "angelegt" if neu else "aktualisiert", bild))
    print("\n".join(zeilen_aus[:12]))
