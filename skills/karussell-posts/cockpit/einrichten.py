"""Einrichtung des Karussell-Cockpits, fuer Windows und Mac.

    <python> einrichten.py                  pruefen, was fehlt (aendert nichts)
    <python> einrichten.py --pakete         fehlende Python-Pakete und den Browser installieren
    <python> einrichten.py --vorschlag      Vorschlag fuer den Karussell-Ordner zeigen
    <python> einrichten.py --ordner <pfad>  Karussell-Ordner festlegen und Startdatei hineinlegen
    <python> einrichten.py --modelle [schnell|genau|alle]
                                            Freisteller laden (180 MB / 973 MB), mit Pruefsumme
    <python> einrichten.py --startdatei     Doppelklick-Datei im Karussell-Ordner erneuern

Exit-Codes: 0 alles da · 1 Fehler · 2 Pflichtteil fehlt (Pakete, Browser, Ordner)
            · 3 nur die Freisteller fehlen (optional, Cockpit laeuft trotzdem)

Pakete: playwright, python-pptx, pillow, numpy, lxml, onnxruntime (Windows:
onnxruntime-directml wie im Setup-Assistenten). Ist schon irgendein onnxruntime
da, wird es nie ersetzt. Der Browser kommt ueber "playwright install chromium".
Freisteller-Modelle landen in ~/.scb-creator-kit/modelle (ausserhalb von
OneDrive und iCloud, gilt fuer alle Karussell-Ordner).
"""
import hashlib, importlib.util, os, platform, shutil, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

import projekt as P

PAKETE = [("playwright", "playwright"), ("pptx", "python-pptx"), ("PIL", "pillow"),
          ("numpy", "numpy"), ("lxml", "lxml"), ("certifi", "certifi")]
# Gleiche Wahl wie scb-setup/beschleunigen.py: Windows mit Grafikeinheit, sonst onnxruntime
# (der Freisteller rechnet auf dem Mac auf dem Prozessor)
ONNX = ("onnxruntime", "onnxruntime-directml" if platform.system() == "Windows" else "onnxruntime")
DOWNLOAD_HOSTS = {"github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}


def _da(modul):
    return importlib.util.find_spec(modul) is not None


def fehlende_pakete():
    fehlt = [pip for mod, pip in PAKETE if not _da(mod)]
    if not _da(ONNX[0]):
        fehlt.append(ONNX[1])
    return fehlt


def browser_da():
    if not _da("playwright"):
        return False
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            b.close()
        return True
    except Exception:
        return False


def pakete_installieren():
    fehlt = fehlende_pakete()
    if fehlt:
        print("Installiere:", ", ".join(fehlt))
        # 1. normal, 2. nur fuer diesen Benutzer, 3. Homebrew-Python (Mac, ab 3.12)
        #    sperrt beides ("externally-managed-environment"): dann ins
        #    Benutzerverzeichnis, das beruehrt Homebrews eigene Pakete nicht.
        for extra in ([], ["--user"], ["--user", "--break-system-packages"]):
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade"] + extra + fehlt,
                               capture_output=True, text=True, cwd=str(P.HIER))
            if r.returncode == 0:
                break
        if r.returncode != 0:
            print((r.stderr or r.stdout).strip()[-800:])
            return False
        # Frisch angelegtes Benutzerverzeichnis (pip --user) steht noch nicht im Suchpfad
        import site
        importlib.invalidate_caches()
        us = site.getusersitepackages()
        if site.ENABLE_USER_SITE and os.path.isdir(us) and us not in sys.path:
            site.addsitedir(us)
    if not browser_da():
        print("Installiere den Browser fuer den Export (Chromium, einmalig ~150 MB) ...")
        r = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], cwd=str(P.HIER))
        if r.returncode != 0:
            return False
    return not fehlende_pakete()


# ------------------------------------------------------------ Freisteller

def modell_ordner():
    return P.KIT_HOME / "modelle"


