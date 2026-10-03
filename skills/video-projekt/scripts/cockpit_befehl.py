#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kleine Aenderungen am Projekt per Zuruf — ohne die projekt.json zu lesen.

Claude muss fuer „Whoosh beim Wort Brieftaube" nicht die ganze projekt.json
(oft 40 KB Woerter) lesen: dieses Script sucht das Wort, rechnet Zeiten um,
setzt den Eintrag so, wie ihn auch das Cockpit setzen wuerde, baut das
Cockpit neu und meldet das Ergebnis in EINER Zeile. Der offene Tab zeigt es
nach ~3 s.

    <python> cockpit_befehl.py <projekt> --liste
    <python> cockpit_befehl.py <projekt> --suche Brieftaube
    <python> cockpit_befehl.py <projekt> --sfx-liste [whoosh]

    <python> cockpit_befehl.py <projekt> --effekt whoosh --wort Brieftaube [--nr 2]
    <python> cockpit_befehl.py <projekt> --effekt whoosh --bei 0:42 [--fertig]
             [--laut 60] [--vor 0.1] [--laenge 1.5]
    <python> cockpit_befehl.py <projekt> --filter sw --von 1:10 --bis 1:20 [--staerke 70]
    <python> cockpit_befehl.py <projekt> --filter warm --wort Sonne --dauer 3
    <python> cockpit_befehl.py <projekt> --filter kino --von 0 --bis 5   (Looks: kino film golden moody bleach)
    <python> cockpit_befehl.py <projekt> --filter farbe --farben rot,blau --wort Turm --dauer 4 [--toleranz 30]
    <python> cockpit_befehl.py <projekt> --text "Kurz erklärt" --von 0 --bis 3
    <python> cockpit_befehl.py <projekt> --zoom 1.2 --wort Turm --dauer 2 [--x 0.5 --y 0.35]
    <python> cockpit_befehl.py <projekt> --cut --wort äh --alle
    <python> cockpit_befehl.py <projekt> --cut --von 1:10 --bis 1:12,5
    <python> cockpit_befehl.py <projekt> --loeschen effekt 3     (cut|effekt|filter|text|zoom)
    <python> cockpit_befehl.py <projekt> --format 16:9 [--einpassen fuellen|unscharf|balken]
             [--ausschnitt 0.3] [--ausschnitt-y 0.5] [--folgen | --nicht-folgen]
             (Formate: 9:16 16:9 1:1 4:5; --folgen = Kamera folgt der Person, nur bei fuellen)

<projekt> = Projektordner oder projekt.json.

ZEITEN: Standard ist die Zeit, die das Cockpit zeigt (ungeschnittenes
Material). Mit --fertig sind Zeiten im FERTIGEN Video gemeint (nach den
Cuts) — das Script rechnet um. Schreibweisen: 42 · 42,5 · 0:42 · 1:10,5.

Nummern (Cut 3, Effekt 2 …) sind dieselben wie im Cockpit: je Art in
Zeitreihenfolge ab 1.

Nach jeder Aenderung laeuft build_editor.py (abschaltbar mit --ohne-bau).
Windows UND Mac — nur Python-Standardbibliothek.
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import unicodedata

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

SFX_ZIEL_DB = -1.5            # wie im Cockpit (sfxNorm) und build_editor.py
FILTER_NAMEN = {
    'sw': 'sw', 'schwarzweiss': 'sw', 'schwarzweiß': 'sw', 'schwarz-weiss': 'sw',
    'schwarz-weiß': 'sw', 'grau': 'sw', 'noir': 'noir', 'sepia': 'sepia',
    'retro': 'retro', 'warm': 'warm', 'kalt': 'kalt', 'kraeftig': 'kraeftig',
    'kräftig': 'kraeftig', 'bunt': 'kraeftig', 'matt': 'matt',
    'verblasst': 'matt', 'heller': 'heller', 'hell': 'heller',
    'dunkler': 'dunkler', 'dunkel': 'dunkler',
    'kino': 'kino', 'teal': 'kino', 'tealorange': 'kino', 'teal-orange': 'kino',
    'cinematic': 'kino', 'film': 'film', 'vintage': 'film', 'golden': 'golden',
    'goldenhour': 'golden', 'golden-hour': 'golden', 'moody': 'moody',
    'bleach': 'bleach', 'bleachbypass': 'bleach', 'farbe': 'farbe',
    'sincity': 'farbe', 'sin-city': 'farbe', 'farbebehalten': 'farbe',
    'colorkey': 'farbe',
}
ARTEN = {'cut': 'cuts', 'cuts': 'cuts', 'schnitt': 'cuts', 'effekt': 'sfx',
         'sfx': 'sfx', 'filter': 'filter', 'text': 'texts', 'texte': 'texts',
         'zoom': 'zooms'}


