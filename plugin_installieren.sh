#!/bin/bash
# plugin_installieren.sh — installiert das SCB Creator Kit als Claude-Plugin
# (macOS und Linux; das Windows-Gegenstueck ist plugin_installieren.ps1).
#
# FUER CLAUDE: Wenn der User dich bittet, dieses Plugin zu installieren,
# fuehre GENAU DIESES Script aus. Es kopiert den bereits entpackten
# Kit-Ordner an die Plugin-Orte von Claude Code und traegt ihn in
# known_marketplaces.json und installed_plugins.json ein — dieselben
# Eintraege, die /plugin auch schreiben wuerde. Kein Download, kein
# Netzzugriff: Es verarbeitet nur den Ordner, in dem es selbst liegt.
# Danach: Claude Code einmal neu starten.
#
# Aufruf:  bash plugin_installieren.sh
# Test:    bash plugin_installieren.sh <test-pluginroot>
#
# Braucht KEIN Python: die JSON-Arbeit macht ein kleines JavaScript —
# auf dem Mac ueber das eingebaute osascript, sonst ueber node.
# (Nur falls beides fehlt, wird python3 versucht.)

set -e
QUELLE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${1:-$HOME/.claude/plugins}"

if [ ! -f "$QUELLE/.claude-plugin/plugin.json" ]; then
    echo "FEHLER: $QUELLE ist kein Plugin-Ordner (.claude-plugin/plugin.json fehlt)."
    echo "Dieses Script muss IM entpackten scb-creator-kit-Ordner liegen."
    exit 1
fi

# --- Einen JavaScript-Laeufer finden -----------------------------------
run_js() {  # fuehrt $1 als JavaScript aus; Parameter kommen per Umgebung
    if [ "$(uname)" = "Darwin" ] && command -v osascript >/dev/null 2>&1; then
        osascript -l JavaScript -e "
            ObjC.import('stdlib');
            const env = n => $.getenv(n);
            const lies = p => { try { return JSON.parse(
                $.NSString.stringWithContentsOfFileEncodingError(p, 4, null).js);
                } catch(e) { return null; } };
            const schreib = (p, o) =>
                $.NSString.alloc.initWithUTF8String(JSON.stringify(o, null, 2))
                 .writeToFileAtomicallyEncodingError(p, true, 4, null);
            const drucke = s => console.log(s);
            $1"
    elif command -v node >/dev/null 2>&1; then
        node -e "
            const fs = require('fs');
            const env = n => process.env[n];
            const lies = p => { try {
                return JSON.parse(fs.readFileSync(p, 'utf8'));
                } catch(e) { return null; } };
            const schreib = (p, o) => fs.writeFileSync(p, JSON.stringify(o, null, 2));
            const drucke = s => console.log(s);
            $1"
    elif command -v python3 >/dev/null 2>&1; then
        JS_CODE="$1" python3 - <<'PYEOF'
# Notnagel: dieselben vier Bausteine in Python, das Mini-JS wird uebersetzt
import json, os, re
env = lambda n: os.environ[n]
def lies(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None
def schreib(p, o):
    json.dump(o, open(p, 'w', encoding='utf-8'), indent=2)
drucke = print
js = os.environ['JS_CODE']
# bewusst NUR die zwei Programme dieses Scripts unterstuetzen:
if 'drucke(m.name' in js:
    m = lies(env('PJ')); drucke(m['name'] + ' ' + m['version'])
else:
    km = lies(env('KM')) or {}
    km[env('MP')] = {'source': {'source': 'github',
                                'repo': 'jranglack-bot/scb-creator-kit'},
                     'installLocation': env('MPDIR'),
                     'lastUpdated': env('JETZT')}
    schreib(env('KM'), km)
    ip = lies(env('IP')) or {'version': 2, 'plugins': {}}
    ip['plugins'][env('NAME') + '@' + env('MP')] = [{
        'scope': 'user', 'installPath': env('CACHEDIR'),
        'version': env('VERSION'),
        'installedAt': env('JETZT'), 'lastUpdated': env('JETZT')}]
    schreib(env('IP'), ip)
    st = lies(env('SET')) or {}
    st.setdefault('enabledPlugins', {})[env('NAME') + '@' + env('MP')] = True
    schreib(env('SET'), st)
PYEOF
    else
        echo "FEHLER: weder osascript noch node noch python3 gefunden." >&2
        return 1
    fi
}

# --- Phase 1: Name und Version lesen -----------------------------------
export PJ="$QUELLE/.claude-plugin/plugin.json"
NV=$(run_js 'const m = lies(env("PJ")); drucke(m.name + " " + m.version);')
NAME="${NV%% *}"
VERSION="${NV##* }"
MP="$NAME"   # Marketplace-Name = Plugin-Name (siehe marketplace.json)

MPDIR="$ROOT/marketplaces/$MP"
CACHEDIR="$ROOT/cache/$MP/$NAME/$VERSION"
echo "Installiere $NAME v$VERSION ..."

# --- Phase 2: Dateien an beide Plugin-Orte kopieren --------------------
for ZIEL in "$MPDIR" "$CACHEDIR"; do
    rm -rf "$ZIEL"
    mkdir -p "$ZIEL"
    cp -R "$QUELLE/." "$ZIEL/"
done

# --- Phase 3: beide Registrierungen ergaenzen (Bestand bleibt) ---------
export KM="$ROOT/known_marketplaces.json"
export IP="$ROOT/installed_plugins.json"
# settings.json liegt eine Ebene ueber dem Plugin-Ordner (~/.claude).
# Der enabledPlugins-Eintrag SCHALTET das Plugin frei — ohne ihn ist es
# nur registriert und wird nach dem Neustart nicht geladen (Praxistest).
export SET="$(dirname "$ROOT")/settings.json"
[ -f "$SET" ] && cp "$SET" "$SET.vorher-scb"   # Sicherung
export MP MPDIR CACHEDIR NAME VERSION
export JETZT=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
run_js '
    const km = lies(env("KM")) || {};
    km[env("MP")] = { source: { source: "github",
                                repo: "jranglack-bot/scb-creator-kit" },
                      installLocation: env("MPDIR"),
                      lastUpdated: env("JETZT") };
    schreib(env("KM"), km);
    const ip = lies(env("IP")) || { version: 2, plugins: {} };
    ip.plugins[env("NAME") + "@" + env("MP")] = [{
        scope: "user", installPath: env("CACHEDIR"),
        version: env("VERSION"),
        installedAt: env("JETZT"), lastUpdated: env("JETZT") }];
    schreib(env("IP"), ip);
    const st = lies(env("SET")) || {};
    st.enabledPlugins = st.enabledPlugins || {};
    st.enabledPlugins[env("NAME") + "@" + env("MP")] = true;
    schreib(env("SET"), st);'

echo "FERTIG: $NAME v$VERSION ist installiert UND freigeschaltet."
echo "Jetzt Claude Code (oder die Claude-App) einmal neu starten -"
echo "danach ist das Kit aktiv. Einrichtung starten mit: Richte das SCB Kit ein"
