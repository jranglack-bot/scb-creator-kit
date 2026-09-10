#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schneidet die markierten Stellen aus einem Video - in EINEM ffmpeg-Lauf.

Claude ruft dieses Script SELBST auf. Es macht alles, was frueher acht
Handgriffe waren: Cuts sortieren und zusammenfassen, die verbleibenden
Segmente berechnen, schneiden, aneinanderhaengen, aufraeumen.

    python schneiden.py <video> --cuts cuts.json -o fertig.mp4
    python schneiden.py <video> --cuts "[[12.4,14.1,\"Fuellwort\"]]" -o fertig.mp4
    python schneiden.py <video> --cuts cuts.json --nur-plan

Format der Cut-Liste (JSON, beide Schreibweisen erlaubt):
    [[start, ende, "Grund"], ...]
    [{"start": 12.4, "end": 14.1, "grund": "Fuellwort"}, ...]
Zeiten in Sekunden. Ein Ende jenseits der Videolaenge (z. B. 9999 fuer
"Endstille") wird auf die Laenge gekuerzt.

Warum ein einziger ffmpeg-Lauf statt Segmentdateien plus concat:
Der Schnitt sitzt bildgenau (Segmentdateien mit -c copy schneiden nur an
Keyframes und laufen aus dem Ton), es wird nur einmal kodiert, und es
bleiben keine Bruchstuecke im Ordner liegen.

Exit 0 = fertig, Exit 1 = fehlgeschlagen (Grund steht dabei).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

# Kuerzere Segmente bringen kein Bild und stoeren nur den Rhythmus.
MIN_SEGMENT = 0.08
# Kurze Blende an jeder Schnittkante gegen Knacksen im Ton.
BLENDE = 0.02


def ffmpeg_pruefen():
    for werkzeug in ("ffmpeg", "ffprobe"):
        if not shutil.which(werkzeug):
            raise RuntimeError(f"{werkzeug} wurde nicht gefunden. Bitte "
                               "ffmpeg installieren und erneut versuchen.")


def videoinfos(pfad):
    """Liefert (dauer, hat_ton)."""
    lauf = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", str(pfad)],
        capture_output=True, text=True)
    if lauf.returncode != 0:
        raise RuntimeError(f"ffprobe konnte {pfad} nicht lesen.")
    daten = json.loads(lauf.stdout)
    dauer = float(daten.get("format", {}).get("duration") or 0)
    spuren = daten.get("streams", []) or []
    hat_ton = any(s.get("codec_type") == "audio" for s in spuren)
    hat_bild = any(s.get("codec_type") == "video" for s in spuren)
    if not hat_bild:
        raise RuntimeError(f"{pfad} enthaelt keine Bildspur.")
    if dauer <= 0:
        raise RuntimeError(f"Konnte die Laenge von {pfad} nicht bestimmen.")
    return dauer, hat_ton


def text_lesen(pfad):
    """Liest eine Textdatei, ohne an der Zeichenkodierung zu scheitern.

    Unter Windows schreibt Python bei einer Umleitung (> cuts.json) in
    cp1252 statt UTF-8. Die Umlaute stehen nur in den Begruendungen, also
    im rein kosmetischen Teil - daran darf der Schnitt nicht scheitern.
    """
    roh = open(pfad, "rb").read()
    for kodierung in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return roh.decode(kodierung)
        except UnicodeDecodeError:
            continue
    return roh.decode("utf-8", errors="replace")


def cuts_lesen(angabe):
    """Nimmt einen Dateipfad ODER direkt einen JSON-Text entgegen."""
    text = angabe
    if os.path.exists(angabe):
        text = text_lesen(angabe)
    try:
        roh = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Cut-Liste ist kein gueltiges JSON: {e}")
    if isinstance(roh, dict):
        roh = roh.get("cuts", [])
    if not isinstance(roh, list):
        raise RuntimeError("Cut-Liste muss eine Liste sein.")

    cuts = []
    for i, eintrag in enumerate(roh):
        if isinstance(eintrag, dict):
            start = eintrag.get("start")
            ende = eintrag.get("end", eintrag.get("ende"))
            grund = eintrag.get("grund", eintrag.get("reason", ""))
        elif isinstance(eintrag, (list, tuple)) and len(eintrag) >= 2:
            start, ende = eintrag[0], eintrag[1]
            grund = eintrag[2] if len(eintrag) > 2 else ""
        else:
            raise RuntimeError(f"Cut {i + 1} hat ein unbekanntes Format.")
        try:
            start, ende = float(start), float(ende)
        except (TypeError, ValueError):
            raise RuntimeError(f"Cut {i + 1} hat keine gueltigen Zeiten.")
        cuts.append((start, ende, str(grund)))
    return cuts


