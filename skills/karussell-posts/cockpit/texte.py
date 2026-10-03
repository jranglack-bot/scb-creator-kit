"""Karussell-Inhalte im Kurzformat lesen und schreiben.

Das Kurzformat enthaelt nur den Text, keine ids, typen oder Klammern. Es kostet
etwa die Haelfte des JSON und sagt genau dasselbe.

    ---                     neue Slide
    # Ueberschrift          Titelblock (Groesse optional als {94} am Zeilenende)
    @ boote.jpg             Bildblock
    +++                     weiterer Textblock auf derselben Slide
    alles andere            Fliesstext, Leerzeile = neuer Absatz

Auszeichnungen bleiben wie im Cockpit: <b> <i> <u> <m> <c=akzent> <f=Poppins>

Arbeitet auf dem aktuellen Projekt (projekte/aktuell.txt), mit --projekt auf
einem bestimmten. texte.txt liegt im Projektordner.

    python texte.py --raus                      inhalt.json -> texte.txt
    python texte.py texte.txt                   texte.txt  -> inhalt.json (stil bleibt)
    python texte.py --raus --projekt kompass    dasselbe fuer ein bestimmtes Projekt
"""
import json, re, sys
from pathlib import Path

import projekt as P


def lesen(text):
    """Kurzformat -> Slideliste"""
    slides, akt = [], None
    nr = [0]

    def neue():
        s = {"bloecke": []}
        slides.append(s)
        return s

    def id_():
        nr[0] += 1
        return "b%d" % nr[0]

    puffer = []

    def puffer_leeren():
        if not puffer:
            return
        txt = "\n".join(puffer).strip("\n")
        puffer.clear()
        if txt.strip():
            akt["bloecke"].append({"id": id_(), "typ": "text", "rolle": "text", "text": txt})

    for zeile in text.splitlines():
        roh = zeile.rstrip()
        if roh.strip() == "---":
            if akt is not None:
                puffer_leeren()
            akt = neue()
            continue
        if akt is None:
            akt = neue()
        if roh.strip() == "+++":
            puffer_leeren()
            continue
        if roh.startswith("# "):
            puffer_leeren()
            t = roh[2:].strip()
            b = {"id": id_(), "typ": "text", "rolle": "titel", "text": t}
            m = re.search(r"\s*\{(\d+)\}$", t)
            if m:
                b["text"] = t[:m.start()].rstrip()
                b["groesse"] = int(m.group(1))
            akt["bloecke"].append(b)
            continue
        if roh.startswith("@ "):
            puffer_leeren()
            akt["bloecke"].append({"id": id_(), "typ": "bild", "rolle": "bild",
                                   "datei": roh[2:].strip()})
            continue
        puffer.append(roh)
    if akt is not None:
        puffer_leeren()
    return [s for s in slides if s["bloecke"]]


def schreiben(slides):
    """Slideliste -> Kurzformat"""
    teile = []
    for s in slides:
        zeilen = []
        erster_text = True
        for b in s.get("bloecke", []):
            if b.get("typ") == "bild":
                zeilen.append("@ " + b.get("datei", ""))
            elif b.get("rolle") == "titel":
                g = (" {%d}" % b["groesse"]) if b.get("groesse") else ""
                zeilen.append("# " + (b.get("text") or "") + g)
            else:
                if not erster_text:
                    zeilen.append("+++")
                erster_text = False
                zeilen.append(b.get("text") or "")
        teile.append("\n".join(zeilen))
    return "---\n" + "\n---\n".join(teile) + "\n"


if __name__ == "__main__":
    name = P.aus_argv(sys.argv)
    ORDNER = P.ordner(name)
    JSON = ORDNER / "inhalt.json"
    d = json.loads(JSON.read_text(encoding="utf-8-sig"))
    if "--raus" in sys.argv:
        ziel = ORDNER / "texte.txt"
        ziel.write_text(schreiben(d["slides"]), encoding="utf-8")
        alt = len(JSON.read_text(encoding="utf-8-sig"))
        neu = len(ziel.read_text(encoding="utf-8"))
        print(f"{ORDNER.name}/{ziel.name}: {neu} B statt {alt} B  ({100 - neu * 100 // alt} % weniger)")
        sys.exit()

    quelle = [a for a in sys.argv[1:] if not a.startswith("--") and a != name]
    if not quelle:
        print(__doc__)
        sys.exit()
    p = Path(quelle[0])
    if not p.is_absolute():
        p = ORDNER / p
    # Das Kurzformat kennt nur Text und Bilder im Raster. Alles darueber hinaus
    # (Farbe, Schrift, Position, Formen, Effekte, Hintergrund, freigestellte
    # Bilder) ginge verloren. Positivliste: was hier nicht steht, gilt als gestaltet.
    SCHLICHT = {"id", "typ", "rolle", "text", "datei", "groesse"}
    gestaltet = [i + 1 for i, s in enumerate(d["slides"])
                 if set(s) - {"bloecke"} or
                 any(set(b) - SCHLICHT or b.get("typ") not in ("text", "bild", None)
                     for b in s.get("bloecke", []))]
    if gestaltet and "--erzwingen" not in sys.argv:
        sys.exit("Abgebrochen: Folie %s ist gestaltet (Positionen, Formen oder Effekte), "
                 "texte.py wuerde das loeschen. Texte dort mit k.py setze aendern, "
                 "oder bewusst mit --erzwingen." % ", ".join(map(str, gestaltet)))
    d["slides"] = lesen(p.read_text(encoding="utf-8-sig"))
    JSON.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(d['slides'])} Slides,",
          sum(len(s['bloecke']) for s in d['slides']), f"Bloecke nach {ORDNER.name}/inhalt.json")
