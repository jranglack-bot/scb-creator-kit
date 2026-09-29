// ---------------------------------------------------------------------------
// 3D-Effekte ohne KI-Video: gemeinsamer Three.js-Code fuer Remotion UND
// HyperFrames (SCB Creator Kit, Skill 3d-effekte).
//
// Jede Szene ist eine reine Funktion der Zeit: render(t) zeichnet genau das
// Bild zur Sekunde t ab Szenenbeginn. Kein Takt, kein Zufall ohne Seed.
// Deshalb rendern beide Werkzeuge Bild fuer Bild dasselbe (gemessen: SSIM
// ueber 0,995).
//
// Was gezeigt wird (Texte, Bilder, Logo, Videos, Logo-Bahn), steht NICHT
// hier, sondern in plan.json. projekt_anlegen.py kopiert diese Datei ins
// Projekt und erzeugt daneben schrift.js und logo.js.
// ---------------------------------------------------------------------------
import * as THREE from "three";
import { SVGLoader } from "three/examples/jsm/loaders/SVGLoader.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { SCHRIFT } from "./schrift.js";
import { LOGO_SVG } from "./logo.js";

// Gesamtdauer eines Plans in Sekunden (Liste der Szenen aus plan.json)
export const dauerGesamt = (szenen) => szenen.reduce((s, z) => s + z.dauer, 0);

const BLAU = 0x597fd9;
const ORANGE = 0xd97757;
const SCHRIFTART = '700 {px}px "Arial Rounded MT Bold", "Arial Rounded MT", Arial, sans-serif';

// ---------- kleine Helfer --------------------------------------------------
const klemm = (v) => Math.min(1, Math.max(0, v));
const bereich = (t, a, b) => klemm((t - a) / (b - a));
const mix = (a, b, p) => a + (b - a) * p;
const easeOut = (p) => 1 - Math.pow(1 - p, 3);
const easeIn = (p) => p * p * p;
const easeInOut = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
// gedaempfte Feder: 0 -> 1 mit leichtem Ueberschwingen
const feder = (t, w = 10, d = 6) => (t <= 0 ? 0 : 1 - Math.exp(-d * t) * Math.cos(w * t));

function zufall(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function neuerRenderer(canvas, W, H) {
  const r = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    preserveDrawingBuffer: true, // sonst ist das Bild beim Abfotografieren leer
    powerPreference: "high-performance",
  });
  r.setPixelRatio(1);
  r.setSize(W, H, false);
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = THREE.ACESFilmicToneMapping;
  r.toneMappingExposure = 1.0;
  r.setClearColor(0x000000, 0);
  return r;
}

// Spiegelungen ohne HDRI-Datei: ein virtueller Raum, einmal vorberechnet
function umgebung(renderer) {
  const pm = new THREE.PMREMGenerator(renderer);
  const tex = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  pm.dispose();
  return tex;
}

function leinwand(w, h, malen) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  malen(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function rundRechteck(g, x, y, w, h, r) {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}

function hintergrund(innen, aussen) {
  return leinwand(540, 960, (g, w, h) => {
    const r = g.createRadialGradient(w * 0.5, h * 0.42, 10, w * 0.5, h * 0.45, h * 0.78);
    r.addColorStop(0, innen);
    r.addColorStop(1, aussen);
    g.fillStyle = r;
    g.fillRect(0, 0, w, h);
  });
}

function funkenTextur() {
  return leinwand(64, 64, (g, w) => {
    const r = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2);
    r.addColorStop(0, "rgba(255,255,255,1)");
    r.addColorStop(0.35, "rgba(255,255,255,0.45)");
    r.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = r;
    g.fillRect(0, 0, w, w);
  });
}

