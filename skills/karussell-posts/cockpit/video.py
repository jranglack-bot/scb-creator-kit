"""Videos im Karussell: hochladen (als H.264 umwandeln, Standbild dazu) und eine Folie
mit Video als MP4 ausgeben. Braucht ffmpeg und ffprobe; fehlen sie, sagt das Cockpit es.

Ein Video ist ein Bild-Block mit datei .mp4 (render.js: istVideo, videoBauen). Neben
der Datei liegt immer <datei>.jpg, das Standbild fuer Minis, Vorschau, PDF und Canva.

Ausgabe einer Video-Folie (aus bauen.messen, in vorlage.html steht das Standbild):
  1. unten.png  alles unter dem Video: Folienhintergrund, Ebenen darunter, Rand und
                Geraet des Video-Blocks (der Bildschirm bleibt leer)
  2. maske.png  nur die Videoflaeche, weiss auf durchsichtig (Form, Ecken, Deckkraft)
  3. oben.png   alles ueber dem Video, durchsichtig
  4. ffmpeg legt das Video (cover, Ausschnitt, Zoom, Spiegeln, Filter) dazwischen.
Unterstuetzt: ein bewegtes Video je Folie (das unterste), nicht gedreht. Sonst bleibt
die Folie ein Bild und die Ausgabe sagt es.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ENDUNGEN = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}      # was hochgeladen werden darf
VIDEO_OK = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]*\.(mp4|m4v|mov|webm)", re.I)   # wie VIDEO_OK in render.js
MAX_VIDEO = 2_000_000_000
MAX_DAUER = 60.0            # Instagram: ein Video im Karussell darf hoechstens 60 s lang sein
SPERRE = threading.Lock()   # nie zwei Umwandlungen zugleich (Laptop)
FILTER_STD = {"hell": 100, "kontrast": 100, "saett": 100, "unschaerfe": 0, "grau": 0, "sepia": 0}


def da():
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def ist_video(b):
    d = b.get("datei") if isinstance(b, dict) else None
    return isinstance(b, dict) and b.get("typ") == "bild" and isinstance(d, str) and bool(VIDEO_OK.fullmatch(d))


def zahl(v, std):
    try:
        v = float(v)
        return v if v == v and abs(v) < 1e9 else std
    except (TypeError, ValueError):
        return std


def info(pfad):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height:format=duration", "-of", "json", str(pfad)],
                       capture_output=True, text=True, timeout=60)
    try:
        j = json.loads(r.stdout or "{}")
    except ValueError:
        j = {}
    st = j.get("streams") or []
    v = next((s for s in st if s.get("codec_type") == "video"), {})
    return {"dauer": round(zahl((j.get("format") or {}).get("duration"), 0), 2),
            "w": int(zahl(v.get("width"), 0)), "h": int(zahl(v.get("height"), 0)),
            "ton": any(s.get("codec_type") == "audio" for s in st)}


def _kodieren(befehl_ohne_codec, ausgabe, qualitaet):
    """Erst die Grafikkarte (Windows: Intel QSV, Mac: VideoToolbox), sonst libx264."""
    versuche = []
    if sys.platform == "win32":
        versuche.append(["-c:v", "h264_qsv", "-global_quality", str(qualitaet), "-preset", "medium"])
    elif sys.platform == "darwin":
        versuche.append(["-c:v", "h264_videotoolbox", "-b:v", "10M"])
    versuche.append(["-c:v", "libx264", "-preset", "medium" if qualitaet < 20 else "veryfast",
                     "-crf", str(qualitaet)])
    letzte = ""
    for enc in versuche:
        r = subprocess.run(befehl_ohne_codec[:-1] + enc + befehl_ohne_codec[-1:], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=3600)
        if r.returncode == 0 and Path(ausgabe).is_file() and Path(ausgabe).stat().st_size > 0:
            return
        letzte = (r.stderr or "")[-400:]
        try:
            Path(ausgabe).unlink()
        except OSError:
            pass
    raise ValueError("ffmpeg ging nicht: " + " ".join(letzte.split())[-240:])


def umwandeln(quelle, ziel):
    """Jedes Video in dieselbe Form: H.264 und AAC, hoechstens 1080 x 1920, 30 Bilder/s,
    ohne Metadaten (Handyvideos tragen sonst Ort und Geraet mit), schnell startbar."""
    vf = ("scale=w='min(1080,iw)':h='min(1920,ih)':force_original_aspect_ratio=decrease,"
          "scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=30,format=yuv420p")
    befehl = ["ffmpeg", "-y", "-v", "error", "-i", str(quelle), "-map", "0:v:0", "-map", "0:a:0?",
              "-map_metadata", "-1", "-map_chapters", "-1", "-vf", vf, "-t", "600",
              "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-movflags", "+faststart", str(ziel)]
    _kodieren(befehl, ziel, 21)


def standbild(video):
    """<datei>.jpg: erstes Bild, fuer Minis, Vorschau, PDF und Canva."""
    ziel = Path(str(video) + ".jpg")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(ziel)],
                   capture_output=True, timeout=120, check=True)
    return ziel


def ablegen(ordner, roh_name, rfile, laenge):
    """Upload in den Projektordner: in Stuecken auf die Platte (nie ganz in den Speicher),
    umwandeln, Standbild. Gleicher Name: neuer Name statt Ueberschreiben."""
    if not da():
        raise ValueError("Fuer Videos braucht das Cockpit ffmpeg. Sag Claude: richte ffmpeg ein.")
    if laenge <= 0:
        raise ValueError("Kein Video angekommen")
    if laenge > MAX_VIDEO:
        raise ValueError("Video zu gross (hoechstens 2 GB)")
    ordner = Path(ordner)
    endung = Path(str(roh_name)).suffix.lower()
    if endung not in ENDUNGEN:
        raise ValueError("Nur Videos (%s)" % ", ".join(sorted(ENDUNGEN)))
    stamm = re.sub(r"[^A-Za-z0-9_\-]", "_", Path(str(roh_name)).stem).strip("_-")[:60] or "video"
    fd, tmp = tempfile.mkstemp(dir=str(ordner), prefix=".upload-", suffix=endung)
    try:
        with os.fdopen(fd, "wb") as f:
            rest = laenge
            while rest > 0:
                stueck = rfile.read(min(1 << 20, rest))
                if not stueck:
                    break
                f.write(stueck)
                rest -= len(stueck)
        if rest:
            raise ValueError("Upload abgebrochen")
        with SPERRE:
            n = 1
            while True:
                name = stamm + (".mp4" if n == 1 else "_%d.mp4" % n)
                if not (ordner / name).exists() and not (ordner / (name + ".jpg")).exists():
                    break
                n += 1
            ziel = ordner / name
            umwandeln(tmp, ziel)
            standbild(ziel)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return dict(info(ziel), datei=name)


# --------------------------------------------------------------- Ausgabe als MP4

# Unterstes Video der Folie in Stapelfolge (die DOM-Reihenfolge der Boxen)
_WAHL = """(ids) => {
  const boxen = [...document.querySelector('.slide').children]
    .filter(e => e.classList && e.classList.contains('box') && !e.classList.contains('gast'));
  const b = boxen.find(e => ids.indexOf(e.dataset.art) >= 0);
  return b ? b.dataset.art : null;
}"""

# Wo liegt das ganze Videobild auf der Folie? Wie object-fit: cover mit Position und
# Zoom (der Zoom steckt im Rechteck der Bildflaeche). Gespiegelt wird um die Mitte.
_GEOMETRIE = """([id, vw, vh, px, py, sh, sv]) => {
  const slide = document.querySelector('.slide'), s0 = slide.getBoundingClientRect();
  const vb = [...slide.children].find(e => e.classList && e.classList.contains('box') &&
                                           !e.classList.contains('gast') && e.dataset.art === id);
  if (!vb) return null;
  const sp = vb.querySelector('.spiegel'), fl = vb.querySelector('.bildflaeche');
  const alt = sp.style.transform; sp.style.transform = '';
  const r = fl.getBoundingClientRect(), c = sp.getBoundingClientRect();
  sp.style.transform = alt;
  const s = Math.max(r.width / vw, r.height / vh), fw = vw * s, fh = vh * s;
  let x = r.left - s0.left + (r.width - fw) * px / 100, y = r.top - s0.top + (r.height - fh) * py / 100;
  if (sh) x = (c.left - s0.left) + (c.right - s0.left) - (x + fw);
  if (sv) y = (c.top - s0.top) + (c.bottom - s0.top) - (y + fh);
  return {x: x, y: y, w: fw, h: fh};
}"""

# Ebenen einzeln sichtbar machen. art: unten | maske | oben | zurueck
_EBENEN = """([id, art]) => {
  let st = document.getElementById('videoStil');
  if (!st){ st = document.createElement('style'); st.id = 'videoStil'; document.head.appendChild(st); }
  const slide = document.querySelector('.slide');
  const boxen = [...slide.children].filter(e => e.classList && e.classList.contains('box'));
  const vb = boxen.find(e => !e.classList.contains('gast') && e.dataset.art === id);
  const idx = boxen.indexOf(vb);
  boxen.forEach(e => { e.style.visibility = ''; delete e.dataset.vid; });
  st.textContent = '';
  if (art === 'zurueck' || !vb) return true;
  vb.dataset.vid = '1';
  const durchsichtig = 'html,body,.slide{background:transparent!important}' +
                       '.slide::before,.slide::after{display:none!important}';
  if (art === 'unten'){
    boxen.forEach((e, j) => { if (j > idx) e.style.visibility = 'hidden'; });
    st.textContent = '.slide [data-vid] .bildflaeche,.slide [data-vid] .geraetoben{visibility:hidden!important}';
  } else if (art === 'maske'){
    boxen.forEach(e => { if (e !== vb) e.style.visibility = 'hidden'; });
    st.textContent = durchsichtig +
      '.slide [data-vid]{filter:none!important;border-color:transparent!important;box-shadow:none!important}' +
      '.slide [data-vid] *{visibility:hidden!important}' +
      '.slide [data-vid] .bildschirm,.slide [data-vid] .spiegel,.slide [data-vid] .bildflaeche{visibility:visible!important}' +
      '.slide [data-vid] .bildschirm{background:transparent!important}' +
      '.slide [data-vid] .bildflaeche{background:#fff!important;filter:none!important}';
  } else if (art === 'oben'){
    boxen.forEach((e, j) => { if (j < idx) e.style.visibility = 'hidden'; });
    st.textContent = durchsichtig +
      '.slide [data-vid]{filter:none!important;border-color:transparent!important}' +
      '.slide [data-vid] *{visibility:hidden!important}' +
      '.slide [data-vid] .geraetoben,.slide [data-vid] .geraetoben *{visibility:visible!important}';
  }
  return true;
}"""


def _filterkette(b):
    """CSS-Filter der Bildflaeche (render.js bildWirkung) fuer ffmpeg, gleiche Reihenfolge."""
    roh = {**FILTER_STD, **(b.get("filter") if isinstance(b.get("filter"), dict) else {})}
    f = {k: zahl(roh.get(k), v) for k, v in FILTER_STD.items()}
    teile = []
    if f["hell"] != 100:
        h = max(0.0, f["hell"] / 100)
        teile.append("colorchannelmixer=rr=%.3f:gg=%.3f:bb=%.3f" % (h, h, h))
    if f["kontrast"] != 100 or f["saett"] != 100:
        teile.append("eq=contrast=%.3f:saturation=%.3f" % (max(0.0, f["kontrast"] / 100), max(0.0, f["saett"] / 100)))
    if f["grau"]:
        teile.append("hue=s=%.3f" % max(0.0, 1 - min(100.0, f["grau"]) / 100))
    if f["sepia"]:
        p = min(100.0, f["sepia"]) / 100
        s = [[.393, .769, .189], [.349, .686, .168], [.272, .534, .131]]
        m = [[(1 - p) * (1 if i == j else 0) + p * s[i][j] for j in range(3)] for i in range(3)]
        teile.append("colorchannelmixer=" + ":".join("%s%s=%.3f" % (a, c, m[i][j]) for i, a in enumerate("rgb")
                                                       for j, c in enumerate("rgb")))
    if f["unschaerfe"]:
        teile.append("gblur=sigma=%.2f" % min(200.0, f["unschaerfe"]))
    return teile


def folie_mp4(pg, slide, ordner, ausgabe, B, H):
    """Video-Folie als MP4. Erwartet die Folie offen in pg (vorlage.html, Standbild).
    Gibt {"ok", "hinweis", "dauer"} zurueck; ok False heisst: Folie bleibt ein Bild."""
    ordner = Path(ordner)
    ids = [b["id"] for b in slide.get("bloecke") or [] if ist_video(b) and isinstance(b.get("id"), str)
           and (ordner / b["datei"]).is_file()]
    if not ids:
        return {"ok": False, "hinweis": "Videodatei fehlt im Projekt, die Folie bleibt ein Bild"}
    if not da():
        return {"ok": False, "hinweis": "ffmpeg fehlt, die Folie bleibt ein Bild"}
    vid = pg.evaluate(_WAHL, ids)
    b = next((x for x in slide["bloecke"] if isinstance(x, dict) and x.get("id") == vid), None)
    if not b:
        return {"ok": False, "hinweis": "Video nicht gefunden, die Folie bleibt ein Bild"}
    if zahl(b.get("dreh"), 0) % 360:
        return {"ok": False, "hinweis": "gedrehtes Video, die Folie bleibt ein Bild (Drehung auf 0 stellen)"}
    quelle = ordner / b["datei"]
    i = info(quelle)
    if not i["w"] or not i["h"]:
        return {"ok": False, "hinweis": "Video unlesbar, die Folie bleibt ein Bild"}
    a = b.get("ausschnitt") if isinstance(b.get("ausschnitt"), dict) else {}
    px, py = zahl(a.get("x"), 50), zahl(a.get("y"), 50)
    sp = str(b.get("spiegeln") or "")
    geo = pg.evaluate(_GEOMETRIE, [vid, i["w"], i["h"], px, py, "h" in sp, "v" in sp])
    if not geo:
        return {"ok": False, "hinweis": "Video nicht vermessen, die Folie bleibt ein Bild"}
    von = max(0.0, zahl(b.get("von"), 0))
    bis = zahl(b.get("bis"), 0)
    ende = bis if von < bis <= i["dauer"] else i["dauer"]
    dauer = round(min(ende - von, MAX_DAUER), 3)
    if dauer <= 0.2:
        return {"ok": False, "hinweis": "Start liegt hinter dem Ende, die Folie bleibt ein Bild"}
    hinweis = "auf 60 s gekuerzt (mehr erlaubt Instagram im Karussell nicht)" if ende - von > MAX_DAUER else ""
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        for art in ("unten", "maske", "oben"):
            pg.evaluate(_EBENEN, [vid, art])
            pg.screenshot(path=str(t / (art + ".png")), omit_background=(art != "unten"))
        pg.evaluate(_EBENEN, [vid, "zurueck"])
        fw, fh = max(2, round(geo["w"])), max(2, round(geo["h"]))
        x, y = round(geo["x"]), round(geo["y"])
        kette = ["setpts=PTS-STARTPTS", "fps=30"]
        if "h" in sp:
            kette.append("hflip")
        if "v" in sp:
            kette.append("vflip")
        kette.append("scale=%d:%d:flags=lanczos" % (fw, fh))
        kette += _filterkette(b) + ["format=rgba"]
        graph = ";".join([
            "[1:v]" + ",".join(kette) + "[v]",
            "color=c=black@0.0:s=%dx%d:r=30:d=%.3f,format=rgba[leer]" % (B, H, dauer),
            "[leer][v]overlay=x=%d:y=%d:format=auto[vp]" % (x, y),
            "[2:v]format=rgba,alphaextract[m]",
            "[vp][m]alphamerge[vm]",
            "[0:v]format=rgba[u]",
            "[u][vm]overlay=0:0:format=auto[a]",
            "[a][3:v]overlay=0:0:format=auto,format=yuv420p[aus]"])
        ton = i["ton"] and not b.get("stumm")
        befehl = (["ffmpeg", "-y", "-v", "error",
                   "-loop", "1", "-framerate", "30", "-i", str(t / "unten.png"),
                   "-ss", "%.3f" % von, "-t", "%.3f" % dauer, "-i", str(quelle),
                   "-loop", "1", "-framerate", "30", "-i", str(t / "maske.png"),
                   "-loop", "1", "-framerate", "30", "-i", str(t / "oben.png"),
                   "-filter_complex", graph, "-map", "[aus]"]
                  + (["-map", "1:a:0", "-c:a", "aac", "-b:a", "160k"] if ton else ["-an"])
                  + ["-t", "%.3f" % dauer, "-r", "30", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                     str(ausgabe)])
        _kodieren(befehl, ausgabe, 18)
    return {"ok": True, "hinweis": hinweis, "dauer": dauer}
