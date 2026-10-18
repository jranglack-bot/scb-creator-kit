"""Karussell-Cockpit als Vorschau in EINER Datei, ohne Server und ohne Installation.

Fuer Leute, die das Cockpit erst ansehen wollen (Drive-Ordner, Link). Packt cockpit.html,
render.js, Bibliotheken, Icons, Schriften und die mitgelieferten Vorlagen zusammen und
ersetzt den Server durch demo_start.js (alles im Speicher des Tabs). Was einen Rechner
braucht (Bilder/PDF/Canva ausgeben, Freisteller, Videos, Schriften laden, An Claude),
zeigt einen Hinweis auf die Vollversion. Nur neutrale Kit-Vorlagen, keine eigenen Daten.

    python tools/karussell_demo/bauen.py <ausgabe.html> [--artifact]

--artifact: ohne <!doctype>/<body> (die Artifact-Seite legt ihr eigenes Geruest darum).
Liegt in tools/ und kommt damit nie ins ausgelieferte Plugin.
"""
import base64
import gzip
import json
import re
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
KIT = HIER.parents[1]
COCKPIT = KIT / "skills" / "karussell-posts" / "cockpit"
START = {"name": "beispiel-anleitung", "vorlage": "schritt-fuer-schritt"}
TITEL = "Karussell-Cockpit Vorschau"


def b64(daten):
    return base64.b64encode(daten).decode("ascii")


def gz64(daten):
    return b64(gzip.compress(daten, 9, mtime=0))


def skript(text):
    """Inline-Skript: '</script' darf nicht vorkommen, sonst endet der Block dort."""
    return text.replace("</script", "<\\/script").replace("</SCRIPT", "<\\/SCRIPT")


def ersetze(text, alt, neu, wo):
    if text.count(alt) != 1:
        raise SystemExit("Stelle nicht gefunden (%dx) in %s: %r" % (text.count(alt), wo, alt[:80]))
    return text.replace(alt, neu)


def schriften_aus_css(css):
    """@font-face-Regeln aus stil.css: die Demo laedt die Dateien selbst (FontFace),
    im CSS bleiben nur die uebrigen Regeln."""
    regeln, rest = [], []
    for zeile in css.splitlines():
        m = re.match(r'@font-face\{font-family:("?)([^;"]+)\1;src:url\("fonts/([^"]+)"\);(?:font-weight:([^;]+);)?', zeile)
        if m:
            regeln.append({"family": m.group(2), "datei": m.group(3), "weight": m.group(4) or "400"})
        else:
            rest.append(zeile)
    return regeln, "\n".join(rest)


def daten_bauen():
    d = {"gz": {}, "schriften": [], "vorlagen": [], "start": START}
    for n in ("index.json", "de.json", "fonts.json", "icons.json"):
        d["gz"]["bib/" + n] = gz64((COCKPIT / "bib" / n).read_bytes())
    css = (COCKPIT / "stil.css").read_text(encoding="utf-8")
    regeln, _ = schriften_aus_css(css)
    if len(regeln) < 5:
        raise SystemExit("stil.css: Schriften nicht gefunden")
    for r in regeln:
        d["schriften"].append({"family": r["family"], "weight": r["weight"],
                               "daten": gz64((COCKPIT / "fonts" / r["datei"]).read_bytes())})
    for o in sorted(p for p in (COCKPIT / "vorlagen").iterdir() if p.is_dir()):
        inhalt = o / "inhalt.json"
        if not inhalt.is_file():
            continue
        fremd = [p.name for p in o.iterdir() if p.name not in ("inhalt.json", ".vorschau.png", ".folien.png")]
        if fremd:   # Vorlagen mit Bildern braeuchten die Bilder mit; bisher hat keine welche
            raise SystemExit("Vorlage %s hat weitere Dateien: %s" % (o.name, fremd))
        v = {"name": o.name, "inhalt": inhalt.read_text(encoding="utf-8-sig")}
        json.loads(v["inhalt"])
        for feld, datei in (("vorschau", ".vorschau.png"), ("folien", ".folien.png")):
            if (o / datei).is_file():
                v[feld] = b64((o / datei).read_bytes())
        d["vorlagen"].append(v)
    if not any(v["name"] == START["vorlage"] for v in d["vorlagen"]):
        raise SystemExit("Startvorlage fehlt: %s" % START["vorlage"])
    return d


def seite_bauen(artifact=False):
    html = (COCKPIT / "cockpit.html").read_text(encoding="utf-8")
    css = (COCKPIT / "stil.css").read_text(encoding="utf-8")
    _, css_rest = schriften_aus_css(css)
    lies = lambda p: p.read_text(encoding="utf-8")

    kopf_alt = '<!doctype html><meta charset="utf-8"><title>Karussell Cockpit</title>'
    kopf_neu = ('<title>%s</title>' % TITEL) if artifact else \
               ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                '<title>%s</title>' % TITEL)
    html = ersetze(html, kopf_alt, kopf_neu, "cockpit.html")
    html = ersetze(html, '<link rel="stylesheet" href="stil.css">',
                   "<style>\n%s\n</style>\n<style>\n%s</style>" % (css_rest, lies(HIER / "demo.css")), "cockpit.html")
    # Google-Schriften kommen in der Vorschau nicht dazu; das leere Stylesheet behaelt die id
    html = ersetze(html, '<link rel="stylesheet" href="fonts/google.css" id="googleCss">',
                   '<style id="googleCss"></style>', "cockpit.html")
    daten = json.dumps(daten_bauen(), ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")
    html = ersetze(html, '<script src="lib/moveable.min.js"></script>',
                   '<script type="application/json" id="demoDaten">%s</script>\n<script>\n%s\n</script>'
                   % (daten, skript(lies(COCKPIT / "lib" / "moveable.min.js"))), "cockpit.html")
    html = ersetze(html, '<script src="lib/selecto.min.js"></script>',
                   "<script>\n%s\n</script>" % skript(lies(COCKPIT / "lib" / "selecto.min.js")), "cockpit.html")
    html = ersetze(html, '<script src="render.js"></script>',
                   "<script>\n%s\n</script>\n<script>\n%s\n</script>"
                   % (skript(lies(COCKPIT / "render.js")), skript(lies(HIER / "demo_start.js"))), "cockpit.html")
    html = ersetze(html, "<body>\n", ("" if artifact else "<body>\n") + lies(HIER / "demo_teile.html"), "cockpit.html")
    # Das Cockpit-Skript ist das letzte; danach die Hinweise
    letztes = html.rindex("</script>")
    html = html[:letztes] + "</script>\n<script>\n%s\n</script>" % skript(lies(HIER / "demo_ende.js")) + \
        html[letztes + len("</script>"):]

    # Kein Weg darf mehr auf Dateien neben der Seite zeigen
    rest = re.findall(r'(?:src|href)="(?!data:|blob:|https?:|#)[^"]+"', html)
    if rest:
        raise SystemExit("Noch externe Verweise: %s" % rest[:5])
    return html


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    ziel = Path(args[0])
    html = seite_bauen(artifact="--artifact" in sys.argv)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(html, encoding="utf-8", newline="\n")
    mb = ziel.stat().st_size / 1e6
    if mb > 15.5:
        raise SystemExit("Zu gross fuer einen Link: %.1f MB" % mb)
    print("%s  %.1f MB" % (ziel, mb))


if __name__ == "__main__":
    main()
