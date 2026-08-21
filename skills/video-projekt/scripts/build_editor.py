#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Baut/aktualisiert das Video-Cockpit fuer ein Projekt (Ein-Tab-Prinzip).

Schreibt zwei Dateien neben die projekt.json:
  - editor.html      (statisch, aus dem Template — laedt die Daten selbst)
  - projekt_data.js  (die Projektdaten; das offene Cockpit laedt diese Datei
                       alle 2,5 s nach -> Aenderungen von Claude erscheinen
                       IM OFFENEN TAB von selbst, kein neues Fenster noetig)

Aufruf:
  Windows:   python  build_editor.py <projekt.json>
  Mac/Linux: python3 build_editor.py <projekt.json>

WICHTIG fuer Claude: editor.html nur beim ERSTEN Mal oeffnen — je nach
System mit Start-Process (Windows), open (macOS) oder xdg-open (Linux).
Danach reicht dieses Script — der offene Tab holt sich die neuen Daten
automatisch.
"""
import array
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
KIT_HOME = os.path.join(os.path.expanduser('~'), '.scb-creator-kit')


# Schriften, die auf dem jeweiligen System wirklich installiert sind.
# WICHTIG: Untertitel werden ins Video GEBRANNT. Steht dort eine Schrift,
# die es auf dem System nicht gibt, ersetzt ffmpeg sie stillschweigend
# durch irgendeine andere — das Ergebnis sieht dann anders aus als die
# Vorschau im Cockpit. Deshalb bekommt jedes System nur seine eigenen.
FONTS_GEMEINSAM = ['Arial', 'Arial Black', 'Impact', 'Georgia', 'Verdana',
                   'Tahoma', 'Trebuchet MS', 'Times New Roman',
                   'Courier New', 'Comic Sans MS']
FONTS_WINDOWS = ['Segoe UI', 'Segoe UI Black', 'Bahnschrift', 'Calibri',
                 'Cambria', 'Candara', 'Consolas', 'Corbel',
                 'Franklin Gothic Demi', 'Gabriola', 'Garamond',
                 'Lucida Sans', 'Palatino Linotype', 'Rockwell',
                 'Sitka Display', 'Arial Rounded MT Bold']
FONTS_MACOS = ['Helvetica Neue', 'Helvetica', 'Avenir Next', 'Avenir',
               'Futura', 'Gill Sans', 'Optima', 'Baskerville', 'Didot',
               'American Typewriter', 'Chalkboard SE', 'Marker Felt',
               'Copperplate', 'Menlo', 'Monaco']
FONTS_LINUX = ['DejaVu Sans', 'DejaVu Serif', 'Liberation Sans',
               'Liberation Serif', 'Ubuntu', 'Noto Sans', 'FreeSans']


def schriften():
    """(Liste, Standardschrift) fuer das laufende System."""
    sys_name = platform.system()
    if sys_name == 'Windows':
        eigen, std = FONTS_WINDOWS, 'Segoe UI'
    elif sys_name == 'Darwin':
        eigen, std = FONTS_MACOS, 'Helvetica Neue'
    else:
        eigen, std = FONTS_LINUX, 'DejaVu Sans'
    liste = []
    for f in [std] + eigen + FONTS_GEMEINSAM:
        if f not in liste:
            liste.append(f)
    return liste, std


def waveform_peaks(path, buckets=600):
    """Lautstaerke-Peaks (0-100) fuer die Tonspur-Anzeige im Cockpit."""
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '8000',
         '-f', 's16le', '-'], capture_output=True, check=True).stdout
    samples = array.array('h')
    samples.frombytes(raw[:len(raw) // 2 * 2])
    n = len(samples)
    if not n:
        return {'d': 0, 'p': []}
    step = max(1, n // buckets)
    peaks = []
    for i in range(0, n, step):
        seg = samples[i:i + step]
        peaks.append(round(max(abs(s) for s in seg) / 32768 * 100))
    return {'d': round(n / 8000.0, 2), 'p': peaks[:buckets]}


def build_waveforms(projekt, projdir, sfx_wellen=None):
    """waveform_data.js schreiben — nur fuer neue/geaenderte Videodateien.

    sfx_wellen: Wellenformen der Soundeffekte (kommen aus build_sfxlib, dort
    faellt beim Vermessen ohnehin schon eine an). Landen in derselben Datei,
    weil das Cockpit sie ueber denselben Weg nachlaedt — und NICHT in
    projekt_data.js, das alle 2,5 s neu geholt wird.
    """
    videos = []
    if projekt.get('video'):
        videos.append(projekt['video'])
    src = (projekt.get('pip') or {}).get('source')
    if src and src not in videos:
        videos.append(src)
    mus = (projekt.get('music') or {}).get('file')
    if mus and mus not in videos:
        videos.append(mus)
    voi = (projekt.get('voiceover') or {}).get('file')
    if voi and voi not in videos:
        videos.append(voi)
    wf_path = os.path.join(projdir, 'waveform_data.js')
    wf = {}
    if os.path.exists(wf_path):
        try:
            txt = open(wf_path, encoding='utf-8').read()
            wf = json.loads(txt[txt.index('=') + 1:].rstrip().rstrip(';'))
        except Exception:
            wf = {}
    changed = False
    for name in videos:
        vpath = os.path.join(projdir, name)
        if not os.path.exists(vpath):
            continue
        if (name in wf and os.path.exists(wf_path)
                and os.path.getmtime(wf_path) >= os.path.getmtime(vpath)):
            continue
        try:
            wf[name] = waveform_peaks(vpath)
            changed = True
        except Exception as e:
            print('WARNUNG: Keine Waveform fuer', name, '-', e)
    for pfad, rec in (sfx_wellen or {}).items():
        if wf.get(pfad) != rec:
            wf[pfad] = rec
            changed = True
    if changed or not os.path.exists(wf_path):
        with open(wf_path, 'w', encoding='utf-8') as f:
            f.write('window.WAVEFORM = ' + json.dumps(wf) + ';\n')
        print('OK: Tonspur-Daten ->', wf_path)


# --------------------------------------------------------------------------
# Soundeffekt-Library: finden, vermessen, ans Cockpit durchreichen
# --------------------------------------------------------------------------
# Die Effekt-Rohdateien sind untereinander sehr unterschiedlich: viele fangen
# mit Stille an, manche laufen 19 Sekunden, und die Spitzenpegel liegen 14 dB
# auseinander. Das Cockpit kann das im Browser nicht messen (eine file://-Seite
# darf fremde Dateien nicht auslesen), deshalb misst es dieses Script einmal
# mit ffmpeg und liefert die Werte fertig mit. Ergebnis wird gecacht — der
# zweite Aufruf kostet nur noch ein os.stat je Datei.
SFX_EXT = ('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.oga', '.opus', '.flac',
           '.mp4', '.m4v', '.webm')     # .mp4 = Essentials (Ton im Container)


SFX_RATE = 48000
SFX_BUCKETS = 140          # Auflösung des Ausschnitt-Streifens im Cockpit
SFX_MAX_DAUER = 30.0       # länger = kein Effekt (Lied/Voiceover aussortieren)


def sound_messen(path):
    """Dauer, Spitzenpegel (dBFS) und Vorlauf (Stille am Anfang) einer Datei.

    'on' ist der erste Sample ueber 2 % der Maximalamplitude — also der
    HOERBARE Einsatz. Das Cockpit zieht ihn spaeter ab, damit ein Effekt
    dort knallt, wo er gesetzt wurde, und nicht eine Sekunde spaeter.

    Gemessen wird in voller Abtastrate: bei 8 kHz rutschen kurze Transienten
    durch und der Spitzenpegel faellt bis zu 4 dB zu niedrig aus — genau die
    Effekte klaengen danach leiser als alle anderen.
    """
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', path, '-vn', '-ac', '1',
         '-ar', str(SFX_RATE), '-f', 's16le', '-'],
        capture_output=True, check=True).stdout
    s = array.array('h')
    s.frombytes(raw[:len(raw) // 2 * 2])
    n = len(s)
    if not n:
        return {'d': 0.0, 'pk': -99.0, 'on': 0.0}
    spitze = max(max(s), -min(s), 1)
    grenze = spitze * 0.02
    # Blockweise suchen (max() laeuft in C), erst im Treffer-Block Sample
    # fuer Sample — sonst laeuft Python ueber ~900.000 Werte je Datei.
    ein = 0
    for start in range(0, n, 4096):
        blk = s[start:start + 4096]
        if max(max(blk), -min(blk)) > grenze:
            for i, w in enumerate(blk):
                if w > grenze or w < -grenze:
                    ein = start + i
                    break
            break
    # Wellenform gleich mitnehmen — die Datei ist ohnehin schon dekodiert.
    # Das Cockpit zeichnet damit den Ausschnitt-Streifen, auf dem der Nutzer
    # Start und Ende in der Datei zieht.
    schritt = max(1, n // SFX_BUCKETS)
    peaks = []
    for i in range(0, n, schritt):
        blk = s[i:i + schritt]
        peaks.append(round(max(max(blk), -min(blk)) / 32768.0 * 100))
    return {'d': round(n / float(SFX_RATE), 3),
            'pk': round(20 * math.log10(spitze / 32768.0), 2),
            'on': round(max(0.0, ein / float(SFX_RATE) - 0.01), 3),
            'p': peaks[:SFX_BUCKETS]}


# Zielpegel, auf den jeder Effekt gebracht wird. Danach bedeutet der Regler
# im Cockpit bei jedem Effekt dasselbe — und, genauso wichtig: der Regler
# bleibt bei oder unter 1,0. Ein Browser kann nicht lauter als 1,0 abspielen;
# muesste der Render einen leisen Effekt erst hochziehen, waere die Vorschau
# leiser als das fertige Video und jede Beurteilung wertlos.
SFX_ZIEL_DB = -1.5
SFX_MAX_BOOST = 18.0        # so viel darf hoechstens angehoben werden


def normalisieren(pfad, pk):
    """Datei auf SFX_ZIEL_DB bringen und in den Kit-Cache legen.

    Rueckgabe: Pfad der normalisierten Datei — oder None, wenn die Datei
    ohnehin schon passt (dann bleibt das Original in Gebrauch).
    FLAC, weil verlustfrei und ohne Encoder-Vorlauf: ein mp3-Encoder wuerde
    vorne ~26 ms Stille anhaengen und damit genau die Falle wieder aufmachen,
    die wir zumachen wollen.
    """
    if pk <= -60 or abs(pk - SFX_ZIEL_DB) <= 0.3:
        return None
    faktor = min(10 ** ((SFX_ZIEL_DB - pk) / 20.0),
                 10 ** (SFX_MAX_BOOST / 20.0))
    ordner = os.path.join(KIT_HOME, 'sound-cache')
    os.makedirs(ordner, exist_ok=True)
    import hashlib
    kurz = hashlib.md5(pfad.replace('\\', '/').encode('utf-8')).hexdigest()[:8]
    stamm = os.path.splitext(os.path.basename(pfad))[0]
    stamm = ''.join(c for c in stamm if c.isalnum() or c in '-_ ').strip()
    out = os.path.join(ordner, '{}__{}.flac'.format(stamm or 'sfx', kurz))
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-v', 'error', '-i', pfad, '-vn',
             '-af', 'volume={:.4f}'.format(faktor),
             '-sample_fmt', 's16', '-c:a', 'flac', out], check=True,
            capture_output=True)
    except Exception:
        return None
    return out.replace('\\', '/')


def sound_ordner(projekt, projdir):
    """Wo liegen die Soundeffekte? Reihenfolge: ausdrueckliche Angabe in der
    projekt.json, Umgebungsvariable, gemerkter Ordner, dann Raten."""
    gefunden = []

    def add(p):
        if not p:
            return
        p = os.path.abspath(os.path.expanduser(str(p).strip()))
        if os.path.isdir(p) and p not in gefunden:
            gefunden.append(p)

    lib = projekt.get('sfx_library') or projekt.get('soundordner')
    for p in ([lib] if isinstance(lib, str) else (lib or [])):
        add(p)
    # Im Cockpit verbundene Library gilt ab jetzt fuer ALLE Projekte —
    # sonst muesste sie in jedem neuen Projekt neu eingetragen werden.
    if gefunden:
        try:
            os.makedirs(KIT_HOME, exist_ok=True)
            merkdatei = os.path.join(KIT_HOME, 'soundlibrary.txt')
            alt = ''
            if os.path.exists(merkdatei):
                with open(merkdatei, encoding='utf-8') as f:
                    alt = f.read()
            if gefunden[0] not in alt:
                with open(merkdatei, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(gefunden) + '\n')
                print('OK: Sound-Library gemerkt ->', gefunden[0])
        except Exception:
            pass
    add(os.environ.get('SCB_SOUNDS'))
    merk = os.path.join(KIT_HOME, 'soundlibrary.txt')
    if os.path.exists(merk):
        try:
            with open(merk, encoding='utf-8') as f:
                for zeile in f:
                    add(zeile)
        except Exception:
            pass
    if gefunden:
        return gefunden
    # Nichts eingestellt: an den ueblichen Stellen nachsehen und den Treffer
    # merken, damit ab dem naechsten Mal nicht mehr geraten werden muss.
    for p in (os.path.join(projdir, '..', 'Soundeffekte'),
              os.path.join(projdir, '..', '..', 'Soundeffekte'),
              os.path.join(projdir, '..', 'Sounds'),
              os.path.join(os.path.expanduser('~'), 'Soundeffekte'),
              os.path.join(HIER, '..', '..', '..', 'sounds')):
        add(p)
    if gefunden:
        try:
            os.makedirs(KIT_HOME, exist_ok=True)
            with open(merk, 'w', encoding='utf-8') as f:
                f.write(gefunden[0] + '\n')
            print('OK: Soundeffekt-Ordner gemerkt ->', merk)
        except Exception:
            pass
    return gefunden


def build_sfxlib(projekt, projdir):
    """Kategorien + vermessene Dateien fuer die Effekt-Auswahl im Cockpit."""
    cache_path = os.path.join(KIT_HOME, 'sound-index.json')
    cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, encoding='utf-8') as f:
                cache = json.load(f)
        except Exception:
            cache = {}
    neu = 0
    wellen = {}          # Pfad -> Wellenform fuer den Ausschnitt-Streifen

    def eintrag(pfad):
        """Messwerte aus dem Cache oder frisch — None, wenn unlesbar.

        Gemessen wird IMMER die Datei, die spaeter auch klingt: gibt es eine
        normalisierte Fassung, gelten deren Werte (Vorlauf, Spitze, Dauer).
        """
        nonlocal neu
        try:
            st = os.stat(pfad)
        except OSError:
            return None
        key = pfad.replace('\\', '/')
        alt = cache.get(key)
        frisch = (alt and alt.get('v') == 4
                  and abs(alt.get('mtime', 0) - st.st_mtime) <= 0.001
                  and alt.get('size') == st.st_size
                  and (not alt.get('norm') or os.path.exists(alt['norm'])))
        if not frisch:
            try:
                mess = sound_messen(pfad)
            except Exception:
                return None
            pk0 = mess['pk']          # Pegel der ORIGINALdatei merken
            # Lieder und Voiceover sind keine Effekte — messen ja (kostet
            # nichts mehr), aber weder normalisieren noch anbieten.
            norm = (normalisieren(pfad, mess['pk'])
                    if mess['d'] <= SFX_MAX_DAUER else None)
            if norm:
                try:
                    mess = sound_messen(norm)
                except Exception:
                    norm = None
            alt = dict(mess, norm=norm, pk0=pk0, mtime=st.st_mtime,
                       size=st.st_size, v=4)
            cache[key] = alt
            neu += 1
        if alt['d'] > SFX_MAX_DAUER or alt['d'] <= 0:
            return None
        # Wellenform unter BEIDEN Pfaden ablegen. Aeltere Projekte zeigen auf
        # die Originaldatei, neue auf die normalisierte — beide muessen ihre
        # Wellenform und ihre Messwerte finden, sonst bleibt die Spur an
        # diesen Stellen leer und der Marker bekommt die falsche Breite.
        ziel = alt.get('norm') or key
        welle = {'d': alt['d'], 'p': alt.get('p') or []}
        wellen[ziel] = welle
        wellen[key] = welle          # Form ist identisch, nur der Pegel nicht
        return {'n': os.path.splitext(os.path.basename(pfad))[0],
                'f': ziel, 'q': key, 'd': alt['d'], 'pk': alt['pk'],
                'pk0': alt.get('pk0', alt['pk']), 'on': alt['on']}

    def sammeln(ordner, titel):
        dateien = []
        try:
            namen = sorted(os.listdir(ordner))
        except OSError:
            return None
        for name in namen:
            p = os.path.join(ordner, name)
            if os.path.isfile(p) and name.lower().endswith(SFX_EXT):
                e = eintrag(p)
                if e:
                    dateien.append(e)
        return {'name': titel, 'dateien': dateien} if dateien else None

    kategorien = []
    # 1. Was im Projekt liegt: der sfx-Unterordner UND kurze Audiodateien im
    #    Projektordner selbst. Letzteres ist der Weg fuer alle ohne Library:
    #    im Cockpit Datei waehlen -> Datei in den Projektordner -> steht hier.
    eigene = []
    for k in (sammeln(os.path.join(projdir, 'sfx'), 'Projekt'),
              sammeln(projdir, 'Projekt')):
        if k:
            for e in k['dateien']:
                if not any(x['f'] == e['f'] for x in eigene):
                    eigene.append(e)
    if eigene:
        kategorien.append({'name': 'Projekt', 'dateien': eigene})
    # 2. Die Library: jeder Unterordner eine Kategorie, lose Dateien darunter
    ordner = sound_ordner(projekt, projdir)
    for basis in ordner:
        k = sammeln(basis, os.path.basename(basis))
        if k:
            kategorien.append(k)
        try:
            unter = sorted(d for d in os.listdir(basis)
                           if os.path.isdir(os.path.join(basis, d)))
        except OSError:
            unter = []
        for d in unter:
            k = sammeln(os.path.join(basis, d), d)
            if k:
                if any(x['name'] == k['name'] for x in kategorien):
                    k['name'] += ' (' + os.path.basename(basis) + ')'
                kategorien.append(k)

    if neu:
        try:
            os.makedirs(KIT_HOME, exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f)
        except Exception:
            pass
    if kategorien:
        anzahl = sum(len(k['dateien']) for k in kategorien)
        print('OK: Soundeffekte: {} Dateien in {} Kategorien{}'.format(
            anzahl, len(kategorien),
            ' ({} neu vermessen)'.format(neu) if neu else ''))
    elif ordner:
        print('Hinweis: In', ordner[0], 'keine Audiodateien gefunden.')
    return ({'ordner': [o.replace('\\', '/') for o in ordner],
             'kategorien': kategorien}, wellen)


def main():
    pj_path = os.path.abspath(sys.argv[1])
    projdir = os.path.dirname(pj_path)
    with open(pj_path, encoding='utf-8-sig') as f:
        projekt = json.load(f)
    projekt['rev'] = int(time.time())
    # Videodateien im Projektordner -> Dropdown "anderes kleines Video"
    # (nur Anzeige-Info; das Cockpit speichert _dateien nicht zurueck)
    projekt['_dateien'] = sorted(
        f for f in os.listdir(projdir)
        if f.lower().endswith(('.mp4', '.mov', '.mkv', '.m4v')))
    projekt['_audiodateien'] = sorted(
        f for f in os.listdir(projdir)
        if f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg',
                               '.webm', '.flac')))
    # Laenge jedes Clips gleich mitliefern — das Cockpit kann sie im Browser
    # nicht zuverlaessig messen (Metadaten laden bei file:// oft nicht) und
    # wuesste sonst nicht, wo Clip 1 endet und Clip 2 beginnt.
    vids = projekt.get('videos') or ([projekt['video']]
                                     if projekt.get('video') else [])
    dauern = []
    for v in vids:
        p = os.path.join(projdir, v)
        try:
            out = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'csv=p=0', p], capture_output=True, text=True,
                check=True).stdout.strip()
            dauern.append(round(float(out), 3))
        except Exception:
            dauern.append(0)
    projekt['_clipdauern'] = dauern
    if dauern and all(d > 0 for d in dauern):
        projekt['duration'] = round(sum(dauern), 2)
    projekt['_schriften'], projekt['_standardschrift'] = schriften()
    # Soundeffekt-Library fuer die 🔊-Spur (Anzeige-Info wie _dateien; das
    # Cockpit speichert sie nicht zurueck)
    projekt['_sfxlib'], sfx_wellen = build_sfxlib(projekt, projdir)

    payload = json.dumps(projekt, ensure_ascii=False)
    payload = payload.replace('</', '<\\/')
    with open(os.path.join(projdir, 'projekt_data.js'), 'w',
              encoding='utf-8') as f:
        f.write('window.PROJEKT = ' + payload + ';\n')

    build_waveforms(projekt, projdir, sfx_wellen)

    tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       '..', 'templates', 'editor.html')
    dest = os.path.join(projdir, 'editor.html')
    existed = os.path.exists(dest)
    shutil.copyfile(tpl, dest)

    # Eigene Erweiterungen des Nutzers: cockpit_custom.js wird NIE
    # ueberschrieben — Kit-Updates ersetzen nur editor.html. Fehlt die Datei,
    # wird die globale Vorlage des Nutzers kopiert (falls vorhanden) oder ein
    # leerer Platzhalter angelegt.
    custom = os.path.join(projdir, 'cockpit_custom.js')
    if not os.path.exists(custom):
        glob_custom = os.path.join(os.path.expanduser('~'),
                                   '.scb-creator-kit', 'cockpit_custom.js')
        if os.path.exists(glob_custom):
            shutil.copyfile(glob_custom, custom)
            print('OK: Eigene Cockpit-Erweiterungen uebernommen ->', custom)
        else:
            with open(custom, 'w', encoding='utf-8') as f:
                f.write(
                    '// Eigene Cockpit-Erweiterungen — diese Datei wird bei\n'
                    '// Kit-Updates NIE ueberschrieben. Alle Funktionen des\n'
                    '// Cockpits sind global und koennen hier ergaenzt oder\n'
                    '// ersetzt werden (danach ggf. renderTL() aufrufen).\n'
                    '// Soll eine Erweiterung in ALLEN Projekten gelten:\n'
                    '// Datei ablegen unter\n'
                    '//   Windows:   %USERPROFILE%\\.scb-creator-kit\\'
                    'cockpit_custom.js\n'
                    '//   Mac/Linux: ~/.scb-creator-kit/cockpit_custom.js\n')

    # Doppelklick-Render: rendert das fertige MP4 ohne Claude (0 Tokens).
    # BEIDE Systeme muessen das koennen — Windows bekommt eine .bat,
    # Mac/Linux eine ausfuehrbare .command. Siehe SKILL.md, Grundregel
    # "Windows UND Mac": nie einen Weg bauen, den nur ein System hat.
    rp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'render_projekt.py')
    if platform.system() == 'Windows':
        starter = os.path.join(projdir, 'video_rendern.bat')
        with open(starter, 'w', encoding='cp1252', errors='replace',
                  newline='') as f:
            f.write('@echo off\r\n'
                    'echo SCB Video-Render laeuft - Fenster offen lassen ...\r\n'
                    'set PY=py\r\n'
                    'where /q py || set PY=python\r\n'
                    '%PY% "{}" "%~dp0projekt.json"\r\n'
                    'echo.\r\n'
                    'echo Fertig! Das Video liegt in diesem Ordner.\r\n'
                    'pause\r\n'.format(rp))
    else:
        starter = os.path.join(projdir, 'video_rendern.command')
        with open(starter, 'w', encoding='utf-8', newline='\n') as f:
            f.write('#!/bin/bash\n'
                    'cd "$(dirname "$0")"\n'
                    'echo "SCB Video-Render laeuft - Fenster offen lassen ..."\n'
                    'python3 "{}" "$(pwd)/projekt.json"\n'
                    'echo ""\n'
                    'echo "Fertig! Das Video liegt in diesem Ordner."\n'
                    'read -n 1 -s -r -p "Zum Schliessen eine Taste druecken"\n'
                    .format(rp))
        os.chmod(starter, 0o755)

    print('OK: Daten aktualisiert ->', os.path.join(projdir, 'projekt_data.js'))
    if existed:
        print('Cockpit-Tab aktualisiert sich innerhalb von ~3 Sekunden von '
              'selbst. (Falls das Editor-Template selbst neuer ist: einmal '
              'F5 im Tab.)')
    else:
        print('NEU: Cockpit erstellt ->', dest,
              '(einmal oeffnen, danach nie wieder — alles Weitere kommt '
              'automatisch in diesen Tab)')


if __name__ == '__main__':
    main()