def cuts_aufraeumen(cuts, dauer):
    """Auf das Video begrenzen, sortieren und Ueberlappungen verschmelzen."""
    sauber = []
    for start, ende, grund in cuts:
        start = max(0.0, min(start, dauer))
        ende = max(0.0, min(ende, dauer))
        if ende - start > 0.001:
            sauber.append((start, ende, grund))
    sauber.sort(key=lambda c: c[0])

    verschmolzen = []
    for start, ende, grund in sauber:
        if verschmolzen and start <= verschmolzen[-1][1] + 0.001:
            vorher_start, vorher_ende, vorher_grund = verschmolzen[-1]
            gruende = [g for g in (vorher_grund, grund) if g]
            verschmolzen[-1] = (vorher_start, max(vorher_ende, ende),
                                " + ".join(dict.fromkeys(gruende)))
        else:
            verschmolzen.append((start, ende, grund))
    return verschmolzen


def segmente_berechnen(cuts, dauer):
    """Kehrt die Cut-Liste um: was bleibt stehen."""
    segmente = []
    zeiger = 0.0
    for start, ende, _ in cuts:
        if start - zeiger >= MIN_SEGMENT:
            segmente.append((zeiger, start))
        zeiger = max(zeiger, ende)
    if dauer - zeiger >= MIN_SEGMENT:
        segmente.append((zeiger, dauer))
    return segmente


def filter_bauen(segmente, hat_ton):
    """Baut das filter_complex-Script fuer einen einzigen ffmpeg-Lauf."""
    zeilen = []
    marken = []
    for i, (start, ende) in enumerate(segmente):
        zeilen.append(
            f"[0:v]trim=start={start:.3f}:end={ende:.3f},"
            f"setpts=PTS-STARTPTS[v{i}]")
        marken.append(f"[v{i}]")
        if hat_ton:
            laenge = ende - start
            ton = (f"[0:a]atrim=start={start:.3f}:end={ende:.3f},"
                   f"asetpts=PTS-STARTPTS")
            if laenge > 3 * BLENDE:
                ton += (f",afade=t=in:st=0:d={BLENDE}"
                        f",afade=t=out:st={laenge - BLENDE:.3f}:d={BLENDE}")
            zeilen.append(f"{ton}[a{i}]")
            marken.append(f"[a{i}]")

    n = len(segmente)
    if hat_ton:
        # Bild- und Tonmarken muessen paarweise abwechselnd stehen.
        paare = "".join(f"[v{i}][a{i}]" for i in range(n))
        zeilen.append(f"{paare}concat=n={n}:v=1:a=1[vout][aout]")
    else:
        nur_bild = "".join(f"[v{i}]" for i in range(n))
        zeilen.append(f"{nur_bild}concat=n={n}:v=1:a=0[vout]")
    # Ohne Zeilenumbrueche: die vertragen aeltere ffmpeg-Versionen nicht.
    return ";".join(zeilen)


# Ab hier passt der Graph nicht mehr sicher auf die Kommandozeile
# (Windows nimmt maximal 32767 Zeichen an) - dann geht er als Datei rein.
INLINE_GRENZE = 20000


def filter_varianten(graph, tempordner):
    """Moegliche Schreibweisen, den Filtergraph an ffmpeg zu uebergeben.

    Kurze Graphen gehen direkt auf die Kommandozeile - das kann jede
    ffmpeg-Version. Lange gehen als Datei, und dafuer gibt es zwei
    Schreibweisen: das alte -filter_complex_script (bis ffmpeg 8) und das
    neue -/filter_complex (ab ffmpeg 7.1). Welche die vorhandene Version
    kennt, probieren wir der Reihe nach aus.
    """
    if len(graph) <= INLINE_GRENZE:
        return [["-filter_complex", graph]]
    pfad = os.path.join(tempordner, "filter.txt")
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(graph)
    return [["-/filter_complex", pfad], ["-filter_complex_script", pfad]]


def option_unbekannt(meldung):
    text = (meldung or "").lower()
    return "option not found" in text or "unrecognized option" in text


def zeit(sekunden):
    m, s = divmod(max(0.0, sekunden), 60)
    return f"{int(m)}:{s:05.2f}"


