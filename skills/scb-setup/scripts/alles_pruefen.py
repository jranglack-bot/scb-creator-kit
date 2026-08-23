#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rundum-Check: Ist alles aus dem SCB Creator Kit auf dem neuesten Stand?

Fuer Leute ohne Technikkenntnisse gedacht: Claude ruft das Script auf,
der Nutzer liest eine Liste in Klartext und entscheidet, ob aktualisiert
werden soll.

    python alles_pruefen.py             # nur pruefen und berichten
    python alles_pruefen.py --update    # zusaetzlich aktualisieren

Geprueft wird:
  - SCB Creator Kit (installierte Fassung gegen GitHub)
  - RTK Token-Sparer: installiert? Hook wirklich aktiv? aktuell?
  - /watch (Video-Analyse)
  - Werkzeuge: ffmpeg, ffprobe, node, yt-dlp, git
  - Freistellung: onnxruntime (RVM) bzw. mediapipe
  - API-Keys: liegt eine keys.env vor?

Exit 0 = alles aktuell
Exit 1 = es gibt etwas zu tun (Details stehen im Bericht)
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

KIT_JSON = ("https://raw.githubusercontent.com/jranglack-bot/"
            "scb-creator-kit/master/.claude-plugin/plugin.json")
RTK_API = "https://api.github.com/repos/rtk-ai/rtk/releases/latest"
KEY_DATEI = Path.home() / ".scb-creator-kit" / "keys.env"
SETTINGS = Path.home() / ".claude" / "settings.json"

OK, ALT, FEHLT, UNKLAR = "aktuell", "veraltet", "fehlt", "unklar"


def run(cmd, **kw):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=120, **kw)
    except Exception:
        class R:
            returncode = 1
            stdout = ""
            stderr = ""
        return R()


def netz(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "scb-kit"})
        with urllib.request.urlopen(req, timeout=30) as a:
            return a.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def claude_cli():
    p = shutil.which("claude")
    if p:
        return p
    name = "claude.exe" if platform.system() == "Windows" else "claude"
    k = Path.home() / ".local" / "bin" / name
    return str(k) if k.exists() else None


def rtk_binary():
    p = shutil.which("rtk")
    if p:
        return p
    la = os.environ.get("LOCALAPPDATA", "")
    kandidaten = [os.path.join(la, "Programs", "rtk", "rtk.exe"),
                  os.path.join(la, "Microsoft", "WinGet", "Links", "rtk.exe"),
                  "/opt/homebrew/bin/rtk", "/usr/local/bin/rtk",
                  str(Path.home() / ".local" / "bin" / "rtk")]
    for k in kandidaten:
        if os.path.exists(k):
            return k
    return None


def versionszahl(text):
    """Erste Zahlenfolge der Form 1.2.3 aus einem Text."""
    import re
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


# ---------------------------------------------------------------- Pruefungen
def quelle_des_kits():
    """'github', 'lokal' oder None.

    Ein aus der heruntergeladenen Datei installiertes Kit haengt an einem
    ORDNER, nicht an GitHub - 'claude plugin update' hat dort nichts zum
    Nachladen und meldet trotzdem Erfolg. Das muss erkannt werden, sonst
    bleibt so ein Kit fuer immer auf seiner alten Fassung stehen.
    """
    pfad = Path.home() / ".claude" / "plugins" / "known_marketplaces.json"
    try:
        with open(pfad, encoding="utf-8-sig") as f:
            eintrag = json.load(f).get("scb-creator-kit") or {}
        q = (eintrag.get("source") or {}).get("source")
        return "github" if q == "github" else "lokal"
    except Exception:
        return None