// schwebender Staub: Position ist reine Funktion der Zeit
function staub(anzahl, seed, [bx, by, bz], farbe, groesse, mitte = [0, 0, 0]) {
  const rnd = zufall(seed);
  const basis = new Float32Array(anzahl * 3);
  const tempo = new Float32Array(anzahl);
  for (let i = 0; i < anzahl; i++) {
    basis[i * 3] = mitte[0] + (rnd() - 0.5) * bx;
    basis[i * 3 + 1] = mitte[1] + (rnd() - 0.5) * by;
    basis[i * 3 + 2] = mitte[2] + (rnd() - 0.5) * bz;
    tempo[i] = 0.08 + rnd() * 0.22;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(basis.slice(), 3));
  const mat = new THREE.PointsMaterial({
    color: farbe,
    size: groesse,
    map: funkenTextur(),
    transparent: true,
    opacity: 0.85,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const pts = new THREE.Points(geo, mat);
  const unten = mitte[1] - by / 2;
  pts.userData.bewege = (t) => {
    const pos = geo.attributes.position.array;
    for (let i = 0; i < anzahl; i++) {
      const y = basis[i * 3 + 1] + t * tempo[i] - unten;
      pos[i * 3 + 1] = unten + (((y % by) + by) % by);
    }
    geo.attributes.position.needsUpdate = true;
  };
  return pts;
}

// Beschriftung als Schild, das immer zur Kamera zeigt
function schild(text, breiteWelt) {
  const tex = leinwand(512, 128, (g, w, h) => {
    rundRechteck(g, 6, 6, w - 12, h - 12, 52);
    g.fillStyle = "rgba(8,12,28,0.84)";
    g.fill();
    g.lineWidth = 5;
    g.strokeStyle = "#597fd9";
    g.stroke();
    g.fillStyle = "#ffffff";
    g.font = SCHRIFTART.replace("{px}", "64");
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillText(text, w / 2, h / 2 + 3);
  });
  tex.anisotropy = 4;
  const mat = new THREE.SpriteMaterial({
    map: tex,
    transparent: true,
    depthTest: false,
    depthWrite: false,
    toneMapped: false,
    opacity: 0,
  });
  const s = new THREE.Sprite(mat);
  s.scale.set(breiteWelt, breiteWelt / 4, 1);
  s.renderOrder = 10;
  return s;
}

// Umriss (SVG-Pfad) -> echter Koerper mit Tiefe und Fase
function koerperAusPfad(d, massstab, tiefe, materialien, fase = 0.035) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg"><path d="${d}"/></svg>`;
  const shapes = new SVGLoader().parse(svg).paths.flatMap((p) => p.toShapes());
  const geo = new THREE.ExtrudeGeometry(shapes, {
    depth: tiefe / massstab,
    bevelEnabled: true,
    bevelThickness: (fase * 1.6) / massstab,
    bevelSize: fase / massstab,
    bevelSegments: 5,
    curveSegments: 12,
  });
  geo.scale(massstab, massstab, massstab);
  geo.computeBoundingBox();
  const mitte = new THREE.Vector3();
  geo.boundingBox.getCenter(mitte);
  geo.translate(-mitte.x, -mitte.y, -mitte.z);
  return { mesh: new THREE.Mesh(geo, materialien), mitte };
}

function zeileFuer(text) {
  const z = SCHRIFT.zeilen[text];
  if (!z) throw new Error(`Text fehlt in schrift.js: "${text}" - projekt_anlegen.py neu laufen lassen`);
  return z;
}

// Logo aus einer SVG-Datei: jeder Pfad wird ein Koerper in seiner Fuellfarbe
function koerperAusSvg(svgText, zielBreite, tiefe, standardFarbe) {
  const pfade = new SVGLoader().parse(svgText).paths;
  const formen = [];
  const kiste = new THREE.Box2();
  for (const p of pfade) {
    const fuellung = p.userData && p.userData.style ? p.userData.style.fill : undefined;
    if (fuellung === "none") continue;
    const shapes = p.toShapes();
    if (!shapes.length) continue;
    shapes.forEach((sh) => sh.getPoints().forEach((pt) => kiste.expandByPoint(pt)));
    const farbe = new THREE.Color(standardFarbe);
    try {
      if (fuellung && !fuellung.startsWith("url(")) farbe.setStyle(fuellung);
    } catch (e) {
      /* unbekannte Farbangabe: Standardfarbe bleibt */
    }
    formen.push({ shapes, farbe });
  }
  if (!formen.length) throw new Error("Im Logo-SVG wurde kein gefuellter Pfad gefunden");
  const groesse = Math.max(kiste.max.x - kiste.min.x, kiste.max.y - kiste.min.y);
  const m = zielBreite / groesse;
  const innen = new THREE.Group();
  for (const { shapes, farbe } of formen) {
    const geo = new THREE.ExtrudeGeometry(shapes, {
      depth: tiefe / m,
      bevelEnabled: true,
      bevelThickness: 0.048 / m,
      bevelSize: 0.03 / m,
      bevelSegments: 5,
      curveSegments: 12,
    });
    geo.scale(m, m, m);
    const vorne = new THREE.MeshPhysicalMaterial({
      color: farbe,
      metalness: 0.3,
      roughness: 0.28,
      clearcoat: 1,
      clearcoatRoughness: 0.1,
    });
    const seite = new THREE.MeshStandardMaterial({
      color: farbe.clone().multiplyScalar(0.72),
      metalness: 0.65,
      roughness: 0.3,
    });
    innen.add(new THREE.Mesh(geo, [vorne, seite]));
  }
  innen.scale.y = -1; // SVG zaehlt y nach unten, Three.js nach oben
  const box = new THREE.Box3().setFromObject(innen);
  const mitte = new THREE.Vector3();
  box.getCenter(mitte);
  innen.position.sub(mitte);
  const aussen = new THREE.Group();
  aussen.add(innen);
  return aussen;
}

// eine Textzeile als einzelne 3D-Buchstaben (fuer Buchstaben-Animation)
function textZeile(zeile, breiteWelt, tiefe, materialien) {
  const s = breiteWelt / zeile.breite;
  const hoehe = SCHRIFT.hoehe * s;
  return zeile.glyphen.map((g) => {
    const { mesh, mitte } = koerperAusPfad(g.d, s, tiefe, materialien);
    mesh.userData.basis = new THREE.Vector3(g.x * s + mitte.x - breiteWelt / 2, mitte.y - hoehe / 2, 0);
    mesh.position.copy(mesh.userData.basis);
    return mesh;
  });
}

// ===========================================================================
// Szene 1: echte 3D-Schrift (aus Arial Rounded, wie die Untertitel)
// ===========================================================================
function szeneSchrift(canvas, W, H, o = {}) {
  const renderer = neuerRenderer(canvas, W, H);
  const scene = new THREE.Scene();
  scene.environment = umgebung(renderer);
  scene.background = hintergrund("#1a2656", "#04050c");
  const cam = new THREE.PerspectiveCamera(32, W / H, 0.1, 100);

  const vorne = new THREE.MeshPhysicalMaterial({
    color: 0xf2f5ff,
    metalness: 0.1,
    roughness: 0.2,
    clearcoat: 1,
    clearcoatRoughness: 0.06,
  });
  const seite = new THREE.MeshStandardMaterial({ color: BLAU, metalness: 0.7, roughness: 0.3 });

  const gruppe = new THREE.Group();
  gruppe.position.x = -0.19; // rechts bleibt die Instagram-Knopfleiste frei
  scene.add(gruppe);
  const oben = textZeile(zeileFuer(o.text1 ?? "ECHTES"), 3.1, 0.22, [vorne, seite]);
  oben.forEach((m) => {
    m.userData.basis.y += 1.2;
    gruppe.add(m);
  });
  const dreiD = new THREE.Group();
  dreiD.position.y = -0.4;
  gruppe.add(dreiD);
  textZeile(zeileFuer(o.text2 ?? "3D"), 3.0, 0.55, [vorne, seite]).forEach((m) => dreiD.add(m));

  scene.add(new THREE.AmbientLight(0x8090c0, 0.3));
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(-4, 6, 8);
  scene.add(key);
  const kante = new THREE.DirectionalLight(0x7fa0ff, 2.4);
  kante.position.set(5, -2, -6);
  scene.add(kante);
  const wisch = new THREE.PointLight(0xffffff, 0, 14, 1.6);
  scene.add(wisch);
  const funken = staub(260, 7, [12, 16, 10], 0x8fb0ff, 0.06);
  scene.add(funken);

  function render(t) {
    oben.forEach((m, i) => {
      const start = 0.15 + i * 0.07;
      const p = feder(t - start, 11, 6.5);
      m.visible = t >= start;
      m.position.set(m.userData.basis.x, m.userData.basis.y + (1 - p) * 3.6, m.userData.basis.z);
      m.rotation.x = (1 - p) * -1.5;
    });
    const q = easeOut(bereich(t, 0.6, 1.75));
    dreiD.visible = t >= 0.6;
    dreiD.position.z = mix(-26, 0, q);
    dreiD.rotation.y = (1 - q) * Math.PI * 2;
    gruppe.rotation.y = Math.sin(t * 0.9) * 0.1 * bereich(t, 1.5, 2.5);
    gruppe.rotation.x = -0.05;

    const k = easeInOut(bereich(t, 0, 5));
    cam.position.set(mix(-2.6, 1.1, k), mix(-1.6, 0.7, k), mix(16, 12.9, k));
    cam.lookAt(-0.15, 0.3, 0);

    const s = bereich(t, 2.0, 3.5);
    wisch.position.set(mix(-5, 5, easeInOut(s)), 0.6, 2.2);
    wisch.intensity = Math.sin(s * Math.PI) * 40;
    funken.userData.bewege(t);
    renderer.render(scene, cam);
  }
  return { bereit: Promise.resolve(), render, dispose: () => renderer.dispose() };
}

// ===========================================================================
// Szene 2: schwebende Bildschirme, Kamera fliegt hindurch
// ===========================================================================
const LAGE = [
  { x: -1.5, y: 1.35, z: 2, ry: 0.35 },
  { x: 1.6, y: -0.9, z: -3, ry: -0.35 },
  { x: -1.7, y: -1.35, z: -8, ry: 0.3 },
  { x: 1.5, y: 1.5, z: -13, ry: -0.3 },
  { x: 0, y: 0.25, z: -19, ry: 0 },
];

function karteTextur(img) {
  return leinwand(540, 960, (g, w, h) => {
    const r = 46;
    g.save();
    rundRechteck(g, 6, 6, w - 12, h - 12, r);
    g.clip();
    const s = Math.max((w - 12) / img.width, (h - 12) / img.height);
    const iw = img.width * s;
    const ih = img.height * s;
    g.drawImage(img, 6 + (w - 12 - iw) / 2, 6 + (h - 12 - ih) / 2, iw, ih);
    const glanz = g.createLinearGradient(0, 0, w, h);
    glanz.addColorStop(0, "rgba(255,255,255,0.2)");
    glanz.addColorStop(0.35, "rgba(255,255,255,0)");
    g.fillStyle = glanz;
    g.fillRect(0, 0, w, h);
    g.restore();
    rundRechteck(g, 6, 6, w - 12, h - 12, r);
    g.lineWidth = 6;
    g.strokeStyle = "rgba(150,178,255,0.95)";
    g.stroke();
  });
}

function glimmTextur() {
  return leinwand(256, 384, (g, w, h) => {
    g.shadowColor = "rgba(89,127,217,1)";
    g.shadowBlur = 42;
    g.fillStyle = "rgba(89,127,217,0.9)";
    rundRechteck(g, 48, 48, w - 96, h - 96, 22);
    g.fill();
  });
}

function szeneBildschirme(canvas, W, H, pfad, o = {}) {
  // bis zu fuenf Bilder, das letzte wird am Ende gross gezeigt
  const bilder = (o.bilder || []).slice(0, LAGE.length);
  if (!bilder.length) throw new Error('Szene "bildschirme" braucht "bilder" im Plan');
  const lagen = LAGE.slice(LAGE.length - bilder.length);
  const renderer = neuerRenderer(canvas, W, H);
  const scene = new THREE.Scene();
  scene.background = hintergrund("#121c40", "#030409");
  scene.fog = new THREE.Fog(0x05070f, 9, 30);
  const cam = new THREE.PerspectiveCamera(40, W / H, 0.1, 100);

  const glimm = glimmTextur();
  const karten = lagen.map((l) => {
    const gruppe = new THREE.Group();
    const bild = new THREE.Mesh(
      new THREE.PlaneGeometry(1.35, 2.4),
      new THREE.MeshBasicMaterial({ color: 0x223055, transparent: true, toneMapped: false, side: THREE.DoubleSide }),
    );
    const schein = new THREE.Mesh(
      new THREE.PlaneGeometry(2.1, 3.3),
      new THREE.MeshBasicMaterial({
        map: glimm,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        toneMapped: false,
      }),
    );
    schein.position.z = -0.03;
    gruppe.add(schein, bild);
    scene.add(gruppe);
    return { gruppe, bild, l };
  });

  const bereit = Promise.all(
    bilder.map(async (datei, i) => {
      const img = await new THREE.ImageLoader().loadAsync(pfad(datei));
      const m = karten[i].bild.material;
      m.map = karteTextur(img);
      m.color.set(0xffffff);
      m.needsUpdate = true;
    }),
  );

  const funken = staub(420, 21, [14, 12, 40], 0x9ab4ff, 0.05, [0, 0, -8]);
  scene.add(funken);

  function render(t) {
    karten.forEach(({ gruppe, l }, i) => {
      gruppe.position.set(l.x, l.y + Math.sin(t * 1.5 + i) * 0.07, l.z);
      gruppe.rotation.y = l.ry + Math.sin(t * 0.8 + i) * 0.05;
      gruppe.rotation.z = Math.sin(t * 0.6 + i * 2) * 0.03;
    });
    const k = easeInOut(bereich(t, 0, 4.7));
    const ruhe = 1 - bereich(t, 3.2, 4.7);
    cam.position.set(Math.sin(t * 0.9) * 0.35 * ruhe, 0.25 + Math.sin(t * 0.7) * 0.2 * ruhe, mix(9, -13.8, k));
    cam.up.set(Math.sin(t * 0.8) * 0.06 * ruhe, 1, 0);
    cam.lookAt(0, 0.25, -19);
    funken.userData.bewege(t);
    renderer.render(scene, cam);
  }
  return { bereit, render, dispose: () => renderer.dispose() };
}

// ===========================================================================
// Szene 3: Explosionsansicht, ein Handy zerlegt sich in seine Teile
// ===========================================================================
function bildschirmTextur() {
  return leinwand(540, 1136, (g, w, h) => {
    const lg = g.createLinearGradient(0, 0, w, h);
    lg.addColorStop(0, "#1b2a66");
    lg.addColorStop(0.55, "#597fd9");
    lg.addColorStop(1, "#8b62f0");
    g.fillStyle = lg;
    g.fillRect(0, 0, w, h);
    g.fillStyle = "#ffffff";
    g.font = SCHRIFTART.replace("{px}", "120");
    g.textAlign = "center";
    g.fillText("9:41", w / 2, 250);
    for (let r = 0; r < 4; r++)
      for (let c = 0; c < 4; c++) {
        rundRechteck(g, 50 + c * 118, 380 + r * 140, 86, 86, 22);
        g.fillStyle = `rgba(255,255,255,${0.22 + ((r + c) % 3) * 0.12})`;
        g.fill();
      }
    rundRechteck(g, 36, h - 170, w - 72, 120, 40);
    g.fillStyle = "rgba(255,255,255,0.18)";
    g.fill();
  });
}

function akkuTextur() {
  return leinwand(512, 700, (g, w, h) => {
    g.fillStyle = "#223458";
    g.fillRect(0, 0, w, h);
    g.fillStyle = "#ffffff";
    g.textAlign = "center";
    g.font = SCHRIFTART.replace("{px}", "70");
    g.fillText("4.500 mAh", w / 2, h / 2);
    g.font = SCHRIFTART.replace("{px}", "40");
    g.fillStyle = "rgba(255,255,255,0.6)";
    g.fillText("Li-Ion", w / 2, h / 2 + 70);
  });
}

function szeneExplosion(canvas, W, H, o = {}) {
  const B = {
    glas: "Glas",
    display: "Display",
    platine: "Platine",
    akku: "Akku",
    rueckseite: "Rückseite",
    kamera: "Kamera",
    ...(o.beschriftungen || {}),
  };
  const renderer = neuerRenderer(canvas, W, H);
  const scene = new THREE.Scene();
  scene.environment = umgebung(renderer);
  scene.background = hintergrund("#161e3c", "#030409");
  const cam = new THREE.PerspectiveCamera(35, W / H, 0.1, 100);
  cam.position.set(0, 0.4, 14);
  cam.lookAt(0, 0.3, 0);

  scene.add(new THREE.AmbientLight(0x8090c0, 0.35));
  const key = new THREE.DirectionalLight(0xffffff, 2.4);
  key.position.set(-5, 6, 9);
  scene.add(key);
  const kante = new THREE.DirectionalLight(0x8fb0ff, 2.2);
  kante.position.set(6, 2, -7);
  scene.add(kante);

  const handy = new THREE.Group();
  handy.position.set(-0.2, 0.35, 0);
  handy.scale.setScalar(0.55);
  scene.add(handy);
  const teile = [];
  const teil = (obj, offen, beschriftung, schildLage) => {
    obj.userData.zu = obj.position.z;
    obj.userData.offen = offen;
    if (beschriftung) {
      const s = schild(beschriftung, 2.5);
      s.position.set(...schildLage);
      obj.add(s);
      obj.userData.schild = s;
    }
    handy.add(obj);
    teile.push(obj);
  };

  const rueck = new THREE.Mesh(
    new RoundedBoxGeometry(3.2, 6.6, 0.16, 5, 0.42),
    new THREE.MeshStandardMaterial({ color: 0x2b2f38, metalness: 0.85, roughness: 0.32 }),
  );
  rueck.position.z = -0.14;
  teil(rueck, -1.0, B.rueckseite, [1.2, -2.4, 0]);

  const kamera = new THREE.Group();
  const platte = new THREE.Mesh(
    new RoundedBoxGeometry(1.4, 1.45, 0.12, 4, 0.3),
    new THREE.MeshStandardMaterial({ color: 0x1c1f26, metalness: 0.8, roughness: 0.25 }),
  );
  platte.position.set(-0.72, 2.3, -0.28);
  kamera.add(platte);
  const glasLinse = new THREE.MeshPhysicalMaterial({ color: 0x05070c, metalness: 0.2, roughness: 0.05, clearcoat: 1 });
  const ringMat = new THREE.MeshStandardMaterial({ color: 0xc8ccd6, metalness: 1, roughness: 0.25 });
  for (const [x, y] of [[-0.98, 2.58], [-0.98, 2.02], [-0.44, 2.3]]) {
    const linse = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.12, 40), glasLinse);
    linse.rotation.x = Math.PI / 2;
    linse.position.set(x, y, -0.38);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.26, 0.035, 12, 40), ringMat);
    ring.position.set(x, y, -0.44);
    kamera.add(linse, ring);
  }
  teil(kamera, -1.9, B.kamera, [1.2, 2.3, -0.3]);

  const akku = new THREE.Mesh(new THREE.BoxGeometry(2.5, 3.4, 0.16), [
    ...Array(4).fill(new THREE.MeshStandardMaterial({ color: 0x223458, metalness: 0.4, roughness: 0.45 })),
    new THREE.MeshStandardMaterial({ map: akkuTextur(), metalness: 0.3, roughness: 0.45 }),
    new THREE.MeshStandardMaterial({ color: 0x223458, metalness: 0.4, roughness: 0.45 }),
  ]);
  akku.position.set(0, -1.3, 0.02);
  teil(akku, 0.8, B.akku, [-1.6, -0.4, 0]);

  const platine = new THREE.Group();
  const brett = new THREE.Mesh(
    new THREE.BoxGeometry(2.7, 2.4, 0.06),
    new THREE.MeshStandardMaterial({ color: 0x0f3b2d, metalness: 0.2, roughness: 0.6 }),
  );
  platine.add(brett);
  const rnd = zufall(5);
  const chipMat = new THREE.MeshStandardMaterial({ color: 0x1a1c20, metalness: 0.5, roughness: 0.4 });
  const goldMat = new THREE.MeshStandardMaterial({ color: 0xc9a24a, metalness: 1, roughness: 0.3 });
  for (let i = 0; i < 9; i++) {
    const w = 0.25 + rnd() * 0.55;
    const h = 0.25 + rnd() * 0.45;
    const chip = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.07), i % 4 === 0 ? goldMat : chipMat);
    chip.position.set((rnd() - 0.5) * (2.5 - w), (rnd() - 0.5) * (2.2 - h), 0.06);
    platine.add(chip);
  }
  platine.position.set(0, 1.75, 0);
  teil(platine, 0.8, B.platine, [1.9, 0.9, 0]);

  const anzeige = new THREE.Mesh(new THREE.BoxGeometry(3.08, 6.48, 0.06), [
    ...Array(4).fill(new THREE.MeshStandardMaterial({ color: 0x050608 })),
    new THREE.MeshStandardMaterial({ color: 0x000000, emissive: 0xffffff, emissiveMap: bildschirmTextur(), emissiveIntensity: 1 }),
    new THREE.MeshStandardMaterial({ color: 0x050608 }),
  ]);
  anzeige.position.z = 0.14;
  teil(anzeige, 1.7, B.display, [-1.6, -2.6, 0]);
  const leuchten = anzeige.material[4];

  const glas = new THREE.Mesh(
    new RoundedBoxGeometry(3.2, 6.6, 0.05, 4, 0.42),
    new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      metalness: 0,
      roughness: 0.04,
      transparent: true,
      opacity: 0.22,
      clearcoat: 1,
      depthWrite: false,
    }),
  );
  glas.position.z = 0.2;
  teil(glas, 2.6, B.glas, [-1.0, 3.4, 0]);

  const funken = staub(200, 33, [12, 16, 8], 0x8fb0ff, 0.05);
  scene.add(funken);

  function drehungY(t) {
    if (t < 1.0) return mix(1.8, -0.25, feder(t, 7, 4.5));
    if (t < 2.3) return mix(-0.25, -0.55, easeInOut(bereich(t, 1.0, 2.3)));
    if (t < 4.4) return mix(-0.55, -0.7, bereich(t, 2.3, 4.4));
    return mix(-0.7, 0, easeInOut(bereich(t, 4.4, 5.3)));
  }
  function drehungX(t) {
    if (t < 1.0) return 0.12;
    if (t < 4.4) return mix(0.12, 0.42, easeInOut(bereich(t, 1.0, 2.3)));
    return mix(0.42, 0.06, easeInOut(bereich(t, 4.4, 5.3)));
  }

  function render(t) {
    handy.rotation.set(drehungX(t), drehungY(t), 0);
    teile.forEach((o, i) => {
      const auf = easeOut(bereich(t, 1.0 + i * 0.06, 2.0 + i * 0.06));
      const zu = easeInOut(bereich(t, 4.4, 5.05));
      o.position.z = mix(o.userData.zu, o.userData.offen, auf * (1 - zu));
      const s = o.userData.schild;
      if (s) s.material.opacity = bereich(t, 2.0 + i * 0.08, 2.3 + i * 0.08) * (1 - bereich(t, 4.2, 4.45));
    });
    leuchten.emissiveIntensity = 1 + (t > 5.05 ? 1.4 * Math.exp(-(t - 5.05) * 6) : 0);
    funken.userData.bewege(t);
    renderer.render(scene, cam);
  }
  return { bereit: Promise.resolve(), render, dispose: () => renderer.dispose() };
}

