#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arbeitsordner — EIN Ort fuer alle Videoprojekte, wie bei CapCut.

    <python> arbeitsordner.py                 # zeigt den Stand (Exit 2 = nicht gesetzt)
    <python> arbeitsordner.py --vorschlag     # sinnvoller Standardort fuer dieses System
    <python> arbeitsordner.py --setzen <pfad> # festlegen (legt Unterordner + Startseite an)
    <python> arbeitsordner.py --startseite    # Startseite neu bauen
    <python> arbeitsordner.py --startseite --oeffnen

Aufbau:
    <Arbeitsordner>/
        Projekte/<name>-projekt/   jedes neue Projekt (projekt_starten.py)
        Fertig/                    jedes fertige Video, Name + Datum (render_projekt.py)
        Startseite.html            alle Projekte, zuletzt bearbeitete zuerst

Gemerkt wird das in ~/.scb-creator-kit/einstellungen.json — gilt fuer alle
Projekte, ueberlebt Kit-Updates. Dort steht auch die Liste ALLER Projekte,
die je ein Cockpit bekommen haben (auch aeltere ausserhalb des
Arbeitsordners), damit die Startseite sie zeigen kann.

Das Cockpit speichert direkt in die projekt.json des Projekts, sobald der
Nutzer EINMAL den Arbeitsordner im Browser freigegeben hat (build_editor.py
gibt dem Cockpit den Weg vom Arbeitsordner zum Projekt mit).
"""
import html
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KIT_HOME = os.path.join(os.path.expanduser('~'), '.scb-creator-kit')
EINST = os.path.join(KIT_HOME, 'einstellungen.json')
STARTSEITE = 'Startseite.html'
MAX_PROJEKTE = 300


# ---------------------------------------------------------------- Ablage
def einstellungen():
    try:
        with open(EINST, encoding='utf-8-sig') as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _schreiben(d):
    os.makedirs(KIT_HOME, exist_ok=True)
    tmp = EINST + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:     # ohne BOM
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, EINST)


def arbeitsordner():
    """Gesetzter Arbeitsordner (absolut) oder None."""
    p = einstellungen().get('arbeitsordner')
    return os.path.abspath(p) if p and os.path.isdir(p) else None


def projekte_ordner():
    a = arbeitsordner()
    return os.path.join(a, 'Projekte') if a else None


def fertig_ordner():
    a = arbeitsordner()
    return os.path.join(a, 'Fertig') if a else None


def vorschlag():
    """Standardort: Videos (Windows/Linux) bzw. Filme (Mac) im Benutzerordner."""
    home = os.path.expanduser('~')
    unter = 'Movies' if platform.system() == 'Darwin' else 'Videos'
    basis = os.path.join(home, unter)
    if not os.path.isdir(basis):
        basis = home
    return os.path.join(basis, 'SCB Projekte')


def setzen(pfad):
    pfad = os.path.abspath(os.path.expanduser(pfad))
    for unter in ('', 'Projekte', 'Fertig'):
        os.makedirs(os.path.join(pfad, unter), exist_ok=True)
    d = einstellungen()
    d['arbeitsordner'] = pfad
    _schreiben(d)
    startseite_bauen()
    return pfad


# ------------------------------------------------------- Projekte merken
def projekt_merken(projdir):
    """Projekt in die Liste aufnehmen (vorne = zuletzt angefasst)."""
    projdir = os.path.abspath(projdir)
    d = einstellungen()
    liste = [p for p in d.get('projekte', []) if os.path.normcase(p)
             != os.path.normcase(projdir)]
    d['projekte'] = ([projdir] + liste)[:MAX_PROJEKTE]
    try:
        _schreiben(d)
    except OSError:
        pass


def relpfad(projdir):
    """Weg vom Arbeitsordner zum Projekt als Liste von Ordnernamen — oder
    None, wenn das Projekt nicht im Arbeitsordner liegt."""
    a = arbeitsordner()
    if not a:
        return None
    try:
        rel = os.path.relpath(os.path.abspath(projdir), a)
    except ValueError:              # anderes Laufwerk (Windows)
        return None
    if rel.startswith('..') or os.path.isabs(rel) or rel == '.':
        return None
    return [t for t in Path(rel).parts if t]


def cockpit_info(projdir):
    """Was das Cockpit zum Speichern braucht (oder None)."""
    a = arbeitsordner()
    if not a:
        return None
    return {'pfad': a, 'name': os.path.basename(a.rstrip('\\/')),
            'rel': relpfad(projdir)}


# ------------------------------------------------------------- Fertig
def fertig_ablegen(video, projname):
    """Fertiges Video zusaetzlich nach <Arbeitsordner>/Fertig legen.
    Name: <projekt> <JJJJ-MM-TT>.mp4 — gleicher Tag = ueberschreiben
    (neueste Fassung), anderer Tag = bleibt daneben erhalten."""
    ziel_ordner = fertig_ordner()
    if not ziel_ordner or not os.path.isfile(video):
        return None
    os.makedirs(ziel_ordner, exist_ok=True)
    name = projname[:-8] if projname.endswith('-projekt') else projname
    ziel = os.path.join(ziel_ordner, '{} {}{}'.format(
        name, datetime.now().strftime('%Y-%m-%d'),
        os.path.splitext(video)[1] or '.mp4'))
    shutil.copy2(video, ziel)
    return ziel


def vorschaubild(projdir, video):
    """Kleines Standbild fuer die Startseite (einmalig, ~20 KB)."""
    ziel = os.path.join(projdir, 'vorschau.jpg')
    quelle = os.path.join(projdir, video) if video else ''
    if os.path.exists(ziel) or not os.path.isfile(quelle):
        return
    try:
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', '1', '-i', quelle,
                        '-frames:v', '1', '-vf', 'scale=360:-2', '-q:v', '5',
                        ziel], capture_output=True, timeout=30)
    except Exception:
        pass


# ---------------------------------------------------------- Startseite
def _projekt_lesen(projdir):
    pj_pfad = os.path.join(projdir, 'projekt.json')
    if not os.path.isfile(pj_pfad) or not os.path.isfile(
            os.path.join(projdir, 'editor.html')):
        return None
    try:
        with open(pj_pfad, encoding='utf-8-sig') as f:
            pj = json.load(f)
    except (OSError, ValueError):
        pj = {}
    stand = os.path.getmtime(pj_pfad)
    try:
        g = datetime.fromisoformat(str(pj.get('_gespeichert', ''))
                                   .replace('Z', '+00:00')).timestamp()
        stand = max(stand, g)
    except ValueError:
        pass
    dauer = float(pj.get('duration') or 0)
    weg = sum(float(c['end']) - float(c['start'])
              for c in (pj.get('cuts') or [])
              if c.get('active', True) and (c.get('track') or 'both')
              in ('both', 'main'))
    out = (pj.get('render') or {}).get('output') or 'final.mp4'
    fertig = None
    for kandidat in (out, os.path.basename(projdir) + '_final.mp4'):
        p = os.path.join(projdir, kandidat)
        if os.path.isfile(p):
            fertig = p
            break
    name = os.path.basename(projdir.rstrip('\\/'))
    if name.endswith('-projekt'):
        name = name[:-8]
    return {'name': name, 'ordner': projdir, 'stand': stand,
            'laenge': max(0.0, dauer - weg),
            'cuts': sum(1 for c in (pj.get('cuts') or []) if c.get('active', True)),
            'bild': os.path.join(projdir, 'vorschau.jpg')
            if os.path.isfile(os.path.join(projdir, 'vorschau.jpg')) else None,
            'fertig': fertig}


def alle_projekte():
    gesehen, aus = set(), []
    kandidaten = list(einstellungen().get('projekte', []))
    po = projekte_ordner()
    if po and os.path.isdir(po):
        kandidaten += [os.path.join(po, n) for n in os.listdir(po)]
    for p in kandidaten:
        key = os.path.normcase(os.path.abspath(p))
        if key in gesehen:
            continue
        gesehen.add(key)
        info = _projekt_lesen(p)
        if info:
            aus.append(info)
    aus.sort(key=lambda x: x['stand'], reverse=True)
    return aus


def _zeit(ts):
    d = datetime.fromtimestamp(ts)
    heute = datetime.now().date()
    if d.date() == heute:
        return 'heute, ' + d.strftime('%H:%M')
    if (heute - d.date()).days == 1:
        return 'gestern, ' + d.strftime('%H:%M')
    return d.strftime('%d.%m.%Y')


def _dauer(s):
    s = int(round(s))
    return '{}:{:02d}'.format(s // 60, s % 60)


def _link(ziel, basis):
    """Relativer Link, wenn ziel im Arbeitsordner liegt (bleibt gueltig,
    wenn der ganze Ordner umzieht), sonst absolute file://-Adresse."""
    from urllib.parse import quote
    try:
        rel = os.path.relpath(ziel, basis)
        if not rel.startswith('..') and not os.path.isabs(rel):
            return quote(rel.replace(os.sep, '/'))
    except ValueError:                  # anderes Laufwerk
        pass
    return Path(ziel).as_uri()


