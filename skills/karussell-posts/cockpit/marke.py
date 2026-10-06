"""Markenpaket: Farben, Schriften, Logos und Instagram-Name fuer alle Karussells.

Liegt im Karussell-Ordner unter marke/ (marke.json plus Logo-Dateien), nie im Kit.

anwenden() bringt ein Karussell in die Marke:
  - Farben: Akzent der Vorlage -> Akzent der Marke, helle Toene davon -> gleich
    helle Toene des neuen Akzents. Hintergrund und Text -> Hell und Dunkel der
    Marke, so dass eine dunkle Vorlage dunkel bleibt und eine helle hell.
    Weitere Farben der Vorlage -> weitere Markenfarben der Reihe nach, sonst
    bleiben sie (z. B. Rot und Gruen fuer falsch und richtig).
  - Schriften: Ueberschriften (ab 56 px oder Rolle titel) -> Titel-Schrift,
    alles andere -> Text-Schrift; Schrift-Tags im Text fallen weg.
  - Logo auf jede Folie: unten links, Folien mit dem Logo bleiben, wie sie sind.
Cockpit (ueber den Server) und k.py rechnen beide hier.
"""
import json
import math
import os
import re
import shutil
from pathlib import Path

import projekt as P

MAX_FARBEN, MAX_LOGOS = 12, 8
LOGO_ARTEN = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
LOGO_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]{0,80}")
SCHRIFT_NAME = re.compile(r"[A-Za-z0-9 ]{1,60}")
FARBE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
FARB_TAG = re.compile(r"<c=(#[0-9a-fA-F]{3,8})>")
SCHRIFT_TAG = re.compile(r"<f=[^>]{0,64}>|</f>")
FARB_FELDER = {"farbe", "farbe2", "fuellung", "geraetfarbe"}
TITEL_AB = 56                      # px: ab hier gilt ein Text als Ueberschrift


def ordner():
    return P.DATEN / "marke"


def leer():
    return {"name": "", "farben": [], "titel": "", "text": "", "logos": []}


# ------------------------------------------------------------ Farben
def norm(f):
    """'#ABC' -> '#aabbcc'. Alpha (#rgba, #rrggbbaa) zaehlt nicht mit."""
    if not isinstance(f, str) or not FARBE.fullmatch(f.strip()):
        return None
    h = f.strip().lower()[1:]
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    return "#" + h[:6]


def _rgb(f):
    return [int(f[i:i + 2], 16) for i in (1, 3, 5)]


