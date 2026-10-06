"""Google Fonts fuers Cockpit: suchen, bei Bedarf laden, danach offline.

    python schriften.py suche <wort> [--art serif|sans|display|hand|mono]
    python schriften.py laden "Roboto Slab"
    python schriften.py liste
    python schriften.py datei <pfad.ttf|.otf|.woff>     eigene Schriftdatei

Verzeichnis: bib/fonts.json (aus fonts.google.com, liegt beim Code).
Geladene Schriften liegen im Karussell-Ordner (ueberleben Updates):
schriften/google/<ordner>/<staerke>[i].ttf, Liste in schriften/google.json,
@font-face-Regeln in schriften/google.css. Der Server liefert sie unter
fonts/google* aus. Lizenzen: OFL oder Apache, frei nutzbar, auch in Canva.
"""
import json, os, re, struct, sys, urllib.parse, urllib.request
from pathlib import Path

import projekt as P

HIER = P.HIER
VERZEICHNIS = HIER / "bib" / "fonts.json"
ORDNER = P.SCHRIFTEN / "google"
LISTE = P.SCHRIFTEN / "google.json"
CSS = P.SCHRIFTEN / "google.css"
HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}
TTF_KOPF = (b"\x00\x01\x00\x00", b"true", b"OTTO")
STAERKEN = ["400", "500", "600", "700", "800"]
KURSIV = ["400", "700"]
MAX_DATEI = 6_000_000
NAME = re.compile(r"[A-Za-z0-9 ]{1,60}")
ARTEN = {"serif": "Serif", "sans": "Sans Serif", "display": "Display",
         "hand": "Handwriting", "mono": "Monospace"}


def verzeichnis():
    return json.loads(VERZEICHNIS.read_text(encoding="utf-8"))


ORDNER_OK = re.compile(r"[a-z0-9][a-z0-9-]{0,79}")
DATEI_OK = re.compile(r"\d{3}(?:-\d{3})?i?\.(?:ttf|otf|woff)")
STAERKE_OK = re.compile(r"\d{3}(?: \d{3})?")


def _eintrag(e):
    """Nur saubere Eintraege aus google.json: sie landen woertlich in google.css."""
    if not (isinstance(e, dict) and isinstance(e.get("family"), str) and NAME.fullmatch(e["family"])
            and isinstance(e.get("ordner"), str) and ORDNER_OK.fullmatch(e["ordner"])
            and isinstance(e.get("dateien"), list)):
        return None
    dateien = [d for d in e["dateien"][:40] if isinstance(d, dict) and isinstance(d.get("datei"), str)
               and DATEI_OK.fullmatch(d["datei"]) and isinstance(d.get("w"), str)
               and STAERKE_OK.fullmatch(d["w"]) and isinstance(d.get("i"), bool)]
    return dict(e, dateien=dateien) if dateien else None


def installiert(streng=False):
    """streng: beim Schreiben lieber abbrechen als eine unlesbare Liste durch eine
    fast leere zu ersetzen."""
    try:
        liste = json.loads(LISTE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, ValueError, RecursionError):
        if streng:
            raise ValueError("schriften/google.json ist nicht lesbar, bitte reparieren")
        return []
    if not isinstance(liste, list):
        if streng:
            raise ValueError("schriften/google.json ist beschaedigt")
        return []
    return [x for x in (_eintrag(e) for e in liste[:500]) if x]


def namen():
    """Familiennamen aller geladenen Google-Schriften."""
    return [e["family"] for e in installiert()]


def ordnername(family):
    return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")


def suchen(frage="", art=None, n=40):
    frage = (frage or "").lower().strip()
    kat = ARTEN.get(art, art)
    treffer = []
    for e in verzeichnis():
        if kat and e["k"] != kat:
            continue
        nm = e["f"].lower()
        if frage and frage not in nm:
            continue
        treffer.append((0 if nm.startswith(frage) else 1, e["p"], e["f"]))
    return [t[2] for t in sorted(treffer)[:n]]


def _holen(url, grenze):
    from urllib.parse import urlsplit
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib"})
    with urllib.request.urlopen(req, timeout=30, context=P.ssl_kontext()) as r:
        if urlsplit(r.geturl()).hostname not in HOSTS:      # keine Umleitung woandershin
            raise ValueError("Umleitung zu fremdem Server")
        daten = r.read(grenze + 1)
    if len(daten) > grenze:
        raise ValueError("Datei zu gross")
    return daten