def startseite_bauen():
    """Startseite.html im Arbeitsordner neu schreiben. Gibt den Pfad zurueck."""
    a = arbeitsordner()
    if not a:
        return None
    karten = []
    for p in alle_projekte():
        uri = _link(os.path.join(p['ordner'], 'editor.html'), a)
        bild = ('<img src="{}" alt="" loading="lazy">'.format(
            html.escape(_link(p['bild'], a))) if p['bild']
            else '<div class="leer"></div>')
        fertig = ('<a class="neben" href="{}">Fertiges Video</a>'.format(
            html.escape(_link(p['fertig'], a))) if p['fertig'] else '')
        karten.append(
            '<article data-name="{n}"><a class="bild" href="{u}">{b}</a>'
            '<div class="txt"><a class="titel" href="{u}">{n}</a>'
            '<div class="meta">{z} · {l} · {c} Cuts</div>'
            '<div class="knoepfe"><a class="haupt" href="{u}">Im Cockpit öffnen</a>{f}</div>'
            '</div></article>'.format(
                n=html.escape(p['name']), u=html.escape(uri), b=bild,
                z=_zeit(p['stand']), l=_dauer(p['laenge']), c=p['cuts'],
                f=fertig))
    fertig_uri = 'Fertig/'
    inhalt = ''.join(karten) or (
        '<p class="nichts">Noch keine Projekte. Sag Claude zum Beispiel '
        '„Schneid mir dieses Video" und zieh die Datei ins Fenster.</p>')
    seite = VORLAGE.format(
        ordner=html.escape(a), fertig=html.escape(fertig_uri),
        anzahl=len(karten), karten=inhalt,
        stand=datetime.now().strftime('%d.%m.%Y %H:%M'))
    ziel = os.path.join(a, STARTSEITE)
    with open(ziel, 'w', encoding='utf-8') as f:
        f.write(seite)
    return ziel


