#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Animierte Wort-fuer-Wort-Untertitel (Pop + Highlight) als .ass-Datei.

Liest ein Transkript-JSON (ElevenLabs/Whisper-Format: words[] mit
start/end/text) und erzeugt deterministisch eine ASS-Datei im
CapCut-Stil: 2-3-Wort-Gruppen, Pop-Animation beim Erscheinen,
farbiges Highlight auf dem gerade gesprochenen Wort, nur waehrend
Sprache sichtbar. Safe-Zone-Werte fuer Reel und Story eingebaut.

Aufruf:
  python animated_captions.py transkript.json out.ass --mode reel
    [--font "..."] (Standard: Systemschrift) [--size 0] [--highlight FFD400] [--group 3]
[--box] [--box-color 000000] [--box-alpha 0.59] [--no-bold]
    [--playresx 1080] [--playresy 1920]

--size 0 = Standardgroesse des Modus (Reel 64 / Story 92).
"""
import argparse
import json
import os
import platform
import re


def standard_schrift():
    """Schrift, die es auf dem laufenden System wirklich gibt — 'Segoe UI'
    existiert auf einem Mac nicht; ffmpeg wuerde beim Einbrennen still
    irgendeine Ersatzschrift nehmen."""
    s = platform.system()
    if s == 'Windows':
        return 'Segoe UI'
    if s == 'Darwin':
        return 'Helvetica Neue'
    return 'DejaVu Sans'



def ass_color(rgbhex):
    """'FFD400' (RGB) -> ASS-Farbcode &H00BGR& (BGR gedreht)."""
    rgbhex = rgbhex.lstrip('#')
    r, g, b = rgbhex[0:2], rgbhex[2:4], rgbhex[4:6]
    return '&H00{}{}{}&'.format(b, g, r).upper()


def _boxcol(args):
    """Boxfarbe + Deckkraft als ASS-Farbwert (&HAABBGGRR)."""
    h = args.box_color.lstrip('#')
    return '&H{:02X}{}{}{}'.format(
        max(0, min(255, int(round((1 - args.box_alpha) * 255)))),
        h[4:6], h[2:4], h[0:2]).upper()


def fmt_time(sec):
    if sec < 0:
        sec = 0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec - h * 3600 - m * 60
    return '{}:{:02d}:{:05.2f}'.format(h, m, s)


MODES = {
    # Safe-Zone-geprueft: Reel = unteres Drittel, rechte Buttons frei;
    # Story = gross, unter dem Kinn (Brusthoehe).
    'reel':  dict(size=64, marginv=460, marginl=55, marginr=165),
    'story': dict(size=92, marginv=730, marginl=55, marginr=55),
}

MAX_GAP = 0.6      # Sekunden: groessere Luecke beendet die Wortgruppe
POP_MS = 90        # Dauer der Pop-Animation in Millisekunden

# --- Gleicher Look wie im Cockpit (06.10.2026) -------------------------------
# Das Cockpit zeigt den Untertitel als CSS. Damit das fertige Video genauso
# aussieht, gelten hier dieselben Werte wie in templates/editor.html
# (CAP_SCHEIN, CAP_ZEILENHOEHE). Werte im Pixelraum des fertigen Videos.
#   Schein: CSS text-shadow "x y r #000"; CSS-Unschaerfe r = Sigma r/2,
#   libass-\blur n = Sigma 0,86 n (gemessen am 06.10.2026 an einer Kante).
SCHEIN = [(0, 0, 30), (0, 0, 15), (5, 5, 5)]
CSS_ZEILENHOEHE = 1.25
LIBASS_BLUR_SIGMA = 0.86
# Groesse: CSS meint mit "83 px" das Geviert der Schrift, libass (wie
# VSFilter) die Hoehe usWinAscent + usWinDescent. Ohne Umrechnung kommt
# Arial im Video 11,7 % kleiner raus als im Cockpit, Arial Rounded 15,7 %.
SCHRIFT_FAKTOR_STANDARD = 1.12


def _schrift_ordner():
    s = platform.system()
    heim = os.path.expanduser('~')
    if s == 'Windows':
        win = os.environ.get('WINDIR', r'C:\Windows')
        return [os.path.join(win, 'Fonts'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft',
                             'Windows', 'Fonts')]
    if s == 'Darwin':
        return ['/System/Library/Fonts', '/System/Library/Fonts/Supplemental',
                '/Library/Fonts', os.path.join(heim, 'Library', 'Fonts')]
    return ['/usr/share/fonts', '/usr/local/share/fonts',
            os.path.join(heim, '.fonts'),
            os.path.join(heim, '.local', 'share', 'fonts')]


def schrift_faktor(name, fett=True):
    """(usWinAscent + usWinDescent) / unitsPerEm der Schrift, die libass
    fuer `name` nimmt. Damit wird die Cockpit-Groesse (CSS) in die
    ASS-Groesse umgerechnet. Ergebnis gemerkt in
    ~/.scb-creator-kit/schrift_masse.json, der erste Suchlauf dauert einige
    Sekunden. Ohne fontTools oder ohne Treffer: SCHRIFT_FAKTOR_STANDARD."""
    cache_pfad = os.path.join(os.path.expanduser('~'), '.scb-creator-kit',
                              'schrift_masse.json')
    schluessel = '{}|{}'.format(name.lower(), 'fett' if fett else 'normal')
    try:
        with open(cache_pfad, encoding='utf-8') as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    if schluessel in cache:
        return cache[schluessel]
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return SCHRIFT_FAKTOR_STANDARD
    treffer = []
    for ordner in _schrift_ordner():
        for wurzel, _, dateien in os.walk(ordner):
            for d in dateien:
                if not d.lower().endswith(('.ttf', '.otf')):
                    continue
                try:
                    f = TTFont(os.path.join(wurzel, d), lazy=True)
                    fam = (f['name'].getDebugName(16)
                           or f['name'].getDebugName(1) or '')
                    if fam.lower() != name.lower() and \
                            (f['name'].getDebugName(1) or '').lower() != name.lower():
                        continue
                    os2, upem = f['OS/2'], f['head'].unitsPerEm
                    ist_fett = bool(os2.fsSelection & 0x20) or os2.usWeightClass >= 600
                    treffer.append(((os2.usWinAscent + os2.usWinDescent) / upem,
                                    ist_fett))
                except Exception:
                    continue
    if not treffer:
        return SCHRIFT_FAKTOR_STANDARD
    passend = [k for k, b in treffer if b == fett] or [k for k, _ in treffer]
    faktor = round(passend[0], 4)
    cache[schluessel] = faktor
    try:
        os.makedirs(os.path.dirname(cache_pfad), exist_ok=True)
        with open(cache_pfad, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
    except OSError:
        pass
    return faktor


def build_cues(words, group_size):
    """Gruppiert Woerter zu Cues (max. group_size, Bruch bei Sprechpausen)."""
    cues, current = [], []
    for w in words:
        if current and (len(current) >= group_size
                        or w['start'] - current[-1]['end'] > MAX_GAP):
            cues.append(current)
            current = []
        current.append(w)
    if current:
        cues.append(current)
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('transcript')
    ap.add_argument('output')
    ap.add_argument('--mode', choices=('reel', 'story'), default='reel')
    ap.add_argument('--font', default=standard_schrift())
    ap.add_argument('--size', type=int, default=0)
    ap.add_argument('--primary', default='FFFFFF',
                    help='Textfarbe als RGB-Hex')
    ap.add_argument('--highlight', default='FFD400')
    ap.add_argument('--outline', type=int, default=0,
                    help='harter Rand in px statt des weichen Scheins wie im '
                         'Cockpit (0 = weicher Schein, Standard seit 06.10.2026)')
    ap.add_argument('--box', action='store_true',
                    help='halbtransparente Box hinter dem Text')
    ap.add_argument('--box-color', default='000000',
                    help='Boxfarbe als RRGGBB (mit --box)')
    ap.add_argument('--box-alpha', type=float, default=0.59,
                    help='Deckkraft der Box 0-1 (mit --box)')
    ap.add_argument('--box-style', choices=('line', 'block'), default='line',
                    help='line = Box schmiegt sich pro Zeile um die Woerter, '
                         'block = EIN symmetrisches Viereck um den ganzen Text')
    ap.add_argument('--no-bold', action='store_true',
                    help='Text nicht fett setzen')
    ap.add_argument('--group', type=int, default=3)
    ap.add_argument('--y', type=float, default=-1,
                    help='Vertikale Position aus dem Cockpit: Oberkante des '
                         'Untertitel-Blocks als Anteil der Bildhoehe (0-1). '
                         'Ohne Angabe gilt die feste Safe-Zone des Modus.')
    ap.add_argument('--playresx', type=int, default=1080)
    ap.add_argument('--playresy', type=int, default=1920)
    ap.add_argument('--transition-cuts', default='',
                    help='Kommagetrennte Schnittzeiten, wenn das Video mit '
                         'xfade-Uebergaengen gerendert wird (prolook '
                         'transition) — Untertitelzeiten werden angepasst')
    ap.add_argument('--transition-duration', type=float, default=0.3)
    ap.add_argument('--emit-times', default='',
                    help='Pfad: schreibt die Cue-Startzeiten als JSON '
                         '(fuer Typewriter-Sound via build_sfx_track.py)')
    args = ap.parse_args()

    mode = MODES[args.mode]
    size = args.size or mode['size']
    hi = ass_color(args.highlight)
    white = ass_color(args.primary)
    # Cockpit-Groesse (CSS-Geviert) in ASS-Groesse umrechnen, siehe
    # schrift_faktor(). Ohne das ist der Untertitel im Video sichtbar kleiner.
    faktor = schrift_faktor(args.font, not args.no_bold)
    ass_size = int(round(size * faktor))
    # Weicher Schein wie im Cockpit, solange keine Box und kein harter Rand
    # (--outline > 0, alter Look) gewuenscht ist.
    schein = not args.box and not args.outline

    # Position: Das Cockpit speichert die OBERKANTE des Untertitel-Blocks
    # als Anteil der Bildhoehe (captions.y). Damit der Render exakt dort
    # brennt, wo die Vorschau den Text zeigt, ankern wir bei --y OBEN
    # (Alignment 8, MarginV = Abstand von oben) statt unten — sonst
    # wuerde die Blockhoehe (1 vs. 2 Zeilen) die Lage verschieben.
    # CSS setzt die Schrift mittig in eine Zeile von 1,25 Geviert, libass
    # direkt an die Oberkante: der halbe Unterschied kommt dazu.
    if args.y >= 0:
        alignment = 8
        marginv = int(round(min(0.95, max(0.0, args.y)) * args.playresy
                            + (CSS_ZEILENHOEHE - faktor) * size / 2))
    else:
        alignment = 2
        marginv = mode['marginv']

    with open(args.transcript, encoding='utf-8') as f:
        data = json.load(f)
    words = [w for w in data.get('words', []) if w.get('type', 'word') == 'word'
             and str(w.get('text', '')).strip()]
    if not words:
        raise SystemExit('Keine Woerter im Transkript gefunden.')

    # Timeline-Korrektur bei xfade-Uebergaengen: jeder Uebergang verkuerzt
    # das Video um seine Dauer — sonst laufen die Untertitel asynchron.
    if args.transition_cuts:
        cuts = sorted(float(c) for c in args.transition_cuts.split(',') if c)
        td = args.transition_duration
        adj = []
        for w in words:
            shift = td * sum(1 for c in cuts if c <= w['start'])
            adj.append(dict(w, start=max(0.0, w['start'] - shift),
                            end=max(0.0, w['end'] - shift)))
        words = adj

    # Wortzeiten monoton machen. Transkriptionen setzen Wortanfaenge
    # regelmaessig schon in die Stille davor (gemessen: bis 0,83 s zu
    # frueh); stammen die Zeiten aus zwei Aufnahmen, ueberlappen sie sich
    # sogar. Beides laesst ZWEI Wortgruppen gleichzeitig im Bild stehen —
    # der Untertitel sieht doppelt aus. Das Wort-ENDE ist der zuverlaessige
    # Wert, also wird der START nachgezogen. Dieselbe Regel benutzt
    # render_projekt.py an Schnittkanten.
    for i in range(1, len(words)):
        if words[i]['start'] < words[i - 1]['end']:
            words[i] = dict(words[i], start=words[i - 1]['end'])

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: {px}
PlayResY: {py}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},{primary},{primary},{outcol},{back},{bold},0,0,0,100,100,0,0,{borderstyle},{outline},{shadow},{align},{ml},{mr},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(px=args.playresx, py=args.playresy, font=args.font, size=ass_size,
           primary=white,
           # libass zeichnet die Box je nach BorderStyle aus verschiedenen
           # Farbfeldern (empirisch verifiziert):
           #   BorderStyle 3 (pro Zeile)      -> Box = OutlineColour
           #   BorderStyle 4 (ganzer Block)   -> Box = BackColour,
           #                                     Textkontur = OutlineColour
           outcol=('&H00000000' if not args.box or args.box_style == 'block'
                   else _boxcol(args)),
           back=_boxcol(args) if args.box and args.box_style == 'block'
                else '&H96000000',
           bold=0 if args.no_bold else -1,
           borderstyle=(4 if args.box_style == 'block' else 3) if args.box
                       else 1,
           shadow=0 if (args.box or schein) else 2,
           outline=0 if schein else (args.outline or max(4, size // 10)),
           align=alignment,
           ml=mode['marginl'], mr=mode['marginr'], mv=marginv)

    def schein_zeilen(start, end, text):
        """Schwarzer, weichgezeichneter Text unter dem eigentlichen Text,
        je CSS-Schatten eine Ebene (gleiche Pop-Animation, ohne Farben)."""
        ohne_farbe = re.sub(r'\{\\1c&H[0-9A-Fa-f]+&\}', '', text)
        raus = []
        for ebene, (x, y, r) in enumerate(SCHEIN):
            blur = round(r / 2 / LIBASS_BLUR_SIGMA, 2)
            if x or y:
                # versetzter Schatten: nur der Schatten, Fuellung unsichtbar
                tags = ('{{\\1a&HFF&\\bord0\\4c&H000000&\\4a&H00&'
                        '\\xshad{}\\yshad{}\\blur{}}}'.format(x, y, blur))
            else:
                tags = '{{\\1c&H000000&\\bord0\\shad0\\blur{}}}'.format(blur)
            raus.append('Dialogue: {},{},{},Cap,,0,0,0,,{}{}'.format(
                ebene, fmt_time(start), fmt_time(end), tags, ohne_farbe))
        return raus

    lines = [header]
    cues = build_cues(words, args.group)
    for ci, cue in enumerate(cues):
        # Die letzte Zeile einer Gruppe steht bis zum Ende ihres letzten
        # Wortes. Reichen die Wortzeiten ueber den Beginn der naechsten
        # Gruppe hinaus — etwa weil Wortzeiten aus zwei Aufnahmen stammen
        # oder von Hand gesetzt wurden — stuenden BEIDE Gruppen gleich-
        # zeitig im Bild und der Untertitel sieht doppelt aus. Deckel:
        cue_end = cue[-1]['end']
        if ci + 1 < len(cues):
            cue_end = min(cue_end, cues[ci + 1][0]['start'])
        for k, w in enumerate(cue):
            start = w['start']
            end = cue[k + 1]['start'] if k + 1 < len(cue) else cue_end
            if end - start < 0.02:
                end = start + 0.02
            parts = []
            for j, cw in enumerate(cue):
                txt = str(cw['text']).strip()
                if j == k:
                    parts.append('{{\\1c{}}}{}{{\\1c{}}}'.format(hi, txt, white))
                else:
                    parts.append(txt)
            text = ' '.join(parts)
            # Pop-Animation nur beim ersten Einblenden der Gruppe
            if k == 0:
                text = ('{{\\fscx118\\fscy118\\t(0,{},\\fscx100\\fscy100)}}'
                        .format(POP_MS)) + text
            if schein:
                lines.extend(schein_zeilen(start, end, text))
            lines.append('Dialogue: {},{},{},Cap,,0,0,0,,{}'.format(
                len(SCHEIN) if schein else 0, fmt_time(start), fmt_time(end),
                text))

    with open(args.output, 'w', encoding='utf-8-sig') as f:
        f.write('\n'.join(lines) + '\n')

    if args.emit_times:
        times = [round(c[0]['start'], 3)
                 for c in build_cues(words, args.group)]
        with open(args.emit_times, 'w', encoding='utf-8') as f:
            json.dump(times, f)

    print('OK: {} Woerter, ASS geschrieben: {}'.format(len(words), args.output))


if __name__ == '__main__':
    main()
