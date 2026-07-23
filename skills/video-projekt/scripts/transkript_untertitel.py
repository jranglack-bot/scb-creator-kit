#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transkribiert ein Video wortgenau und schreibt die Untertitel-Woerter
direkt in die projekt.json — OHNE dass die Wortliste je in Claudes Kontext
landet (Token-Regel: Scripts arbeiten, Claude liest nur die Zusammenfassung).

Aufruf:
  python transkript_untertitel.py <projekt.json> <video> [--sprache de]

API-Key (einer reicht, Reihenfolge = Vorrang):
  - Umgebungsvariable GROQ_API_KEY       (Groq Whisper, schnell + kostenlos)
  - Umgebungsvariable ELEVENLABS_API_KEY (ElevenLabs Scribe)
Danach build_editor.py ausfuehren, damit das Cockpit die Woerter bekommt.
"""
import json
import os
import subprocess
import sys
import tempfile


def main():
    pj_path = os.path.abspath(sys.argv[1])
    video = sys.argv[2]
    lang = sys.argv[4] if '--sprache' in sys.argv else None
    projdir = os.path.dirname(pj_path)
    vpath = video if os.path.isabs(video) else os.path.join(projdir, video)

    audio = os.path.join(tempfile.gettempdir(), 'transkript_audio.mp3')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', vpath, '-vn',
                    '-ac', '1', '-acodec', 'libmp3lame', '-q:a', '4', audio],
                   check=True)

    groq = os.environ.get('GROQ_API_KEY')
    eleven = os.environ.get('ELEVENLABS_API_KEY')
    out = os.path.join(tempfile.gettempdir(), 'transkript_result.json')
    if groq:
        cmd = ['curl', '-s', '-X', 'POST',
               'https://api.groq.com/openai/v1/audio/transcriptions',
               '-H', 'Authorization: Bearer ' + groq,
               '-F', 'file=@' + audio, '-F', 'model=whisper-large-v3',
               '-F', 'response_format=verbose_json',
               '-F', 'timestamp_granularities[]=word', '-o', out]
        if lang:
            cmd += ['-F', 'language=' + lang]
        subprocess.run(cmd, check=True)
        data = json.load(open(out, encoding='utf-8'))
        words = [{'text': w['word'].strip(),
                  'start': round(w['start'], 2), 'end': round(w['end'], 2),
                  'type': 'word'} for w in data.get('words', [])]
    elif eleven:
        cmd = ['curl', '-s', '-X', 'POST',
               'https://api.elevenlabs.io/v1/speech-to-text',
               '-H', 'xi-api-key: ' + eleven,
               '-F', 'file=@' + audio, '-F', 'model_id=scribe_v1',
               '-F', 'timestamps_granularity=word', '-o', out]
        if lang:
            cmd += ['-F', 'language_code=' + lang]
        subprocess.run(cmd, check=True)
        data = json.load(open(out, encoding='utf-8'))
        words = [{'text': w.get('text', '').strip(),
                  'start': round(w['start'], 2), 'end': round(w['end'], 2),
                  'type': 'word'}
                 for w in data.get('words', [])
                 if w.get('type', 'word') == 'word']
    else:
        sys.exit('FEHLER: Kein API-Key (GROQ_API_KEY oder '
                 'ELEVENLABS_API_KEY setzen).')

    if not words:
        sys.exit('FEHLER: Transkription leer — Antwort: '
                 + json.dumps(data)[:300])

    pj = json.load(open(pj_path, encoding='utf-8-sig'))
    pj['words'] = words
    cap = pj.get('captions') or {}
    cap['enabled'] = True
    cap.setdefault('y', 0.72)
    pj['captions'] = cap
    with open(pj_path, 'w', encoding='utf-8') as f:
        json.dump(pj, f, ensure_ascii=False, indent=2)
    os.remove(audio)
    print('OK:', len(words), 'Woerter |', data.get('language', '?'),
          '| Untertitel aktiv (y={})'.format(cap['y']))
    print('TEXT-ANFANG:', ' '.join(w['text'] for w in words[:14]), '...')


if __name__ == '__main__':
    main()
