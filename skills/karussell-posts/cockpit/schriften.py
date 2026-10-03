"""Google Fonts fuers Cockpit: suchen, bei Bedarf laden, danach offline.

    python schriften.py suche <wort> [--art serif|sans|display|hand|mono]
    python schriften.py laden "Roboto Slab"
    python schriften.py liste

Verzeichnis: bib/fonts.json (aus fonts.google.com, liegt beim Code).
Geladene Schriften liegen im Karussell-Ordner (ueberleben Updates):
schriften/google/<ordner>/<staerke>[i].ttf, Liste in schriften/google.json,
@font-face-Regeln in schriften/google.css. Der Server liefert sie unter
fonts/google* aus. Lizenzen: OFL oder Apache, frei nutzbar, auch in Canva.
"""
import json, re, sys, urllib.parse, urllib.request
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


def installiert():
    try:
        liste = json.loads(LISTE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [e for e in liste if isinstance(e, dict) and NAME.fullmatch(str(e.get("family", "")))]


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
    CSS.write_text("\n".join(zeilen) + "\n", encoding="utf-8")


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
    liste = [e for e in installiert() if e["family"] != family]
    liste.append({"family": family, "ordner": ordnername(family), "art": eintrag["k"],
                  "dateien": dateien})
    liste.sort(key=lambda e: e["family"].lower())
    LISTE.parent.mkdir(parents=True, exist_ok=True)
    LISTE.write_text(json.dumps(liste, ensure_ascii=False, indent=1), encoding="utf-8")
    _css_schreiben(liste)
    return family


def ttf_datei(family, fett=False):
    """Pfad einer geladenen Schrift (fuer die Schriftprobe)."""
    for e in installiert():
        if e["family"] == family:
            ziel = "700" if fett else "400"
            wahl = next((d for d in e["dateien"] if d["w"] == ziel and not d["i"]), e["dateien"][0])
            return ORDNER / e["ordner"] / wahl["datei"]
    return None


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
    elif a[0] == "liste":
        print("  ".join(namen()) or "noch keine Google-Schrift geladen")