def main():
    p = argparse.ArgumentParser(
        description="Markierte Stellen aus einem Video schneiden")
    p.add_argument("video", help="Eingangsvideo")
    p.add_argument("--cuts", required=True,
                   help="Pfad zur Cut-Liste (JSON) oder JSON direkt")
    p.add_argument("-o", "--ausgabe", default=None,
                   help="Zielvideo (Standard: <name>_geschnitten.mp4)")
    p.add_argument("--nur-plan", action="store_true",
                   help="nur rechnen und anzeigen, nicht rendern")
    p.add_argument("--crf", default="18",
                   help="Bildqualitaet, kleiner = besser (Standard 18)")
    p.add_argument("--preset", default="medium")
    a = p.parse_args()

    try:
        ffmpeg_pruefen()
        if not os.path.exists(a.video):
            raise RuntimeError(f"Video nicht gefunden: {a.video}")
        dauer, hat_ton = videoinfos(a.video)
        cuts = cuts_aufraeumen(cuts_lesen(a.cuts), dauer)
        segmente = segmente_berechnen(cuts, dauer)
    except RuntimeError as e:
        print(f"FEHLER: {e}")
        return 1

    if not segmente:
        print("FEHLER: Nach den Cuts bliebe nichts uebrig. Cut-Liste pruefen.")
        return 1
    if not cuts:
        print("Keine Cuts uebergeben - es gibt nichts zu schneiden.")
        return 1

    entfernt = sum(e - s for s, e, _ in cuts)
    neue_dauer = sum(e - s for s, e in segmente)

    print(f"Video:      {os.path.basename(a.video)}")
    print(f"Laenge:     {zeit(dauer)}"
          + ("" if hat_ton else "   (ohne Tonspur)"))
    print(f"Cuts:       {len(cuts)}  ->  {zeit(entfernt)} raus "
          f"({entfernt / dauer * 100:.0f} %)")
    print(f"Bleibt:     {zeit(neue_dauer)} in {len(segmente)} Segmenten")
    print()
    for i, (start, ende, grund) in enumerate(cuts, 1):
        print(f"  {i:>3}. {zeit(start)} - {zeit(ende)}  "
              f"({ende - start:.2f}s)  {grund}")

    if a.nur_plan:
        print("\n--nur-plan: nichts gerendert.")
        return 0

    ziel = a.ausgabe
    if not ziel:
        wurzel, _ = os.path.splitext(a.video)
        ziel = wurzel + "_geschnitten.mp4"
    ziel = os.path.abspath(ziel)
    if os.path.abspath(a.video) == ziel:
        print("FEHLER: Ziel darf nicht die Eingangsdatei sein.")
        return 1
    os.makedirs(os.path.dirname(ziel) or ".", exist_ok=True)

    tempordner = tempfile.mkdtemp(prefix="scb_")
    neben = ziel + ".teil.mp4"
    try:
        graph = filter_bauen(segmente, hat_ton)
        print(f"\nRendere nach {ziel} ...")

        meldung = ""
        fertig = False
        for filterteil in filter_varianten(graph, tempordner):
            befehl = ["ffmpeg", "-i", str(a.video)] + filterteil + \
                     ["-map", "[vout]"]
            if hat_ton:
                befehl += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
            befehl += ["-c:v", "libx264", "-preset", a.preset,
                       "-crf", str(a.crf), "-pix_fmt", "yuv420p",
                       "-movflags", "+faststart",
                       "-y", "-loglevel", "error", neben]

            lauf = subprocess.run(befehl, capture_output=True, text=True)
            meldung = (lauf.stderr or "").strip()
            if lauf.returncode == 0 and os.path.exists(neben):
                fertig = True
                break
            if not option_unbekannt(meldung):
                break  # echter Fehler, eine andere Schreibweise hilft nicht

        if not fertig:
            print("FEHLER: ffmpeg ist fehlgeschlagen.")
            for zeile in meldung.splitlines()[-8:]:
                print("  ", zeile)
            return 1
        os.replace(neben, ziel)
    finally:
        shutil.rmtree(tempordner, ignore_errors=True)
        if os.path.exists(neben):
            os.remove(neben)

    try:
        ist_dauer, _ = videoinfos(ziel)
    except RuntimeError:
        ist_dauer = neue_dauer
    groesse_mb = os.path.getsize(ziel) / (1024 * 1024)
    print(f"FERTIG: {ziel}")
    print(f"  {zeit(dauer)} -> {zeit(ist_dauer)}, {groesse_mb:.1f} MB")
    if abs(ist_dauer - neue_dauer) > 1.0:
        print(f"  Hinweis: erwartet waren {zeit(neue_dauer)}. Bitte das "
              "Ergebnis anschauen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
