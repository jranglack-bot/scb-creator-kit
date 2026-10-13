#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Serie: viele Reels auf einmal aus EINER gestalteten Vorlage, wie die
Massenerstellung in Canva. Gleicher Aufbau (Texte mit Schrift, Position,
Kasten und Einblendung, dazu Musik, Filter, Format), je Tabellenzeile neue
Texte. Die Videos laufen der Reihe nach durch: 4 Videos, 10 Zeilen ergibt
Video 1 2 3 4 1 2 3 4 1 2.

    <python> serie_reels.py --felder <vorlage>
        Spalten der Serie zeigen (die Texte der Vorlage in Zeitfolge)
    <python> serie_reels.py <vorlage> --videos a.mp4 b.mp4 ... --tabelle texte.tsv
                            [--name x] [--nicht-oeffnen]
        je Zeile ein Projekt anlegen (alle in EINEM Serienordner neben der
        Vorlage), Cockpits bauen, die Serien-Vorschau oeffnen. Rendert NICHT:
        erst zeigen, dann auf das Okay warten.
    <python> serie_reels.py --rendern <serienordner> [--nur 3,5]
        alle (oder einzelne) Reels der Serie nacheinander mit
        render_projekt.py rendern, fertig liegen sie in <serienordner>/fertig/

<vorlage> = Projektordner (oder dessen projekt.json), in dem die Texte im
Cockpit fertig gestaltet sind (Kachel "Texte"). Tabelle: erste Zeile =
Spaltennamen. Die Texte der Vorlage heissen "Text 1", "Text 2" ... nach
ihrer Startzeit, ausser ein Text traegt ein eigenes "feld". Optional eine
Spalte "Video" (Dateiname aus --videos) fuer eine eigene Zuordnung. Getrennt
mit Tab (Excel, Google Sheets), ; oder ,. Leere Zelle = dieser Text faellt in
diesem Reel weg.

