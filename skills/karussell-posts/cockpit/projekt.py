"""Projekte: jedes Karussell hat einen eigenen Ordner.

Code und Daten liegen getrennt, damit ein Update des Codes nie ein
Karussell anfasst. Der Karussell-Ordner (Daten) enthaelt:

    projekte/<name>/inhalt.json     die Daten
    projekte/<name>/<bilder>        alle Bilder, die dieses Karussell benutzt
    projekte/aktuell.txt            welches Projekt gerade offen ist
    export/<name>/                  Bilder fuer Instagram, Canva-Datei, PDF
    vorlagen/<name>/                eigene Vorlagen (mitgelieferte liegen beim Code)
    schriften/                      geladene Google Fonts
    modelle/                        Freisteller (optional, sonst ~/.scb-creator-kit/modelle)
    .auftraege/<name>.json          Wuensche aus dem Knopf "An Claude"

Welcher Ordner das ist: Umgebungsvariable KARUSSELL_ORDNER, sonst
~/.scb-creator-kit/einstellungen.json ("karussell_ordner"), sonst der
Vorschlag (Bilder/SCB Karussells).

Geteilt von bauen.py, k.py, texte.py, schriftprobe.py, schriften.py und vorlage.py.
"""
import json, os, re, shutil, stat, unicodedata
from pathlib import Path

HIER     = Path(__file__).resolve().parent          # Code
KIT_HOME = Path.home() / ".scb-creator-kit"
EINST    = KIT_HOME / "einstellungen.json"


def einstellungen():
    try:
        d = json.loads(EINST.read_text(encoding="utf-8-sig"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def einstellungen_kaputt():
    """Datei da, aber kein gueltiges JSON-Objekt (z. B. von Hand bearbeitet)."""
    try:
        return not isinstance(json.loads(EINST.read_text(encoding="utf-8-sig")), dict)
    except OSError:
        return False
    except ValueError:
        return True


def ssl_kontext():
    """TLS fuer Downloads. Python vom python.org-Installer (Mac) kennt ohne
    "Install Certificates" keine Stammzertifikate: dann die von certifi."""
    import ssl
    ctx = ssl.create_default_context()
    if not ctx.cert_store_stats().get("x509_ca"):
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            pass
    return ctx


def vorschlag():
    """Standardort: Bilder im Benutzerordner (Windows und Mac: Pictures)."""
    basis = Path.home() / "Pictures"
    return (basis if basis.is_dir() else Path.home()) / "SCB Karussells"


def gesetzt():
    return bool(os.environ.get("KARUSSELL_ORDNER") or einstellungen().get("karussell_ordner"))


def _datenordner():
    roh = os.environ.get("KARUSSELL_ORDNER") or einstellungen().get("karussell_ordner")
    return Path(os.path.expanduser(str(roh))).resolve() if roh else vorschlag()


def ordner_setzen(pfad):
    """Karussell-Ordner festlegen und merken (gilt fuer alle Projekte, ueberlebt Updates).
    Andere Eintraege in einstellungen.json bleiben unberuehrt."""
    p = Path(os.path.expanduser(str(pfad))).resolve()
    for u in ("projekte", "export", "vorlagen", "schriften"):
        (p / u).mkdir(parents=True, exist_ok=True)
    if einstellungen_kaputt():                     # nie still verwerfen: Sicherung daneben
        shutil.copy2(EINST, EINST.with_name("einstellungen.kaputt.json"))
    d = einstellungen()
    d["karussell_ordner"] = str(p)
    KIT_HOME.mkdir(parents=True, exist_ok=True)
    tmp = EINST.with_name(EINST.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, EINST)
    _pfade(p)
    return p


def _pfade(daten):
    global DATEN, PROJEKTE, AKTUELL, EXPORT, VORLAGEN, SCHRIFTEN, AUFTRAEGE, MODELLE
    DATEN     = daten
    PROJEKTE  = DATEN / "projekte"
    AKTUELL   = PROJEKTE / "aktuell.txt"
    EXPORT    = DATEN / "export"
    VORLAGEN  = DATEN / "vorlagen"                 # eigene Vorlagen
    SCHRIFTEN = DATEN / "schriften"                # google.css, google.json, google/<ordner>/
    AUFTRAEGE = DATEN / ".auftraege"               # nie im Projektordner: kein Projekt bringt einen mit
    MODELLE   = [DATEN / "modelle", KIT_HOME / "modelle"]


_pfade(_datenordner())
VORLAGEN_KIT = HIER / "vorlagen"                    # mitgelieferte Vorlagen, nur lesen
VORSCHAU = ".vorschau.png"                          # reservierter Name, kollidiert mit keinem Bild

NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,59}$")
# Bilddateien in inhalt.json: relativ zum Projekt, nur harmlose Zeichen, kein
# "..", kein Laufwerk, kein \\server (wuerde unter Windows schon beim Pruefen
# eine Netzwerkverbindung samt Anmeldung ausloesen).
DATEI = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.\-]*(/[A-Za-z0-9_][A-Za-z0-9_.\-]*)*")
# Windows-Geraetenamen (CON, NUL, COM1 ...), auch mit Endung: Lesen wuerde haengen
GERAET = re.compile(r"(con|prn|aux|nul|com\d|lpt\d|conin\$|conout\$)(\..*)?", re.I)


