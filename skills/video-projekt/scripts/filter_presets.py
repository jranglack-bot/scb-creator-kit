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


# ---------------------------------------------------------------------------
# LOOKS UND „FARBE BEHALTEN" — ueber 3D-Farbtabellen (LUT)
# ---------------------------------------------------------------------------
# Kino-Looks (Teal & Orange …) und Sin City lassen sich nicht als einfache
# Farbfaktoren schreiben. Sie werden als 3D-LUT berechnet (33³ Stuetzpunkte):
#   Render:  ffmpeg lut3d=…:interp=trilinear  (Datei r_filter_<n>.cube)
#   Cockpit: dieselbe Tabelle, Pixel fuer Pixel auf einem Canvas, ebenfalls
#            trilinear. (WebGL waere schneller, ist aber bei lokal geoeffneten
#            Dateien gesperrt — getestet 01.10.2026 in Chrome und Edge.)
# Die Looks rechnet NUR dieses Modul; build_editor.py legt die Tabellen als
# filter_luts.js ins Projekt. „Farbe behalten" haengt von den gewaehlten
# Farben ab — die Formel steht deshalb zusaetzlich im Cockpit (farbeRgb),
# beide sind im Test gegeneinander geprueft.
import math
import os

LUT_N = 33
LOOKS = {
    'kino':   'Kino (Teal & Orange)',
    'film':   'Film verblasst',
    'golden': 'Golden Hour',
    'moody':  'Moody',
    'bleach': 'Bleach Bypass',
}
FARBE = 'farbe'
FARBE_NAME = 'Farbe behalten (Sin City)'
FARB_NAMEN = {'rot': '#d02020', 'blau': '#2050d0', 'gelb': '#e0c020',
              'gruen': '#20a040', 'grün': '#20a040', 'orange': '#e07020',
              'pink': '#e040a0', 'lila': '#8040c0', 'tuerkis': '#20b0b0',
              'türkis': '#20b0b0'}


