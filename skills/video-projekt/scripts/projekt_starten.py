#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legt ein Videoprojekt an und macht ALLES bis zum offenen Cockpit in EINEM
Aufruf: Ordner, Zusammenfuegen, projekt.json, Transkript, Pausensuche,
Cockpit.

    python projekt_starten.py <clip1> [clip2 ...] [--name reel-42]
    python projekt_starten.py roh.mp4 --setzen      # Vorschlaege gleich setzen

Optionen:
    --name    Projektname (Standard: Dateiname des ersten Clips)
    --ziel    Wo der Projektordner entsteht (Standard: neben Clip 1)
    --min     Mindestlaenge einer Pause in Sekunden (Standard 0,45)
    --setzen  Schnittvorschlaege direkt in die projekt.json schreiben.
              NUR wenn der Nutzer "mach fertig" gesagt hat - sonst prueft
              Claude erst den Inhalt (doppelte Aussagen, Versprecher).

WARUM ES DIESES SCRIPT GIBT (gemessen am 23.08.2026): Derselbe Ablauf aus
Einzelschritten brauchte sieben Minuten - davon rund drei Minuten, in denen
der Rechner NICHTS tat, weil zwischen sechs bis acht Script-Aufrufen jeweils
neu nachgedacht wurde. Ein Aufruf statt acht loescht diese Wartezeit. Der
Nutzer sieht das Cockpit nach rund einer Minute (Wartezeit-Regel 1a).

Jeder Abschnitt meldet seine Dauer. Wird es je wieder langsam, steht sofort
da, WO - kein Schaetzen.

Exit 0 = Cockpit steht, Claude kann Schnitte setzen
Exit 1 = etwas fehlt (Datei, ffmpeg, API-Key) - die Meldung sagt was
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PRO = os.path.join(HERE, '..', '..', 'pro-look-editing', 'scripts')
sys.path.insert(0, PRO)

try:
    from prolook import video_encoder          # Hardware-Encoder, 5-10x
except Exception:
    def video_encoder(cfg, zwischenstufe=False):
        return ['-c:v', 'libx264', '-crf', '20', '-preset', 'medium']

# Julians zuletzt gewaehlte Untertitel-Werte - als Startwert, er justiert
# im Cockpit selbst nach.
CAPTIONS = {
    "enabled": True,
    "font": "Arial Rounded MT Bold",
    "size": 83,
    "y": 0.494,
    "primary": "FFFFFF",
    "highlight": "597fd9",
    "highlight_on": True,
    "group": 3,
    "bold": True,
    "box": False,
}


def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def ffdur(pfad):
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'csv=p=0', pfad], capture_output=True, text=True)
    try:
        return round(float(out.stdout.strip()), 2)
    except Exception:
        return 0.0


def spur(pfad):
    """(breite, hoehe, fps) - fuer die Entscheidung Schnellweg oder nicht."""
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
         'stream=width,height,r_frame_rate', '-of', 'csv=p=0', pfad],
        capture_output=True, text=True).stdout.strip()
    return out


def unterschritt(titel, funktion):
    """Fuehrt einen Abschnitt aus und meldet seine Dauer.

    Das flush() ist Pflicht: Pythons eigene Ausgabe ist gepuffert, die der
    Unterscripts nicht. Ohne flush erscheinen die Schnittvorschlaege VOR
    der Ueberschrift, zu der sie gehoeren - die Bilanz liest sich dann
    falsch herum.
    """
    t0 = time.time()
    print("--- " + titel + " ...")
    sys.stdout.flush()
    ergebnis = funktion()
    dauer = time.time() - t0
    print("    fertig in {:.1f}s".format(dauer))
    return ergebnis, dauer


