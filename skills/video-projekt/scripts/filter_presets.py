"""Farbfilter fuer das Video-Cockpit — EINE Quelle fuer Vorschau und Render.

Ein Filter ist eine Folge einfacher Schritte, die es im Browser genau so
als CSS gibt (saturate, contrast, brightness, sepia) plus eine Farbschicht
„Multiplizieren" (tint) fuer warm/kalt. Der Render macht jeden Schritt als
eigenen ffmpeg-colorchannelmixer — auch der Browser schneidet nach jedem
CSS-Schritt bei 0 und 100 % ab, deshalb stimmt das Ergebnis ueberein.

Warum kein SVG-Filter: Safari wendet SVG-Filter nicht auf laufendes Video
an (WebKit-Bug 184601) — auf dem Mac waere die Vorschau leer geblieben.

build_editor.py legt die Rezepte als P._filterlib ins Cockpit,
render_projekt.py rechnet aus projekt.json → "filter" die Abschnitte.

projekt.json:
    "filter": [{"start": 3.0, "end": 6.5, "preset": "sw", "staerke": 1.0}]
Zeiten in Timelinezeit (wie Texte), staerke 0..1.
"""

# Schritte (Reihenfolge = Anwendung; tint immer zuerst):
#   tint r g b  Farbschicht multiplizieren (je Kanal 0..1)
#   sat s       saturate(s)   — 0 = grau, 1 = unveraendert
#   con c       contrast(c)   — um Mittelgrau
#   mul m       brightness(m) — alles mal m
#   sepia a     sepia(a)      — Anteil 0..1
PRESETS = {
    'sw':       ('Schwarz-Weiß',      [('sat', 0.0)]),
    'noir':     ('Noir (hartes S/W)', [('sat', 0.0), ('con', 1.35)]),
    'sepia':    ('Sepia',             [('sepia', 1.0)]),
    'retro':    ('Retro',             [('sepia', 0.4), ('con', 0.9),
                                       ('mul', 1.04)]),
    'warm':     ('Warm',              [('tint', 1.0, 0.93, 0.8),
                                       ('mul', 1.07)]),
    'kalt':     ('Kalt',              [('tint', 0.86, 0.95, 1.0),
                                       ('mul', 1.06)]),
    'kraeftig': ('Kräftig',           [('sat', 1.4), ('con', 1.12)]),
    'matt':     ('Matt / verblasst',  [('con', 0.82), ('sat', 0.75),
                                       ('mul', 1.03)]),
    'heller':   ('Heller',            [('mul', 1.12)]),
    'dunkler':  ('Dunkler',           [('mul', 0.75)]),
}


def schritte(preset, staerke=1.0):
    """Schritte mit Staerke: jeder Wert wandert zwischen „wirkungslos"
    und dem Rezeptwert (im Cockpit genau gleich gerechnet)."""
    s = max(0.0, min(1.0, float(staerke)))
    aus = []
    for op in PRESETS[preset][1]:
        if op[0] == 'sepia':
            aus.append(('sepia', s * op[1]))
        else:
            aus.append((op[0],) + tuple(1 + s * (w - 1) for w in op[1:]))
    return aus


def _matrix(op):
    """3x3-Matrix eines Schritts (wie in der Filter-Effects-Spezifikation)."""
    art = op[0]
    if art == 'sat':
        s = op[1]
        return [[0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s],
                [0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s],
                [0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s]], 0.0
    if art == 'sepia':
        a = 1 - op[1]
        return [[0.393 + 0.607 * a, 0.769 - 0.769 * a, 0.189 - 0.189 * a],
                [0.349 - 0.349 * a, 0.686 + 0.314 * a, 0.168 - 0.168 * a],
                [0.272 - 0.272 * a, 0.534 - 0.534 * a, 0.131 + 0.869 * a]], 0.0
    if art == 'con':
        c = op[1]
        return [[c, 0, 0], [0, c, 0], [0, 0, c]], 0.5 * (1 - c)
    if art == 'mul':
        m = op[1]
        return [[m, 0, 0], [0, m, 0], [0, 0, m]], 0.0
    if art == 'tint':
        return [[op[1], 0, 0], [0, op[2], 0], [0, 0, op[3]]], 0.0
    raise ValueError('unbekannter Filterschritt: {}'.format(art))


def bibliothek():
    """Fuers Cockpit: {kennung: {n: Anzeigename, ops: Schritte bei 100 %}}."""
    return {k: {'n': v[0], 'ops': [list(o) for o in v[1]]}
            for k, v in PRESETS.items()}


def abschnitte(filterliste, zeit_umrechnen=lambda t: t):
    """Abschnitte fuer den Render: Zeiten umrechnen, Ueberlappungen kappen
    (der spaeter beginnende Filter gewinnt — genau wie in der Vorschau)."""
    roh = []
    for f in (filterliste or []):
        if f.get('preset') not in PRESETS or f.get('enabled') is False:
            continue
        roh.append((zeit_umrechnen(float(f['start'])),
                    zeit_umrechnen(float(f['end'])), f))
    roh.sort(key=lambda x: x[0])
    aus = []
    for i, (s, e, f) in enumerate(roh):
        if i + 1 < len(roh):
            e = min(e, roh[i + 1][0])
        if e - s < 0.05:
            continue
        aus.append({'start': round(s, 3), 'end': round(e, 3),
                    'ops': schritte(f['preset'], f.get('staerke', 1.0))})
    return aus


def ffmpeg_kette(abschnitt):
    """Ein colorchannelmixer je Schritt, zeitgesteuert per enable.

    Der Versatz (nur bei contrast) laeuft ueber die Alpha-Spalte (ra/ga/ba
    bei deckendem Alpha) — so rechnet derselbe Schritt Faktor UND Versatz,
    ohne dass vorher abgeschnitten wird. Davor muss das Bild im rgba-Format
    liegen (ffmpeg_filter macht das)."""
    an = "enable='between(t,{},{})'".format(abschnitt['start'], abschnitt['end'])
    teile = []
    for op in abschnitt['ops']:
        m, o = _matrix(op)
        werte = ['{}{}={}'.format(a, b, round(m[i][j], 5))
                 for i, a in enumerate('rgb') for j, b in enumerate('rgb')]
        werte += ['{}a={}'.format(a, round(o, 5)) for a in 'rgb']
        teile.append('colorchannelmixer={}:{}'.format(':'.join(werte), an))
    return ','.join(teile)


def ffmpeg_filter(abschnitte_liste):
    """Komplette Kette fuer alle Abschnitte, '' wenn keine."""
    if not abschnitte_liste:
        return ''
    return ','.join(['format=rgba'] + [ffmpeg_kette(a) for a in abschnitte_liste])