// ===========================================================================
// Szene 5: drei Ebenen. Wand (leere Platte), 3D-Schrift, Person (Freisteller).
// Die Ebenen selbst sind flache Karten, die das Werkzeug per CSS-3D im Raum
// auffaechert (ebenenLage). Hier entsteht nur die mittlere Ebene: echte
// 3D-Schrift auf durchsichtigem Grund.
// ===========================================================================
export const EBENEN_SCHILDER = ["Hintergrund", "3D-Objekt", "Du"];

// Lage der drei Karten zur Sekunde t: Drehung in Grad, Tiefe in Pixeln
export function ebenenLage(t) {
  const p = easeInOut(bereich(t, 0.8, 2.1)) * (1 - easeInOut(bereich(t, 4.2, 5.1)));
  const drift = Math.sin((t - 2.1) * 0.9) * 4 * p;
  return {
    drehY: -42 * p + drift,
    drehX: 8 * p,
    massstab: 1 - 0.44 * p,
    tiefe: { wand: -900 * p, objekt: 0, person: 650 * p },
    rahmen: p,
    schild: bereich(t, 1.6, 2.0) * (1 - bereich(t, 4.0, 4.25)),
  };
}

function szeneEbenen(canvas, W, H, o = {}) {
  const renderer = neuerRenderer(canvas, W, H);
  const scene = new THREE.Scene();
  scene.environment = umgebung(renderer);
  const cam = new THREE.PerspectiveCamera(40, W / H, 0.1, 100);
  cam.position.set(0, 0, 10);
  cam.lookAt(0, 0, 0);
  const PX = H / 2 / (10 * Math.tan(THREE.MathUtils.degToRad(20)));
  const welt = (px, py, z) => {
    const f = (10 - z) / 10;
    return new THREE.Vector3(((px - W / 2) / PX) * f, ((H / 2 - py) / PX) * f, z);
  };

  const vorne = new THREE.MeshPhysicalMaterial({
    color: BLAU,
    metalness: 0.35,
    roughness: 0.25,
    clearcoat: 1,
    clearcoatRoughness: 0.08,
  });
  const seite = new THREE.MeshStandardMaterial({ color: 0x24366e, metalness: 0.6, roughness: 0.35 });
  const halter = new THREE.Group();
  const [tx, ty] = o.textLage ?? [490, 520];
  halter.position.copy(welt(tx, ty, 0));
  scene.add(halter);
  const gruppe = new THREE.Group();
  halter.add(gruppe);
  const buchstaben = textZeile(zeileFuer(o.text ?? "3D"), (o.textBreite ?? 800) / PX, 0.34, [vorne, seite]);
  buchstaben.forEach((m) => gruppe.add(m));

  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  const key = new THREE.DirectionalLight(0xffffff, 2.4);
  key.position.set(-3, 4, 6);
  scene.add(key);
  const kante = new THREE.DirectionalLight(0xbfd0ff, 1.6);
  kante.position.set(4, -2, -5);
  scene.add(kante);

  function render(t) {
    const rein = easeOut(bereich(t, 0.05, 0.85));
    halter.visible = t >= 0.05;
    halter.position.z = mix(-14, 0, rein);
    buchstaben.forEach((m, i) => {
      const p = feder(t - 0.1 - i * 0.05, 9, 5);
      m.position.copy(m.userData.basis);
      m.rotation.y = (1 - p) * 1.8;
    });
    gruppe.rotation.y = easeInOut(bereich(t, 2.2, 3.9)) * Math.PI * 2 + Math.sin(t * 1.1) * 0.08;
    gruppe.rotation.x = Math.sin(t * 0.7) * 0.05;
    renderer.render(scene, cam);
  }
  return { bereit: Promise.resolve(), render, dispose: () => renderer.dispose() };
}