def zusammenfuegen(clips, ziel):
    """Mehrere Clips zu EINER Datei - Schnellweg, sonst normalisieren.

    Eine Datei ist Pflicht: Die Wiedergabe ueber Dateigrenzen hinweg ist im
    Browser unzuverlaessig (Clip-Laengen werden bei lokalen Dateien oft
    nicht gemeldet, die Wiedergabe bleibt beim ersten Clip haengen).
    """
    liste = os.path.join(os.path.dirname(ziel), 's_concat.txt')
    with open(liste, 'w', encoding='utf-8') as f:
        for c in clips:
            f.write("file '{}'\n".format(os.path.abspath(c).replace('\\', '/')))

    schnell = subprocess.run(
        ['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
         '-i', liste, '-c', 'copy', ziel], capture_output=True)
    if schnell.returncode == 0 and os.path.exists(ziel):
        os.remove(liste)
        print("    Schnellweg (ohne Neuberechnung)")
        return True

    # Formate unterschiedlich: jeden Clip auf 1080x1920/30fps bringen.
    print("    Clips haben verschiedene Formate - werden angeglichen")
    teile = []
    for i, c in enumerate(clips):
        p = os.path.join(os.path.dirname(ziel), 's_clip{}.mp4'.format(i))
        r = subprocess.run(
            ['ffmpeg', '-y', '-v', 'error', '-i', c, '-vf',
             'scale=1080:1920:force_original_aspect_ratio=decrease,'
             'pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1', '-r', '30']
            + video_encoder({}, zwischenstufe=True)
            + ['-c:a', 'aac', '-b:a', '192k', '-ar', '48000', p],
            capture_output=True)
        if r.returncode != 0:
            print("FEHLER beim Angleichen von " + c)
            print(r.stderr.decode('utf-8', 'replace')[-500:])
            return False
        teile.append(p)

    with open(liste, 'w', encoding='utf-8') as f:
        for p in teile:
            f.write("file '{}'\n".format(os.path.abspath(p).replace('\\', '/')))
    r = subprocess.run(
        ['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0',
         '-i', liste, '-c', 'copy', ziel], capture_output=True)
    for p in teile:
        try:
            os.remove(p)
        except OSError:
            pass
    try:
        os.remove(liste)
    except OSError:
        pass
    if r.returncode != 0:
        print("FEHLER beim Zusammenfuegen:")
        print(r.stderr.decode('utf-8', 'replace')[-500:])
        return False
    return True