def modell_laden(modell, fortschritt=None):
    """Laedt genau die Datei aus freisteller.QUELLEN und prueft die
    SHA-256-Pruefsumme. Bricht ab, wenn der Platz nicht reicht."""
    import freisteller as F
    q = F.QUELLEN[modell]
    if F.pfad(modell):
        return F.pfad(modell)
    ordner = modell_ordner()
    ordner.mkdir(parents=True, exist_ok=True)
    noetig = q["mb"] * 1_000_000
    if shutil.disk_usage(ordner).free < noetig * 1.2:
        raise RuntimeError("Nicht genug Platz: der Freisteller braucht %d MB" % q["mb"])
    ziel = ordner / F.DATEIEN[modell]
    teil = ziel.with_name(ziel.name + ".teil")
    h = hashlib.sha256()
    gelesen = 0
    req = urllib.request.Request(q["url"], headers={"User-Agent": "scb-karussell-cockpit"})
    from urllib.parse import urlsplit
    try:
        with urllib.request.urlopen(req, timeout=60, context=P.ssl_kontext()) as r, open(teil, "wb") as f:
            if urlsplit(r.geturl()).hostname not in DOWNLOAD_HOSTS or urlsplit(r.geturl()).scheme != "https":
                raise RuntimeError("Download wurde zu einem fremden Server umgeleitet")
            gesamt = int(r.headers.get("Content-Length") or noetig)
            while True:
                stueck = r.read(1 << 20)
                if not stueck:
                    break
                gelesen += len(stueck)
                if gelesen > noetig * 1.1:
                    raise RuntimeError("Datei groesser als erwartet")
                h.update(stueck)
                f.write(stueck)
                if fortschritt:
                    fortschritt(gelesen, gesamt)
        if h.hexdigest() != q["sha256"]:
            raise RuntimeError("Pruefsumme stimmt nicht, Datei verworfen")
        os.replace(teil, ziel)
    except urllib.error.URLError as e:
        raise RuntimeError("Download nicht erreichbar, bitte Internet pruefen und noch einmal versuchen (%s)"
                           % getattr(e, "reason", e))
    finally:
        if teil.exists():                      # halbe oder falsche Datei nie liegen lassen
            teil.unlink()
    return ziel


# ------------------------------------------------------------ Startdatei

def startdatei():
    """Doppelklick-Datei in den Karussell-Ordner legen. Wird bei jedem
    Cockpit-Start erneuert, damit sie nach einem Kit-Update weiter stimmt.
    Wechselt zuerst in den Code-Ordner und sucht Python nie im Karussell-Ordner
    (dort koennten fremde Dateien liegen). Geschrieben ueber eine Zwischendatei,
    damit nie einer Verknuepfung gefolgt wird."""
    bauen = P.HIER / "bauen.py"
    if platform.system() == "Windows":
        ziel = P.DATEN / "Karussell Cockpit.bat"
        q = lambda x: str(x).replace("%", "%%")
        text = ('@echo off\r\n'
                'chcp 65001 >nul\r\n'
                'set NoDefaultCurrentDirectoryInExePath=1\r\n'
                'cd /d "{hier}"\r\n'
                'title Karussell Cockpit\r\n'
                'echo.\r\n'
                'echo   Karussell Cockpit - http://127.0.0.1:8720/cockpit.html\r\n'
                'echo   Dieses Fenster offen lassen. Schliessen beendet das Cockpit.\r\n'
                'echo.\r\n'
                'set "PY=python"\r\n'
                'if exist "{exe}" set "PY={exe}"\r\n'
                '"%PY%" "{bauen}" --cockpit\r\n'
                'pause\r\n').format(exe=q(sys.executable), hier=q(P.HIER), bauen=q(bauen))
        daten = text.encode("utf-8")
    else:
        import shlex
        ziel = P.DATEN / "Karussell Cockpit.command"
        # Nur ein Python, das die Pakete wirklich hat. /usr/bin/python3 ist ohne
        # Xcode-Werkzeuge nur ein Platzhalter, der einen Installationsdialog oeffnet.
        text = ('#!/bin/bash\n'
                'cd {hier} 2>/dev/null || {{ echo "Kit nicht gefunden - sag Claude: starte das Karussell-Cockpit."; '
                'read -n 1 -s -r -p "Zum Schliessen eine Taste druecken"; exit 1; }}\n'
                'echo "Karussell Cockpit - http://127.0.0.1:8720/cockpit.html"\n'
                'echo "Dieses Fenster offen lassen. Schliessen beendet das Cockpit."\n'
                'PY=""\n'
                'for K in {exe} python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do\n'
                '  command -v "$K" >/dev/null 2>&1 || continue\n'
                '  [ "$(command -v "$K")" = /usr/bin/python3 ] && ! xcode-select -p >/dev/null 2>&1 && continue\n'
                '  "$K" -c "import playwright, pptx, PIL" >/dev/null 2>&1 && PY="$K" && break\n'
                'done\n'
                'if [ -z "$PY" ]; then\n'
                '  echo "Python mit den Cockpit-Paketen nicht gefunden - sag Claude: richte das Karussell-Cockpit ein."\n'
                '  read -n 1 -s -r -p "Zum Schliessen eine Taste druecken"\n'
                '  exit 1\n'
                'fi\n'
                'exec "$PY" {bauen} --cockpit\n').format(exe=shlex.quote(sys.executable),
                                                     hier=shlex.quote(str(P.HIER)),
                                                     bauen=shlex.quote(str(bauen)))
        daten = text.encode("utf-8")
    P.DATEN.mkdir(parents=True, exist_ok=True)
    tmp = ziel.with_name(ziel.name + ".tmp")
    if tmp.is_symlink():
        tmp.unlink()
    tmp.write_bytes(daten)
    if platform.system() != "Windows":
        os.chmod(tmp, 0o755)
    os.replace(tmp, ziel)                      # ersetzt auch eine Verknuepfung, statt ihr zu folgen
    return ziel