def _css_schreiben(liste):
    zeilen = ["/* Von schriften.py erzeugt. Nicht von Hand aendern. */"]
    for e in liste:
        for d in e["dateien"]:
            zeilen.append("@font-face{font-family:'%s';src:url('google/%s/%s');font-weight:%s;"
                          "font-style:%s;font-display:block}" % (
                              e["family"], e["ordner"], d["datei"], d["w"],
                              "italic" if d["i"] else "normal"))
    P.sicher_schreiben(CSS, ("\n".join(zeilen) + "\n").encode("utf-8"))


def laden(family):
    """Schrift von Google holen. Nur Familien aus dem Verzeichnis, nur Dateien
    von fonts.gstatic.com, nur TTF. Gibt den Familiennamen zurueck."""
    eintrag = next((e for e in verzeichnis() if e["f"] == family), None)
    if not eintrag or not NAME.fullmatch(family):
        raise ValueError("Schrift nicht im Verzeichnis: %s" % family)
    if family in namen():
        return family
    normal = [w for w in STAERKEN if w in eintrag["v"]] or [eintrag["v"][0].rstrip("i")]
    kursiv = [w for w in KURSIV if w + "i" in eintrag["v"]]
    achsen = ";".join(["0," + w for w in normal] + ["1," + w for w in kursiv])
    url = "https://fonts.googleapis.com/css2?family=%s:ital,wght@%s" % (
        urllib.parse.quote(family), achsen)
    css = _holen(url, 200_000).decode("utf-8", "replace")
    blocke = re.findall(r"@font-face\s*\{(.*?)\}", css, re.S)
    if not blocke:
        raise ValueError("Google lieferte keine Schriftdateien")
    ziel = ORDNER / ordnername(family)
    ziel.mkdir(parents=True, exist_ok=True)
    dateien = []
    # Nur die angefragten Schnitte, jeden genau einmal, nur echte Schriftdateien
    gewollt = {(w, False) for w in normal} | {(w, True) for w in kursiv}
    for b in blocke:
        u = re.search(r"url\((https://fonts\.gstatic\.com/[A-Za-z0-9/._-]+\.ttf)\)", b)
        w = re.search(r"font-weight:\s*(\d{3})", b)
        stil = re.search(r"font-style:\s*(\w+)", b)
        if not (u and w):
            continue
        i = bool(stil and stil.group(1) == "italic")
        if (w.group(1), i) not in gewollt or ".." in u.group(1):
            continue
        gewollt.discard((w.group(1), i))
        daten = _holen(u.group(1), MAX_DATEI)
        if daten[:4] not in TTF_KOPF:
            raise ValueError("Google lieferte keine Schriftdatei")
        name = w.group(1) + ("i" if i else "") + ".ttf"
        (ziel / name).write_bytes(daten)
        dateien.append({"w": w.group(1), "i": i, "datei": name})
    if not dateien:
        raise ValueError("keine TTF-Dateien gefunden")
    liste = [e for e in installiert(streng=True) if e["family"] != family]
    liste.append({"family": family, "ordner": ordnername(family), "art": eintrag["k"],
                  "dateien": dateien})
    liste.sort(key=lambda e: e["family"].lower())
    LISTE.parent.mkdir(parents=True, exist_ok=True)
    P.sicher_schreiben(LISTE, json.dumps(liste, ensure_ascii=False, indent=1).encode("utf-8"))
    _css_schreiben(liste)
    return family


def ttf_datei(family, fett=False):
    """Pfad einer geladenen Schrift (fuer die Schriftprobe)."""
    for e in installiert():
        if e["family"] == family and not e.get("eigen"):   # eigene Dateien nie durch FreeType
            ziel = "700" if fett else "400"
            wahl = next((d for d in e["dateien"] if d["w"] == ziel and not d["i"]), e["dateien"][0])
            return ORDNER / e["ordner"] / wahl["datei"]
    return None


# ------------------------------------------------------------ eigene Schriftdateien
# TTF, OTF oder WOFF vom Rechner. Name, Staerke und Kursiv stehen in der Datei
# (Tabellen name, OS/2, head); so finden Regular und Bold zur selben Familie.
# Abgelegt wie die Google-Schriften, also ueberall waehlbar, auch im Export.
EINGEBAUT = {"Montserrat", "Poppins", "Inter", "Oswald", "Playfair Display", "Lora", "Bebas Neue"}
EIGENE_ARTEN = {".ttf": b"", ".otf": b"", ".woff": b""}
MAX_EIGENE = 10_000_000
_TABELLEN = {b"name", b"OS/2", b"head", b"fvar"}