def script(name, *argumente):
    """Ruft ein Nachbarscript mit demselben Python auf. True = Exit 0."""
    sys.stdout.flush()
    r = subprocess.run([sys.executable, os.path.join(HERE, name)]
                       + list(argumente))
    sys.stdout.flush()
    return r.returncode == 0


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith('--'):
        print(__doc__)
        return 1

    clips = []
    for a in sys.argv[1:]:
        if a.startswith('--'):
            break
        clips.append(a)

    fehlend = [c for c in clips if not os.path.exists(c)]
    if fehlend:
        print("FEHLER: nicht gefunden: " + ", ".join(fehlend))
        return 1
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        print("FEHLER: ffmpeg/ffprobe fehlen.")
        print("Nachziehen mit: alles_pruefen.py --update")
        return 1

    name = arg('--name') or os.path.splitext(os.path.basename(clips[0]))[0]
    basis = arg('--ziel') or os.path.dirname(os.path.abspath(clips[0]))
    # ABSOLUT halten: die Unterscripts wechseln selbst ins Projektverzeichnis
    # und wuerden einen relativen Pfad ein zweites Mal aufloesen
    # (".../testlauf-projekt/./testlauf-projekt/original.mp4").
    projdir = os.path.abspath(os.path.join(basis, name + '-projekt'))
    os.makedirs(projdir, exist_ok=True)
    pj_pfad = os.path.join(projdir, 'projekt.json')

    print("Projekt: " + projdir)
    print("Clips:   " + str(len(clips)))
    print("")
    gesamt0 = time.time()
    zeiten = []

    # 1. Material in den Projektordner ------------------------------------
    quelle = os.path.join(projdir, 'original.mp4')

    def schritt_material():
        if len(clips) > 1:
            return zusammenfuegen(clips, quelle)
        shutil.copy2(clips[0], quelle)
        return True

    ok, d = unterschritt("Material vorbereiten", schritt_material)
    zeiten.append(("Material", d))
    if not ok:
        return 1

    dauer = ffdur(quelle)
    if dauer <= 0:
        print("FEHLER: " + quelle + " hat keine lesbare Laenge.")
        return 1

    # 2. projekt.json ------------------------------------------------------
    projekt = {
        "videos": ["original.mp4"],
        "duration": dauer,
        "cuts": [],
        "words": [],
        "captions": dict(CAPTIONS),
        "gains": {"main": 1.0},
        "volumes": [],
        "zooms": [],
        "texts": [],
        "render": {"crf": 20, "output": "final.mp4"},
    }
    with open(pj_pfad, 'w', encoding='utf-8') as f:
        json.dump(projekt, f, ensure_ascii=False, indent=2)
    print("--- projekt.json angelegt ({:.2f}s Material)".format(dauer))

    # 3. Transkript --------------------------------------------------------
    ok, d = unterschritt(
        "Transkript", lambda: script('transkript_untertitel.py', pj_pfad,
                                     quelle))
    zeiten.append(("Transkript", d))
    if not ok:
        print("")
        print("Das Transkript fehlt - ohne Woerter keine Untertitel und")
        print("keine Pausensuche. Der Grund steht in der Meldung DARUEBER.")
        key_da = (os.environ.get('GROQ_API_KEY')
                  or os.environ.get('ELEVENLABS_API_KEY')
                  or os.path.exists(os.path.join(
                      os.path.expanduser('~'), '.scb-creator-kit', 'keys.env')))
        if not key_da:
            print("")
            print("Hier fehlt der API-Key - weder GROQ_API_KEY noch")
            print("ELEVENLABS_API_KEY gesetzt und keine Datei")
            print("  ~/.scb-creator-kit/keys.env")
            print("Groq ist schnell und kostenlos und hat Vorrang.")
        return 1

    # 4. Pausen ------------------------------------------------------------
    pausen_args = [pj_pfad, '--min', arg('--min', '0.45')]
    if '--setzen' in sys.argv:
        pausen_args.append('--setzen')
    print("")
    ok, d = unterschritt("Pausen messen",
                         lambda: script('pausen_finden.py', *pausen_args))
    zeiten.append(("Pausen", d))

    # 5. Cockpit -----------------------------------------------------------
    print("")
    ok, d = unterschritt("Cockpit bauen",
                         lambda: script('build_editor.py', pj_pfad))
    zeiten.append(("Cockpit", d))
    if not ok:
        return 1

    # --- Bilanz -----------------------------------------------------------
    print("")
    print("=" * 58)
    print("FERTIG in {:.1f}s".format(time.time() - gesamt0))
    for titel, d in zeiten:
        print("  {:<12} {:>6.1f}s".format(titel, d))
    print("=" * 58)
    print("")
    print("Cockpit: " + os.path.join(projdir, 'editor.html'))
    print("")
    print("NAECHSTE SCHRITTE FUER CLAUDE:")
    if '--setzen' in sys.argv:
        print("  1. pruef_text.py " + pj_pfad + " - Text lesen: vollstaendig?")
        print("     fluessig? keine zerschnittenen Woerter, keine Dopplungen?")
        print("  2. build_editor.py erneut, dann rendern.")
    else:
        print("  1. Inhalt pruefen: Versprecher, verbale Fehlersignale und")
        print("     vor allem DOPPELTE AUSSAGEN. Sagt der Sprecher denselben")
        print("     Gedanken zweimal, fliegt der schwaechere Anlauf KOMPLETT")
        print("     raus - nicht nur der abgebrochene Zwischenteil.")
        print("  2. Schnitte in die projekt.json setzen (die Vorschlaege oben")
        print("     haben bereits sichere Grenzen - Werte uebernehmen, NICHT")
        print("     selbst nachmessen).")
        print("  3. Video muss mit dem ERSTEN gesprochenen Wort beginnen.")
        print("  4. pruef_text.py " + pj_pfad + " - PFLICHT.")
        print("  5. build_editor.py erneut - der offene Tab holt sich die")
        print("     Daten selbst. NICHT ein zweites Mal oeffnen.")
    print("")
    print("Das Cockpit einmal oeffnen und den Nutzer schauen lassen -")
    print("es braucht KEINEN Render, es spielt das Rohmaterial und")
    print("ueberspringt Schnitte live.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