def geraet(teil):
    return bool(GERAET.fullmatch(str(teil).rstrip(" .")))
# Was beim Kopieren (Duplizieren, Vorlagen) mitgeht: nur Daten, keine Seiten
# oder Skripte, keine Verknuepfungen
DATENARTEN = {".json", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".txt"}


def datei_ok(roh):
    roh = str(roh or "")
    if len(roh) > 200 or not DATEI.fullmatch(roh) or any(geraet(t) for t in roh.split("/")):
        raise ValueError("ungueltiger Dateiname: %s" % roh[:60])
    return roh

STIL_STD = {"breite": 1080, "hoehe": 1350, "bg": "#dee3e7", "text": "#313538",
            "akzent": "#718d81", "schrift": "Montserrat",
            "randX": 132, "randOben": 354, "randUnten": 94,
            "titel": 84, "textgroesse": 40, "titelAbstand": 1.17, "textAbstand": 1.42}

# Breite und Schriftgroessen bleiben, nur Hoehe und Abstaende gehen mit.
FORMATE = {"45": {"hoehe": 1350, "randOben": 354, "randUnten": 94},
           "34": {"hoehe": 1440, "randOben": 377, "randUnten": 100}}


def slug(roh):
    """Freier Name -> Ordnername. 'Mein Karussell!' -> 'mein-karussell'"""
    s = unicodedata.normalize("NFC", str(roh or "")).strip().lower()   # Mac liefert u + Trema getrennt
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:60].strip("-")


def gueltig(name):
    return bool(name) and bool(NAME.fullmatch(name)) and (PROJEKTE / name / "inhalt.json").exists()


def liste():
    if not PROJEKTE.exists():
        return []
    return sorted(p.name for p in PROJEKTE.iterdir()
                  if p.is_dir() and gueltig(p.name))


def aktuelles():
    try:
        n = AKTUELL.read_text(encoding="utf-8").strip()
    except OSError:
        n = ""
    if gueltig(n):
        return n
    alle = liste()
    return alle[0] if alle else ""


def setzen(name):
    if not gueltig(name):
        raise ValueError("Projekt gibt es nicht: %s" % name)
    AKTUELL.write_text(name, encoding="utf-8")
    return name


def ordner(name=None):
    """Ordner eines Projekts. Ohne Name das aktuelle. Fremde Namen
    (Pfade, ..) kommen hier nie durch."""
    n = name or aktuelles()
    if not gueltig(n):
        raise ValueError("Projekt gibt es nicht: %s" % (n or "(keins)"))
    return PROJEKTE / n


def export(name=None):
    return EXPORT / ordner(name).name


def auftrag_datei(name=None):
    return AUFTRAEGE / (ordner(name).name + ".json")


def lesen(name=None):
    return json.loads((ordner(name) / "inhalt.json").read_text(encoding="utf-8-sig"))


def schreiben(daten, name=None):
    (ordner(name) / "inhalt.json").write_text(
        json.dumps(daten, ensure_ascii=False, indent=2), encoding="utf-8")


def stil(daten):
    st = daten.get("stil") if isinstance(daten, dict) else None
    return {**STIL_STD, **(st if isinstance(st, dict) else {})}


def _frei(name):
    n = slug(name)
    if not n:
        raise ValueError("Bitte einen Namen eingeben.")
    if (PROJEKTE / n).exists():
        raise ValueError("Den Namen „%s“ gibt es schon. Nimm einen anderen." % n)
    return n