VORLAGE = """<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Meine Videoprojekte</title>
<style>
:root {{ --bg:#0b0b0d; --panel:#111113; --card:#17171a; --line:rgba(255,255,255,.07);
  --line2:rgba(255,255,255,.15); --txt:#ecebe6; --txt2:#8f8d87; --acc:#d4af6a;
  --acc-auf:#1a150b; --font:-apple-system,BlinkMacSystemFont,'Segoe UI Variable Text',
  'Segoe UI',system-ui,sans-serif; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:var(--bg); color:var(--txt); font-family:var(--font);
  -webkit-font-smoothing:antialiased; min-height:100vh; }}
header {{ display:flex; align-items:center; gap:14px; flex-wrap:wrap;
  padding:18px 28px; background:var(--panel); border-bottom:1px solid var(--line); }}
header h1 {{ font-size:18px; font-weight:600; }}
header .ort {{ color:var(--txt2); font-size:12px; flex:1; min-width:200px;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
input {{ background:var(--card); border:1px solid var(--line); color:var(--txt);
  border-radius:8px; padding:8px 12px; font:inherit; font-size:13px; width:220px; }}
input:focus {{ outline:none; border-color:var(--acc); }}
a.knopf {{ color:var(--txt); text-decoration:none; font-size:13px; padding:8px 12px;
  border:1px solid var(--line); border-radius:8px; background:var(--card); }}
a.knopf:hover {{ border-color:var(--line2); }}
main {{ padding:26px 28px 60px; display:grid; gap:18px;
  grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); }}
article {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
  overflow:hidden; display:flex; flex-direction:column; transition:border-color .15s; }}
article:hover {{ border-color:var(--line2); }}
.bild {{ display:block; aspect-ratio:9/12; background:#060607; overflow:hidden; }}
.bild img {{ width:100%; height:100%; object-fit:cover; display:block; }}
.leer {{ width:100%; height:100%; background:linear-gradient(160deg,#1d1d22,#0b0b0d); }}
.txt {{ padding:12px 13px 13px; display:flex; flex-direction:column; gap:5px; }}
.titel {{ color:var(--txt); text-decoration:none; font-weight:600; font-size:14px;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.meta {{ color:var(--txt2); font-size:11.5px; }}
.knoepfe {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:6px; }}
.knoepfe a {{ font-size:12px; text-decoration:none; border-radius:7px; padding:6px 10px; }}
.haupt {{ background:var(--acc); color:var(--acc-auf); font-weight:600; }}
.neben {{ color:var(--txt); border:1px solid var(--line); }}
.neben:hover {{ border-color:var(--line2); }}
.nichts {{ color:var(--txt2); grid-column:1/-1; padding:40px 0; text-align:center; }}
footer {{ color:var(--txt2); font-size:11px; padding:0 28px 24px; }}
@media (max-width:520px) {{ header, main {{ padding-left:16px; padding-right:16px; }}
  input {{ width:100%; }} }}
</style></head><body>
<header><h1>Meine Videoprojekte</h1><span class="ort" title="{ordner}">{ordner} · {anzahl} Projekte</span>
<input id="suche" type="search" placeholder="Projekt suchen …" aria-label="Projekt suchen">
<a class="knopf" href="{fertig}">Ordner „Fertig" öffnen</a></header>
<main id="liste">{karten}</main>
<footer>Stand {stand} · Diese Seite baut Claude bei jedem Projekt neu. Zuletzt bearbeitete Projekte stehen vorne.</footer>
<script>
document.getElementById('suche').addEventListener('input', e => {{
  const q = e.target.value.trim().toLowerCase();
  document.querySelectorAll('article').forEach(a => {{
    a.style.display = !q || a.dataset.name.toLowerCase().includes(q) ? '' : 'none'; }});
}});
</script></body></html>
"""