def pruefe_kit():
    cli = claude_cli()
    installiert = None
    if cli:
        r = run([cli, "plugin", "list"])
        # WICHTIG: 'plugin list' listet ALLE Plugins. Erst den Block des
        # Kits finden, dann dessen Version - sonst wird die Version eines
        # fremden Plugins gelesen (real passiert).
        treffer = False
        for zeile_ in (r.stdout or "").splitlines():
            if "scb-creator-kit@" in zeile_:
                treffer = True
                continue
            if treffer and "Version:" in zeile_:
                installiert = zeile_.split("Version:")[-1].strip()
                break
    roh = netz(KIT_JSON)
    aktuell = None
    if roh:
        try:
            aktuell = json.loads(roh).get("version")
        except Exception:
            pass
    if not installiert:
        return (FEHLT, "nicht als Plugin installiert", aktuell)
    if not aktuell:
        return (UNKLAR, installiert + " (GitHub nicht erreichbar)", None)
    if versionszahl(installiert) == versionszahl(aktuell):
        return (OK, installiert, aktuell)
    return (ALT, installiert, aktuell)


def pruefe_rtk():
    exe = rtk_binary()
    if not exe:
        return (FEHLT, "nicht installiert", None, False)
    v = (run([exe, "--version"]).stdout or "").strip()
    hook = False
    try:
        with open(SETTINGS, encoding="utf-8-sig") as f:
            hook = "rtk" in json.dumps(json.load(f).get("hooks") or {})
    except Exception:
        pass
    roh = netz(RTK_API)
    neueste = None
    if roh:
        try:
            neueste = (json.loads(roh).get("tag_name") or "").lstrip("v")
        except Exception:
            pass
    if not hook:
        return ("HOOK FEHLT", v, neueste, False)
    if neueste and versionszahl(v) and versionszahl(v) != versionszahl(neueste):
        return (ALT, v, neueste, True)
    return (OK, v, neueste, True)


def pruefe_watch():
    cli = claude_cli()
    if not cli:
        return (UNKLAR, "claude-Befehl nicht gefunden")
    r = run([cli, "plugin", "list"])
    return ((OK, "installiert") if "watch@claude-video" in (r.stdout or "")
            else (FEHLT, "nicht installiert"))


def pruefe_werkzeuge():
    ergebnis = {}
    for name, befehl in (("ffmpeg", ["ffmpeg", "-version"]),
                         ("ffprobe", ["ffprobe", "-version"]),
                         ("node", ["node", "--version"]),
                         ("yt-dlp", ["yt-dlp", "--version"]),
                         ("git", ["git", "--version"])):
        pfad = shutil.which(befehl[0])
        if not pfad:
            k = Path.home() / ".local" / "bin" / befehl[0]
            pfad = str(k) if k.exists() else None
        if not pfad:
            ergebnis[name] = (FEHLT, "-")
            continue
        r = run([pfad] + befehl[1:])
        erste = (r.stdout or r.stderr or "").splitlines()
        ergebnis[name] = ((OK, (erste[0] if erste else "")[:45])
                          if r.returncode == 0 else (FEHLT, "startet nicht"))
    return ergebnis


def pruefe_freistellung():
    try:
        import onnxruntime as ort
        gpu = [a for a in ort.get_available_providers()
               if a != "CPUExecutionProvider"]
        return (OK, "RVM bereit " + ort.__version__
                + (", GPU: " + gpu[0] if gpu else ", nur CPU"))
    except Exception:
        pass
    try:
        import mediapipe  # noqa: F401
        return (ALT, "nur MediaPipe - flackert unter Grafik")
    except Exception:
        return (FEHLT, "nicht eingerichtet (nur fuer 'Text hinter mir')")


def pruefe_grafik():
    """Motion Canvas / Remotion - beide werden BEI BEDARF angelegt.

    Sie gehoeren bewusst nicht zur Grundinstallation: Erst wenn der Nutzer
    animierte Grafik will und sich fuer eines der beiden entscheidet, wird
    das Projekt erzeugt. Fehlt hier etwas, ist das KEIN Mangel.
    """
    node = shutil.which("node")
    if not node:
        return (FEHLT, "Node.js fehlt - ohne das geht keines von beiden")
    gefunden = []
    for name, marker in (("Motion Canvas", "motion-canvas"),
                         ("Remotion", "remotion")):
        for basis in (Path.home(), Path("D:/Instagram Content"),
                      Path.cwd()):
            try:
                if (basis / marker / "package.json").exists():
                    gefunden.append(name)
                    break
            except Exception:
                pass
    if gefunden:
        return (OK, " + ".join(gefunden) + " eingerichtet")
    return (UNKLAR, "noch keins angelegt - wird bei Bedarf erzeugt")



