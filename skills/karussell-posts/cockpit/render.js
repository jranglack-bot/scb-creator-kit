// Gemeinsame Renderlogik fuer vorlage.html (Export) und cockpit.html (Bearbeiten).
//
// Eine Slide ist eine Liste gleichartiger Bloecke. Jeder Block ist Text oder
// Bild. Bloecke ohne x/y liegen im Raster und werden bei Platznot gemeinsam
// verkleinert; sobald ein Block x/y hat, steht er frei.
// Die rolle (titel/text) steuert nur, welcher globale Groessenregler greift.
//
// Textformat: Tags, beliebig ueberlagerbar.
//   <b>fett</b> <i>kursiv</i> <u>unterstrichen</u>
//   <c=akzent>farbig</c> <c=#ff0000>farbig</c> <m>hinterlegt</m> <f=Poppins>Schrift</f>

const SCHRIFTEN = ['Montserrat', 'Poppins', 'Inter', 'Oswald',
                   'Playfair Display', 'Lora', 'Bebas Neue'];

// 4:5, fuer automatisches Posten. Alte Projekte tragen ihr 3:4 im eigenen stil.
const STIL_STD = {
  breite: 1080, hoehe: 1350,
  bg: "#dee3e7", text: "#313538", akzent: "#718d81", schrift: "Montserrat",
  randX: 132, randOben: 354, randUnten: 94,
  titel: 84, textgroesse: 40, titelAbstand: 1.17, textAbstand: 1.42
};
// Ordner des offenen Projekts, z. B. "projekte/kompass/". Bilddateien in
// inhalt.json sind relativ dazu. Cockpit und vorlage.html setzen ihn beim Laden.
let BASIS = '';
const BILD_MIN = 0.22;   // Anteil der Slidehoehe, den ein fliessendes Bild behaelt

const FORMATE = ['b', 'i', 'u', 'm', 'c', 'f', 'd'];
const TAG = /<(\/?)(b|i|u|m|c|f|d)(?:=([^>]{0,64}))?>/y;   // sticky: kein slice, linear
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                          .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

// ------------------------------------------------------------- Textformat

function zerlege(s){
  const aus = [], st = {};
  let i = 0;
  s = String(s == null ? '' : s);
  while (i < s.length){
    if (s[i] === '<'){
      TAG.lastIndex = i;
      const m = TAG.exec(s);
      if (m){
        if (m[1]) delete st[m[2]];
        else st[m[2]] = (m[3] === undefined) ? true : m[3];
        i += m[0].length;
        continue;
      }
    }
    aus.push({c: s[i], f: Object.assign({}, st)});
    i++;
  }
  return aus;
}

function gleich(a, b){ return FORMATE.every(t => a[t] === b[t]); }

function serialisiere(z){
  let aus = '';
  const offen = [];
  z.forEach(x => {
    let n = 0;
    while (n < offen.length && x.f[offen[n][0]] === offen[n][1]) n++;
    while (offen.length > n) aus += '</' + offen.pop()[0] + '>';
    FORMATE.forEach(t => {
      if (x.f[t] !== undefined && !offen.some(o => o[0] === t)){
        aus += (x.f[t] === true) ? '<' + t + '>' : '<' + t + '=' + x.f[t] + '>';
        offen.push([t, x.f[t]]);
      }
    });
    aus += x.c;
  });
  while (offen.length) aus += '</' + offen.pop()[0] + '>';
  return aus;
}