// ===========================================================================
// Szene 4: 3D-Logo kommt hinter der Person hervor, landet ueber den Haenden
// und wird in die Kamera geworfen, das Glas springt.
// ===========================================================================
// Standardwerte, im Plan je Szene ueberschreibbar ("wechsel", "aufprall", "bahn")
const WECHSEL = 1.2; // ab hier liegt das Logo VOR der Person
const AUFPRALL = 4.3;
// Bahn in Bildschirm-Pixeln (x, y) und Tiefe z (Kamera bei z = 10).
// Diese Werte passen zu EINEM Testclip: fuer jedes Video Kopf, Schulter und
// Haende am Kontaktbogen messen und die Punkte anpassen (siehe SKILL.md).
const BAHN = {
  start: [430, 470, -3.0], // hinter dem Kopf
  auftauchen: [760, 450, -1.2], // rechts neben dem Kopf
  schulter: [800, 520, -0.3], // ueber der Schulter: hier Ebenenwechsel
  bogen: [770, 880, 0.6], // Bogen an der Seite hinunter
  schweben: [500, 960, 1.3], // vor der Brust
  ausholen: [505, 1030, 0.8],
  einschlag: [545, 880, 9.25], // direkt vor der Linse
};

export function logoEbene(t, o = {}) {
  return t < (o.wechsel ?? WECHSEL) ? "hinten" : "vorne";
}

