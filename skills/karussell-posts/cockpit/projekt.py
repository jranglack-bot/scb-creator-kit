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
import json, os, re, shutil, stat, tempfile, time, unicodedata
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
    global DATEN, PROJEKTE, AKTUELL, EXPORT, VORLAGEN, SCHRIFTEN, AUFTRAEGE, MODELLE, PAPIERKORB
    DATEN     = daten
    PROJEKTE  = DATEN / "projekte"
    AKTUELL   = PROJEKTE / "aktuell.txt"
    EXPORT    = DATEN / "export"
    VORLAGEN  = DATEN / "vorlagen"                 # eigene Vorlagen
    SCHRIFTEN = DATEN / "schriften"                # google.css, google.json, google/<ordner>/
    AUFTRAEGE = DATEN / ".auftraege"               # nie im Projektordner: kein Projekt bringt einen mit
    MODELLE   = [DATEN / "modelle", KIT_HOME / "modelle"]
    PAPIERKORB = DATEN / "papierkorb"              # geloeschte Karussells samt Ausgabe, zurueckholbar


_pfade(_datenordner())
VORLAGEN_KIT = HIER / "vorlagen"                    # mitgelieferte Vorlagen, nur lesen
VORSCHAU = ".vorschau.png"                          # reservierter Name, kollidiert mit keinem Bild
FOLIEN = ".folien.png"                              # alle Folien einer Vorlage als Streifen

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
DATENARTEN = {".json", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".txt", ".mp4"}   # .mp4: Videos (video.py)


def datei_ok(roh):
    roh = str(roh or "")
    if len(roh) > 200 or not DATEI.fullmatch(roh) or any(geraet(t) for t in roh.split("/")):
        raise ValueError("ungueltiger Dateiname: %r" % roh[:60])
    return roh

STIL_STD = {"breite": 1080, "hoehe": 1350, "bg": "#dee3e7", "text": "#313538",
            "akzent": "#718d81", "schrift": "Montserrat",
            "randX": 132, "randOben": 354, "randUnten": 94,
            "titel": 84, "textgroesse": 40, "titelAbstand": 1.17, "textAbstand": 1.42}

# Breite und Schriftgroessen bleiben, nur Hoehe und Abstaende gehen mit.
FORMATE = {"45": {"hoehe": 1350, "randOben": 354, "randUnten": 94},
           "34": {"hoehe": 1440, "randOben": 377, "randUnten": 100},
           "916": {"hoehe": 1920, "randOben": 420, "randUnten": 330}}     # Story, Reel-Titelbild


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