def pruefe_keys():
    if not KEY_DATEI.exists():
        return (FEHLT, "keine keys.env")
    inhalt = KEY_DATEI.read_text(encoding="utf-8", errors="replace")
    hat = [n for n in ("GROQ_API_KEY", "ELEVENLABS_API_KEY")
           if n + "=" in inhalt]
    if "GROQ_API_KEY" in hat:
        return (OK, " + ".join(hat))
    if hat:
        return (ALT, " + ".join(hat) + " (Groq fehlt - der schnellere Weg)")
    return (FEHLT, "Datei da, aber kein Key darin")


# ---------------------------------------------------------------- Aktualisieren
def aktualisiere(befunde):
    """Nur das anfassen, was wirklich veraltet ist."""
    getan, offen = [], []
    cli = claude_cli()

    if befunde["kit"][0] == ALT and cli:
        if quelle_des_kits() == "lokal":
            # Aus der Datei installiert: 'plugin update' hat keine Quelle
            # und meldet trotzdem Erfolg. Also umhaengen auf GitHub, dann
            # bleibt das Kit dauerhaft aktuell.
            print("Das Kit haengt an einem Ordner statt an GitHub - "
                  "haenge es um, damit Updates kuenftig ankommen ...")
            run([cli, "plugin", "marketplace", "remove", "scb-creator-kit"])
            r1 = run([cli, "plugin", "marketplace", "add",
                      "jranglack-bot/scb-creator-kit"])
            r2 = run([cli, "plugin", "install",
                      "scb-creator-kit@scb-creator-kit"])
            ok = r1.returncode == 0 and r2.returncode == 0
            (getan if ok else offen).append("SCB Creator Kit (auf GitHub umgehaengt)")
        else:
            print("Aktualisiere das SCB Creator Kit ...")
            r = run([cli, "plugin", "update", "scb-creator-kit@scb-creator-kit"])
            (getan if r.returncode == 0 else offen).append("SCB Creator Kit")

    zustand, version, neueste, hook = befunde["rtk"]
    exe = rtk_binary()
    if zustand == "HOOK FEHLT" and exe:
        print("Aktiviere den RTK-Hook ...")
        r = run([exe, "init", "-g"])
        (getan if r.returncode == 0 else offen).append("RTK-Hook")
    elif zustand == ALT:
        print("Aktualisiere RTK ...")
        r = None
        if platform.system() == "Windows":
            r = run(["winget", "upgrade", "--silent",
                     "--accept-package-agreements",
                     "--accept-source-agreements", "-e", "--id", "rtk-ai.rtk"])
            kennt = "kein installiertes Paket" not in (r.stdout or "")
        else:
            r = run(["brew", "upgrade", "rtk"])
            kennt = r.returncode == 0
        if not kennt:
            # RTK kam seinerzeit per Direkt-Download, der Paketmanager
            # kennt es nicht. Dann die neueste Fassung direkt holen.
            print("  Paketmanager kennt RTK nicht - hole die neueste "
                  "Fassung direkt.")
            eigener = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "install_rtk.py")
            r = run([sys.executable, eigener, "--neu"])
        (getan if r.returncode == 0 else offen).append("RTK")

    if befunde["watch"][0] == OK and cli:
        r = run([cli, "plugin", "update", "watch@claude-video"])
        if r.returncode == 0 and "updated" in (r.stdout or "").lower():
            getan.append("/watch")

    # Neu dazugekommene Faehigkeiten wirklich nachliefern: Wenn das
    # Kit ein Grafik-Werkzeug kennt, das hier fehlt, wird es beim
    # Update eingerichtet. Sonst waere "Update" ein leeres Wort -
    # der Nutzer bekaeme neue Skills, aber nicht das, was sie
    # brauchen (real passiert: Remotion kam in v0.43.0 dazu und
    # fehlte nach dem Update trotzdem).
    # Tempo-Wege nachziehen: fehlt onnxruntime, ist die Freistellung
    # unnoetig langsam und schlechter. Das Update muss das mitbringen.
    if befunde.get("freistellung", ("",))[0] != OK:
        besch = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "beschleunigen.py")
        print("Richte die schnellen Wege fuer die Freistellung ein ...")
        r = run([sys.executable, besch])
        (getan if r.returncode == 0 else offen).append("Beschleunigung")

    if befunde.get("grafik", ("",))[0] != OK:
        eigener = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "grafik_einrichten.py")
        print("Richte fehlende Grafik-Werkzeuge ein "
              "(laedt einige hundert MB) ...")
        r = run([sys.executable, eigener])
        (getan if r.returncode == 0 else offen).append("Grafik-Werkzeuge")

    return getan, offen