// Erschuetterung des Videos nach dem Aufprall (Pixel)
export function logoWackeln(t, o = {}) {
  const d = t - (o.aufprall ?? AUFPRALL);
  if (d < 0) return { x: 0, y: 0 };
  const a = 24 * Math.exp(-d * 7);
  return { x: a * Math.sin(d * 57), y: a * Math.cos(d * 43) };
}

// eigenes Strahlenzeichen (keine Kopie eines geschuetzten Logos) als SVG-Pfad:
// genau so kommt spaeter jede Logo-Datei des Nutzers herein.
function strahlenPfad(anzahl, seed) {
  const rnd = zufall(seed);
  const pt = (a, r) => `${(50 + Math.cos(a) * r).toFixed(2)} ${(50 + Math.sin(a) * r).toFixed(2)}`;
  const innen = 12;
  let d = "";
  for (let k = 0; k < anzahl; k++) {
    const a = (k / anzahl) * Math.PI * 2 - Math.PI / 2;
    const L = 50 * (0.8 + rnd() * 0.2);
    const delta = 3.2 / L;
    d += `${k === 0 ? "M" : "L"}${pt(a - Math.PI / anzahl, innen)} `;
    d += `L${pt(a - delta, L - 3)} Q${pt(a, L + 3.5)} ${pt(a + delta, L - 3)} `;
  }
  return d + "Z";
}