Zu lange Texte (mit Text-Breite) werden in 5-%-Schritten bis 60 % kleiner,
bis sie nicht in einen anderen Text oder in die Instagram-Zonen laufen, in die
der Text der Vorlage auch nicht lief. Gemessen wird mit Chromium (Playwright)
und derselben Rechnung wie im Cockpit, damit Vorschau und Render dieselben
Zeilen zeigen.
"""
import csv
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

MAX_ZEILEN = 100
MIN_GROESSE = 0.6
VIDEO_ENDUNGEN = ('.mp4', '.mov', '.m4v', '.mkv', '.webm')
# Instagram-Zonen fuer 1080 x 1920 (Skill reel-layout): oben 14 % frei, unten ab
# 80 % (1536 px) tabu, rechts ab 915 px zwischen 30 % und 88 % Hoehe die Knoepfe.
ZONEN_9_16 = {'oben': 269, 'unten': 1536, 'rechts': 915, 'rOben': 576, 'rUnten': 1690}
ZONEN_NAMEN = {'oben': 'den oberen Rand', 'unten': 'den unteren Bereich (Caption)',
               'rechts': 'den rechten Rand (Herz, Kommentare)'}


def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
            return sys.argv[i + 1]
    return default


def args_liste(name):
    """--videos a.mp4 b.mp4 ... bis zum naechsten --"""
    if name not in sys.argv:
        return []
    aus = []
    for a in sys.argv[sys.argv.index(name) + 1:]:
        if a.startswith('--'):
            break
        aus.append(a)
    return aus


def name_sauber(v):
    s = re.sub(r'[\x00-\x1f\x7f<>{}]', '', str('' if v is None else v)[:200])
    return ' '.join(s.split())[:40]


def ordnername(v):
    s = str(v or '').lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        s = s.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:40].strip('-')


def ffdur(pfad):
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                              '-of', 'csv=p=0', pfad], capture_output=True, text=True,
                             check=True).stdout.strip()
        return round(float(out), 3)
    except Exception:
        return 0.0


def hat_ton(pfad):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries',
                        'stream=index', '-of', 'csv=p=0', pfad], capture_output=True, text=True)
    return bool(r.stdout.strip())


def vorlage_laden(pfad):
    pfad = os.path.abspath(pfad)
    if os.path.isdir(pfad):
        pfad = os.path.join(pfad, 'projekt.json')
    if not os.path.isfile(pfad):
        sys.exit('FEHLER: Vorlage nicht gefunden: %s' % pfad)
    with open(pfad, encoding='utf-8-sig') as f:          # PowerShell schreibt mit BOM
        return json.load(f), os.path.dirname(pfad)


def felder(pj):
    """[(Index in texts, Spaltenname)] in Zeitfolge."""
    t = [x for x in (pj.get('texts') or []) if isinstance(x, dict)]
    folge = sorted(range(len(t)), key=lambda i: (float(t[i].get('start') or 0), i))
    aus = []
    for n, i in enumerate(folge, 1):
        aus.append((i, name_sauber(t[i].get('feld')) or 'Text %d' % n))
    return aus


def tabelle_lesen(pfad):
    if not os.path.isfile(pfad):
        sys.exit('FEHLER: Tabelle nicht gefunden: %s' % pfad)
    if os.path.getsize(pfad) > 2_000_000:
        sys.exit('FEHLER: Tabelle zu gross (hoechstens 2 MB)')
    with open(pfad, encoding='utf-8-sig') as f:
        roh = f.read()
    kopf = roh.lstrip('\r\n').split('\n', 1)[0]
    trenner = next((t for t in ('\t', ';', ',') if t in kopf), '\t')
    zeilen = [z for z in csv.reader(io.StringIO(roh), delimiter=trenner) if any(c.strip() for c in z)]
    if len(zeilen) < 2:
        sys.exit('FEHLER: Die Tabelle braucht eine Kopfzeile mit den Spaltennamen und darunter Zeilen')
    return [name_sauber(c) for c in zeilen[0]], zeilen[1:]


def zeiten_anpassen(liste, alt, neu):
    """Abschnitte (start/end) auf eine andere Videolaenge: was nach dem Ende
    anfaengt, faellt weg; was in der Vorlage bis zum Schluss lief, laeuft auch
    hier bis zum Schluss."""
    aus = []
    for e in liste or []:
        if not isinstance(e, dict):
            continue
        try:
            s, en = float(e.get('start', 0)), float(e.get('end', 0))
        except (TypeError, ValueError):
            continue
        if s >= neu - 0.05:
            continue
        if en >= alt - 0.15 or en > neu:
            en = neu
        aus.append(dict(e, start=round(s, 3), end=round(en, 3)))
    return aus


def datei_mitnehmen(rel, vorlage_dir, medien, serie_dir):
    """Musik oder Voiceover der Vorlage einmal in den Serienordner, Weg von den
    Reels aus gesehen zurueck."""
    if not rel:
        return rel
    q = rel if os.path.isabs(rel) else os.path.join(vorlage_dir, rel)
    if not os.path.isfile(q):
        return rel
    os.makedirs(medien, exist_ok=True)
    ziel = os.path.join(medien, os.path.basename(q))
    if not os.path.exists(ziel):
        shutil.copy2(q, ziel)
    return '../' + os.path.relpath(ziel, serie_dir).replace(os.sep, '/')


# ------------------------------------------------------------- Messen (Chromium)
# Gleiche Rechnung wie computeLines im Cockpit (templates/editor.html): Woerter
# auffuellen, bis die Zeile breiter als width * Bildbreite wird.
MESSEN_JS = r"""(job) => {
  const ctx = document.createElement('canvas').getContext('2d');
  const schrift = (tx, g) => (tx.bold === false ? '500 ' : '800 ') + g + "px '" + (tx.font || job.std) + "'";
  function zeilen(tx, g){
    if (!tx.width) return String(tx.text || '').split('\n');
    ctx.font = schrift(tx, g);
    const maxW = tx.width * job.W, aus = [];
    String(tx.text || '').split('\n').forEach(par => {
      let cur = '';
      par.split(' ').forEach(w => {
        const t = cur ? cur + ' ' + w : w;
        if (cur && ctx.measureText(t).width > maxW){ aus.push(cur); cur = w; } else cur = t;
      });
      aus.push(cur);
    });
    return aus;
  }
  // Flaeche eines Texts im Bild (Mitte = x/y wie im Render, \an5), mit Kasten
  function flaeche(tx, g, z){
    ctx.font = schrift(tx, g);
    const br = Math.max(0, ...z.map(l => ctx.measureText(l).width)) + (tx.box ? g * 0.7 : 0);
    const ho = z.length * g * 1.25 + (tx.box ? g * 0.3 : 0);
    const cx = (+tx.x || 0.5) * job.W, cy = (+tx.y || 0.3) * job.H;
    return {l: cx - br / 2, r: cx + br / 2, o: cy - ho / 2, u: cy + ho / 2,
            s: +tx.start || 0, e: +tx.end || 0};
  }
  function konflikte(f){
    return f.map((a, i) => {
      const k = [];
      const Z = job.zonen;
      if (Z){
        if (a.o < Z.oben) k.push('oben');
        if (a.u > Z.unten) k.push('unten');
        if (a.r > Z.rechts && a.u > Z.rOben && a.o < Z.rUnten) k.push('rechts');
      }
      f.forEach((b, j) => {
        if (j === i) return;
        const zeit = Math.min(a.e, b.e) - Math.max(a.s, b.s) > 0.05;
        if (zeit && Math.min(a.r, b.r) - Math.max(a.l, b.l) > 2 && Math.min(a.u, b.u) - Math.max(a.o, b.o) > 2)
          k.push('text:' + b.id);
      });
      return k;
    });
  }
  const vorlage = job.vorlage.map(tx => flaeche(tx, +tx.size || 72, zeilen(tx, +tx.size || 72)));
  vorlage.forEach((f, i) => { f.id = job.vorlage[i]._i; });
  const erlaubt = {}, vorher = {};
  konflikte(vorlage).forEach((k, i) => { erlaubt[job.vorlage[i]._i] = new Set(k); });
  vorlage.forEach(f => { vorher[f.id] = f; });
  // Gewachsen gegenueber der Vorlage? Bei zwei Texten, die sich neu ueberlappen,
  // wird nur der kleiner, der laenger geworden ist, nicht der unschuldige Nachbar.
  const gewachsen = (a) => { const v = vorher[a.id]; return !v || (a.u - a.o) > (v.u - v.o) + 1; };   // mehr Zeilen
  return job.reels.map(texte => {
    const g0 = texte.map(tx => +tx.size || 72), faktor = texte.map(() => 1);
    let z = [], f = [], neu = [];
    for (let runde = 0; runde < 12; runde++){
      z = texte.map((tx, i) => zeilen(tx, Math.round(g0[i] * faktor[i])));
      f = texte.map((tx, i) => { const a = flaeche(tx, Math.round(g0[i] * faktor[i]), z[i]); a.id = tx._i; return a; });
      neu = konflikte(f).map((k, i) => k.filter(x => !(erlaubt[texte[i]._i] || new Set()).has(x)));
      let weiter = false;
      neu.forEach((k, i) => {
        const zone = k.some(x => x.indexOf('text:') !== 0), text = k.some(x => x.indexOf('text:') === 0);
        if ((zone || (text && gewachsen(f[i]))) && texte[i]._feld && faktor[i] > job.min + 1e-6){
          faktor[i] = Math.max(job.min, faktor[i] * 0.95); weiter = true;
        }
      });
      if (!weiter) break;
    }
    return texte.map((tx, i) => ({_i: tx._i, size: Math.round(g0[i] * faktor[i]), lines: z[i],
                                  faktor: faktor[i], konflikt: neu[i]}));
  });
}"""


def messen(job):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit('FEHLER: Zum Messen der Zeilen fehlt Playwright. Einmal: '
                 '<python> -m pip install playwright && <python> -m playwright install chromium')
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        try:
            pg = b.new_page()
            pg.set_content('<!doctype html><meta charset="utf-8"><body></body>')
            # Schriften wie im Cockpit: erst laden, dann messen
            pg.evaluate("(fs) => Promise.all(fs.map(f => document.fonts.load(f).catch(() => null)))",
                        sorted({("500 72px '%s'" % t.get('font', job['std'])) for t in job['vorlage']}
                               | {("800 72px '%s'" % t.get('font', job['std'])) for t in job['vorlage']}))
            return pg.evaluate(MESSEN_JS, job)
        finally:
            b.close()


# ------------------------------------------------------------------ Anlegen

def felder_zeigen(vorlage):
    pj, _ = vorlage_laden(vorlage)
    t = pj.get('texts') or []
    f = felder(pj)
    if not f:
        sys.exit('Die Vorlage hat noch keine Texte. Erst im Cockpit (Kachel "Texte") gestalten.')
    print('Spalten der Serie (Texte der Vorlage nach Startzeit):')
    for i, n in f:
        tx = t[i]
        print('  %-12s %5.1f-%5.1f s  %s' % (n, float(tx.get('start') or 0), float(tx.get('end') or 0),
                                             ' / '.join(str(tx.get('text', '')).split('\n'))[:60]))
    print('Dazu optional eine Spalte "Video". Erste Zeile der Tabelle = diese Namen.')


def anlegen():
    vorlage = sys.argv[1]
    pj0, vdir = vorlage_laden(vorlage)
    videos = [os.path.abspath(v) for v in args_liste('--videos')]
    tab = arg('--tabelle')
    if not videos or not tab:
        sys.exit(__doc__)
    for v in videos:
        if not os.path.isfile(v) or not v.lower().endswith(VIDEO_ENDUNGEN):
            sys.exit('FEHLER: kein Video: %s' % v)
    texte0 = [x for x in (pj0.get('texts') or []) if isinstance(x, dict)]
    pj0['texts'] = texte0
    fl = felder(pj0)
    if not fl:
        sys.exit('FEHLER: Die Vorlage hat noch keine Texte. Erst im Cockpit (Kachel "Texte") gestalten.')
    kopf, zeilen = tabelle_lesen(tab)
    namen = {n.lower(): i for i, n in fl}
    fremd = [k for k in kopf if k and k.lower() not in namen and k.lower() != 'video']
    if fremd:
        sys.exit('FEHLER: Spalte ohne Text in der Vorlage: %s. Spalten: %s, Video'
                 % (', '.join(fremd[:5]), ', '.join(n for _, n in fl)))
    zeilen = [z for z in zeilen if any(c.strip() for c in z)]
    if len(zeilen) > MAX_ZEILEN:
        sys.exit('FEHLER: Hoechstens %d Reels auf einmal (%d Zeilen)' % (MAX_ZEILEN, len(zeilen)))
    spalte = {k.lower(): i for i, k in enumerate(kopf) if k}

    name = ordnername(arg('--name') or os.path.basename(vdir).replace('-projekt', '') + '-serie') or 'serie'
    if not name.endswith('-serie'):
        name += '-serie'
    serie_dir = os.path.join(os.path.dirname(vdir), name)
    n = 2
    while os.path.exists(serie_dir):
        serie_dir = os.path.join(os.path.dirname(vdir), '%s-%d' % (name, n)); n += 1
    name = os.path.basename(serie_dir)
    kurz = name[:-6] if name.endswith('-serie') else name
    os.makedirs(os.path.join(serie_dir, 'videos'))

    # Videos einmal in den Serienordner (Reels zeigen mit ../videos/ darauf)
    vrel = {}
    for v in videos:
        ziel = os.path.join(serie_dir, 'videos', re.sub(r'[^A-Za-z0-9_.\-]', '_', os.path.basename(v)))
        if v not in vrel:
            if not os.path.exists(ziel):
                if hat_ton(v):
                    shutil.copy2(v, ziel)
                else:
                    # Stummer Clip (typisch B-Roll): stille Tonspur dazu, Bild unveraendert.
                    # Der Render mischt sonst Musik und Ton aus einer Spur, die es nicht gibt.
                    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', v, '-f', 'lavfi', '-i',
                                    'anullsrc=r=48000:cl=stereo', '-map', '0:v:0', '-map', '1:a',
                                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '128k', '-shortest', ziel],
                                   check=True)
            vrel[v] = 'videos/' + os.path.basename(ziel)
    vorlage_videos = [os.path.join(vdir, x) if not os.path.isabs(x) else x
                      for x in (pj0.get('videos') or ([pj0['video']] if pj0.get('video') else []))]
    alt_dauer = float(pj0.get('duration') or 0) or sum(ffdur(x) for x in vorlage_videos)

    def gleich(v):
        return (len(vorlage_videos) == 1 and os.path.isfile(vorlage_videos[0])
                and os.path.normcase(os.path.abspath(vorlage_videos[0])) == os.path.normcase(v))

    dauer = {v: ffdur(v) for v in videos}
    reels, hinweise = [], []
    medien = os.path.join(serie_dir, 'medien')
    std = '_standardschrift'
    std_schrift = pj0.get(std) or ('Segoe UI' if os.name == 'nt' else 'Helvetica Neue')
    worte_weg = False
    for zi, z in enumerate(zeilen):
        vcell = z[spalte['video']].strip() if 'video' in spalte and spalte['video'] < len(z) else ''
        if vcell:
            treffer = [v for v in videos if os.path.basename(v).lower() == os.path.basename(vcell).lower()]
            if not treffer:
                sys.exit('FEHLER: Zeile %d: Video "%s" ist nicht unter --videos' % (zi + 1, vcell[:80]))
            v = treffer[0]
        else:
            v = videos[zi % len(videos)]
        d = dauer[v] or alt_dauer
        pj = json.loads(json.dumps(pj0))
        for k in list(pj):
            if k.startswith('_') or k in ('rev', 'video'):
                del pj[k]                         # Anzeige-Felder des Cockpits, baut build_editor neu
        pj['videos'] = ['../' + vrel[v]]
        pj['duration'] = d
        if not gleich(v):
            # anderes Video: Schnitte und Transkript der Vorlage passen nicht
            pj['cuts'] = []
            if pj.get('words'):
                pj['words'] = []
                worte_weg = True
            if (pj.get('captions') or {}).get('enabled'):
                pj['captions']['enabled'] = False
            pj.pop('freistellung', None)
            for k in ('zooms', 'volumes'):
                if isinstance(pj.get(k), list):
                    pj[k] = zeiten_anpassen(pj[k], alt_dauer, d)
            if isinstance(pj.get('filter'), list):
                pj['filter'] = zeiten_anpassen(pj['filter'], alt_dauer, d)
        for k in ('music', 'voiceover'):
            if isinstance(pj.get(k), dict) and pj[k].get('file'):
                pj[k]['file'] = datei_mitnehmen(pj[k]['file'], vdir, medien, serie_dir)
        # Texte: Feld ersetzen, leere Zelle = Text faellt weg
        neue = []
        for i, tx in enumerate(pj['texts']):
            tx = dict(tx, _i=i)
            feldname = next(n for j, n in fl if j == i)
            if feldname.lower() in spalte:
                c = spalte[feldname.lower()]
                wert = (z[c] if c < len(z) else '').replace('\r\n', '\n').strip()
                if not wert:
                    continue
                tx['text'] = wert[:2000]
                tx['_feld'] = True
            tx.pop('lines', None)
            tx.pop('feld', None)
            neue.append(tx)
        if not gleich(v):
            neue = zeiten_anpassen(neue, alt_dauer, d)
        pj['texts'] = neue
        nr = zi + 1
        ordner = '%s-%02d-projekt' % (kurz, nr)
        # Ausgabe im eigenen Ordner (prolook rechnet relativ zum Ordner des fertigen
        # Videos); rendern() kopiert es danach nach <serie>/fertig/
        pj['render'] = dict(pj.get('render') or {}, output='%s-%02d.mp4' % (kurz, nr))
        reels.append({'nr': nr, 'ordner': ordner, 'video': vrel[v], 'pj': pj})
    if worte_weg:
        hinweise.append('Die Vorlage hatte Untertitel aus ihrem Video. Die anderen Videos haben eigene '
                        'Worte, dort sind die Untertitel aus (bei Bedarf je Reel transkribieren).')

    # Zeilen messen und zu lange Texte verkleinern, eine Chromium-Sitzung fuer alle
    W, H = 1080, 1920
    try:
        import bildformat
        W, H, _f = bildformat.ziel(pj0)
    except Exception:
        pass
    job = {'W': W, 'H': H, 'std': std_schrift, 'min': MIN_GROESSE,
           'zonen': ZONEN_9_16 if (W, H) == (1080, 1920) else None,
           'vorlage': [dict(t, _i=i) for i, t in enumerate(texte0)],
           'reels': [r['pj']['texts'] for r in reels]}
    ergebnis = messen(job)
    for r, mess in zip(reels, ergebnis):
        nach_i = {m['_i']: m for m in mess}
        for tx in r['pj']['texts']:
            m = nach_i.get(tx['_i'])
            if m:
                if tx.get('width'):                   # ohne Breite: eine Zeile je Enter, wie im Cockpit
                    tx['lines'] = m['lines']
                if m['faktor'] < 0.999:
                    tx['size'] = m['size']
                    hinweise.append('Reel %d: „%s“ auf %d %% verkleinert' % (
                        r['nr'], next(n for j, n in fl if j == tx['_i']), round(m['faktor'] * 100)))
                for k in m['konflikt']:
                    wo = ZONEN_NAMEN.get(k) or ('„%s“' % next((n for j, n in fl if 'text:%d' % j == k), k))
                    hinweise.append('Reel %d: „%s“ reicht in %s, bitte ansehen' % (
                        r['nr'], next(n for j, n in fl if j == tx['_i']), wo))
            tx.pop('_i', None)
            tx.pop('_feld', None)

    # Projekte schreiben, Cockpits bauen
    for r in reels:
        pdir = os.path.join(serie_dir, r['ordner'])
        os.makedirs(pdir)
        with open(os.path.join(pdir, 'projekt.json'), 'w', encoding='utf-8') as f:
            json.dump(r['pj'], f, ensure_ascii=False, indent=1)
        b = subprocess.run([sys.executable, os.path.join(HIER, 'build_editor.py'),
                            os.path.join(pdir, 'projekt.json')], capture_output=True, text=True)
        if b.returncode:
            sys.exit('FEHLER beim Cockpit fuer %s:\n%s' % (r['ordner'], (b.stderr or b.stdout)[-800:]))
    os.makedirs(os.path.join(serie_dir, 'fertig'), exist_ok=True)
    serie = {'name': kurz, 'vorlage': vdir, 'erstellt': time.strftime('%Y-%m-%d %H:%M'),
             'reels': [{'nr': r['nr'], 'ordner': r['ordner'], 'video': r['video']} for r in reels],
             'hinweise': hinweise[:80]}
    with open(os.path.join(serie_dir, 'serie.json'), 'w', encoding='utf-8') as f:
        json.dump(serie, f, ensure_ascii=False, indent=1)
    vorschau_bauen(serie_dir)
    starter_schreiben(serie_dir)
    print('SERIE: %s, %d Reels (%s)' % (serie_dir, len(reels), ', '.join(
        '%d=%s' % (r['nr'], os.path.basename(r['video'])) for r in reels[:12])
        + (' ...' if len(reels) > 12 else '')))
    for h in hinweise[:40]:
        print('  ' + h)
    if not hinweise:
        print('  Alles passt.')
    if '--nicht-oeffnen' not in sys.argv:
        import cockpit_oeffnen
        cockpit_oeffnen.oeffnen(os.path.join(serie_dir, 'serie_vorschau.html'))


def vorschau_bauen(serie_dir):
    """serie_vorschau.html (aus dem Kit) + serie_data.js (Daten aller Reels).
    Der offene Tab holt serie_data.js alle 3 s nach: nach Aenderungen an einem
    Reel genuegt ein neuer Aufruf mit --vorschau."""
    with open(os.path.join(serie_dir, 'serie.json'), encoding='utf-8-sig') as f:
        serie = json.load(f)
    daten = {'name': serie.get('name'), 'rev': int(time.time()), 'hinweise': serie.get('hinweise') or [],
             'reels': []}
    W, H, modus = 1080, 1920, 'balken'
    for r in serie.get('reels') or []:
        pfad = os.path.join(serie_dir, r['ordner'], 'projekt.json')
        try:
            with open(pfad, encoding='utf-8-sig') as f:
                pj = json.load(f)
        except (OSError, ValueError):
            continue
        try:
            import bildformat
            W, H, _f = bildformat.ziel(pj)
            modus = bildformat.render_einstellung(pj)
        except Exception:
            pass
        schnitte = [[float(c['start']), float(c['end'])] for c in pj.get('cuts') or []
                    if isinstance(c, dict) and c.get('active', True) and c.get('track', 'both') in ('both', 'main')]
        fertig = os.path.join(serie_dir, 'fertig', os.path.basename(str((pj.get('render') or {}).get('output') or '')))
        daten['reels'].append({
            'nr': r['nr'], 'ordner': r['ordner'], 'video': r['video'],
            'dauer': pj.get('duration'), 'texts': pj.get('texts') or [], 'schnitte': schnitte,
            'fertig': os.path.isfile(fertig) and ('fertig/' + os.path.basename(fertig)) or ''})
    daten['W'], daten['H'], daten['modus'] = W, H, str(modus)
    roh = json.dumps(daten, ensure_ascii=False).replace('</', '<\\/')
    with open(os.path.join(serie_dir, 'serie_data.js'), 'w', encoding='utf-8') as f:
        f.write('window.SERIE = ' + roh + ';\n')
    shutil.copyfile(os.path.join(HIER, '..', 'templates', 'serie_vorschau.html'),
                    os.path.join(serie_dir, 'serie_vorschau.html'))


# ------------------------------------------------------------------ Rendern

def starter_schreiben(serie_dir):
    """Doppelklick-Datei 'alle_rendern' im Serienordner (0 Tokens), wie
    video_rendern im einzelnen Projekt: Windows .bat, Mac/Linux .command."""
    import platform
    me = os.path.abspath(__file__)
    if platform.system() == 'Windows':
        with open(os.path.join(serie_dir, 'alle_rendern.bat'), 'w', encoding='cp1252',
                  errors='replace', newline='') as f:
            f.write('@echo off\r\n'
                    'echo Serie wird gerendert - Fenster offen lassen ...\r\n'
                    'set PY=py\r\n'
                    'where /q py || set PY=python\r\n'
                    '%PY% "{}" --rendern "%~dp0."\r\n'
                    'echo.\r\n'
                    'echo Fertig! Die Videos liegen im Ordner fertig.\r\n'
                    'pause\r\n'.format(me))
    else:
        pfad = os.path.join(serie_dir, 'alle_rendern.command')
        with open(pfad, 'w', encoding='utf-8', newline='\n') as f:
            f.write('#!/bin/bash\n'
                    'cd "$(dirname "$0")"\n'
                    'echo "Serie wird gerendert - Fenster offen lassen ..."\n'
                    'PY=""\n'
                    'for K in python3 python /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do\n'
                    '  command -v "$K" >/dev/null 2>&1 && PY="$K" && break\n'
                    'done\n'
                    '"$PY" "{}" --rendern "$(pwd)"\n'
                    'echo ""\n'
                    'echo "Fertig! Die Videos liegen im Ordner fertig."\n'
                    'read -n 1 -s -r -p "Zum Schliessen eine Taste druecken"\n'.format(me))
        os.chmod(pfad, 0o755)


def rendern(serie_dir):
    serie_dir = os.path.abspath(serie_dir)
    try:
        with open(os.path.join(serie_dir, 'serie.json'), encoding='utf-8-sig') as f:
            serie = json.load(f)
    except (OSError, ValueError):
        sys.exit('FEHLER: keine Serie in %s' % serie_dir)
    nur = arg('--nur')
    wahl = {int(x) for x in nur.split(',') if x.strip().isdigit()} if nur else None
    reels = [r for r in serie.get('reels') or [] if not wahl or r['nr'] in wahl]
    os.makedirs(os.path.join(serie_dir, 'fertig'), exist_ok=True)
    rp = os.path.join(HIER, 'render_projekt.py')
    fehler = []
    start = time.time()
    for k, r in enumerate(reels, 1):
        pj = os.path.join(serie_dir, r['ordner'], 'projekt.json')
        t0 = time.time()
        p = subprocess.run([sys.executable, rp, pj], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        with open(os.path.join(serie_dir, r['ordner'], 'render.log'), 'w', encoding='utf-8') as f:
            f.write(p.stdout + '\n' + p.stderr)
        fertig = [z for z in p.stdout.splitlines() if z.startswith('FERTIG:')]
        datei = fertig[-1][7:].split('|')[0].strip() if fertig else ''
        quelle = os.path.join(serie_dir, r['ordner'], datei)
        if p.returncode or not datei or not os.path.isfile(quelle):
            fehler.append(r['nr'])
            print('Reel %d/%d FEHLER (%s, render.log)' % (k, len(reels), r['ordner']), flush=True)
        else:
            shutil.copy2(quelle, os.path.join(serie_dir, 'fertig', os.path.basename(datei)))
            print('Reel %d/%d fertig in %.0f s: fertig/%s' % (k, len(reels), time.time() - t0,
                                                              os.path.basename(datei)), flush=True)
    vorschau_bauen(serie_dir)
    print('SERIE GERENDERT: %d von %d in %.0f s, Ordner: %s' % (
        len(reels) - len(fehler), len(reels), time.time() - start, os.path.join(serie_dir, 'fertig')))
    if fehler:
        print('Fehlgeschlagen: Reel %s' % ', '.join(map(str, fehler)))
        sys.exit(1)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == '--felder' and len(sys.argv) > 2:
        felder_zeigen(sys.argv[2])
    elif sys.argv[1] == '--rendern' and len(sys.argv) > 2:
        rendern(sys.argv[2])
    elif sys.argv[1] == '--vorschau' and len(sys.argv) > 2:
        vorschau_bauen(os.path.abspath(sys.argv[2]))
        print('OK: Vorschau aktualisiert, der offene Tab laedt sie von selbst.')
    elif sys.argv[1].startswith('--'):
        sys.exit(__doc__)
    else:
        anlegen()


if __name__ == '__main__':
    main()
