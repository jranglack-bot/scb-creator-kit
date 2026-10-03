"""Hintergrund entfernen, lokal und ohne Kosten.

    python freisteller.py <bild> [<ziel.png>] [--modell schnell|genau]

Zwei Stufen (nach Vergleich an drei Bildern ausgewaehlt):
  schnell  IS-Net (MIT, 180 MB): unter 1 Sekunde. Standard.
           Bei Glas, Fell und Illustrationen manchmal halb durchsichtig.
  genau    BiRefNet (MIT, 928 MB): sauberste Trennung, auf einem Laptop
           2 bis 2,5 Minuten und rund 3 GB Arbeitsspeicher. Darum laeuft
           es aus dem Cockpit in einem eigenen Prozess.

Ohne Ziel entsteht <bild>_frei.png (schnell) bzw. <bild>_frei_genau.png
daneben. Das Original bleibt unberuehrt.
Die Modelle liegen in <Karussell-Ordner>/modelle oder ~/.scb-creator-kit/modelle
(laden: python einrichten.py --modelle) und werden direkt ueber onnxruntime benutzt,
nicht ueber das Paket rembg: das wuerde onnxruntime nachinstallieren und
onnxruntime-directml verdraengen, das die Video-Freisteller brauchen.
"""
import hashlib, sys, time
from pathlib import Path

import numpy as np
from PIL import Image

import projekt as P

HIER = P.HIER
DATEIEN = {"schnell": "isnet.onnx", "genau": "birefnet-gross.onnx"}
# Herkunft (rembg-Releases, MIT) mit Pruefsumme: einrichten.py laedt nur genau diese Dateien
QUELLEN = {
    "schnell": {"url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx",
                "sha256": "60920e99c45464f2ba57bee2ad08c919a52bbf852739e96947fbb4358c0d964a",
                "mb": 179},
    "genau": {"url": "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx",
              "sha256": "58f621f00f5d756097615970a88a791584600dcf7c45b18a0a6267535a1ebd3c",
              "mb": 973},
}
ANDERE_NAMEN = {"isnet": "schnell", "gross": "genau", "birefnet": "genau"}
STANDARD = "schnell"
ENDUNG = {"schnell": "_frei", "genau": "_frei_genau"}
GROESSE = 1024
MITTEL = np.array([0.485, 0.456, 0.406], dtype=np.float32)
# BiRefNet will ImageNet-Streuung und gibt Logits aus, IS-Net nur Mittelwert
# abziehen und liefert schon Wahrscheinlichkeiten (wie rembg es macht)
STREUUNG = {"schnell": np.array([1.0, 1.0, 1.0], dtype=np.float32),
            "genau": np.array([0.229, 0.224, 0.225], dtype=np.float32)}
OHNE_SIGMOID = {"schnell"}

_sitzungen = {}


def name_von(modell):
    m = ANDERE_NAMEN.get(modell or STANDARD, modell or STANDARD)
    if m not in DATEIEN:
        raise ValueError("Freisteller gibt es nicht: %s (schnell oder genau)" % modell)
    return m


_GEPRUEFT = {}


def _echt(datei, modell):
    """Pruefsumme einer Datei im Karussell-Ordner (dort koennen fremde Dateien
    liegen). Einmal je Programmlauf und Dateistand."""
    st = datei.stat()
    schluessel = (str(datei), st.st_size, st.st_mtime_ns)
    if schluessel not in _GEPRUEFT:
        ok = st.st_size <= (QUELLEN[modell]["mb"] + 5) * 1_000_000
        if ok:
            h = hashlib.sha256()
            with open(datei, "rb") as f:
                for stueck in iter(lambda: f.read(1 << 20), b""):
                    h.update(stueck)
            ok = h.hexdigest() == QUELLEN[modell]["sha256"]
        _GEPRUEFT[schluessel] = ok
    return _GEPRUEFT[schluessel]


