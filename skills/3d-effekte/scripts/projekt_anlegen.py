#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legt die 3D-Effekte nach einem Plan in Remotion ODER HyperFrames an.

Aufruf:
  python projekt_anlegen.py <plan.json> --remotion [remotion-projekt]
  python projekt_anlegen.py <plan.json> --hyperframes <zielordner>

Optionen:
  --quelle <ordner>   wo die Dateien aus dem Plan liegen (Standard: Ordner des Plans)
  --schrift <ttf>     Schriftdatei fuer die 3D-Schrift (Standard: Arial Rounded)

Was passiert:
  - schrift.js (Umrisse aller Texte), logo.js (Logo-SVG oder keins) erzeugen
  - szenen.js und die Huelle des Werkzeugs ins Projekt kopieren
  - Bilder und Videos aus dem Plan nach public/3d (Remotion) bzw. assets
    (HyperFrames) kopieren
  - Remotion: three nachinstallieren, falls es fehlt, und die Komposition
    "DreiDEffekte" in src/Root.tsx eintragen
  - HyperFrames: index.html passend zum Plan erzeugen

Danach: Vorschau oeffnen und zeigen, erst dann rendern (siehe SKILL.md).
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
VORLAGEN = HIER.parent / "vorlagen"
sys.path.insert(0, str(HIER))
from text_zu_pfad import schrift_modul, standard_schrift  # noqa: E402

THREE_VERSION = "0.185.1"  # in beiden Werkzeugen dieselbe Fassung
EIGENE_ORTE = [Path.home() / ".scb-creator-kit" / "grafik", Path.home(),
               Path("D:/Instagram Content"), Path("C:/Instagram Content")]
DATEI_FELDER = ("video", "person", "wand")


def npm_befehl(name):
    """Auf Windows heissen npm/npx .cmd - sonst findet Python sie nicht."""
    for k in ([name + ".cmd", name] if platform.system() == "Windows" else [name]):
        p = shutil.which(k)
        if p:
            return p
    return None


def plan_lesen(pfad):
    with open(pfad, encoding="utf-8-sig") as f:
        plan = json.load(f)
    if not plan.get("szenen"):
        raise SystemExit("Der Plan braucht eine Liste \"szenen\"")
    for i, s in enumerate(plan["szenen"]):
        if "name" not in s or "dauer" not in s:
            raise SystemExit(f"Szene {i + 1}: \"name\" und \"dauer\" fehlen")
    return plan


def texte(plan):
    aus = []
    for s in plan["szenen"]:
        if s["name"] == "schrift":
            aus += [s.get("text1", "ECHTES"), s.get("text2", "3D")]
        elif s["name"] == "ebenen":
            aus.append(s.get("text", "3D"))
    return aus or ["3D"]


def dateien(plan):
    aus = []
    for s in plan["szenen"]:
        aus += s.get("bilder", [])
        aus += [s[k] for k in DATEI_FELDER if k in s]
    return list(dict.fromkeys(aus))


def gemeinsame_dateien(plan, ziel, quelle, ttf):
    ziel.mkdir(parents=True, exist_ok=True)
    shutil.copy2(VORLAGEN / "szenen.js", ziel / "szenen.js")
    (ziel / "schrift.js").write_text(schrift_modul(ttf, texte(plan)), encoding="utf-8")
    logo = None
    if plan.get("logo"):
        logo = (quelle / plan["logo"]).read_text(encoding="utf-8")
    (ziel / "logo.js").write_text(
        "// Automatisch erzeugt von projekt_anlegen.py. null = eingebautes Strahlenzeichen.\n"
        "export const LOGO_SVG = " + json.dumps(logo, ensure_ascii=False) + ";\n", encoding="utf-8")


def medien_kopieren(plan, quelle, ziel):
    ziel.mkdir(parents=True, exist_ok=True)
    fehlt = []
    for d in dateien(plan):
        q = quelle / d
        if not q.exists():
            fehlt.append(str(q))
            continue
        z = ziel / Path(d).name
        if not z.exists() or z.stat().st_size != q.stat().st_size:
            shutil.copy2(q, z)
    if fehlt:
        raise SystemExit("Diese Dateien aus dem Plan fehlen:\n  " + "\n  ".join(fehlt))


def flach(plan):
    """Dateinamen im Plan auf den reinen Namen kuerzen (liegen danach in einem Ordner)."""
    p = json.loads(json.dumps(plan))
    for s in p["szenen"]:
        if "bilder" in s:
            s["bilder"] = [Path(b).name for b in s["bilder"]]
        for k in DATEI_FELDER:
            if k in s:
                s[k] = Path(s[k]).name
    return p


