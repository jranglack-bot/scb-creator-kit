#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bildformat des fertigen Videos — EINE Quelle fuer Projektstart, Cockpit,
Render und Zuruf-Befehle.

projekt.json:
    "format":     "9:16" | "16:9" | "1:1" | "4:5"
    "einpassen":  "fuellen"   (zuschneiden, Ausschnitt per "ausschnitt")
                | "unscharf"  (ganzes Bild, Rand = unscharfe Vergroesserung)
                | "balken"    (ganzes Bild, schwarze Raender)
    "ausschnitt": {"x": 0.5, "y": 0.5}   nur bei "fuellen": 0 = links/oben,
                                          1 = rechts/unten

Altprojekte ohne "format" bleiben, wie sie immer waren: 9:16 mit
schwarzen Raendern (genau die bisherige Render-Kette). Neue Projekte
bekommen ihr Format beim Anlegen aus dem ersten Clip (projekt_starten.py).
"render": {"width", "height"} ueberstimmt alles (Sonderfaelle).
"""
import json
import math
import subprocess

FORMATE = {
    '9:16': (1080, 1920, 'Reel · TikTok · Story'),
    '16:9': (1920, 1080, 'YouTube · Querformat'),
    '1:1':  (1080, 1080, 'Quadrat'),
    '4:5':  (1080, 1350, 'Instagram-Feed'),
}
EINPASSEN = {
    'fuellen':  'Füllen (zuschneiden)',
    'unscharf': 'Unscharfer Hintergrund',
    'balken':   'Schwarze Balken',
}
STANDARD = '9:16'


def quelle_masse(pfad):
    """(Breite, Hoehe) wie das Video ANGEZEIGT wird — Handyvideos speichern
    Hochkant oft als 1920x1080 mit Drehungs-Markierung."""
    try:
        out = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height:stream_tags=rotate:'
             'stream_side_data=rotation', '-of', 'json', pfad],
            capture_output=True, text=True, timeout=30).stdout
        st = json.loads(out)['streams'][0]
    except Exception:
        return None
    w, h = int(st.get('width') or 0), int(st.get('height') or 0)
    dreh = 0
    try:
        dreh = int(float((st.get('tags') or {}).get('rotate') or 0))
    except ValueError:
        pass
    for sd in st.get('side_data_list') or []:
        if 'rotation' in sd:
            dreh = int(float(sd['rotation']))
    if abs(dreh) % 180 == 90:
        w, h = h, w
    return (w, h) if w and h else None


def passendes_format(w, h):
    """Das naechstliegende Format. Querformat bleibt Querformat (auch 4:3),
    Hochkant waehlt zwischen 9:16 und 4:5, fast Quadratisches wird 1:1."""
    r = w / h
    if r > 1.15:
        return '16:9'
    if r >= 0.87:
        return '1:1'
    lr = math.log(r)
    return min(('9:16', '4:5'),
               key=lambda k: abs(math.log(FORMATE[k][0] / FORMATE[k][1]) - lr))


def ziel(pj):
    """(Breite, Hoehe, Format) des fertigen Videos."""
    fmt = pj.get('format') if pj.get('format') in FORMATE else STANDARD
    w, h = FORMATE[fmt][:2]
    render = pj.get('render') or {}
    if render.get('width') and render.get('height'):
        w, h = int(render['width']), int(render['height'])
    return w, h, fmt


def einpassen(pj):
    """Einpass-Art: ausdruecklich gesetzt, sonst bei Altprojekten (ohne
    "format") die bisherigen schwarzen Raender, bei neuen der unscharfe
    Hintergrund (sieht bei Formatwechsel am besten aus)."""
    e = pj.get('einpassen')
    if e in EINPASSEN:
        return e
    return 'balken' if 'format' not in pj else 'unscharf'


def ausschnitt(pj):
    a = pj.get('ausschnitt') or {}
    klemm = lambda v: max(0.0, min(1.0, float(v)))
    return klemm(a.get('x', 0.5)), klemm(a.get('y', 0.5))


def render_einstellung(pj):
    """Was prolook unter cfg['einpassen'] erwartet."""
    x, y = ausschnitt(pj)
    return {'modus': einpassen(pj), 'x': round(x, 4), 'y': round(y, 4)}


def gerade(n):
    return int(n) // 2 * 2