# ------------------------------------------------------------------ CLI
def main():
    args = sys.argv[1:]
    if '--vorschlag' in args:
        print(vorschlag())
        return 0
    if '--setzen' in args:
        i = args.index('--setzen')
        if i + 1 >= len(args):
            print('FEHLER: Pfad fehlt:  arbeitsordner.py --setzen <pfad>')
            return 1
        p = setzen(args[i + 1])
        print('OK: Arbeitsordner = ' + p)
        print('    Projekte:   ' + os.path.join(p, 'Projekte'))
        print('    Fertig:     ' + os.path.join(p, 'Fertig'))
        print('    Startseite: ' + os.path.join(p, STARTSEITE))
        return 0
    if '--startseite' in args:
        ziel = startseite_bauen()
        if not ziel:
            print('Kein Arbeitsordner gesetzt.')
            return 2
        print('OK: ' + ziel)
        if '--oeffnen' in args:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import cockpit_oeffnen
            cockpit_oeffnen.oeffnen(ziel)
        return 0
    a = arbeitsordner()
    if not a:
        print('Kein Arbeitsordner gesetzt.')
        print('Vorschlag: ' + vorschlag())
        return 2
    print('Arbeitsordner: ' + a)
    print('Projekte:      {} bekannt'.format(len(alle_projekte())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