def pfad(modell):
    """Wo das Modell liegt, sonst None. ~/.scb-creator-kit/modelle fuellt nur
    einrichten.py (mit Pruefsumme). Im Karussell-Ordner zaehlt eine Datei nur,
    wenn ihre Pruefsumme stimmt."""
    kit = P.KIT_HOME / "modelle" / DATEIEN[modell]
    if kit.is_file() and not kit.is_symlink():
        return kit
    eigen = P.DATEN / "modelle" / DATEIEN[modell]
    if eigen.is_file() and not eigen.is_symlink() and _echt(eigen, modell):
        return eigen
    return None


def vorhanden():
    return [k for k in DATEIEN if pfad(k)]


def _sitzung(modell, nur_cpu=False):
    schluessel = (modell, nur_cpu)
    if schluessel not in _sitzungen:
        import onnxruntime as ort
        datei = pfad(modell)
        if datei is None:
            raise FileNotFoundError("Freisteller fehlt: %s (python einrichten.py --modelle %s)"
                                    % (DATEIEN[modell], modell))
        anbieter = ["CPUExecutionProvider"]
        if not nur_cpu and "DmlExecutionProvider" in ort.get_available_providers():
            anbieter.insert(0, "DmlExecutionProvider")    # Windows-Grafikkarte zuerst
        _sitzungen[schluessel] = ort.InferenceSession(str(datei), providers=anbieter)
    return _sitzungen[schluessel]


def _rechnen(modell, x):
    """Erst Grafikkarte, bei Fehler (z. B. zu wenig Grafikspeicher) Prozessor.
    Ein Fehlschlag merkt sich, damit nicht jedes Bild erneut scheitert."""
    if not _sitzungen.get((modell, "gpu_kaputt")):
        try:
            s = _sitzung(modell)
            return s.run(None, {s.get_inputs()[0].name: x})[0]
        except Exception:
            _sitzungen[(modell, "gpu_kaputt")] = True
            _sitzungen.pop((modell, False), None)
    s = _sitzung(modell, nur_cpu=True)
    return s.run(None, {s.get_inputs()[0].name: x})[0]


def maske(bild, modell=STANDARD):
    """PIL-Bild -> Maske (L) in Originalgroesse, 255 = Vordergrund."""
    modell = name_von(modell)
    rgb = bild.convert("RGB")
    x = np.asarray(rgb.resize((GROESSE, GROESSE), Image.BICUBIC), dtype=np.float32) / 255.0
    x = ((x - MITTEL) / STREUUNG[modell]).transpose(2, 0, 1)[None]
    roh = _rechnen(modell, x)[0, 0]
    p = roh if modell in OHNE_SIGMOID else 1.0 / (1.0 + np.exp(-roh))
    p = (p - p.min()) / max(p.max() - p.min(), 1e-6)
    m = Image.fromarray((p * 255).astype(np.uint8), "L")
    return m.resize(rgb.size, Image.LANCZOS)


def zielname(quelle, modell=STANDARD):
    quelle = Path(quelle)
    return quelle.with_name(quelle.stem + ENDUNG[name_von(modell)] + ".png")


def freistellen(quelle, ziel=None, modell=STANDARD):
    """Bild mit durchsichtigem Hintergrund als PNG. Gleiche Groesse wie das
    Original, damit es in seiner Box an derselben Stelle bleibt."""
    quelle = Path(quelle)
    ziel = Path(ziel) if ziel else zielname(quelle, modell)
    bild = Image.open(quelle)
    rgba = bild.convert("RGBA")
    m = maske(bild, modell)
    if bild.mode in ("RGBA", "LA", "P"):      # vorhandene Transparenz behalten
        m = Image.fromarray(np.minimum(np.asarray(m), np.asarray(rgba.getchannel("A"))))
    rgba.putalpha(m)
    if ziel.is_symlink():
        raise ValueError("Ziel ist eine Verknuepfung")
    rgba.save(ziel, optimize=True)
    return ziel


if __name__ == "__main__":
    args = sys.argv[1:]
    modell = STANDARD
    if "--modell" in args:
        i = args.index("--modell"); modell = args[i + 1]; del args[i:i + 2]
    if not args:
        print(__doc__); sys.exit()
    t = time.time()
    z = freistellen(args[0], args[1] if len(args) > 1 else None, modell)
    print("%s (%s, %.1f s)" % (z, name_von(modell), time.time() - t))