function rissTextur(W, H, cx, cy, seed) {
  return leinwand(W, H, (g) => {
    const rnd = zufall(seed);
    const N = 17;
    const strahlen = [];
    for (let k = 0; k < N; k++) {
      let a = (k / N) * Math.PI * 2 + (rnd() - 0.5) * 0.3;
      const laenge = 420 + rnd() * 1250;
      const pts = [[cx, cy]];
      let x = cx;
      let y = cy;
      let l = 0;
      while (l < laenge) {
        const s = 28 + rnd() * 70;
        a += (rnd() - 0.5) * 0.24;
        x += Math.cos(a) * s;
        y += Math.sin(a) * s;
        l += s;
        pts.push([x, y]);
      }
      strahlen.push(pts);
    }
    const beiRadius = (pts, R) => pts.find(([x, y]) => Math.hypot(x - cx, y - cy) >= R);
    const linien = strahlen.map((p) => p);
    const facetten = [];
    for (const R of [36, 92, 175, 295, 460]) {
      for (let k = 0; k < N; k++) {
        const A = beiRadius(strahlen[k], R);
        const B = beiRadius(strahlen[(k + 1) % N], R * (0.85 + rnd() * 0.3));
        if (!A || !B) continue;
        if (R === 92) facetten.push([A, B]);
        if (rnd() < 0.3) continue;
        const M = [(A[0] + B[0]) / 2 + (rnd() - 0.5) * 16, (A[1] + B[1]) / 2 + (rnd() - 0.5) * 16];
        linien.push([A, M, B]);
      }
    }
    for (const [A, B] of facetten) {
      g.beginPath();
      g.moveTo(cx, cy);
      g.lineTo(A[0], A[1]);
      g.lineTo(B[0], B[1]);
      g.closePath();
      g.fillStyle = `rgba(255,255,255,${(0.04 + rnd() * 0.12).toFixed(3)})`;
      g.fill();
    }
    const zeichne = (breite, farbe) => {
      g.lineWidth = breite;
      g.strokeStyle = farbe;
      g.lineJoin = "round";
      g.lineCap = "round";
      for (const pts of linien) {
        g.beginPath();
        g.moveTo(pts[0][0], pts[0][1]);
        for (const [x, y] of pts.slice(1)) g.lineTo(x, y);
        g.stroke();
      }
    };
    zeichne(5, "rgba(0,0,0,0.35)");
    zeichne(2.2, "rgba(255,255,255,0.8)");
    zeichne(0.9, "rgba(255,255,255,1)");
    const kern = g.createRadialGradient(cx, cy, 0, cx, cy, 70);
    kern.addColorStop(0, "rgba(255,255,255,0.9)");
    kern.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = kern;
    g.fillRect(cx - 80, cy - 80, 160, 160);
  });
}