def zeile(name, zustand, zusatz=""):
    zeichen = {OK: "[ok]     ", ALT: "[alt]    ", FEHLT: "[fehlt]  ",
               UNKLAR: "[?]      "}.get(zustand, "[!]      ")
    print("  " + zeichen + name.ljust(22) + str(zusatz))


def main():
    p = argparse.ArgumentParser(description="Alles pruefen und aktualisieren")
    p.add_argument("--update", action="store_true",
                   help="veraltete Bestandteile gleich aktualisieren")
    a = p.parse_args()

    print("SCB Creator Kit - Rundum-Check")
    print("=" * 52)
    b = {}

    b["kit"] = pruefe_kit()
    zustand, inst, akt = b["kit"]

    quelle = quelle_des_kits()
    zusatz = inst + (" -> " + akt if zustand == ALT and akt else "")
    if quelle == "lokal":
        zusatz += " | aus Datei installiert - bekommt KEINE Updates"
    zeile("SCB Creator Kit", zustand, zusatz)

    b["rtk"] = pruefe_rtk()
    zustand, v, neu, hook = b["rtk"]
    if zustand == "HOOK FEHLT":
        zeile("Token-Sparer (RTK)", "!",
              v + " - installiert, aber NICHT aktiv (spart nichts)")
    else:
        zeile("Token-Sparer (RTK)", zustand,
              v + (" -> " + neu if zustand == ALT and neu else "")
              + (" | Hook aktiv" if hook else ""))

    b["watch"] = pruefe_watch()
    zeile("Video-Analyse /watch", b["watch"][0], b["watch"][1])

    print("")
    print("  Werkzeuge:")
    b["werkzeuge"] = pruefe_werkzeuge()
    for name, (zustand, info) in b["werkzeuge"].items():
        zeile("  " + name, zustand, info)

    print("")
    b["freistellung"] = pruefe_freistellung()
    zeile("Freistellung", b["freistellung"][0], b["freistellung"][1])
    b["grafik"] = pruefe_grafik()
    zeile("Grafik-Werkzeuge", b["grafik"][0], b["grafik"][1])
    b["keys"] = pruefe_keys()
    zeile("Transkriptions-Keys", b["keys"][0], b["keys"][1])

    zutun = []
    if b["kit"][0] == ALT:
        zutun.append("Kit aktualisieren")
    if b["rtk"][0] == "HOOK FEHLT":
        zutun.append("RTK aktivieren")
    elif b["rtk"][0] == ALT:
        zutun.append("RTK aktualisieren")
    for name, (zustand, _) in b["werkzeuge"].items():
        if zustand == FEHLT:
            zutun.append(name + " fehlt")

    print("")
    print("=" * 52)
    if not zutun:
        print("Alles auf dem neuesten Stand - nichts zu tun.")
        return 0

    print("Zu erledigen: " + ", ".join(zutun))
    if not a.update:
        print("")
        print("Zum Aktualisieren dasselbe Script mit --update aufrufen.")
        return 1

    print("")
    getan, offen = aktualisiere(b)
    print("")
    if getan:
        print("Aktualisiert: " + ", ".join(getan))
        print("WICHTIG: Claude Code einmal neu starten, damit alles greift.")
    if offen:
        print("NICHT geklappt: " + ", ".join(offen))
    fehlend = [n for n, (z, _) in b["werkzeuge"].items() if z == FEHLT]
    if fehlend:
        print("Fehlende Werkzeuge nachinstallieren mit: "
              "install_tools.py " + " ".join(fehlend))
    return 0 if getan and not offen else 1


if __name__ == "__main__":
    sys.exit(main())
