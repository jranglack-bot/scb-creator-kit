#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Karussell-Renderer: ein JSON rein, fertige Folien + Kontaktbogen raus.

Rendert HTML-Templates (hook/content/cta) per vorinstalliertem
Edge/Chrome headless zu 1080x1350-Folien und baut einen Kontaktbogen
(alle Folien in EINEM Bild) fuer die tokensparende Qualitaetskontrolle.

Aufruf:
  python build_carousel.py config.json

config.json:
{
  "output_dir": "karussell",
  "brand": {"bg1": "#1F2430", "bg2": "#3B2F63", "accent": "#FFD400",
             "text": "#FFFFFF", "font": "Segoe UI", "account": "@name"},
  "slides": [
    {"type": "hook", "kicker": "REEL-WISSEN",
     "title": "5 Fehler, die dein <em>Reel unsichtbar</em> machen"},
    {"type": "content", "number": "1", "title": "Kein Hook in Sekunde 1",
     "body": "Die ersten 3 Sekunden entscheiden.\nStarte mit ..."},
    {"type": "cta", "title": "Willst du die <em>Vorlage</em>?",
     "body": "Kommentiere das Wort unten und ich schicke sie dir.",
     "pill": "KEYWORD"}
  ]
}
"""
import glob
import json
import os
import subprocess
import sys

BROWSERS = [
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
]

DEFAULT_BRAND = {'bg1': '#1F2430', 'bg2': '#3B2F63', 'accent': '#FFD400',
                 'text': '#FFFFFF', 'font': 'Segoe UI', 'account': ''}


def find_browser():
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    raise SystemExit('Kein Edge/Chrome gefunden — Pfade in BROWSERS pruefen.')


def main():
    with open(sys.argv[1], encoding='utf-8-sig') as f:
        cfg = json.load(f)
    outdir = os.path.abspath(cfg.get('output_dir', 'karussell'))
    os.makedirs(outdir, exist_ok=True)
    tpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'templates')
    brand = dict(DEFAULT_BRAND, **(cfg.get('brand') or {}))
    browser = find_browser()

    slides = cfg['slides']
    total = len(slides)
    for i, s in enumerate(slides, 1):
        with open(os.path.join(tpl_dir, s['type'] + '.html'),
                  encoding='utf-8') as f:
            html = f.read()
        img_url = ''
        if s.get('image'):
            img_url = 'file:///' + os.path.abspath(s['image']).replace('\\', '/')
        repl = {
            'FONT': brand['font'], 'BG1': brand['bg1'], 'BG2': brand['bg2'],
            'ACCENT': brand['accent'], 'TEXT': brand['text'],
            'ACCOUNT': brand['account'],
            'KICKER': s.get('kicker', ''), 'TITLE': s.get('title', ''),
            'BODY': str(s.get('body', '')).replace('\n', '<br>'),
            'NUMBER': str(s.get('number', '')),
            'PILL': s.get('pill', ''),
            'IMAGE': img_url,
            'PAGE': '{}/{}'.format(i, total),
        }
        for k, v in repl.items():
            html = html.replace('{{' + k + '}}', v)
        hpath = os.path.join(outdir, 'slide{:02d}.html'.format(i))
        with open(hpath, 'w', encoding='utf-8') as f:
            f.write(html)
        png = os.path.join(outdir, 'slide{:02d}.png'.format(i))
        subprocess.run(
            [browser, '--headless', '--disable-gpu', '--hide-scrollbars',
             '--window-size=1080,1350', '--screenshot=' + png,
             'file:///' + hpath.replace('\\', '/')],
            check=True, capture_output=True)
        os.unlink(hpath)

    # Kontaktbogen: alle Folien in EINEM Bild (fuer die QC mit 1 Bild-Ansicht)
    try:
        from PIL import Image
        thumbs = []
        for p in sorted(glob.glob(os.path.join(outdir, 'slide*.png'))):
            im = Image.open(p)
            im.thumbnail((360, 450))
            thumbs.append(im)
        cols = min(4, len(thumbs))
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 370 + 10, rows * 460 + 10),
                          (24, 24, 28))
        for k, im in enumerate(thumbs):
            sheet.paste(im, (10 + (k % cols) * 370, 10 + (k // cols) * 460))
        sheet_path = os.path.join(outdir, 'kontaktbogen.jpg')
        sheet.save(sheet_path, quality=88)
        print('Kontaktbogen:', sheet_path)
    except ImportError:
        print('Hinweis: Pillow fehlt (pip install pillow) — '
              'kein Kontaktbogen, Folien liegen einzeln vor.')

    print('OK: {} Folien in {}'.format(total, outdir))


if __name__ == '__main__':
    main()
