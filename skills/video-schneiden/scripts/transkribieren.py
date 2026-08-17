#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transkribiert eine Audiodatei - Windows, macOS, Linux.

Bevorzugt laeuft die Transkription ueber Groq (Whisper, schnell und
kostenlos). ElevenLabs ist die Rueckfallebene - der Key bleibt trotzdem
wertvoll, weil ElevenLabs auch Musik und Soundeffekte erzeugen kann.

    python transkribieren.py <audio.mp3> [elevenlabs-key]
                             [--groq-key <key>] [-o transkript.json]
                             [--sprache de] [--modell scribe_v1]

Keys (Reihenfolge = Vorrang):
  --groq-key oder Umgebungsvariable GROQ_API_KEY        -> Groq Whisper
  Positionsargument oder ELEVENLABS_API_KEY             -> ElevenLabs Scribe
Werte, die mit "~~" beginnen, sind unersetzte Platzhalter und gelten
als nicht gesetzt.

Ausgabeformat ist bei BEIDEN Diensten identisch (ElevenLabs-Schema):
{"text": ..., "words": [{"text","start","end","type":"word"}, ...]} -
nachgelagerte Scripts muessen den Dienst nicht kennen.

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

URL_GROQ = "https://api.groq.com/openai/v1/audio/transcriptions"
URL_ELEVEN = "https://api.elevenlabs.io/v1/speech-to-text"


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


def anfrage(url, body, content_type, extra_header):
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": content_type, **extra_header})
    with urllib.request.urlopen(req, timeout=900) as antwort:
        return json.loads(antwort.read().decode("utf-8"))


def echter_key(wert):
    """None fuer leere Werte und unersetzte ~~Platzhalter."""
    if not wert or wert.startswith("~~"):
        return None
    return wert


def via_groq(audio, key, sprache):
    felder = {"model": "whisper-large-v3",
              "response_format": "verbose_json",
              "timestamp_granularities[]": "word"}
    if sprache:
        felder["language"] = sprache
    body, ct = multipart(felder, audio)
    daten = anfrage(URL_GROQ, body, ct,
                    {"Authorization": "Bearer " + key})
    # Auf das ElevenLabs-Schema normalisieren, damit alle nachgelagerten
    # Scripts (Schnitt-Analyse, Untertitel, animated_captions) den
    # Dienst nicht kennen muessen.
    return {"text": daten.get("text", ""),
            "words": [{"text": (w.get("word") or "").strip(),
                       "start": round(w["start"], 2),
                       "end": round(w["end"], 2),
                       "type": "word"}
                      for w in daten.get("words", []) or []]}


def via_eleven(audio, key, sprache, modell):
    felder = {"model_id": modell, "timestamps_granularity": "word"}
    if sprache:
        felder["language_code"] = sprache
    body, ct = multipart(felder, audio)
    return anfrage(URL_ELEVEN, body, ct, {"xi-api-key": key})


def fehler_text(e, dienst):
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 401:
            return f"{dienst}: API-Key abgelehnt (401)."
        if e.code == 429:
            return f"{dienst}: Limit erreicht oder Guthaben aufgebraucht (429)."
        roh = e.read().decode("utf-8", errors="replace")[:300]
        return f"{dienst}: HTTP {e.code}: {roh}"
    if isinstance(e, urllib.error.URLError):
        return f"{dienst}: Keine Verbindung ({e.reason})."
    return f"{dienst}: {e}"


def main():
    p = argparse.ArgumentParser(
        description="Audio transkribieren (Groq bevorzugt, ElevenLabs als "
                    "Rueckfallebene)")
    p.add_argument("audio", help="Pfad zur Audiodatei (z. B. audio_temp.mp3)")
    p.add_argument("api_key", nargs="?",
                   default=os.environ.get("ELEVENLABS_API_KEY"),
                   help="ElevenLabs-Key (oder ELEVENLABS_API_KEY)")
    p.add_argument("--groq-key", default=os.environ.get("GROQ_API_KEY"),
                   help="Groq-Key (oder GROQ_API_KEY) - bevorzugter Dienst")
    p.add_argument("-o", "--ausgabe", default="transkript.json")
    p.add_argument("--sprache", default="de")
    p.add_argument("--modell", default="scribe_v1",
                   help="ElevenLabs-Modell (nur fuer die Rueckfallebene)")
    a = p.parse_args()

    groq = echter_key(a.groq_key)
    eleven = echter_key(a.api_key)
    if not groq and not eleven:
        print("FEHLER: Kein API-Key. Groq-Key (bevorzugt) oder "
              "ElevenLabs-Key angeben.")
        return 1
    if not os.path.exists(a.audio):
        print(f"FEHLER: Audiodatei nicht gefunden: {a.audio}")
        return 1

    groesse_mb = os.path.getsize(a.audio) / (1024 * 1024)
    print(f"Transkribiere {os.path.basename(a.audio)} ({groesse_mb:.1f} MB) ...")

    daten = None
    fehler = []
    if groq:
        print("Dienst: Groq Whisper (bevorzugt)")
        try:
            daten = via_groq(a.audio, groq, a.sprache)
        except Exception as e:
            fehler.append(fehler_text(e, "Groq"))
            print(f"  {fehler[-1]}")
    if daten is None and eleven:
        if groq:
            print("Weiche auf die Rueckfallebene aus: ElevenLabs Scribe")
        else:
            print("Dienst: ElevenLabs Scribe")
        try:
            daten = via_eleven(a.audio, eleven, a.sprache, a.modell)
        except Exception as e:
            fehler.append(fehler_text(e, "ElevenLabs"))
            print(f"  {fehler[-1]}")

    if daten is None:
        print("FEHLER: Transkription fehlgeschlagen.")
        for f in fehler:
            print("  -", f)
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