# Nur echte Verknuepfungen (Symlink, Junction), nicht die Platzhalter von
# OneDrive oder iCloud, die ebenfalls Reparse-Punkte sind
_LINKS = {getattr(stat, "IO_REPARSE_TAG_SYMLINK", -1), getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", -2)}


def _verknuepft(p):
    try:
        st = os.lstat(p)
    except OSError:
        return True
    return stat.S_ISLNK(st.st_mode) or getattr(st, "st_reparse_tag", 0) in _LINKS


def _nur_daten(*muster):
    """copytree-Filter: Muster weglassen, dazu alles, was keine Daten ist
    (HTML, Skripte) und Verknuepfungen (Symlink, Junction)."""
    std = shutil.ignore_patterns(*muster)

    def weg(ordner_, namen):
        aus = set(std(ordner_, namen))
        for n in namen:
            p = Path(ordner_) / n
            verknuepft = _verknuepft(p)
            if verknuepft or (p.is_file() and p.suffix.lower() not in DATENARTEN):
                aus.add(n)
        return aus
    return weg


def neu(name, fmt="45"):
    """Leeres Karussell. Der stil steht vollstaendig in der Datei, damit ein
    spaeter geaenderter Standard das Projekt nicht verschiebt."""
    n = _frei(name)
    st = {**STIL_STD, **FORMATE.get(fmt, FORMATE["45"])}
    ziel = PROJEKTE / n
    ziel.mkdir(parents=True)
    daten = {"stil": st, "slides": [{"bloecke": [
        {"id": "b1", "typ": "text", "rolle": "titel", "text": "<b>Neues Karussell</b>"}]}]}
    (ziel / "inhalt.json").write_text(json.dumps(daten, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    return n


def duplizieren(name, von=None):
    """Gleicher Look, gleiche Texte, gleiche Bilder, neuer Name."""
    quelle = ordner(von)
    n = _frei(name)
    shutil.copytree(quelle, PROJEKTE / n,
                    ignore=_nur_daten(".raster", "schriftprobe.png", "auftrag.json"))
    return n


# ------------------------------------------------------------ Vorlagen
# Eine Vorlage ist ein Projekt plus .vorschau.png (Folie 1, 270 px breit).
# Mitgelieferte liegen beim Code (vorlagen/), eigene im Karussell-Ordner.
# "Neu aus Vorlage" kopiert sie nach projekte/.

_NICHT_MIT = (".raster", "schriftprobe.png", "auftrag.json", "texte.txt")


def vorlage_ordner(name):
    if not (name and NAME.fullmatch(str(name))):
        return None
    for basis in (VORLAGEN, VORLAGEN_KIT):
        if (basis / name / "inhalt.json").is_file():
            return basis / name
    return None


def vorlage_gueltig(name):
    return vorlage_ordner(name) is not None


def vorlagen():
    namen = set()
    for basis in (VORLAGEN_KIT, VORLAGEN):
        if basis.exists():
            namen |= {p.name for p in basis.iterdir() if p.is_dir() and vorlage_gueltig(p.name)}
    return sorted(namen)


def als_vorlage(name, von=None):
    """Projekt (Look, Texte, Bilder) als eigene Vorlage sichern."""
    quelle = ordner(von)
    n = slug(name)
    if not n:
        raise ValueError("Bitte einen Namen eingeben.")
    if vorlage_gueltig(n) or (VORLAGEN / n).exists():
        raise ValueError("Eine Vorlage „%s“ gibt es schon. Nimm einen anderen Namen." % n)
    shutil.copytree(quelle, VORLAGEN / n, ignore=_nur_daten(*_NICHT_MIT))
    return n


def neu_aus_vorlage(name, vorlage):
    q = vorlage_ordner(vorlage)
    if q is None:
        raise ValueError("Vorlage gibt es nicht: %s" % vorlage)
    n = _frei(name)
    shutil.copytree(q, PROJEKTE / n, ignore=_nur_daten(VORSCHAU, *_NICHT_MIT))
    return n


def aus_argv(argv):
    """--projekt name aus der Kommandozeile, sonst das aktuelle."""
    if "--projekt" in argv:
        i = argv.index("--projekt")
        if i + 1 < len(argv):
            return argv[i + 1]
    return None