function szeneLogo(canvas, W, H, o = {}) {
  const LOGO_WECHSEL = o.wechsel ?? WECHSEL;
  const LOGO_AUFPRALL = o.aufprall ?? AUFPRALL;
  const bahn = { ...BAHN, ...(o.bahn || {}) };
  const renderer = neuerRenderer(canvas, W, H);
  renderer.autoClear = false;
  const scene = new THREE.Scene();
  scene.environment = umgebung(renderer);
  const cam = new THREE.PerspectiveCamera(40, W / H, 0.05, 100);
  cam.position.set(0, 0, 10);
  cam.lookAt(0, 0, 0);
  // Bildschirm-Pixel -> Weltpunkt in Tiefe z (Kamera bei z = 10)
  const PX = H / 2 / (10 * Math.tan(THREE.MathUtils.degToRad(20)));
  const welt = (px, py, z) => {
    const f = (10 - z) / 10;
    return new THREE.Vector3(((px - W / 2) / PX) * f, ((H / 2 - py) / PX) * f, z);
  };

  const vorne = new THREE.MeshPhysicalMaterial({
    color: ORANGE,
    metalness: 0.3,
    roughness: 0.28,
    clearcoat: 1,
    clearcoatRoughness: 0.1,
  });
  const seite = new THREE.MeshStandardMaterial({ color: 0xa4502f, metalness: 0.65, roughness: 0.3 });
  const logo = LOGO_SVG
    ? koerperAusSvg(LOGO_SVG, 0.78, 0.16, ORANGE)
    : koerperAusPfad(strahlenPfad(12, 11), 0.0078, 0.16, [vorne, seite], 0.03).mesh;
  scene.add(logo);
  scene.add(new THREE.AmbientLight(0xffffff, 0.45));
  const key = new THREE.DirectionalLight(0xffffff, 2.6);
  key.position.set(-3, 4, 6);
  scene.add(key);
  const fuell = new THREE.DirectionalLight(0xffe2d0, 0.9);
  fuell.position.set(3, -1, 4);
  scene.add(fuell);

  // Glasriss als Vollbild-Ebene, die sich vom Einschlag aus aufdeckt
  const MITTE = [bahn.einschlag[0], bahn.einschlag[1]];
  const riss = new THREE.ShaderMaterial({
    uniforms: {
      karte: { value: rissTextur(W, H, MITTE[0], MITTE[1], 3) },
      mitte: { value: new THREE.Vector2(MITTE[0] / W, 1 - MITTE[1] / H) },
      verhaeltnis: { value: W / H },
      radius: { value: 0 },
      blitz: { value: 0 },
    },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: `
      uniform sampler2D karte; uniform vec2 mitte; uniform float verhaeltnis;
      uniform float radius; uniform float blitz; varying vec2 vUv;
      void main(){
        vec4 c = texture2D(karte, vUv);
        float r = length((vUv - mitte) * vec2(verhaeltnis, 1.0));
        float sicht = 1.0 - smoothstep(radius - 0.03, radius, r);
        float a = max(c.a * sicht, blitz);
        gl_FragColor = vec4(mix(c.rgb, vec3(1.0), blitz), a);
        #include <colorspace_fragment>
      }`,
    transparent: true,
    depthTest: false,
    depthWrite: false,
  });
  const ueber = new THREE.Scene();
  ueber.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), riss));
  const ortho = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const K0 = welt(...bahn.start);
  const K1 = welt(...bahn.auftauchen);
  const K2 = welt(...bahn.schulter);
  const KC = welt(...bahn.bogen);
  const K4 = welt(...bahn.schweben);
  const K5 = welt(...bahn.ausholen);
  const K6 = welt(...bahn.einschlag);
  const tmp = new THREE.Vector3();

  function lage(t) {
    if (t < 0.8) return tmp.lerpVectors(K0, K1, easeInOut(bereich(t, 0, 0.8)));
    if (t < LOGO_WECHSEL) return tmp.lerpVectors(K1, K2, easeInOut(bereich(t, 0.8, LOGO_WECHSEL)));
    if (t < 2.05) {
      const p = easeInOut(bereich(t, LOGO_WECHSEL, 2.05));
      const a = (1 - p) * (1 - p);
      const b = 2 * (1 - p) * p;
      const c = p * p;
      return tmp.set(
        a * K2.x + b * KC.x + c * K4.x,
        a * K2.y + b * KC.y + c * K4.y,
        a * K2.z + b * KC.z + c * K4.z,
      );
    }
    const schweben = (u) => {
      const d = u - 2.05;
      return new THREE.Vector3(K4.x, K4.y + Math.sin(d * 3.2) * 0.05 - 0.1 * Math.exp(-d * 6) * Math.sin(d * 14), K4.z);
    };
    if (t < 3.6) return tmp.copy(schweben(t));
    if (t < 3.85) return tmp.lerpVectors(schweben(3.6), K5, easeOut(bereich(t, 3.6, 3.85)));
    return tmp.lerpVectors(K5, K6, easeIn(bereich(t, 3.85, LOGO_AUFPRALL)));
  }

  function render(t) {
    renderer.clear();
    if (t < LOGO_AUFPRALL) {
      logo.position.copy(lage(t));
      const flug = easeIn(bereich(t, 3.85, LOGO_AUFPRALL));
      logo.rotation.set(
        Math.sin(t * 1.3) * 0.22 + flug * 5,
        2.4 * Math.min(t, 2.05) + 1.2 * Math.max(0, Math.min(t, 3.85) - 2.05) + flug * 3,
        Math.sin(t * 0.9) * 0.1 + flug * 2,
      );
      renderer.render(scene, cam);
    }
    const d = t - LOGO_AUFPRALL;
    riss.uniforms.radius.value = d < 0 ? 0 : 1.3 * easeOut(bereich(d, 0, 0.16));
    riss.uniforms.blitz.value = d < 0 ? 0 : 0.85 * Math.exp(-d * 16);
    if (d >= 0) renderer.render(ueber, ortho);
  }
  return { bereit: Promise.resolve(), render, dispose: () => renderer.dispose() };
}

// ===========================================================================
// Erzeugt eine Szene. optionen = der Eintrag dieser Szene aus plan.json.
export function erstelleSzene(name, canvas, { breite = 1080, hoehe = 1920, pfad = (d) => d, optionen = {} } = {}) {
  if (name === "schrift") return szeneSchrift(canvas, breite, hoehe, optionen);
  if (name === "bildschirme") return szeneBildschirme(canvas, breite, hoehe, pfad, optionen);
  if (name === "explosion") return szeneExplosion(canvas, breite, hoehe, optionen);
  if (name === "logo") return szeneLogo(canvas, breite, hoehe, optionen);
  if (name === "ebenen") return szeneEbenen(canvas, breite, hoehe, optionen);
  throw new Error("Unbekannte Szene: " + name);
}