# ------------------------------------------------------------------ Hilfen
def fehler(text):
    print('FEHLER: ' + text)
    sys.exit(1)


def arg(name, standard=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return standard


def zeit_lesen(s):
    """42 · 42,5 · 0:42 · 1:10,5 -> Sekunden."""
    s = str(s).strip().replace(',', '.')
    if ':' in s:
        teile = [float(t) for t in s.split(':')]
        sek = 0.0
        for t in teile:
            sek = sek * 60 + t
        return sek
    return float(s)


def zeit_text(t):
    t = max(0.0, t)
    return '{}:{:04.1f}'.format(int(t // 60), t % 60).replace('.', ',')


def norm(w):
    w = unicodedata.normalize('NFKC', str(w)).lower()
    return re.sub(r'[^\w]+', '', w)


# --------------------------------------------------------------- Projekt
def projekt_pfad(roh):
    p = os.path.abspath(roh)
    if os.path.isdir(p):
        p = os.path.join(p, 'projekt.json')
    if not os.path.isfile(p):
        fehler('projekt.json nicht gefunden: ' + p)
    return p


def laden(pfad):
    with open(pfad, encoding='utf-8-sig') as f:
        return json.load(f)


def speichern(pfad, pj):
    tmp = pfad + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(pj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, pfad)


def bauen(pfad):
    if '--ohne-bau' in sys.argv:
        return
    r = subprocess.run([sys.executable, os.path.join(HIER, 'build_editor.py'),
                        pfad], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        print('WARNUNG: Cockpit-Bau meldet einen Fehler:')
        print((r.stdout + r.stderr)[-600:])


def aktive_cuts(pj):
    """Video-Cuts (wie render_projekt: aktiv, Spur both/main), verschmolzen."""
    standard = pj.get('cuts_apply') or 'both'
    roh = sorted((float(c['start']), float(c['end']))
                 for c in (pj.get('cuts') or [])
                 if c.get('active', True)
                 and (c.get('track') or standard) in ('both', 'main'))
    aus = []
    for s, e in roh:
        if aus and s <= aus[-1][1]:
            aus[-1] = (aus[-1][0], max(aus[-1][1], e))
        else:
            aus.append((s, e))
    return aus


def fertig_aus_roh(t, cuts):
    d = 0.0
    for s, e in cuts:
        if t > s:
            d += min(e, t) - s
    return t - d


def roh_aus_fertig(t, cuts, ende=False):
    """Fertig-Zeit -> Rohzeit. Ein ENDE genau an einem Cut bleibt vor dem
    Cut (sonst reichte der Abschnitt im Rohmaterial ueber den Cut hinweg)."""
    r = t
    for s, e in cuts:
        if r > s or (r == s and not ende):
            r += e - s
        else:
            break
    return r


def in_cut(t, cuts):
    return any(s <= t < e for s, e in cuts)


def woerter(pj):
    return [w for w in (pj.get('words') or [])
            if (w.get('type') or 'word') == 'word']


def wort_treffer(pj, suche):
    """Alle Fundstellen [(start, ende, text)] — mehrere Woerter moeglich,
    das letzte darf nur Anfang sein (Brieftaube findet Brieftauben)."""
    q = [norm(t) for t in str(suche).split() if norm(t)]
    if not q:
        return []
    ws = woerter(pj)
    toks = [norm(w.get('text') or w.get('word') or '') for w in ws]
    treffer = []
    for i in range(len(ws) - len(q) + 1):
        ok = all(toks[i + k] == q[k] for k in range(len(q) - 1)) \
            and toks[i + len(q) - 1].startswith(q[-1])
        if ok:
            a, b = ws[i], ws[i + len(q) - 1]
            text = ' '.join((ws[i + k].get('text') or ws[i + k].get('word') or '')
                            .strip() for k in range(len(q)))
            treffer.append((float(a['start']), float(b['end']), text))
    return treffer


def anker(pj, cuts):
    """Startzeit (Rohzeit) aus --wort/--bei/--von, dazu eine Beschreibung."""
    wort = arg('--wort')
    if wort:
        alle = wort_treffer(pj, wort)
        if not alle:
            fehler('„{}" kommt im Transkript nicht vor. --suche zeigt ähnliche '
                   'Stellen.'.format(wort))
        sichtbar = [t for t in alle if not in_cut(t[0], cuts)]
        nr = arg('--nr')
        if nr:
            n = int(nr)
            if not 1 <= n <= len(alle):
                fehler('„{}" gibt es {}-mal, --nr {} geht nicht.'.format(
                    wort, len(alle), n))
            t = alle[n - 1]
        else:
            t = (sichtbar or alle)[0]
        n_txt = ' ({}. von {} Treffern)'.format(alle.index(t) + 1, len(alle)) \
            if len(alle) > 1 else ''
        if in_cut(t[0], cuts):
            n_txt += ' — ACHTUNG: diese Stelle ist rausgeschnitten'
        return t[0], t[1], 'Wort „{}"{}'.format(t[2], n_txt)
    for name in ('--bei', '--von'):
        if arg(name) is not None:
            t = zeit_lesen(arg(name))
            if '--fertig' in sys.argv:
                return roh_aus_fertig(t, cuts), None, '{} im fertigen Video'.format(
                    zeit_text(t))
            return t, None, ''
    fehler('Wo? --wort <Wort>, --bei <Zeit> oder --von <Zeit> angeben.')


def bis_zeit(pj, cuts, start, wort_ende, standard_dauer):
    if arg('--bis') is not None:
        t = zeit_lesen(arg('--bis'))
        return roh_aus_fertig(t, cuts, True) if '--fertig' in sys.argv else t
    if arg('--dauer') is not None:
        d = zeit_lesen(arg('--dauer'))
        # Dauer im fertigen Video: Cuts dazwischen ueberspringen
        return roh_aus_fertig(fertig_aus_roh(start, cuts) + d, cuts, True)
    if wort_ende is not None and standard_dauer is None:
        return wort_ende
    return roh_aus_fertig(fertig_aus_roh(start, cuts) + (standard_dauer or 3.0),
                          cuts, True)


def wo(t, cuts):
    return '{} (im fertigen Video {})'.format(zeit_text(t),
                                             zeit_text(fertig_aus_roh(t, cuts)))


def nummer(liste, obj, key):
    s = sorted(liste, key=lambda x: float(x.get(key) or 0))
    return next(i + 1 for i, x in enumerate(s) if x is obj)


# --------------------------------------------------------------- Effekte
def sfx_bibliothek(pj, projdir):
    import build_editor
    with contextlib.redirect_stdout(io.StringIO()):
        lib, _ = build_editor.build_sfxlib(pj, projdir)
    return lib.get('kategorien') or []


def sfx_finden(pj, projdir, suche):
    q = norm(suche)
    kandidaten = []
    for k in sfx_bibliothek(pj, projdir):
        for e in k['dateien']:
            n = norm(e['n'])
            rang = 0 if n == q else 1 if n.startswith(q) else 2 if q in n \
                else 3 if q in norm(k['name']) else None
            if rang is not None:
                kandidaten.append((rang, len(e['n']), k['name'], e))
    kandidaten.sort(key=lambda x: (x[0], x[1]))
    return kandidaten


def gain_aus_level(level, peak):
    if peak is None or peak <= -98:
        faktor = 1.0
    else:
        faktor = min(8.0, 10 ** ((SFX_ZIEL_DB - peak) / 20))
    return min(1.0, round(level * faktor, 3))


# ---------------------------------------------------------------- Befehle
def befehl_liste(pj):
    cuts = aktive_cuts(pj)
    dauer = float(pj.get('duration') or 0)
    weg = sum(e - s for s, e in cuts)
    print('Länge: {} roh, {} fertig · {} Wörter'.format(
        zeit_text(dauer), zeit_text(dauer - weg), len(woerter(pj))))

    def zeile(titel, liste, key, beschr):
        if not liste:
            return
        print(titel + ':')
        for i, x in enumerate(sorted(liste, key=lambda x: float(x.get(key) or 0))):
            print('  {} {}'.format(i + 1, beschr(x)))

    zeile('Cuts', pj.get('cuts') or [], 'start', lambda c: '{}–{} {}{}'.format(
        zeit_text(float(c['start'])), zeit_text(float(c['end'])),
        c.get('reason') or '', '' if c.get('active', True) else ' (aus)'))
    zeile('Effekte', (pj.get('effekte') or {}).get('sfx') or [], 'time',
          lambda e: '{} {}'.format(wo(float(e['time']), cuts),
                                   e.get('name') or os.path.splitext(
                                       os.path.basename(str(e.get('file'))))[0]))
    zeile('Filter', pj.get('filter') or [], 'start', lambda f: '{}–{} {} {}%'.format(
        zeit_text(float(f['start'])), zeit_text(float(f['end'])), f.get('preset'),
        int(round(float(f.get('staerke', 1)) * 100))))
    zeile('Texte', pj.get('texts') or [], 'start', lambda t: '{}–{} „{}"'.format(
        zeit_text(float(t['start'])), zeit_text(float(t['end'])),
        str(t.get('text', '')).split('\n')[0][:40]))
    zeile('Zooms', pj.get('zooms') or [], 'start', lambda z: '{}–{} {}%'.format(
        zeit_text(float(z['start'])), zeit_text(float(z['end'])),
        int(round(float(z.get('zoom', 1.15)) * 100))))


def befehl_suche(pj):
    cuts = aktive_cuts(pj)
    suche = arg('--suche')
    alle = wort_treffer(pj, suche)
    if not alle:
        # aehnliche Woerter als Hilfe
        q = norm(suche)
        aehnlich = sorted({(w.get('text') or w.get('word') or '').strip()
                           for w in woerter(pj)
                           if q[:4] and norm(w.get('text') or w.get('word') or '')
                           .startswith(q[:4])})
        print('Kein Treffer für „{}".{}'.format(
            suche, ' Ähnlich: ' + ', '.join(aehnlich[:12]) if aehnlich else ''))
        return
    for i, (s, e, text) in enumerate(alle):
        print('{} {} „{}"{}'.format(i + 1, wo(s, cuts), text,
                                    ' — rausgeschnitten' if in_cut(s, cuts) else ''))


def befehl_sfx_liste(pj, projdir):
    q = norm(arg('--sfx-liste') or '')
    for k in sfx_bibliothek(pj, projdir):
        namen = [e['n'] for e in k['dateien'] if not q or q in norm(e['n'])
                 or q in norm(k['name'])]
        if namen:
            print('{} ({}): {}'.format(k['name'], len(namen), ', '.join(namen[:40])))


def befehl_effekt(pj, projdir, pfad):
    cuts = aktive_cuts(pj)
    gefunden = sfx_finden(pj, projdir, arg('--effekt'))
    if not gefunden:
        fehler('Kein Soundeffekt passt zu „{}". --sfx-liste zeigt alle.'.format(
            arg('--effekt')))
    _, _, kat, s = gefunden[0]
    start, _, beschr = anker(pj, cuts)
    start = max(0.0, start - zeit_lesen(arg('--vor', '0')))
    level = max(0.0, min(1.0, float(arg('--laut', '60')) / 100))
    ev = {'time': round(start, 2), 'file': s['f'], 'name': s['n']}
    if s.get('pk') is not None:
        ev['peak'] = s['pk']
    trim = float(s.get('on') or 0)          # stiller Vorlauf weg (wie Cockpit)
    if trim > 0.02:
        ev['trim'] = round(trim, 3)
    ev['level'] = round(level, 2)
    ev['gain'] = gain_aus_level(level, s.get('pk'))
    hoerbar = max(0.0, float(s['d']) - trim)
    laenge = zeit_lesen(arg('--laenge')) if arg('--laenge') else (
        2.5 if hoerbar > 4 else 0)          # Ueberlaenge kuerzen (wie Cockpit)
    if 0.05 < laenge < hoerbar - 0.05:
        ev['len'] = round(laenge, 2)
        ev['fade'] = round(min(0.2, laenge / 3), 3)
    sfx = pj.setdefault('effekte', {}).setdefault('sfx', [])
    sfx.append(ev)
    sfx.sort(key=lambda e: float(e['time']))
    speichern(pfad, pj)
    bauen(pfad)
    andere = [g[3]['n'] for g in gefunden[1:6] if g[3]['n'] != s['n']]
    print('OK Effekt {}: {} ({}) bei {}{}{} · {} s · Lautstärke {}%'.format(
        nummer(sfx, ev, 'time'), s['n'], kat, wo(ev['time'], cuts),
        ' · ' + beschr if beschr else '',
        '' if not andere else ' · auch passend: ' + ', '.join(andere),
        str(ev.get('len') or round(hoerbar, 2)).replace('.', ','),
        int(level * 100)))


def befehl_filter(pj, pfad):
    import filter_presets
    cuts = aktive_cuts(pj)
    name = norm(arg('--filter')).replace('_', '')
    preset = FILTER_NAMEN.get(arg('--filter').strip().lower()) \
        or FILTER_NAMEN.get(name) or (name if filter_presets.bekannt(name) else None)
    if not preset:
        fehler('Filter „{}" gibt es nicht. Möglich: {}'.format(
            arg('--filter'), ', '.join(list(filter_presets.PRESETS)
                                       + list(filter_presets.LOOKS) + ['farbe'])))
    start, wende, beschr = anker(pj, cuts)
    ende = bis_zeit(pj, cuts, start, wende, 3.0)
    if ende - start < 0.2:
        fehler('Der Abschnitt ist kürzer als 0,2 s.')
    f = {'start': round(start, 2), 'end': round(ende, 2), 'preset': preset,
         'staerke': round(max(0.1, min(1.0, float(arg('--staerke', '100')) / 100)), 2)}
    if preset == 'farbe':
        farben = []
        for x in (arg('--farben') or 'rot').split(','):
            x = x.strip()
            h = filter_presets.FARB_NAMEN.get(x.lower(), x)
            if not re.match(r'^#?[0-9a-fA-F]{6}$', h):
                fehler('Farbe „{}" unbekannt. Möglich: rot, blau, gelb, gruen, '
                       'orange, pink, lila, tuerkis oder #rrggbb'.format(x))
            farben.append('#' + h.lstrip('#').lower())
        f['farben'] = farben
        f['toleranz'] = int(arg('--toleranz', '25'))
    liste = pj.setdefault('filter', [])
    liste.append(f)
    liste.sort(key=lambda x: float(x['start']))
    speichern(pfad, pj)
    bauen(pfad)
    name = (filter_presets.PRESETS[preset][0] if preset in filter_presets.PRESETS
            else filter_presets.LOOKS.get(preset) or filter_presets.FARBE_NAME)
    if preset == 'farbe':
        name += ' (' + ', '.join(f['farben']) + ')'
    print('OK Filter {}: {} {}% von {} bis {}{}'.format(
        nummer(liste, f, 'start'), name,
        int(f['staerke'] * 100), wo(f['start'], cuts), wo(f['end'], cuts),
        ' · ' + beschr if beschr else ''))


def befehl_text(pj, pfad):
    import build_editor
    cuts = aktive_cuts(pj)
    start, wende, beschr = anker(pj, cuts)
    ende = bis_zeit(pj, cuts, start, None, 3.0)
    t = {'text': arg('--text'), 'start': round(start, 2), 'end': round(ende, 2),
         'x': float(arg('--x', '0.5')), 'y': float(arg('--y', '0.3')),
         'font': build_editor.schriften()[1], 'size': int(arg('--groesse', '72')),
         'color': '#FFFFFF', 'bold': True, 'box': True, 'box_color': '000000',
         'box_alpha': 0.55, 'box_style': 'line', 'anim': 'fade', 'width': 0}
    liste = pj.setdefault('texts', [])
    liste.append(t)
    liste.sort(key=lambda x: float(x['start']))
    speichern(pfad, pj)
    bauen(pfad)
    print('OK Text {}: „{}" von {} bis {}{}'.format(
        nummer(liste, t, 'start'), t['text'], wo(t['start'], cuts),
        wo(t['end'], cuts), ' · ' + beschr if beschr else ''))


def befehl_zoom(pj, pfad):
    cuts = aktive_cuts(pj)
    start, wende, beschr = anker(pj, cuts)
    ende = bis_zeit(pj, cuts, start, None, 2.0)
    z = {'start': round(start, 2), 'end': round(ende, 2),
         'zoom': max(1.05, min(2.0, float(arg('--zoom')))),
         'x': float(arg('--x', '0.5')), 'y': float(arg('--y', '0.35')),
         'ramp_in': 0.6, 'ramp_out': 0.6}
    liste = pj.setdefault('zooms', [])
    liste.append(z)
    liste.sort(key=lambda x: float(x['start']))
    speichern(pfad, pj)
    bauen(pfad)
    print('OK Zoom {}: {}% von {} bis {}{} · Ziel x={} y={}'.format(
        nummer(liste, z, 'start'), int(round(z['zoom'] * 100)),
        wo(z['start'], cuts), wo(z['end'], cuts),
        ' · ' + beschr if beschr else '', z['x'], z['y']))


def befehl_cut(pj, pfad):
    cuts = aktive_cuts(pj)
    neue = []
    if arg('--wort'):
        alle = wort_treffer(pj, arg('--wort'))
        if not alle:
            fehler('„{}" kommt im Transkript nicht vor.'.format(arg('--wort')))
        if '--alle' in sys.argv:
            ziele = alle
        elif arg('--nr'):
            ziele = [alle[int(arg('--nr')) - 1]]
        else:
            ziele = [alle[0]]
        for s, e, text in ziele:
            if not in_cut(s, cuts):
                neue.append({'start': round(s, 2), 'end': round(e, 2),
                             'reason': '„{}" raus'.format(text), 'active': True,
                             'track': 'both'})
    else:
        s, _, _ = anker(pj, cuts)
        e = bis_zeit(pj, cuts, s, None, None)
        if e - s < 0.1:
            fehler('Der Cut ist kürzer als 0,1 s.')
        neue.append({'start': round(s, 2), 'end': round(e, 2),
                     'reason': 'Per Zuruf', 'active': True, 'track': 'both'})
    if not neue:
        print('Nichts zu tun — die Stelle(n) sind schon rausgeschnitten.')
        return
    liste = pj.setdefault('cuts', [])
    liste.extend(neue)
    liste.sort(key=lambda c: float(c['start']))
    speichern(pfad, pj)
    bauen(pfad)
    for c in neue:
        print('OK Cut {}: {}–{} {}'.format(nummer(liste, c, 'start'),
                                          zeit_text(c['start']), zeit_text(c['end']),
                                          c['reason']))


def befehl_format(pj, pfad):
    import bildformat
    fmt = arg('--format').replace('x', ':').replace('/', ':').strip()
    if fmt not in bildformat.FORMATE:
        fehler('Format „{}" gibt es nicht. Möglich: {}'.format(
            arg('--format'), ', '.join(bildformat.FORMATE)))
    pj['format'] = fmt
    ein = arg('--einpassen')
    if ein:
        ein = {'zuschneiden': 'fuellen', 'füllen': 'fuellen', 'fill': 'fuellen',
               'blur': 'unscharf', 'unschaerfe': 'unscharf', 'schwarz': 'balken',
               'raender': 'balken'}.get(ein.lower(), ein.lower())
        if ein not in bildformat.EINPASSEN:
            fehler('Einpassen „{}" gibt es nicht. Möglich: fuellen, unscharf, balken'
                   .format(arg('--einpassen')))
        pj['einpassen'] = ein
    if arg('--ausschnitt') is not None or arg('--ausschnitt-y') is not None:
        a = pj.get('ausschnitt') or {}
        if arg('--ausschnitt') is not None:
            a['x'] = max(0.0, min(1.0, float(arg('--ausschnitt').replace(',', '.'))))
        if arg('--ausschnitt-y') is not None:
            a['y'] = max(0.0, min(1.0, float(arg('--ausschnitt-y').replace(',', '.'))))
        pj['ausschnitt'] = dict(a, x=a.get('x', 0.5), y=a.get('y', 0.5))
    if '--folgen' in sys.argv or '--nicht-folgen' in sys.argv:
        a = pj.get('ausschnitt') or {}
        a['folgen'] = '--folgen' in sys.argv
        pj['ausschnitt'] = a
        if a['folgen'] and 'einpassen' not in pj:
            pj['einpassen'] = 'fuellen'      # Folgen braucht den Zuschnitt
    speichern(pfad, pj)
    bauen(pfad)
    w, h, _ = bildformat.ziel(pj)
    q = bildformat.quelle_masse(os.path.join(os.path.dirname(pfad),
                                             (pj.get('videos') or [pj.get('video', '')])[0]))
    passt = q and abs(q[0] / q[1] - w / h) < 0.01
    x, y = bildformat.ausschnitt(pj)
    folgt = (pj.get('ausschnitt') or {}).get('folgen') and bildformat.einpassen(pj) == 'fuellen'
    print('OK Format {} ({}×{}){}{}'.format(
        fmt, w, h, ' · Video passt genau' if passt else ' · Einpassen: {}{}'.format(
            bildformat.EINPASSEN[bildformat.einpassen(pj)],
            ' · Ausschnitt x={} y={}'.format(x, y)
            if bildformat.einpassen(pj) == 'fuellen' and not folgt else ''),
        ' · Kamera folgt der Person' if folgt and not passt else ''))


def befehl_loeschen(pj, pfad):
    i = sys.argv.index('--loeschen')
    if len(sys.argv) < i + 3:
        fehler('So: --loeschen effekt 3')
    art = ARTEN.get(sys.argv[i + 1].lower())
    if not art:
        fehler('Art unbekannt: {} (cut, effekt, filter, text, zoom)'.format(
            sys.argv[i + 1]))
    n = int(sys.argv[i + 2])
    if art == 'sfx':
        liste, key = (pj.get('effekte') or {}).get('sfx') or [], 'time'
    else:
        liste, key = pj.get(art) or [], 'start'
    sortiert = sorted(liste, key=lambda x: float(x.get(key) or 0))
    if not 1 <= n <= len(sortiert):
        fehler('Davon gibt es {}, Nummer {} gibt es nicht.'.format(
            len(sortiert), n))
    weg = sortiert[n - 1]
    liste.remove(weg)
    if art == 'sfx' and not liste:
        pj['effekte'].pop('sfx', None)
        if not pj['effekte']:
            pj.pop('effekte')
    speichern(pfad, pj)
    bauen(pfad)
    print('OK gelöscht: {} {} ({})'.format(sys.argv[i + 1], n, zeit_text(
        float(weg.get(key) or 0))))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    pfad = projekt_pfad(sys.argv[1])
    projdir = os.path.dirname(pfad)
    pj = laden(pfad)                       # IMMER frisch: der Nutzer kann im
    if '--liste' in sys.argv:              # Cockpit weitergearbeitet haben
        befehl_liste(pj)
    elif '--suche' in sys.argv:
        befehl_suche(pj)
    elif '--sfx-liste' in sys.argv:
        befehl_sfx_liste(pj, projdir)
    elif '--effekt' in sys.argv:
        befehl_effekt(pj, projdir, pfad)
    elif '--filter' in sys.argv:
        befehl_filter(pj, pfad)
    elif '--text' in sys.argv:
        befehl_text(pj, pfad)
    elif '--zoom' in sys.argv:
        befehl_zoom(pj, pfad)
    elif '--cut' in sys.argv:
        befehl_cut(pj, pfad)
    elif '--format' in sys.argv:
        befehl_format(pj, pfad)
    elif '--loeschen' in sys.argv:
        befehl_loeschen(pj, pfad)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.exit(main())