def _clip(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _luma(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _sstep(a, b, x):
    t = _clip((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def _sat(c, s):
    y = _luma(*c)
    return [y + (k - y) * s for k in c]


def _con(c, f):
    return [(k - 0.5) * f + 0.5 for k in c]


def look_rgb(name, r, g, b):
    """Ein Look auf einen Farbwert (0..1, gammakodiert) — volle Staerke."""
    c = [r, g, b]
    y = _luma(r, g, b)
    if name == 'kino':                       # Schatten tuerkis, Lichter orange
        t = _sstep(0.1, 0.9, y)
        tint = [0.0 + t * 1.0, 0.45 + t * 0.17, 0.55 - t * 0.23]
        c = [k + 0.2 * (tk - y) for k, tk in zip(c, tint)]
        c = _sat(_con(c, 1.08), 1.05)
    elif name == 'film':                     # angehobene Schwaerzen, weich, warm
        c = [0.06 + 0.86 * k for k in c]
        c = _sat(c, 0.78)
        c = [c[0] * 1.02, c[1], c[2] * 0.96]
    elif name == 'golden':                   # warmes Gold in den Lichtern
        w = _sstep(0.3, 1.0, y)
        c = [c[0] * (1 + 0.12 * w) + 0.02, c[1] * (1 + 0.04 * w),
             c[2] * (1 - 0.15 * w) - 0.01]
        c = _con(_sat(c, 1.08), 0.97)
    elif name == 'moody':                    # gedeckt, dunkel, kuehle Schatten
        c = [k * 0.9 for k in _con(_sat(c, 0.65), 1.15)]
        sh = 1 - _sstep(0.0, 0.5, y)
        c = [c[0] - 0.02 * sh, c[1], c[2] + 0.04 * sh]
    elif name == 'bleach':                   # halb entsaettigt, harter Kontrast
        c = [k + (y - k) * 0.55 for k in c]
        c = [k * 0.98 for k in _con(c, 1.35)]
    return [_clip(k) for k in c]


def _hex_rgb(h):
    h = FARB_NAMEN.get(str(h).lower(), str(h)).lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _chroma(r, g, b):
    """Farbanteil wie im Video (BT.709, 8-bit-Einheiten)."""
    y = _luma(r, g, b)
    return y, (b - y) / 1.8556 * 224, (r - y) / 1.5748 * 224


def farbe_rgb(r, g, b, farben, toleranz=25, staerke=1.0):
    """Sin City: gewaehlte Farbtoene bleiben, alles andere wird grau.
    toleranz in Grad um den Farbton, staerke 0..1 (wie grau der Rest wird)."""
    y, u, v = _chroma(r, g, b)
    ton = math.atan2(v, u)
    weich = math.radians(12)
    tol = math.radians(float(toleranz))
    sat = math.hypot(u, v)
    w = 0.0
    for f in farben:
        _, fu, fv = _chroma(*_hex_rgb(f))
        d = abs((ton - math.atan2(fv, fu) + 3 * math.pi) % (2 * math.pi) - math.pi)
        # Mindest-Saettigung = halbe Saettigung der gewaehlten Farbe: Haut
        # liegt im Farbton mitten im Rot (103-138 Grad, gemessen 01.10.2026),
        # ist aber deutlich blasser als ein rotes Kleidungsstueck.
        smin = max(6.0, 0.5 * math.hypot(fu, fv))
        w = max(w, _clip((tol + weich - d) / weich) * _clip((sat - smin) / 8))
    f = 1 - float(staerke) * (1 - w)
    return [_clip(y + f * (k - y)) for k in (r, g, b)]


def lut_werte(abschnitt_lut, n=LUT_N):
    """Tabelle als Liste von RGB-Tripeln in .cube-Reihenfolge (Rot laeuft
    am schnellsten). abschnitt_lut: {'preset', 'staerke', 'farben', 'toleranz'}."""
    pre = abschnitt_lut['preset']
    st = max(0.0, min(1.0, float(abschnitt_lut.get('staerke', 1.0))))
    aus = []
    for bi in range(n):
        for gi in range(n):
            for ri in range(n):
                r, g, b = ri / (n - 1), gi / (n - 1), bi / (n - 1)
                if pre == FARBE:
                    o = farbe_rgb(r, g, b, abschnitt_lut.get('farben') or ['#d02020'],
                                  abschnitt_lut.get('toleranz', 25), st)
                else:
                    l = look_rgb(pre, r, g, b)
                    o = [k + st * (lk - k) for k, lk in zip((r, g, b), l)]
                aus.append(o)
    return aus


def cube_schreiben(pfad, werte, n=LUT_N):
    with open(pfad, 'w', encoding='ascii', newline='\n') as f:
        f.write('LUT_3D_SIZE {}\n'.format(n))
        for o in werte:
            f.write('{:.6f} {:.6f} {:.6f}\n'.format(*o))


def filter_luts_js():
    """Die festen Looks fuers Cockpit (8 bit je Wert, base64)."""
    import base64
    import json
    d = {}
    for k in LOOKS:
        werte = lut_werte({'preset': k, 'staerke': 1.0})
        roh = bytes(int(round(_clip(x) * 255)) for o in werte for x in o)
        d[k] = {'n': LUT_N, 'd': base64.b64encode(roh).decode('ascii')}
    return 'window.FILTER_LUTS = ' + json.dumps(d) + ';\n'


def bibliothek():
    """Fuers Cockpit: {kennung: {n: Name, art: matrix|lut|farbe, ops: …}}."""
    lib = {k: {'n': v[0], 'art': 'matrix', 'ops': [list(o) for o in v[1]]}
           for k, v in PRESETS.items()}
    for k, n in LOOKS.items():
        lib[k] = {'n': n, 'art': 'lut'}
    lib[FARBE] = {'n': FARBE_NAME, 'art': 'farbe'}
    return lib


def bekannt(preset):
    return preset in PRESETS or preset in LOOKS or preset == FARBE


def abschnitte(filterliste, zeit_umrechnen=lambda t: t):
    """Abschnitte fuer den Render: Zeiten umrechnen, Ueberlappungen kappen
    (der spaeter beginnende Filter gewinnt — genau wie in der Vorschau)."""
    roh = []
    for f in (filterliste or []):
        if not bekannt(f.get('preset')) or f.get('enabled') is False:
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
        if f['preset'] in PRESETS:
            aus.append({'start': round(s, 3), 'end': round(e, 3),
                        'ops': schritte(f['preset'], f.get('staerke', 1.0))})
        else:
            aus.append({'start': round(s, 3), 'end': round(e, 3),
                        'lut': {'preset': f['preset'],
                                'staerke': f.get('staerke', 1.0),
                                'farben': f.get('farben') or ['#d02020'],
                                'toleranz': f.get('toleranz', 25)}})
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


def ffmpeg_filter(abschnitte_liste, ordner='.'):
    """Komplette Kette fuer alle Abschnitte, '' wenn keine. LUT-Abschnitte
    bekommen ihre Tabelle als r_filter_<n>.cube in <ordner> (relativer Name
    in der Kette: ffmpeg-Filterpfade vertragen unter Windows keinen
    Laufwerks-Doppelpunkt — der Render laeuft im Projektordner)."""
    if not abschnitte_liste:
        return ''
    teile = ['format=rgba']
    for i, a in enumerate(abschnitte_liste):
        if 'lut' in a:
            name = 'r_filter_{}.cube'.format(i + 1)
            cube_schreiben(os.path.join(ordner, name), lut_werte(a['lut']))
            teile.append("lut3d=file={}:interp=trilinear:enable='between(t,{},{})'"
                         .format(name, a['start'], a['end']))
        else:
            teile.append(ffmpeg_kette(a))
    return ','.join(teile)