def _tabellen(daten):
    """name, OS/2, head und fvar aus einer TTF-, OTF- oder WOFF-Datei (alles mit Grenzen)."""
    import struct, zlib
    kopf, aus = daten[:4], {}
    if kopf in TTF_KOPF:
        n = struct.unpack(">H", daten[4:6])[0]
        for i in range(min(n, 200)):
            e = daten[12 + 16 * i: 28 + 16 * i]
            if len(e) < 16:
                raise ValueError("Datei unvollstaendig")
            tag, _, off, ln = struct.unpack(">4sIII", e)
            if tag in _TABELLEN:
                if off + ln > len(daten) or ln > 2_000_000:
                    raise ValueError("Tabelle ausserhalb der Datei")
                aus[tag] = daten[off:off + ln]
    elif kopf == b"wOFF":
        n = struct.unpack(">H", daten[12:14])[0]
        for i in range(min(n, 200)):
            e = daten[44 + 20 * i: 64 + 20 * i]
            if len(e) < 20:
                raise ValueError("Datei unvollstaendig")
            tag, off, laenge, original, _ = struct.unpack(">4sIIII", e)
            if tag in _TABELLEN:
                if off + laenge > len(daten) or original > 2_000_000:
                    raise ValueError("Tabelle ausserhalb der Datei")
                roh = daten[off:off + laenge]
                aus[tag] = zlib.decompressobj().decompress(roh, original) if laenge < original else roh
    else:
        raise ValueError("Keine TTF-, OTF- oder WOFF-Datei (WOFF2 bitte vorher als TTF speichern)")
    return aus


def _namen(tab):
    import struct
    if len(tab) < 6:
        return {}
    _, anzahl, start = struct.unpack(">HHH", tab[:6])
    beste = {}
    for i in range(min(anzahl, 1000)):
        p = 6 + 12 * i
        if p + 12 > len(tab):
            break
        plat, _, sprache, nid, ln, off = struct.unpack(">HHHHHH", tab[p:p + 12])
        if nid not in (1, 2, 16, 17):
            continue
        roh = tab[start + off: start + off + ln]
        if plat in (0, 3):
            text = roh.decode("utf-16-be", "ignore")
        elif plat == 1:
            text = roh.decode("mac_roman", "ignore")
        else:
            continue
        rang = 0 if (plat == 3 and sprache == 0x409) else 1 if plat in (0, 3) else 2
        if text.strip() and (nid not in beste or rang < beste[nid][0]):
            beste[nid] = (rang, text.strip())
    return {k: v[1] for k, v in beste.items()}


def _familienname(roh):
    """Nur Buchstaben, Ziffern, Leerzeichen (wie im ganzen Cockpit), hoechstens 60 Zeichen."""
    import unicodedata
    t = unicodedata.normalize("NFKD", roh or "").encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^A-Za-z0-9 ]+", " ", t).split())[:60].strip()


def datei_lesen(daten, dateiname=""):
    """(Familie, Staerke als '400', kursiv) aus einer Schriftdatei."""
    import struct
    if len(daten) > MAX_EIGENE:
        raise ValueError("Schriftdatei zu gross (hoechstens 10 MB)")
    import zlib
    try:
        return _datei_lesen(daten, dateiname)
    except (struct.error, zlib.error, IndexError, OverflowError):
        raise ValueError("Keine gueltige Schriftdatei")