function attr(f){
  const kl = [], st = [];
  if (f.b) kl.push('f-b');
  if (f.i) kl.push('f-i');
  if (f.u) kl.push('f-u');
  if (f.m) kl.push('f-m');
  if (f.d) kl.push('f-d');   // 3D-Extrusion, Tiefe ueber --tiefe
  // Nur bekannte Werte: ein Text wie <c=red" onmouseover="..."> darf kein Attribut einschleusen
  if (f.c && /^(akzent|#[0-9a-f]{3,8})$/i.test(f.c))
    st.push('color:' + (f.c === 'akzent' ? 'var(--akzent)' : f.c));
  if (f.f && alleSchriften().indexOf(f.f) >= 0) st.push("font-family:'" + f.f + "',var(--schrift),sans-serif");
  return (kl.length ? ' class="' + kl.join(' ') + '"' : '') +
         (st.length ? ' style="' + st.join(';') + '"' : '');
}

function inline(z, off){
  let aus = '', i = 0;
  while (i < z.length){
    if (z[i].c === '\n'){ aus += '<br>'; i++; continue; }
    let j = i;
    while (j < z.length && z[j].c !== '\n' && gleich(z[j].f, z[i].f)) j++;
    aus += '<span data-von="' + (off + i) + '" data-bis="' + (off + j) + '"' + attr(z[i].f) + '>' +
           esc(z.slice(i, j).map(x => x.c).join('')) + '</span>';
    i = j;
  }
  return aus;
}

function absaetze(text){
  const z = zerlege(text);
  const txt = (a, b) => z.slice(a, b).map(x => x.c).join('');
  const zeilen = [];
  let s = 0;
  for (let i = 0; i <= z.length; i++)
    if (i === z.length || z[i].c === '\n'){ zeilen.push([s, i]); s = i + 1; }

  const bloecke = [];
  let akt = [];
  zeilen.forEach(zl => {
    if (txt(zl[0], zl[1]).trim() === ''){ if (akt.length){ bloecke.push(akt); akt = []; } }
    else akt.push(zl);
  });
  if (akt.length) bloecke.push(akt);

  return bloecke.map(bl => {
    const liste = bl.every(zl => txt(zl[0], zl[1]).replace(/^\s+/, '').indexOf('- ') === 0);
    if (liste){
      return bl.map(zl => {
        const roh = txt(zl[0], zl[1]);
        const a = zl[0] + (roh.length - roh.replace(/^\s+/, '').length) + 2;
        return '<p class="li">•  ' + inline(z.slice(a, zl[1]), a) + '</p>';
      }).join('');
    }
    return '<p>' + bl.map((zl, k) => (k ? '<br>' : '') + inline(z.slice(zl[0], zl[1]), zl[0])).join('') + '</p>';
  }).join('');
}

// ----------------------------------------------------------------- Bloecke

function frei(b){ return b && b.x !== undefined && b.y !== undefined; }

function groesseVon(b, st){
  if (b.groesse) return b.groesse;
  if (b.rolle === 'titel') return st.titel;
  if (b.rolle === 'text')  return st.textgroesse;
  return 48;
}
function abstandVon(b, st){
  if (b.abstand) return b.abstand;
  return (b.rolle === 'titel') ? st.titelAbstand : st.textAbstand;
}
function nameVon(b){
  if (b.typ === 'bild') return b.datei || 'Bild';
  if (b.typ === 'form') return b.form === 'icon' ? 'Icon ' + String(b.icon || '').split('/').pop() : 'Form ' + (b.form || '');
  const roh = String(b.text || '').replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
  return roh ? (roh.length > 24 ? roh.slice(0, 24) + '…' : roh) : 'leerer Text';
}

function stilAnwenden(el, stil){
  const s = Object.assign({}, STIL_STD, stil || {});
  const px = ['breite','hoehe','randX','randOben','randUnten','titel','textgroesse'];
  for (const k in s){
    if (k !== 'schrift' && /url|image|\\/i.test(String(s[k]))) continue;   // keine Netzadressen ueber CSS-Variablen
    if (k === 'schrift') el.style.setProperty('--schrift', "'" + (SCHRIFT_OK.test(s[k]) ? s[k] : 'Montserrat') + "'");
    else el.style.setProperty('--' + k, px.indexOf(k) >= 0 ? s[k] + 'px' : s[k]);
  }
  return s;
}

// Stapelung von unten nach oben.
function ebenen(slide){
  const bl = slide.bloecke || [];
  const da = bl.map(b => b.id);
  const folge = (slide.ebenen || []).filter(k => da.indexOf(k) >= 0);
  // Standard: fliessende Bilder nach hinten, danach die Liste
  bl.filter(b => b.typ === 'bild' && !frei(b)).forEach(b => {
    if (folge.indexOf(b.id) < 0) folge.push(b.id);
  });
  da.forEach(k => { if (folge.indexOf(k) < 0) folge.push(k); });
  return folge;
}

function blockBauen(b){
  const el = document.createElement('div');
  el.className = 'box ' + (b.typ === 'bild' ? 'bild' : 'text') +
                 (b.rolle === 'titel' ? ' b-titel' : '') + (b.fett ? ' fett' : '');
  el.dataset.art = b.id;
  if (b.typ === 'bild'){
    // Box (Rahmen, Ecken, Schatten, Deckkraft) > .spiegel (Spiegeln um die Mitte)
    // > .bildflaeche (Bild als cover, Ausschnitt, Filter)
    const sp = document.createElement('div'); sp.className = 'spiegel';
    const fl = document.createElement('div'); fl.className = 'bildflaeche';
    fl.style.backgroundImage = bildUrl(b.datei);
    sp.appendChild(fl); el.appendChild(sp);
    el.dataset.datei = b.datei || '';   // stil.css erkennt daran die Prompt-Kacheln
    bildWirkung(el, b);
  }
  else if (b.typ === 'form'){
    el.className = 'box form' + (b.form === 'icon' ? ' icon' : '');
    if (b.form === 'icon'){
      // Icon als Farbmaske: jede Farbe moeglich, Datei bleibt unveraendert
      const z = document.createElement('div'); z.className = 'zeichen';
      if (ICON_OK.test(b.icon || '')){
        const u = 'url("bib/' + b.icon + '.svg")';
        z.style.webkitMaskImage = u; z.style.maskImage = u;
      }
      z.style.backgroundColor = farbeOder(b.fuellung, '#7fb3a3');
      el.appendChild(z);
    }
    boxWirkung(el, b);                  // die SVG-Form zeichnet renderSlide, sie braucht die Groesse
  }
  else {
    el.innerHTML = '<div class="body">' + absaetze(b.text || '') + '</div>';
    textWirkung(el, b);
  }
  return el;
}

// ------------------------------------------------------------ Formen
const FARBE_OK = /^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;
const ICON_OK = /^(lucide|tabler|tabler-voll)\/[a-z0-9-]{1,80}$/;
const DATEI_OK = /^[A-Za-z0-9_][A-Za-z0-9_.\-]*(\/[A-Za-z0-9_][A-Za-z0-9_.\-]*)*$/;
const FORMEN = ['rechteck', 'kreis', 'dreieck', 'raute', 'stern', 'linie', 'pfeil'];

function farbeOder(v, std){ return FARBE_OK.test(String(v || '')) ? v : std; }
function zahlOder(v, std){ const n = +v; return (v !== null && v !== '' && isFinite(n)) ? n : std; }
// Bilddatei nur mit harmlosen Zeichen in eine CSS-url (wie P.DATEI in projekt.py)
function bildUrl(d){ return DATEI_OK.test(String(d || '')) ? 'url("' + BASIS + d + '")' : 'none'; }

function eingepasst(punkte, w, h, s){
  const xs = punkte.map(p => p[0]), ys = punkte.map(p => p[1]);
  const x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
  const y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
  return punkte.map(p => (s / 2 + (p[0] - x0) / (x1 - x0) * Math.max(0, w - s)).toFixed(2) + ',' +
                         (s / 2 + (p[1] - y0) / (y1 - y0) * Math.max(0, h - s)).toFixed(2)).join(' ');
}
function sternPunkte(){
  const p = [];
  for (let i = 0; i < 10; i++){
    const a = (-90 + i * 36) * Math.PI / 180, r = i % 2 ? 0.382 : 1;
    p.push([Math.cos(a) * r, Math.sin(a) * r]);
  }
  return p;
}
// Form als SVG in Box-Koordinaten. Beim Ziehen streckt der Browser sie
// (preserveAspectRatio none), Linien bleiben dabei gleich dick.
function formSvg(b, w, h){
  w = Math.min(10000, Math.max(1, +w || 200)); h = Math.min(10000, Math.max(1, +h || 200));
  const f = b.form, fill = b.fuellung === 'keine' ? 'none' : farbeOder(b.fuellung, '#7fb3a3');
  const r = b.rand || {}, s = Math.max(0, +r.breite || 0);
  const rand = s ? ' stroke="' + farbeOder(r.farbe, '#000000') + '" stroke-width="' + s + '" stroke-linejoin="round"'
                 : ' stroke="none"';
  const ve = ' vector-effect="non-scaling-stroke"';
  let inhalt = '';
  if (f === 'rechteck'){
    const rx = Math.max(0, Math.min(+b.ecken || 0, (w - s) / 2, (h - s) / 2));
    inhalt = '<rect x="' + s / 2 + '" y="' + s / 2 + '" width="' + Math.max(0, w - s) + '" height="' +
             Math.max(0, h - s) + '" rx="' + rx + '" fill="' + fill + '"' + rand + ve + '/>';
  } else if (f === 'kreis'){
    inhalt = '<ellipse cx="' + w / 2 + '" cy="' + h / 2 + '" rx="' + Math.max(0, (w - s) / 2) + '" ry="' +
             Math.max(0, (h - s) / 2) + '" fill="' + fill + '"' + rand + ve + '/>';
  } else if (f === 'dreieck' || f === 'raute' || f === 'stern'){
    const p = f === 'dreieck' ? [[0.5, 0], [1, 1], [0, 1]]
            : f === 'raute' ? [[0.5, 0], [1, 0.5], [0.5, 1], [0, 0.5]] : sternPunkte();
    inhalt = '<polygon points="' + eingepasst(p, w, h, s) + '" fill="' + fill + '"' + rand + ve + '/>';
  } else if (f === 'linie' || f === 'pfeil'){
    const d = Math.max(1, +b.staerke || 8), farbe = farbeOder(b.fuellung, '#7fb3a3'), y = h / 2;
    const kopf = f === 'pfeil' ? Math.min(w / 2, Math.max(d * 3.2, 18)) : 0;
    const strich = b.strich === 'gestrichelt' ? ' stroke-dasharray="' + d * 3 + ' ' + d * 2 + '"'
                 : b.strich === 'gepunktet' ? ' stroke-dasharray="0.1 ' + d * 2 + '"' : '';
    inhalt = '<line x1="' + d / 2 + '" y1="' + y + '" x2="' + (kopf ? w - kopf * 0.8 : w - d / 2) + '" y2="' + y +
             '" stroke="' + farbe + '" stroke-width="' + d + '" stroke-linecap="round"' + strich + ve + '/>';
    if (kopf) inhalt += '<polygon points="' + (w - kopf) + ',' + (y - kopf * 0.6) + ' ' + w + ',' + y + ' ' +
                        (w - kopf) + ',' + (y + kopf * 0.6) + '" fill="' + farbe + '"/>';
  }
  return '<svg class="formsvg" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none">' + inhalt + '</svg>';
}

// Deckkraft und Schatten fuer Bilder und Formen (Schatten folgt der Form)
function boxWirkung(el, b){
  el.style.opacity = (b.deckkraft !== undefined && +b.deckkraft < 100) ? Math.max(0, +b.deckkraft) / 100 : '';
  el.style.filter = b.schatten ? schattenCss(b.schatten) : '';
}

// ------------------------------------------------------------ Text-Effekte
// Obergrenzen wie im PowerPoint-Export (bauen.py): absurde Werte aus einer
// fremden inhalt.json lassen Chrome sonst minutenlang rechnen.
function grenze(v, std, min, max){ v = +v; return isFinite(v) ? Math.max(min, Math.min(v, max)) : std; }
function textSchatten(s){
  const winkel = ((s.winkel === undefined ? 45 : +s.winkel) * Math.PI) / 180;
  const abstand = grenze(s.abstand === undefined ? 6 : s.abstand, 6, -400, 400);
  return Math.round(Math.cos(winkel) * abstand) + 'px ' + Math.round(Math.sin(winkel) * abstand) + 'px ' +
         Math.min(200, Math.max(0, s.weich === undefined ? 10 : +s.weich || 0)) + 'px ' +
         farbeMitDeckkraft(farbeOder(s.farbe, '#000000'), s.deck === undefined ? 50 : s.deck);
}
function textWirkung(el, b){
  el.style.letterSpacing = b.zeichen ? grenze(b.zeichen, 0, -1000, 5000) / 1000 + 'em' : '';
  el.style.textTransform = b.gross ? 'uppercase' : '';
  el.style.textShadow = b.schatten ? textSchatten(b.schatten) : '';
  const u = b.umriss || {}, ub = grenze(u.breite, 0, 0, 200);
  // Umriss aussen um die Buchstaben (paint-order), hohl = nur der Umriss
  el.style.webkitTextStroke = ub ? (u.hohl ? ub : ub * 2) + 'px ' + farbeOder(u.farbe, '#000000') : '';
  el.style.paintOrder = ub ? 'stroke fill' : '';
  el.style.webkitTextFillColor = (ub && u.hohl) ? 'transparent' : '';
  const fl = b.flaeche;
  el.style.backgroundColor = fl ? farbeMitDeckkraft(farbeOder(fl.farbe, '#ffffff'), fl.deck === undefined ? 100 : fl.deck) : '';
  el.style.borderRadius = fl ? grenze(fl.rund, 0, 0, 2000) + 'px' : '';
  el.style.padding = fl ? (fl.innen === undefined ? 24 : grenze(fl.innen, 24, 0, 500)) + 'px' : '';
}

// ------------------------------------------------------------ Folienhintergrund
function hintergrundCss(hg, st, basis){
  if (!hg) return '';
  if (hg.art === 'verlauf')
    return 'linear-gradient(' + (hg.winkel === undefined ? 180 : +hg.winkel) + 'deg, ' +
           farbeOder(hg.farbe, st.bg) + ', ' + farbeOder(hg.farbe2, '#000000') + ')';
  if (hg.art === 'bild' && DATEI_OK.test(hg.datei || ''))
    return farbeOder(hg.farbe, st.bg) + ' url("' + basis + hg.datei + '") center / cover no-repeat';
  return farbeOder(hg.farbe, '');
}

// ------------------------------------------------------------ Bildwirkung
// Gleiche Regeln in bauen.py (braucht_raster): was hier wirkt, rastert der
// Browser fuer die Canva-Datei, weil PowerPoint es nicht nachbauen kann.

const FILTER_STD = {hell: 100, kontrast: 100, saett: 100, unschaerfe: 0, grau: 0, sepia: 0};

function ausschnittVon(b){
  const a = b.ausschnitt || {};
  return {z: Math.max(1, +a.z || 1),
          x: (a.x === undefined || a.x === null) ? 50 : +a.x,
          y: (a.y === undefined || a.y === null) ? 50 : +a.y};
}
function farbeMitDeckkraft(hex, prozent){
  const h = String(hex || '#000000').replace('#', '');
  const v = h.length === 3 ? h.split('').map(c => c + c).join('') : h.slice(0, 6);
  const n = parseInt(v, 16) || 0;
  return 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' +
         Math.max(0, Math.min(100, +prozent)) / 100 + ')';
}
// Schatten folgt der Form (drop-shadow), auch bei freigestellten Bildern
function schattenCss(s){
  const winkel = ((s.winkel === undefined ? 45 : +s.winkel) * Math.PI) / 180;
  const abstand = grenze(s.abstand === undefined ? 14 : s.abstand, 14, -400, 400);
  return 'drop-shadow(' + Math.round(Math.cos(winkel) * abstand) + 'px ' +
         Math.round(Math.sin(winkel) * abstand) + 'px ' +
         Math.min(200, Math.max(0, s.weich === undefined ? 24 : +s.weich || 0)) + 'px ' +
         farbeMitDeckkraft(farbeOder(s.farbe, '#000000'), s.deck === undefined ? 45 : s.deck) + ')';
}
function bildWirkung(el, b){
  const sp = el.querySelector('.spiegel'), fl = el.querySelector('.bildflaeche');
  if (!sp || !fl) return;
  const a = ausschnittVon(b);
  fl.style.backgroundPosition = a.x + '% ' + a.y + '%';
  fl.style.transformOrigin = a.x + '% ' + a.y + '%';     // Zoom um den gewaehlten Punkt
  fl.style.transform = a.z !== 1 ? 'scale(' + a.z + ')' : '';
  const s = String(b.spiegeln || '');
  const sh = s.indexOf('h') >= 0, sv = s.indexOf('v') >= 0;
  sp.style.transform = (sh || sv) ? 'scale(' + (sh ? -1 : 1) + ',' + (sv ? -1 : 1) + ')' : '';
  const roh = Object.assign({}, FILTER_STD, b.filter || {}), f = {}, t = [];
  for (const k in FILTER_STD) f[k] = zahlOder(roh[k], FILTER_STD[k]);   // nur Zahlen in den Filter
  if (f.hell !== 100)     t.push('brightness(' + f.hell + '%)');
  if (f.kontrast !== 100) t.push('contrast(' + f.kontrast + '%)');
  if (f.saett !== 100)    t.push('saturate(' + f.saett + '%)');
  if (f.grau)             t.push('grayscale(' + f.grau + '%)');
  if (f.sepia)            t.push('sepia(' + f.sepia + '%)');
  if (f.unschaerfe)       t.push('blur(' + Math.min(200, f.unschaerfe) + 'px)');
  fl.style.filter = t.join(' ');
  el.style.borderRadius = b.ecken ? b.ecken + 'px' : '';
  const r = b.rahmen || {};
  el.style.border = +r.breite ? r.breite + 'px solid ' + farbeOder(r.farbe, '#ffffff') : '';
  boxWirkung(el, b);
}

function setzeBox(el, p){
  el.style.left  = p.x + 'px';
  el.style.top   = p.y + 'px';
  el.style.width = p.w + 'px';
  el.style.height = (p.h === undefined || p.h === null) ? 'auto' : p.h + 'px';
  el.style.textAlign = p.aus || 'left';
  el.style.fontFamily = (p.font && SCHRIFT_OK.test(p.font)) ? ("'" + p.font + "', var(--schrift), sans-serif") : '';
  el.style.color = p.farbe || '';
  // Drehung um die Mitte, wie PowerPoint und Canva es auch tun
  el.style.transform = p.dreh ? 'rotate(' + p.dreh + 'deg)' : '';
}

function renderSlide(slide, stil, ziel){
  const st = Object.assign({}, STIL_STD, stil || {});
  ['bg', 'text', 'akzent'].forEach(k => { st[k] = farbeOder(st[k], STIL_STD[k]); });
  const el = document.createElement('div');
  el.className = 'slide';
  stilAnwenden(el, st);
  const hg = hintergrundCss(slide.hg, st, BASIS);    // eigener Hintergrund dieser Folie
  if (hg) el.style.background = hg;
  ziel.appendChild(el);

  const bl = slide.bloecke || [];
  bl.forEach((b, i) => { if (!b.id) b.id = 'b' + (i + 1); });

  const boxen = {};
  bl.forEach(b => { const bx = blockBauen(b); el.appendChild(bx); boxen[b.id] = bx; });

  // Formen stehen immer frei; fehlt die Position, oben links in Standardgroesse
  bl.forEach(b => { if (b.typ === 'form' && !frei(b)){ b.x = b.x || 0; b.y = b.y || 0; b.w = b.w || 200; b.h = b.h || 200; } });
  const flussText = bl.filter(b => !frei(b) && b.typ !== 'bild' && b.typ !== 'form');
  const flussBild = bl.filter(b => !frei(b) && b.typ === 'bild');
  const unten = st.hoehe - st.randUnten - (flussBild.length ? Math.round(st.hoehe * BILD_MIN) : 0);
  const w = st.breite - 2 * st.randX;

  let faktor = 1, layout = {};
  for (let versuch = 0; versuch < 60; versuch++){
    layout = {};
    bl.forEach(b => {
      if (b.typ !== 'bild') boxen[b.id].style.fontSize = (groesseVon(b, st) * faktor) + 'px';
      boxen[b.id].style.lineHeight = abstandVon(b, st);
    });
    bl.forEach(b => { if (frei(b)){ layout[b.id] = Object.assign({}, b); setzeBox(boxen[b.id], b); } });

    let y = st.randOben, erste = true;
    flussText.forEach(b => {
      if (!erste) y += groesseVon(b, st) * faktor * 1.25;
      layout[b.id] = {x: st.randX, y: Math.round(y), w: w,
                      aus: b.aus, font: b.font, farbe: b.farbe,
                      zeichen: b.zeichen, gross: b.gross, schatten: b.schatten,
                      umriss: b.umriss, flaeche: b.flaeche};
      setzeBox(boxen[b.id], layout[b.id]);
      y += boxen[b.id].offsetHeight;
      erste = false;
    });
    const oben = Math.round(y + (erste ? 0 : st.textgroesse * faktor * 1.4));
    flussBild.forEach(b => {
      layout[b.id] = {x: 0, y: oben, w: st.breite, h: Math.max(60, st.hoehe - oben)};
      setzeBox(boxen[b.id], layout[b.id]);
    });
    if (y <= unten || !flussText.length) break;
    faktor *= 0.97;
  }

  // Formen zeichnen, jetzt steht ihre Groesse fest
  bl.forEach(b => {
    if (b.typ === 'form' && b.form !== 'icon' && layout[b.id])
      boxen[b.id].innerHTML = formSvg(b, layout[b.id].w, layout[b.id].h);
  });

  // Endgueltige Werte fuer den Export mitgeben
  bl.forEach(b => {
    const L = layout[b.id];
    if (!L) return;
    if (b.typ !== 'bild' && b.typ !== 'form'){
      L.groesse  = groesseVon(b, st) * faktor;
      L.abstand  = abstandVon(b, st);
      L.rolle    = b.rolle || null;
      if (b.fett) L.fett = true;
    }
    L.hBox = boxen[b.id].offsetHeight;     // echte Hoehe, auch bei Text (Ausrichten, Drehen im Export)
  });

  ebenen(slide).forEach(k => { if (boxen[k]) el.appendChild(boxen[k]); });
  return {el: el, boxen: boxen, masse: {faktor: faktor, layout: layout}};
}

// Google Fonts, die im Cockpit geladen wurden (schriften.py), kommen dazu
const SCHRIFT_OK = /^[A-Za-z0-9 ]{1,60}$/;
let SCHRIFTEN_EXTRA = [];
function alleSchriften(){
  return SCHRIFTEN.concat(SCHRIFTEN_EXTRA.filter(n => SCHRIFTEN.indexOf(n) < 0));
}
async function schriftenLaden(){
  try {
    const l = await (await fetch('fonts/google.json', {cache: 'no-store'})).json();
    SCHRIFTEN_EXTRA = l.map(e => e.family).filter(n => SCHRIFT_OK.test(n));
  } catch (e) { SCHRIFTEN_EXTRA = []; }
}
// Welche Schriften benutzt ein Karussell? (globale, je Block, <f=...> im Text)
function benutzteSchriften(d){
  const n = new Set();
  if (!d) return n;
  if (d.stil && d.stil.schrift) n.add(d.stil.schrift);
  (d.slides || []).forEach(s => (s.bloecke || []).forEach(b => {
    if (b.font) n.add(b.font);
    String(b.text || '').replace(/<f=([^>]{1,64})>/g, (m, f) => { n.add(f); return m; });
  }));
  return n;
}
async function schriftBereit(d){
  const auf = [];
  const extra = d ? SCHRIFTEN_EXTRA.filter(x => benutzteSchriften(d).has(x)) : [];
  SCHRIFTEN.concat(extra).forEach(n => {
    auf.push(document.fonts.load("400 40px '" + n + "'"));
    auf.push(document.fonts.load("700 84px '" + n + "'"));
    auf.push(document.fonts.load("800 84px '" + n + "'"));
  });
  await Promise.all(auf.map(x => x.catch(() => null)));
  await document.fonts.ready;
}
