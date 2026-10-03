"""Alle verfuegbaren Schriften nebeneinander als EIN Bild.

Beim Nachbauen einer fremden Vorlage laesst sich die Schriftart nicht aus
Pixeln messen. Statt zu raten: diese Probe bauen, dem Menschen zeigen, er
zeigt auf die richtige. Ein Bild, eine Runde.

    python schriftprobe.py "Was ist dein unfairer Vorteil"
    python schriftprobe.py "Text" --projekt kompass

Farben aus dem stil des Projekts (sonst des aktuellen). Das Bild liegt als
schriftprobe.png im Projektordner.
"""
import json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

import projekt as P

HIER = P.HIER
DATEIEN = [("Montserrat", "Montserrat.ttf"), ("Poppins", "Poppins-700.ttf"),
           ("Inter", "Inter.ttf"), ("Oswald", "Oswald.ttf"),
           ("Playfair Display", "PlayfairDisplay.ttf"), ("Lora", "Lora.ttf"),
           ("Bebas Neue", "BebasNeue.ttf")]


FARBE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")


def google():
    """Geladene Google Fonts (python schriften.py laden ...) kommen dazu."""
    try:
        import schriften
        return [(n, schriften.ttf_datei(n, fett=True)) for n in schriften.namen()
                if schriften.ttf_datei(n, fett=True)]
    except Exception:
        return []


def schrift(datei, groesse, gewicht=700):
    """Variable Schriften auf die gewuenschte Strichstaerke stellen. Die
    Gewichtsachse gezielt suchen, sonst erwischt man z. B. bei Inter die
    optische Groesse."""
    f = ImageFont.truetype(str(HIER / "fonts" / datei), groesse)
    try:
        achsen = f.get_variation_axes()
        werte = []
        for a in achsen:
            n = a.get("name", b"")
            n = n.decode("utf-8", "ignore") if isinstance(n, bytes) else str(n)
            if "weight" in n.lower() or "wght" in n.lower():
                werte.append(min(max(gewicht, a["minimum"]), a["maximum"]))
            else:
                werte.append(a["default"])
        if werte:
            f.set_variation_by_axes(werte)
    except Exception:
        pass
    return f


def bauen(text, breite=1100, name=None):
    try:
        ordner = P.ordner(name)
    except ValueError:
        ordner = P.DATEN
    try:
        stil = json.loads((ordner / "inhalt.json").read_text(encoding="utf-8-sig"))["stil"]
    except Exception:
        stil = {}
    if not isinstance(stil, dict):
        stil = {}
    bg = stil.get("bg", "#dee3e7")
    fg = stil.get("text", "#313538")

    if not (isinstance(bg, str) and FARBE.fullmatch(bg)):
        bg = "#dee3e7"
    if not (isinstance(fg, str) and FARBE.fullmatch(fg)):
        fg = "#313538"
    alle = DATEIEN + google()
    zeile, rand, gross, klein = 132, 40, 58, 20
    bild = Image.new("RGB", (breite, zeile * len(alle) + rand), bg)
    d = ImageDraw.Draw(bild)
    marke = ImageFont.truetype(str(HIER / "fonts" / "Inter.ttf"), klein)

    for i, (name, datei) in enumerate(alle):
        y = rand // 2 + i * zeile
        d.text((rand, y + 4), "%d  %s" % (i + 1, name), font=marke, fill="#8a9296")
        try:
            d.text((rand, y + 30), text, font=schrift(datei, gross), fill=fg)
        except Exception as e:
            d.text((rand, y + 30), "Fehler: %s" % e, font=marke, fill="#b04040")
        if i:
            d.line([(rand, y - 6), (breite - rand, y - 6)], fill="#c3cacd", width=1)

    ziel = ordner / "schriftprobe.png"
    bild.save(ziel)
    return ziel


if __name__ == "__main__":
    name = P.aus_argv(sys.argv)
    text = (" ".join(a for a in sys.argv[1:] if a != "--projekt" and a != name)
            or "Was ist dein unfairer Vorteil")
    p = bauen(text, name=name)
    print(p, "gebaut:", ", ".join(n for n, _ in DATEIEN + google()))