def _datei_lesen(daten, dateiname):
    import struct
    tab = _tabellen(daten)
    if b"head" not in tab:                  # jede echte Schrift hat sie
        raise ValueError("Keine gueltige Schriftdatei")
    namen = _namen(tab.get(b"name", b""))
    familie = _familienname(namen.get(16) or namen.get(1) or "") or _familienname(Path(dateiname).stem.split("-")[0])
    if not familie:
        raise ValueError("Die Datei nennt keinen Schriftnamen")
    unter = (namen.get(17) or namen.get(2) or "").lower()
    os2, head = tab.get(b"OS/2", b""), tab.get(b"head", b"")
    staerke = struct.unpack(">H", os2[4:6])[0] if len(os2) >= 6 else 0
    if not 100 <= staerke <= 900:
        staerke = 700 if "bold" in unter else 300 if "light" in unter else 900 if "black" in unter else 400
    staerke = str(min(900, max(100, int(round(staerke / 100.0)) * 100)))
    # Variable Schrift (Tabelle fvar mit Achse wght): ein Bereich, z. B. "100 900"
    fvar = tab.get(b"fvar", b"")
    if len(fvar) >= 16:
        ab, anzahl, groesse = struct.unpack(">H", fvar[4:6])[0], struct.unpack(">H", fvar[8:10])[0],             struct.unpack(">H", fvar[10:12])[0]
        for i in range(min(anzahl, 50)):
            p = ab + i * max(groesse, 20)
            if p + 20 > len(fvar):
                break
            tag, mini, _, maxi = struct.unpack(">4siii", fvar[p:p + 16])
            if tag == b"wght":
                mini, maxi = round(mini / 65536), round(maxi / 65536)
                if 1 <= mini < maxi <= 1000:
                    staerke = "%d %d" % (mini, maxi)
                break
    kursiv = (len(os2) >= 64 and bool(struct.unpack(">H", os2[62:64])[0] & 1)) or \
             (len(head) >= 46 and bool(struct.unpack(">H", head[44:46])[0] & 2)) or \
             "italic" in unter or "oblique" in unter
    return familie, staerke, kursiv


def eigene_laden(daten, dateiname):
    """Eigene Schriftdatei ablegen und anmelden. Gibt den Familiennamen zurueck."""
    endung = Path(str(dateiname)).suffix.lower()
    if endung not in EIGENE_ARTEN:
        raise ValueError("Bitte eine TTF-, OTF- oder WOFF-Datei")
    familie, staerke, kursiv = datei_lesen(daten, dateiname)
    if any(e.get("f", "").lower() == familie.lower() for e in verzeichnis()):
        # sonst bekaemen Vorlagen mit dieser Google-Schrift still die fremde Datei
        raise ValueError("%s gibt es bei Google Fonts, bitte dort laden (Schriften, Suche)" % familie)
    liste = installiert(streng=True)
    da = next((e for e in liste if e["family"].lower() == familie.lower()), None)
    if familie.lower() in {x.lower() for x in EINGEBAUT} or (da and not da.get("eigen")):   # CSS-Namen: Gross/klein egal
        raise ValueError("Die Schrift %s gibt es schon im Cockpit" % familie)
    if da:
        familie = da["family"]
    ziel = ORDNER / ordnername(familie)
    for o in (P.SCHRIFTEN, ORDNER, ziel):
        if os.path.lexists(o) and P._verknuepft(o):
            raise ValueError("Schriftordner ist eine Verknuepfung")
    ziel.mkdir(parents=True, exist_ok=True)
    name = staerke.replace(" ", "-") + ("i" if kursiv else "") + endung
    P.sicher_schreiben(ziel / name, daten)
    dateien = [x for x in (da or {}).get("dateien", []) if not (x["w"] == staerke and x["i"] == kursiv)]
    dateien.append({"w": staerke, "i": kursiv, "datei": name})
    dateien.sort(key=lambda x: (x["i"], x["w"]))
    liste = [e for e in liste if e is not da]
    liste.append({"family": familie, "ordner": ordnername(familie), "art": "eigen", "eigen": True,
                  "dateien": dateien})
    liste.sort(key=lambda e: e["family"].lower())
    LISTE.parent.mkdir(parents=True, exist_ok=True)
    P.sicher_schreiben(LISTE, json.dumps(liste, ensure_ascii=False, indent=1).encode("utf-8"))
    _css_schreiben(liste)
    return familie


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit()
    if a[0] == "suche":
        art = a[a.index("--art") + 1] if "--art" in a else None
        wort = " ".join(x for x in a[1:] if x != "--art" and x != art)
        print("  ".join(suchen(wort, art, 25)) or "keine Treffer")
    elif a[0] == "laden":
        print("geladen:", laden(" ".join(a[1:])))
    elif a[0] == "datei" and len(a) > 1:
        p = Path(" ".join(a[1:]))
        print("geladen:", eigene_laden(p.read_bytes()[:MAX_EIGENE + 1], p.name))
    elif a[0] == "liste":
        print("  ".join(namen()) or "noch keine Google-Schrift geladen")