# ------------------------------------------------------------ Pruefen

def pruefen():
    """-> (exitcode, zeilen)"""
    zeilen, code = [], 0
    if sys.version_info < (3, 9):
        zeilen.append("FEHLT  Python 3.9 oder neuer (gefunden %s)" % platform.python_version())
        code = 2
    else:
        zeilen.append("ok     Python %s" % platform.python_version())
    fehlt = fehlende_pakete()
    if fehlt:
        zeilen.append("FEHLT  Pakete: %s  (einrichten.py --pakete)" % ", ".join(fehlt)); code = 2
    else:
        zeilen.append("ok     Pakete")
    if not fehlt or "playwright" not in fehlt:
        if browser_da():
            zeilen.append("ok     Browser fuer den Export")
        else:
            zeilen.append("FEHLT  Browser fuer den Export  (einrichten.py --pakete)"); code = 2
    if P.einstellungen_kaputt():
        zeilen.append("FEHLT  %s ist beschaedigt (kein gueltiges JSON), erst reparieren" % P.EINST)
        code = 2
    elif P.gesetzt():
        zeilen.append("ok     Karussell-Ordner: %s" % P.DATEN)
    else:
        zeilen.append("FEHLT  Karussell-Ordner (Vorschlag: %s)  (einrichten.py --ordner <pfad>)"
                      % P.vorschlag())
        code = 2
    try:
        import freisteller as F
        da = F.vorhanden()
        for m in F.DATEIEN:
            zeilen.append(("ok     Freisteller %s" if m in da else
                           "fehlt  Freisteller %s (optional, %d MB, laedt auch per Knopf im Cockpit)")
                          % ((m,) if m in da else (m, F.QUELLEN[m]["mb"])))
        if code == 0 and len(da) < len(F.DATEIEN):
            code = 3
    except Exception as e:
        zeilen.append("fehlt  Freisteller (%s)" % str(e)[:80])
        code = code or 3
    return code, zeilen


def main(a):
    if "--pakete" in a:
        ok = pakete_installieren()
        print("Pakete und Browser: fertig." if ok else "Installation ging nicht vollstaendig.")
        sys.exit(0 if ok else 1)
    if "--vorschlag" in a:
        print(P.vorschlag()); return
    if "--ordner" in a:
        i = a.index("--ordner")
        pfad = a[i + 1] if i + 1 < len(a) and not a[i + 1].startswith("--") else P.vorschlag()
        p = P.ordner_setzen(pfad)
        print("Karussell-Ordner:", p)
        print("Startdatei:", startdatei())
        return
    if "--startdatei" in a:
        print(startdatei()); return
    if "--modelle" in a:
        i = a.index("--modelle")
        wahl = a[i + 1] if i + 1 < len(a) else "schnell"
        import freisteller as F
        liste = list(F.DATEIEN) if wahl == "alle" else [F.name_von(wahl)]
        for m in liste:
            letzte = [-1]

            def zeige(n, g, m=m):
                pz = int(n * 100 / max(1, g))
                if pz != letzte[0] and pz % 10 == 0:
                    print("  %s: %d %%" % (m, pz), flush=True); letzte[0] = pz
            print("Freisteller %s:" % m, modell_laden(m, zeige))
        return
    code, zeilen = pruefen()
    print("\n".join(zeilen))
    sys.exit(code)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