def helligkeit(f):
    """Relative Leuchtdichte 0 bis 1 (WCAG)."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(f)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _ton_von(farbe, basis):
    """Ist farbe ein mit Weiss aufgehellter Ton von basis? Dann der Anteil Weiss (0 bis 1)."""
    if not basis or farbe == basis:
        return None
    a, c = _rgb(basis), _rgb(farbe)
    anteile = [(cc - aa) / (255 - aa) for aa, cc in zip(a, c) if aa < 245]
    if not anteile or min(anteile) < 0.3:
        return None
    t = sum(anteile) / len(anteile)
    rest = max(abs(round(aa + (255 - aa) * t) - cc) for aa, cc in zip(a, c))
    return t if rest <= 14 and t < 0.98 else None


def _aufhellen(farbe, t):
    return "#" + "".join("%02x" % round(c + (255 - c) * t) for c in _rgb(farbe))


def _mischen(a, b, t):
    return "#" + "".join("%02x" % round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b)))


def farbtausch(stil, marke):
    """Alte Farbe -> neue Farbe (beide als #rrggbb)."""
    f = list(marke.get("farben") or [])
    if not f:
        return {}
    tausch = {}
    alt_akz, alt_bg, alt_txt = norm(stil.get("akzent")), norm(stil.get("bg")), norm(stil.get("text"))
    if alt_akz:
        tausch[alt_akz] = f[0]
    dunkel = f[1] if len(f) > 1 else None
    hell = f[2] if len(f) > 2 else None
    dunkle_vorlage = bool(alt_bg) and helligkeit(alt_bg) < 0.2
    if alt_bg and alt_txt and alt_bg != alt_txt:
        dunkle_vorlage = helligkeit(alt_bg) < helligkeit(alt_txt)
        neu_bg, neu_txt = (dunkel, hell) if dunkle_vorlage else (hell, dunkel)
        if neu_bg and alt_bg not in tausch:
            tausch[alt_bg] = neu_bg
        if neu_txt and alt_txt not in tausch:
            tausch[alt_txt] = neu_txt
    weitere = f[3:]
    palette = stil.get("palette") if isinstance(stil.get("palette"), list) else []
    for roh in palette[:MAX_FARBEN]:
        alt = norm(roh)
        if not alt or alt in tausch:
            continue
        t = _ton_von(alt, alt_akz)
        if t is not None:
            tausch[alt] = _aufhellen(f[0], t)
        elif weitere:
            tausch[alt] = weitere.pop(0)
        # Ohne weitere Markenfarben: sehr dunkle Toene einer dunklen Vorlage (z. B. der
        # zweite Ton eines Verlaufs) werden ein Hauch Akzent im Markendunkel, sehr helle
        # einer hellen Vorlage ein Hauch Akzent im Markenhell. Mittlere Farben bleiben
        # (Silber und Bronze, Rot und Gruen fuer falsch und richtig).
        elif dunkle_vorlage and dunkel and helligkeit(alt) < 0.1:
            tausch[alt] = _mischen(dunkel, f[0], 0.18)
        elif not dunkle_vorlage and hell and helligkeit(alt) > 0.8:
            tausch[alt] = _mischen(hell, f[0], 0.08)
    return {a: n for a, n in tausch.items() if a != n}


def _farbe_neu(wert, tausch):
    """Farbwert tauschen, Alpha bleibt (#rrggbbaa)."""
    alt = norm(wert)
    if not alt or alt not in tausch:
        return wert, False
    h = wert.strip().lower()[1:]
    alpha = h[6:8] if len(h) == 8 else (h[3] * 2 if len(h) == 4 else "")
    return tausch[alt] + alpha, True


def _farben_im_baum(o, tausch, zaehler, tiefe=0):
    """Farbfelder in Bloecken und Folienhintergruenden, auch verschachtelt (rand, schatten ...)."""
    if tiefe > 8:
        return
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k in FARB_FELDER and isinstance(v, str):
                neu, ja = _farbe_neu(v, tausch)
                if ja:
                    o[k] = neu
                    zaehler[0] += 1
            elif k == "text" and isinstance(v, str) and "<c=#" in v:
                def tag(m):
                    neu, ja = _farbe_neu(m.group(1), tausch)
                    zaehler[0] += ja
                    return "<c=%s>" % neu
                o[k] = FARB_TAG.sub(tag, v)
            elif isinstance(v, (dict, list)):
                _farben_im_baum(v, tausch, zaehler, tiefe + 1)
    elif isinstance(o, list):
        for x in o[:5000]:
            _farben_im_baum(x, tausch, zaehler, tiefe + 1)


# ------------------------------------------------------------ Schriften
def _zahl(v, std):
    try:
        z = float(v)
        return z if z == z and abs(z) < 1e6 else std
    except (TypeError, ValueError):
        return std


def _ist_ueberschrift(b, stil):
    if b.get("rolle") == "titel":
        return True
    g = b.get("groesse")
    if g in (None, ""):
        g = stil.get("textgroesse", 40) if b.get("rolle") == "text" else 48
    return _zahl(g, 0) >= TITEL_AB


# ------------------------------------------------------------ Markenpaket lesen und schreiben
def pruefen(roh):
    """Nur gueltige Werte, alles andere faellt weg (auch bei fremden Dateien)."""
    m = leer()
    if not isinstance(roh, dict):
        return m
    if isinstance(roh.get("name"), str):
        m["name"] = re.sub(r"[^A-Za-z0-9._]", "", roh["name"])[:30]
    if isinstance(roh.get("farben"), list):
        for f in roh["farben"][:MAX_FARBEN]:
            n = norm(f)
            if n and n not in m["farben"]:
                m["farben"].append(n)
    for k in ("titel", "text"):
        if isinstance(roh.get(k), str) and SCHRIFT_NAME.fullmatch(roh[k]):
            m[k] = roh[k]
    if isinstance(roh.get("logos"), list):
        for l in roh["logos"][:MAX_LOGOS]:
            if isinstance(l, str) and LOGO_NAME.fullmatch(l) and Path(l).suffix.lower() in LOGO_ARTEN \
                    and l not in m["logos"] and (ordner() / l).is_file():
                m["logos"].append(l)
    return m


def lesen():
    """Fehlt die Datei, ist das Paket leer. Jeder andere Fehler bricht ab: sonst
    schriebe die naechste Aenderung ein leeres Paket ueber das echte."""
    p = ordner() / "marke.json"
    try:
        if p.stat().st_size > 256_000:
            raise ValueError("marke.json ist zu gross")
        roh = p.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return leer()
    try:
        return pruefen(json.loads(roh))
    except (ValueError, RecursionError):
        raise ValueError("marke/marke.json ist beschaedigt, bitte reparieren oder loeschen")


def _ordner_sicher():
    o = ordner()
    if os.path.lexists(o) and P._verknuepft(o):
        raise ValueError("marke ist eine Verknuepfung")
    o.mkdir(parents=True, exist_ok=True)
    return o


def schreiben(roh):
    o = _ordner_sicher()
    m = pruefen(roh)
    P.sicher_schreiben(o / "marke.json", json.dumps(m, ensure_ascii=True, indent=2).encode("ascii"))
    return m


def logo_ablegen(dateiname, daten, ablegen):
    """Logo hochladen. ablegen(ordner, datei, daten) prueft und speichert das Bild
    (bauen.bild_ablegen). Gibt das neue Markenpaket zurueck."""
    m = lesen()
    if len(m["logos"]) >= MAX_LOGOS:
        raise ValueError("Höchstens %d Logos" % MAX_LOGOS)
    datei = re.sub(r"[^A-Za-z0-9_.\-]", "_", Path(str(dateiname)).name).strip(". -")[:60] or "logo.png"
    if not LOGO_NAME.fullmatch(datei) or Path(datei).suffix.lower() not in LOGO_ARTEN:
        raise ValueError("Logo bitte als PNG, JPG, WEBP oder SVG")
    if datei == "marke.json" or datei.startswith("."):
        raise ValueError("ungueltiger Dateiname")
    name = ablegen(_ordner_sicher(), datei, daten)
    m["logos"] = [l for l in m["logos"] if l != name] + [name]
    return schreiben(m)


def logo_weg(datei):
    m = lesen()
    if datei in m["logos"]:
        m["logos"] = [l for l in m["logos"] if l != datei]
        p = ordner() / datei
        if p.is_file() and not p.is_symlink():
            p.unlink()
    return schreiben(m)


RASTER = ["PNG", "JPEG", "WEBP", "GIF"]       # nur diese Formate oeffnet PIL (kein EPS, kein PSD)


def _logo_gueltig(pfad):
    """Nur echte Bilder aus einem (vielleicht fremden) Markenordner ins Projekt."""
    if pfad.suffix.lower() == ".svg":
        return "<svg" in pfad.read_bytes()[:4096].decode("utf-8", "ignore").lower()
    try:
        from PIL import Image
        with Image.open(pfad, formats=RASTER) as im:
            im.verify()
        return True
    except Exception:
        return False


def _logo_masse(pfad):
    """Breite zu Hoehe des Logos (fuer eine Box ohne Anschnitt), immer endlich."""
    v = _logo_masse_roh(pfad)
    return v if math.isfinite(v) and 0.05 <= v <= 20 else 1.0


def _logo_masse_roh(pfad):
    try:
        if pfad.suffix.lower() == ".svg":
            kopf = pfad.read_text(encoding="utf-8", errors="ignore")[:4000]
            vb = re.search(r'viewBox\s*=\s*["\']\s*[-\d.]+[ ,]+[-\d.]+[ ,]+([\d.]+)[ ,]+([\d.]+)', kopf)
            if vb and float(vb.group(2)) > 0:
                return float(vb.group(1)) / float(vb.group(2))
            w = re.search(r'\swidth\s*=\s*["\']([\d.]+)', kopf)
            h = re.search(r'\sheight\s*=\s*["\']([\d.]+)', kopf)
            if w and h and float(h.group(1)) > 0:
                return float(w.group(1)) / float(h.group(1))
            return 1.0
        from PIL import Image
        with Image.open(pfad, formats=RASTER) as im:
            return im.width / im.height if im.height else 1.0
    except Exception:
        return 1.0


def logo_ins_projekt(name, logo):
    """Logo in den Projektordner kopieren (Exporte brauchen alle Bilder dort).
    Gibt (Dateiname im Projekt, Seitenverhaeltnis) zurueck."""
    if not (isinstance(logo, str) and logo in lesen()["logos"]):
        raise ValueError("Logo gibt es nicht im Markenpaket")
    q = ordner() / logo
    if q.is_symlink() or not q.is_file() or q.stat().st_size > 20_000_000 or not _logo_gueltig(q):
        raise ValueError("Logo nicht lesbar")
    ziel_ordner = P.ordner(name)
    daten = q.read_bytes()
    stamm, endung = Path("marke-" + logo).stem, Path(logo).suffix
    ziel, n = ziel_ordner / ("marke-" + logo), 2
    while ziel.exists() and ziel.read_bytes() != daten:
        ziel = ziel_ordner / ("%s_%d%s" % (stamm, n, endung))
        n += 1
    if ziel.is_symlink():
        raise ValueError("Ziel ist eine Verknuepfung")
    if not ziel.exists():
        shutil.copyfile(q, ziel)
    return ziel.name, _logo_masse(q)


def logo_block(datei, verhaeltnis, stil, neue_id):
    """Logo unten links, 160 px breit (hoechstens 120 px hoch)."""
    B, H = _zahl(stil.get("breite"), 1080), _zahl(stil.get("hoehe"), 1350)
    v = max(0.2, min(_zahl(verhaeltnis, 1), 8))
    w = 160.0
    h = w / v
    if h > 120:
        h, w = 120.0, 120.0 * v
    rand = round(B * 0.089)                 # wie die Raender der Vorlagen (96 px bei 1080)
    return {"id": neue_id, "typ": "bild", "datei": datei, "x": rand, "y": round(H - rand - h),
            "w": round(w), "h": round(h)}


# ------------------------------------------------------------ Anwenden
def _neue_id(d):
    da = set()
    for s in d.get("slides") or []:
        for b in (s.get("bloecke") or []) if isinstance(s, dict) else []:
            if isinstance(b, dict) and isinstance(b.get("id"), str):
                da.add(b["id"])
    n = 1
    while "b%d" % n in da:
        n += 1
    return "b%d" % n


def anwenden(d, marke=None, farben=True, schriften=True, logo=False, projekt=None):
    """Karussell-Daten in die Marke bringen (aendert d). Gibt eine kurze Meldung zurueck."""
    marke = marke or lesen()
    if not isinstance(d, dict) or not isinstance(d.get("slides"), list):
        raise ValueError("keine Karusselldaten")
    st = d.setdefault("stil", {})
    if not isinstance(st, dict):
        st = d["stil"] = {}
    st_voll = P.stil(d)
    teile = []
    if farben and marke["farben"]:
        tausch = farbtausch(st_voll, marke)
        z = [0]
        for k in ("bg", "text", "akzent"):
            neu, ja = _farbe_neu(st_voll.get(k), tausch) if isinstance(st_voll.get(k), str) else (None, False)
            if ja:
                st[k] = neu
                z[0] += 1
        if isinstance(st.get("palette"), list):
            st["palette"] = [(_farbe_neu(c, tausch)[0] if isinstance(c, str) else c) for c in st["palette"][:MAX_FARBEN]]
        for m in marke["farben"]:                       # Markenfarben stehen danach in der Palette
            if isinstance(st.get("palette"), list) and m not in [norm(c) for c in st["palette"]]:
                st["palette"] = (st["palette"] + [m])[:MAX_FARBEN]
        _farben_im_baum(d["slides"], tausch, z)
        teile.append("Farben an %d Stellen" % z[0])
    if schriften and (marke["titel"] or marke["text"]):
        text = marke["text"] or st_voll.get("schrift")
        titel = marke["titel"] or text
        st["schrift"] = text
        n = 0
        for s in d["slides"]:
            for b in (s.get("bloecke") or []) if isinstance(s, dict) else []:
                if not isinstance(b, dict) or b.get("typ") in ("bild", "form"):
                    continue
                ziel = titel if _ist_ueberschrift(b, st_voll) else text
                if ziel != text:
                    b["font"] = ziel
                else:
                    b.pop("font", None)
                if isinstance(b.get("text"), str):
                    b["text"] = SCHRIFT_TAG.sub("", b["text"])
                n += 1
        teile.append("Schriften in %d Texten" % n)
    if logo and marke["logos"] and projekt:
        datei, v = logo_ins_projekt(projekt, marke["logos"][0])
        da = {b.get("id") for s in d["slides"] if isinstance(s, dict)
              for b in (s.get("bloecke") or []) if isinstance(b, dict)}
        zaehler, n = [1], 0

        def neue_id():                      # einmal zaehlen statt je Folie neu suchen
            while "b%d" % zaehler[0] in da:
                zaehler[0] += 1
            da.add("b%d" % zaehler[0])
            return "b%d" % zaehler[0]
        for s in d["slides"][:100]:
            if not isinstance(s, dict):
                continue
            bl = s.setdefault("bloecke", [])
            if not isinstance(bl, list) or any(isinstance(b, dict) and b.get("datei") == datei for b in bl):
                continue
            bl.append(logo_block(datei, v, st_voll, neue_id()))
            n += 1
        teile.append("Logo auf %d Folien" % n)
    return ", ".join(teile) or "nichts zu tun (Markenpaket leer)"


def anwenden_auf_projekt(name, **wahl):
    d = P.lesen(name)
    meldung = anwenden(d, projekt=name, **wahl)
    P.schreiben(d, name)
    return meldung