def sicher_schreiben(ziel, roh):
    """Datei ersetzen statt ueberschreiben: erst vollstaendig in eine neue Zwischendatei
    im selben Ordner (mkstemp folgt keiner Verknuepfung), dann os.replace. Geht etwas
    schief, bleibt das Original. Nie durch eine Verknuepfung hindurch."""
    ziel = Path(ziel)
    if ziel.is_symlink():
        raise ValueError("%s ist eine Verknuepfung" % ziel.name)
    fd, tmp = tempfile.mkstemp(dir=str(ziel.parent), prefix="." + ziel.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(roh)
        for versuch in range(40):            # Windows: kurz gesperrt, solange jemand liest
            try:
                os.replace(tmp, ziel)
                return
            except PermissionError:
                if versuch == 39:
                    raise
                time.sleep(0.05)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _endlich(o, tiefe=0):
    """inf und nan (etwa aus 1e400 in einer fremden Datei) werden 0, sonst entsteht ungueltiges JSON."""
    if isinstance(o, float):
        return o if o == o and o not in (float("inf"), float("-inf")) else 0
    if tiefe > 60:
        return o
    if isinstance(o, dict):
        return {k: _endlich(v, tiefe + 1) for k, v in o.items()}
    if isinstance(o, list):
        return [_endlich(v, tiefe + 1) for v in o]
    return o


def json_bytes(daten):
    """Ganz kodieren, bevor irgendetwas geschrieben wird. Einzelne Surrogate aus fremden
    Dateien gehen dann als \\u-Folgen hinaus, statt mitten im Schreiben abzubrechen."""
    daten = _endlich(daten)
    try:
        return json.dumps(daten, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
    except UnicodeEncodeError:
        return json.dumps(daten, ensure_ascii=True, indent=2, allow_nan=False).encode("ascii")


def schreiben(daten, name=None):
    sicher_schreiben(ordner(name) / "inhalt.json", json_bytes(daten))


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


SERIE_MAX = 30          # Karussells je Serie, wie SERIE_MAX_KARUSSELLS in render.js


def frei_name(name):
    """Wie _frei, vergibt aber selbst den naechsten freien Namen (name, name-2, name-3 ...)."""
    basis = slug(name)[:55].strip("-")
    if not basis:
        raise ValueError("Bitte einen Namen eingeben.")
    for i in range(1, 1000):
        n = basis if i == 1 else "%s-%d" % (basis, i)
        if not (PROJEKTE / n).exists():
            return n
    raise ValueError("Kein freier Name fuer %s" % basis)


def serie_anlegen(von, karussells):
    """Massenerstellung: je Eintrag {"name", "slides"} ein neues Karussell mit Look und
    Bildern der Vorlage (von) und den fertig gerechneten Folien (render.js, serieBauen).
    Gibt die angelegten Namen zurueck. Geht eins schief, kommen alle wieder weg."""
    if not isinstance(karussells, list) or not 1 <= len(karussells) <= SERIE_MAX:
        raise ValueError("1 bis %d Karussells je Serie" % SERIE_MAX)
    for k in karussells:
        if not (isinstance(k, dict) and isinstance(k.get("name"), str) and isinstance(k.get("slides"), list)
                and 1 <= len(k["slides"]) <= 100 and all(isinstance(s, dict) for s in k["slides"])):
            raise ValueError("ungueltige Serie")
    quelle = ordner(von)
    # Alles ausser Folien, Tabelle und Vorlagen-Info kommt aus der Vorlage (stil ...)
    kopf = {k: v for k, v in lesen(von).items() if k not in ("slides", "serie", "vorlage")}
    namen = []
    try:
        for k in karussells:
            n = frei_name(k["name"])
            ziel = PROJEKTE / n
            ziel.mkdir()                       # exklusiv: ab hier gehoert der Ordner dieser Serie
            namen.append(n)
            daten = dict(kopf, slides=k["slides"])
            benutzt = set()
            _texte_in(daten, benutzt)
            daten_filter = _nur_daten(".raster", "schriftprobe.png", "auftrag.json")

            def weg(ordner_, namen_, benutzt=benutzt, daten_filter=daten_filter):
                # Nur Bilder mitnehmen, die das neue Karussell auch zeigt (die Vorlage
                # sammelt die Bilder aller Zeilen), alle anderen Daten wie beim Duplizieren
                aus = set(daten_filter(ordner_, namen_))
                rel = Path(ordner_).relative_to(quelle)
                for x in namen_:
                    p = Path(ordner_) / x
                    r = (rel / x).as_posix()
                    if r.endswith('.mp4.jpg') and r[:-4] in benutzt:
                        continue                   # Standbild eines benutzten Videos
                    if p.suffix.lower() in BILDARTEN and p.is_file() and r not in benutzt:
                        aus.add(x)
                return aus
            shutil.copytree(quelle, ziel, ignore=weg, dirs_exist_ok=True)
            schreiben(daten, n)
    except BaseException:
        for n in namen:
            shutil.rmtree(PROJEKTE / n, ignore_errors=True)
        raise
    return namen


BILDARTEN = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4"}


def _texte_in(o, aus, tiefe=0):
    """Alle Zeichenketten in verschachtelten Daten: Bilddateien stehen in verschiedenen
    Feldern (datei, original, bildfuellung, hg.datei ...)."""
    if tiefe > 40:
        return
    if isinstance(o, str):
        aus.add(o)
    elif isinstance(o, dict):
        for v in o.values():
            _texte_in(v, aus, tiefe + 1)
    elif isinstance(o, list):
        for v in o:
            _texte_in(v, aus, tiefe + 1)


# ------------------------------------------------------------ Papierkorb
# Loeschen verschiebt nur: papierkorb/<name>__<zeit>/ mit projekt/, export/ (falls da)
# und info.json. Zurueckholen geht, bis der User den Papierkorb im Cockpit leert.

EINTRAG = re.compile(r"[a-z0-9][a-z0-9-]{0,59}__\d{8}-\d{6}(-\d{1,3})?")


def in_papierkorb(name):
    """Ein Karussell samt seinen fertigen Bildern in den Papierkorb. Gibt den Eintrag zurueck."""
    quelle = ordner(name)                       # nur gueltige, vorhandene Projekte
    if _verknuepft(quelle):
        raise ValueError("%s ist eine Verknuepfung" % quelle.name)
    try:
        slides = len(lesen(quelle.name).get("slides") or [])
    except (OSError, ValueError, AttributeError):
        slides = 0
    PAPIERKORB.mkdir(parents=True, exist_ok=True)
    basis = "%s__%s" % (quelle.name, time.strftime("%Y%m%d-%H%M%S"))
    eintrag, n = basis, 2
    while (PAPIERKORB / eintrag).exists():
        eintrag = "%s-%d" % (basis, n); n += 1
    ziel = PAPIERKORB / eintrag
    ziel.mkdir()
    try:
        shutil.move(str(quelle), str(ziel / "projekt"))
    except OSError:
        shutil.rmtree(ziel, ignore_errors=True)
        raise ValueError("%s laesst sich gerade nicht verschieben (ist eine Datei daraus noch offen?)" % quelle.name)
    ex = EXPORT / quelle.name
    if ex.is_dir() and not _verknuepft(ex):
        try:
            shutil.move(str(ex), str(ziel / "export"))
        except OSError:
            pass                                # dann bleiben nur die fertigen Bilder liegen
    try:
        (AUFTRAEGE / (quelle.name + ".json")).unlink()
    except OSError:
        pass
    (ziel / "info.json").write_text(json.dumps({"name": quelle.name, "slides": slides,
                                                "geloescht": time.strftime("%Y-%m-%d %H:%M")},
                                               ensure_ascii=False), encoding="utf-8")
    try:
        if AKTUELL.read_text(encoding="utf-8").strip() == quelle.name:
            rest = liste()
            if rest:
                AKTUELL.write_text(rest[0], encoding="utf-8")
            else:
                AKTUELL.unlink()
    except OSError:
        pass
    return eintrag


def _eintrag_ordner(eintrag):
    if not isinstance(eintrag, str) or not EINTRAG.fullmatch(eintrag):
        raise ValueError("unbekannter Eintrag im Papierkorb")
    o = PAPIERKORB / eintrag
    if not o.is_dir() or _verknuepft(o):
        raise ValueError("Eintrag gibt es nicht mehr")
    return o


def papierkorb():
    """[{eintrag, name, slides, geloescht, mb}], neueste zuerst."""
    if not PAPIERKORB.is_dir():
        return []
    aus = []
    for o in PAPIERKORB.iterdir():
        if not (o.is_dir() and EINTRAG.fullmatch(o.name)) or _verknuepft(o):
            continue
        try:
            i = json.loads((o / "info.json").read_text(encoding="utf-8"))
            i = i if isinstance(i, dict) else {}
        except (OSError, ValueError):
            i = {}
        groesse = 0
        for wurzel, _, dateien in os.walk(o):
            for d in dateien:
                try:
                    groesse += os.path.getsize(os.path.join(wurzel, d))
                except OSError:
                    pass
        aus.append({"eintrag": o.name, "name": kurztext(i.get("name"), 60) or o.name.split("__")[0],
                    "slides": int(i.get("slides") or 0) if str(i.get("slides", "")).isdigit() else 0,
                    "geloescht": kurztext(i.get("geloescht"), 20), "mb": round(groesse / 1e6, 1)})
    return sorted(aus, key=lambda x: x["eintrag"].split("__")[-1], reverse=True)


def zurueckholen(eintrag):
    """Zurueck nach projekte/ (bei Namensgleichheit mit -2 ...), fertige Bilder wieder nach export/."""
    o = _eintrag_ordner(eintrag)
    if not (o / "projekt" / "inhalt.json").is_file():
        raise ValueError("Im Eintrag fehlt das Karussell")
    n = frei_name(eintrag.split("__")[0])
    shutil.move(str(o / "projekt"), str(PROJEKTE / n))
    if (o / "export").is_dir() and not (EXPORT / n).exists():
        EXPORT.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(o / "export"), str(EXPORT / n))
        except OSError:
            pass
    shutil.rmtree(o, ignore_errors=True)
    return n


def papierkorb_leeren(eintraege=None):
    """Endgueltig loeschen: alle oder die genannten Eintraege. Nur auf Wunsch des Users."""
    ziele = [_eintrag_ordner(e) for e in eintraege] if eintraege else \
            [_eintrag_ordner(x["eintrag"]) for x in papierkorb()]
    for o in ziele:
        shutil.rmtree(o, ignore_errors=True)
    return len(ziele)


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
    _ohne_vorlagen_info(VORLAGEN / n)
    return n


def neu_aus_vorlage(name, vorlage):
    q = vorlage_ordner(vorlage)
    if q is None:
        raise ValueError("Vorlage gibt es nicht: %s" % vorlage)
    n = _frei(name)
    shutil.copytree(q, PROJEKTE / n, ignore=_nur_daten(VORSCHAU, FOLIEN, *_NICHT_MIT))
    _ohne_vorlagen_info(PROJEKTE / n)
    return n


def _ohne_vorlagen_info(o):
    """Titel und Beschreibung gehoeren zur Vorlage, nicht zum neuen Projekt
    (sonst traegt eine daraus gespeicherte eigene Vorlage den fremden Titel).
    Erst fertig in eine Zwischendatei, dann ersetzen: Geht etwas schief (kaputtes
    JSON, einzelne Surrogate, 1e400), bleibt die frische Kopie unveraendert."""
    p = o / "inhalt.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        if not (isinstance(d, dict) and ("vorlage" in d or "serie" in d)):
            return
        d.pop("vorlage", None)
        d.pop("serie", None)                    # Tabelle einer Serie: Inhalt, kein Teil der Vorlage
        sicher_schreiben(p, json_bytes(d))
    except Exception:
        pass


# Unsichtbares und Kaputtes aus fremden kurzen Texten (Titel, Beschreibung):
# Steuer-, Format- und Privatzeichen, einzelne Surrogate, Tag-Zeichen, Variantenwaehler
_UNSICHTBAR = {"Cc", "Cf", "Cs", "Co", "Cn"}


def kurztext(v, n):
    """Kurzer sichtbarer Text, Leerraum zusammengefasst, hoechstens n Zeichen."""
    if not isinstance(v, str):
        return ""
    teile = []
    for c in v[:4 * n]:                     # erst kuerzen: riesige Texte kosten sonst Sekunden
        o = ord(c)
        if c.isspace() or unicodedata.category(c) in ("Zl", "Zp"):
            teile.append(" ")
        elif unicodedata.category(c) in _UNSICHTBAR or 0xFE00 <= o <= 0xFE0F or \
                0xE0100 <= o <= 0xE01EF or 0x180B <= o <= 0x180F:
            continue
        else:
            teile.append(c)
    return " ".join("".join(teile).split())[:n]


def aus_argv(argv):
    """--projekt name aus der Kommandozeile, sonst das aktuelle."""
    if "--projekt" in argv:
        i = argv.index("--projekt")
        if i + 1 < len(argv):
            return argv[i + 1]
    return None