# ------------------------------------------------------------------ Remotion
def remotion_finden(angabe):
    if angabe:
        return Path(angabe)
    for ort in EIGENE_ORTE:
        k = ort / "remotion"
        if (k / "package.json").exists():
            return k
    raise SystemExit("Kein Remotion-Projekt gefunden. Pfad angeben: --remotion <ordner> "
                     "(einrichten: scb-setup, Bereich Grafik)")


def three_sicherstellen(projekt):
    paket = json.loads((projekt / "package.json").read_text(encoding="utf-8"))
    alle = {**paket.get("dependencies", {}), **paket.get("devDependencies", {})}
    if "three" in alle:
        return
    npm = npm_befehl("npm")
    if not npm:
        raise SystemExit("npm fehlt (Node.js installieren)")
    print(f"three {THREE_VERSION} wird installiert ...")
    r = subprocess.run([npm, "install", f"three@{THREE_VERSION}", "--save-exact"],
                       cwd=str(projekt), stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("npm install three schlug fehl:\n" + (r.stderr or r.stdout)[-800:])


def root_eintragen(projekt):
    root = projekt / "src" / "Root.tsx"
    if not root.exists():
        print("HINWEIS: src/Root.tsx fehlt - Komposition von Hand eintragen.")
        return
    s = root.read_text(encoding="utf-8")
    if "DreiDEffekte" in s:
        return
    imp = 'import { DreiDEffekte, DREI_D_FRAMES, DREI_D_FPS } from "./DreiDEffekte";\n'
    letzte = max(s.rfind("\nimport "), 0)
    ende = s.index("\n", s.index(";", letzte)) + 1 if letzte else 0
    s = s[:ende] + imp + s[ende:]
    eintrag = ('      {/* 3D-Effekte (Skill 3d-effekte) */}\n'
               '      <Composition\n        id="DreiDEffekte"\n        component={DreiDEffekte}\n'
               '        durationInFrames={DREI_D_FRAMES}\n        fps={DREI_D_FPS}\n'
               '        width={1080}\n        height={1920}\n      />\n')
    if "<>\n" not in s:
        root.write_text(s, encoding="utf-8")
        print("HINWEIS: Komposition bitte von Hand in Root.tsx eintragen:\n" + eintrag)
        return
    s = s.replace("<>\n", "<>\n" + eintrag, 1)
    root.write_text(s, encoding="utf-8")
    print("Root.tsx: Komposition DreiDEffekte eingetragen")


def remotion(plan, quelle, ttf, angabe):
    projekt = remotion_finden(angabe)
    ziel = projekt / "src" / "DreiDEffekte"
    gemeinsame_dateien(plan, ziel, quelle, ttf)
    for d in ("index.tsx", "szenen.d.ts"):
        shutil.copy2(VORLAGEN / "remotion" / d, ziel / d)
    (ziel / "plan.json").write_text(json.dumps(flach(plan), ensure_ascii=False, indent=2), encoding="utf-8")
    medien_kopieren(plan, quelle, projekt / "public" / "3d")
    three_sicherstellen(projekt)
    root_eintragen(projekt)
    sek = sum(s["dauer"] for s in plan["szenen"])
    print(f"OK Remotion: {ziel} | {len(plan['szenen'])} Szenen, {sek:g} s")
    print("Vorschau: <python> skills/motion-grafik/scripts/editor_oeffnen.py --remotion")


# --------------------------------------------------------------- HyperFrames
HF_KOPF = """<!DOCTYPE html>
<html lang="de">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width={B}, height={H}">
    <title>3D-Effekte</title>
    <script type="importmap">
      {{
        "imports": {{
          "three": "https://cdn.jsdelivr.net/npm/three@{V}/build/three.module.js",
          "three/examples/jsm/": "https://cdn.jsdelivr.net/npm/three@{V}/examples/jsm/"
        }}
      }}
    </script>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {B}px; height: {H}px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: {B}px; height: {H}px; overflow: hidden; background: #000; }}
      .flaeche {{ position: absolute; left: 0; top: 0; width: {B}px; height: {H}px; }}
      .flaeche video {{ position: absolute; left: 0; top: 0; width: {B}px; height: {H}px; object-fit: cover; }}
      .buehne {{ perspective: 2600px; background: radial-gradient(ellipse at 50% 45%, #16204a 0%, #04050c 75%); visibility: hidden; }}
      .dreh {{ transform-style: preserve-3d; }}
      .rahmen {{ position: absolute; left: 0; top: 0; width: {B}px; height: {H}px; opacity: 0;
        border: 6px solid rgba(150,178,255,0.95); border-radius: 28px; box-shadow: 0 0 48px rgba(89,127,217,0.65); }}
      .schild {{ position: absolute; right: 44px; top: 200px; opacity: 0; color: #fff; transform-origin: 100% 0;
        font: 700 58px "Arial Rounded MT Bold", "Arial Rounded MT", Arial, sans-serif;
        padding: 14px 34px; background: rgba(8,12,28,0.86); border: 4px solid #597fd9; border-radius: 60px; }}
    </style>
  </head>
  <body>
    <!-- Erzeugt von projekt_anlegen.py (Skill 3d-effekte). Aenderungen am Inhalt
         in plan.json, dann das Script erneut laufen lassen. -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="{D}" data-width="{B}" data-height="{H}">
"""

HF_SKRIPT = """    </div>

    <script type="module">
      import { dauerGesamt, ebenenLage, erstelleSzene, logoEbene, logoWackeln } from "./js/szenen.js";
      import { PLAN } from "./js/plan.js";

      const $ = (id) => document.getElementById(id);
      const szenen = [];
      let von = 0;
      PLAN.szenen.forEach((s, i) => {
        const obj = erstelleSzene(s.name, $("c" + i), {
          breite: PLAN.breite, hoehe: PLAN.hoehe, pfad: (d) => "assets/" + d, optionen: s,
        });
        szenen.push({ ...s, i, von, obj });
        von += s.dauer;
      });
      window.__hf = window.__hf || {};
      window.__hf.buildReady = window.__hf.buildReady || {};
      window.__hf.buildReady["drei-d-effekte"] = Promise.all(szenen.map((s) => s.obj.bereit));

      function ebenen(s, t) {
        const buehne = $("e" + s.i);
        const sichtbar = t >= 0 && t < s.dauer;
        buehne.style.visibility = sichtbar ? "visible" : "hidden";
        if (!sichtbar) return;
        const L = ebenenLage(t);
        $("e" + s.i + "-dreh").style.transform = `scale(${L.massstab}) rotateX(${L.drehX}deg) rotateY(${L.drehY}deg)`;
        ["wand", "objekt", "person"].forEach((k) => ($("e" + s.i + "-" + k).style.transform = `translateZ(${L.tiefe[k]}px)`));
        buehne.querySelectorAll(".rahmen").forEach((r) => (r.style.opacity = L.rahmen));
        buehne.querySelectorAll(".schild").forEach((r) => {
          // wachsen statt blenden: der Text bleibt deckend und lesbar
          r.style.opacity = L.schild > 0.001 ? 1 : 0;
          r.style.transform = `scale(${0.4 + 0.6 * L.schild})`;
        });
      }

      function logo(s, t) {
        $("c" + s.i).style.zIndex = logoEbene(t, s) === "hinten" ? "1" : "3";
        const w = logoWackeln(t, s);
        const tf = t >= (s.aufprall ?? 4.3) ? `translate(${w.x}px, ${w.y}px) scale(1.05)` : "none";
        $("l" + s.i + "-video").style.transform = tf;
        $("l" + s.i + "-person").style.transform = tf;
      }

      function zeige(zeit) {
        for (const s of szenen) {
          const t = zeit - s.von;
          if (t >= 0 && t < s.dauer) s.obj.render(t);
          if (s.name === "ebenen") ebenen(s, t);
          if (s.name === "logo" && t >= 0 && t < s.dauer) logo(s, t);
        }
      }
      window.addEventListener("hf-seek", (e) => zeige(e.detail.time));
      zeige(window.__hfThreeTime || 0);

      const tl = gsap.timeline({ paused: true });
      tl.set({}, {}, dauerGesamt(PLAN.szenen));
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def hf_koerper(plan):
    B, H = plan["breite"], plan["hoehe"]
    zeilen, von = [], 0.0
    for i, s in enumerate(plan["szenen"]):
        zeit = f'data-start="{von:g}" data-duration="{s["dauer"]:g}"'
        leinwand = f'<canvas id="c{i}" class="flaeche" width="{B}" height="{H}"></canvas>'
        if s["name"] == "ebenen":
            sch = s.get("schilder", ["Hintergrund", "3D-Objekt", "Du"])
            zeilen.append(f'''      <div id="e{i}" class="flaeche buehne">
        <div id="e{i}-dreh" class="flaeche dreh">
          <div id="e{i}-wand" class="flaeche"><img src="assets/{s["wand"]}" class="flaeche" alt="">
            <div class="rahmen"></div><div class="schild">{sch[0]}</div></div>
          <div id="e{i}-objekt" class="flaeche">{leinwand}
            <div class="rahmen"></div><div class="schild">{sch[1]}</div></div>
          <div id="e{i}-person" class="flaeche">
            <video id="v{i}-person" class="clip" src="assets/{s["person"]}" {zeit} data-media-start="0" data-track-index="{20 + i}" muted playsinline></video>
            <div class="rahmen"></div><div class="schild">{sch[2]}</div></div>
        </div>
      </div>''')
        elif s["name"] == "logo":
            zeilen.append(f'''      <div id="l{i}-video" class="flaeche" style="z-index: 0">
        <video id="v{i}-video" class="clip" src="assets/{s["video"]}" {zeit} data-media-start="0" data-track-index="{20 + i}" muted playsinline></video>
      </div>
      <div id="l{i}-person" class="flaeche" style="z-index: 2">
        <video id="v{i}-person" class="clip" src="assets/{s["person"]}" {zeit} data-media-start="0" data-track-index="{40 + i}" muted playsinline></video>
      </div>
      <canvas id="c{i}" class="clip flaeche" width="{B}" height="{H}" {zeit} data-track-index="{60 + i}" style="z-index: 1"></canvas>''')
        else:
            zeilen.append(f'      <canvas id="c{i}" class="clip flaeche" width="{B}" height="{H}" {zeit} data-track-index="1"></canvas>')
        von += s["dauer"]
    return "\n".join(zeilen) + "\n", von


def hyperframes(plan, quelle, ttf, ziel):
    ziel = Path(ziel)
    js = ziel / "js"
    gemeinsame_dateien(plan, js, quelle, ttf)
    p = flach(plan)
    p.setdefault("breite", 1080)
    p.setdefault("hoehe", 1920)
    (js / "plan.js").write_text("// Automatisch erzeugt von projekt_anlegen.py\nexport const PLAN = "
                                + json.dumps(p, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    medien_kopieren(plan, quelle, ziel / "assets")
    koerper, dauer = hf_koerper(p)
    kopf = HF_KOPF.format(B=p["breite"], H=p["hoehe"], V=THREE_VERSION, D=f"{dauer:g}")
    (ziel / "index.html").write_text(kopf + koerper + HF_SKRIPT, encoding="utf-8")
    name = ziel.name
    fest = {
        "package.json": {"name": name, "private": True, "type": "module",
                         "scripts": {"dev": "hyperframes preview", "check": "hyperframes check",
                                     "render": "hyperframes render"}},
        "hyperframes.json": {"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                             "paths": {"blocks": "compositions", "components": "compositions/components",
                                       "assets": "assets"},
                             "media": {"autoProxy": True}},
        "meta.json": {"id": name, "name": name},
    }
    for datei, inhalt in fest.items():
        if not (ziel / datei).exists():
            (ziel / datei).write_text(json.dumps(inhalt, indent=2) + "\n", encoding="utf-8")
    print(f"OK HyperFrames: {ziel} | {len(p['szenen'])} Szenen, {dauer:g} s")
    print("Pruefen: hyperframes lint && hyperframes check (im Projektordner)")
    print("Vorschau: hyperframes preview --port 3003 --background")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    wahl = ap.add_mutually_exclusive_group(required=True)
    wahl.add_argument("--remotion", nargs="?", const="", metavar="PROJEKT")
    wahl.add_argument("--hyperframes", metavar="ZIEL")
    ap.add_argument("--quelle")
    ap.add_argument("--schrift")
    a = ap.parse_args()

    plan = plan_lesen(a.plan)
    quelle = Path(a.quelle) if a.quelle else Path(a.plan).resolve().parent
    ttf = a.schrift or plan.get("schriftart") or standard_schrift()
    if not ttf or not os.path.exists(ttf):
        raise SystemExit("Keine Schriftdatei gefunden: --schrift <datei.ttf> angeben")
    if a.hyperframes:
        hyperframes(plan, quelle, ttf, a.hyperframes)
    else:
        remotion(plan, quelle, ttf, a.remotion or None)


if __name__ == "__main__":
    main()
