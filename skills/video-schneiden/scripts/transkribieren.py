#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transkribiert eine Audiodatei ueber ElevenLabs - Windows, macOS, Linux.

Ersetzt die frueher genutzte .bat-Datei, die nur unter Windows lief.

    python transkribieren.py <audio.mp3> <api-key> [-o transkript.json]
                             [--sprache de] [--modell scribe_v1]

Exit 0 = fertig, Exit 1 = fehlgeschlagen (Grund steht dabei).
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid

URL = "https://api.elevenlabs.io/v1/speech-to-text"


def multipart(felder, dateipfad, feldname="file"):
    """Baut einen multipart/form-data-Body ohne Fremdbibliotheken."""
    grenze = "----SCBKit" + uuid.uuid4().hex
    zeilen = []
    for name, wert in felder.items():
        zeilen.append(f"--{grenze}\r\n".encode())
        zeilen.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        zeilen.append(f"{wert}\r\n".encode())

    dateiname = os.path.basename(dateipfad)
    typ = mimetypes.guess_type(dateiname)[0] or "application/octet-stream"
    with open(dateipfad, "rb") as f:
        inhalt = f.read()
    zeilen.append(f"--{grenze}\r\n".encode())
    zeilen.append((f'Content-Disposition: form-data; name="{feldname}"; '
                   f'filename="{dateiname}"\r\n').encode())
    zeilen.append(f"Content-Type: {typ}\r\n\r\n".encode())
    zeilen.append(inhalt)
    zeilen.append(b"\r\n")
    zeilen.append(f"--{grenze}--\r\n".encode())

    return b"".join(zeilen), f"multipart/form-data; boundary={grenze}"


def main():
    p = argparse.ArgumentParser(description="Audio ueber ElevenLabs transkribieren")
    p.add_argument("audio", help="Pfad zur Audiodatei (z. B. audio_temp.mp3)")
    p.add_argument("api_key", nargs="?", default=os.environ.get("ELEVENLABS_API_KEY"),
                   help="ElevenLabs API-Key (oder Umgebungsvariable ELEVENLABS_API_KEY)")
    p.add_argument("-o", "--ausgabe", default="transkript.json")
    p.add_argument("--sprache", default="de")
    p.add_argument("--modell", default="scribe_v1")
    a = p.parse_args()

    if not a.api_key:
        print("FEHLER: Kein API-Key uebergeben.")
        return 1
    if not os.path.exists(a.audio):
        print(f"FEHLER: Audiodatei nicht gefunden: {a.audio}")
        return 1

    groesse_mb = os.path.getsize(a.audio) / (1024 * 1024)
    print(f"Transkribiere {os.path.basename(a.audio)} ({groesse_mb:.1f} MB) ...")
    print("Das dauert je nach Laenge etwas. Bitte warten.")

    body, content_type = multipart(
        {"model_id": a.modell,
         "language_code": a.sprache,
         "timestamps_granularity": "word"},
        a.audio)

    anfrage = urllib.request.Request(
        URL, data=body,
        headers={"xi-api-key": a.api_key, "Content-Type": content_type})

    try:
        with urllib.request.urlopen(anfrage, timeout=900) as antwort:
            daten = json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        rohtext = e.read().decode("utf-8", errors="replace")[:500]
        if e.code == 401:
            print("FEHLER: API-Key wurde abgelehnt (401). Key pruefen.")
        elif e.code == 429:
            print("FEHLER: Zu viele Anfragen oder Guthaben aufgebraucht (429).")
        else:
            print(f"FEHLER von ElevenLabs (HTTP {e.code}): {rohtext}")
        return 1
    except urllib.error.URLError as e:
        print(f"FEHLER: Keine Verbindung zu ElevenLabs ({e.reason}).")
        return 1

    # Direkt neben das Ziel schreiben - kein Umweg ueber temporaere Ordner
    ziel = os.path.abspath(a.ausgabe)
    os.makedirs(os.path.dirname(ziel) or ".", exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

    woerter = len(daten.get("words", []) or [])
    zeichen = len((daten.get("text") or ""))
    print(f"FERTIG: {ziel}")
    print(f"  {woerter} Wortmarken, {zeichen} Zeichen Text")
    if woerter == 0:
        print("  Hinweis: Keine Wortmarken erhalten - fuer den Schnitt noetig. "
              "Pruefen, ob die Tonspur wirklich Sprache enthaelt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
