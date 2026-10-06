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
// Nur gepruefte Werte, kurz und einzeilig: Namen landen auch in Hinweisen fuer k.py
function nameVon(b){
  if (b.typ === 'bild') return (typeof b.datei === 'string' && DATEI_OK.test(b.datei) && b.datei.slice(0, 40)) ||
                               (istGeraet(b) ? GERAETE_NAMEN[b.geraet] + ' (leer)' : istMaske(b) ? 'Rahmen ' + MASKEN_NAMEN[b.maske] : 'Bild');
  if (b.typ === 'form') return b.form === 'icon' ? 'Icon' + (ICON_OK.test(b.icon || '') ? ' ' + b.icon.split('/').pop() : '')
                                                 : 'Form' + (FORMEN.indexOf(b.form) >= 0 ? ' ' + b.form : '');
  // [^<>] statt [^>]: bleibt linear, auch bei Tausenden "<" ohne ">"
  const roh = String(b.text || '').slice(0, 2000).replace(/<[^<>]*>/g, '').replace(/\s+/g, ' ').trim();
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
  if (b.nahtlos && frei(b)) el.dataset.nahtlos = '1';   // je Box, nicht je ID (IDs koennen doppelt sein)
  if (b.typ === 'bild'){
    // Box (Rahmen, Ecken, Schatten, Deckkraft) > .spiegel (Spiegeln um die Mitte)
    // > .bildflaeche (Bild als cover, Ausschnitt, Filter)
    const sp = document.createElement('div'); sp.className = 'spiegel';
    const fl = document.createElement('div'); fl.className = 'bildflaeche';
    if (b.datei) fl.style.backgroundImage = bildUrl(b.datei);   // leer: Platzhalter aus dem Cockpit-CSS
    sp.appendChild(fl); el.appendChild(sp);
    el.dataset.datei = b.datei || '';   // stil.css erkennt daran die Prompt-Kacheln
    if (!b.datei) el.classList.add('leer');
    if (istGeraet(b)) el.classList.add('geraet');
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
const MAX_BLOECKE = 200;                         // je Folie, wie in bauen.py
const ICON_OK = /^(lucide|tabler|tabler-voll)\/[a-z0-9-]{1,80}$/;
const DATEI_OK = /^[A-Za-z0-9_][A-Za-z0-9_.\-]*(\/[A-Za-z0-9_][A-Za-z0-9_.\-]*)*$/;
const FORMEN = ['rechteck', 'kreis', 'dreieck', 'raute', 'stern', 'linie', 'pfeil'];

function farbeOder(v, std){ return typeof v === 'string' && FARBE_OK.test(v) ? v : std; }
// Nur echte Namen aus den Listen, nie Objekte oder Prototyp-Schluessel aus einer fremden Datei
function istGeraet(b){ return !!b && typeof b.geraet === 'string' && Object.prototype.hasOwnProperty.call(GERAETE, b.geraet); }
function istMaske(b){ return !!b && typeof b.maske === 'string' && MASKEN.indexOf(b.maske) >= 0; }
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

// ------------------------------------------------------------ Bild in Form, Geraete-Rahmen
// maske: das Bild wird in eine Form geschnitten (CSS-Maske aus einem SVG).
// geraet: das Bild sitzt als Bildschirm in einem gezeichneten Geraet.
// Beides zeichnet renderSlide, sobald die Groesse feststeht; fuer die
// Canva-Datei rastert der Browser es (braucht_raster in bauen.py).
const MASKEN = ['kreis', 'bogen', 'herz', 'stern', 'sechseck', 'blob', 'raute', 'dreieck'];
const MASKEN_NAMEN = {kreis: 'Kreis', bogen: 'Bogen', herz: 'Herz', stern: 'Stern', sechseck: 'Sechseck',
                      blob: 'Organisch', raute: 'Raute', dreieck: 'Dreieck'};
// Seitenverhaeltnis Breite/Hoehe, 0 = frei
const GERAETE = {handy: 0.49, tablet: 0.75, laptop: 1.6, browser: 0};
const GERAETE_NAMEN = {handy: 'Handy', tablet: 'Tablet', laptop: 'Laptop', browser: 'Browserfenster'};
const GERAET_FARBE = {handy: '#1d1d1f', tablet: '#1d1d1f', laptop: '#2b2c2f', browser: '#e9ebee'};
// Formen im Feld 0..100, nur absolute M/L/C/Z mit Zahlenpaaren (werden auf die Box skaliert)
const MASKE_PFAD = {
  herz: 'M50,94 C34,82 4,64 4,36 C4,18 17,6 31,6 C40,6 46,11 50,18 C54,11 60,6 69,6 C83,6 96,18 96,36 C96,64 66,82 50,94 Z',
  blob: 'M52,4 C70,3 88,13 95,30 C102,48 96,68 84,82 C72,96 52,100 35,94 C18,88 4,74 2,56 C0,38 8,22 22,12 C31,6 41,4 52,4 Z',
  sechseck: 'M25,0 L75,0 L100,50 L75,100 L25,100 L0,50 Z',
  raute: 'M50,0 L100,50 L50,100 L0,50 Z',
  dreieck: 'M50,0 L100,100 L0,100 Z'
};
(function(){                                   // Stern aus sternPunkte, auf 0..100 gebracht
  const p = sternPunkte(), xs = p.map(q => q[0]), ys = p.map(q => q[1]);
  const x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
  const y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys);
  MASKE_PFAD.stern = p.map((q, i) => (i ? 'L' : 'M') + ((q[0] - x0) / (x1 - x0) * 100).toFixed(2) + ',' +
                                     ((q[1] - y0) / (y1 - y0) * 100).toFixed(2)).join(' ') + ' Z';
})();

// Umriss als SVG-Element in Box-Pixeln. e = Einzug (fuer einen Rand, der sonst
// an der Boxkante halb abgeschnitten wuerde).
function maskeForm(form, w, h, attr, e){
  e = e || 0;
  const W = Math.max(1, w - 2 * e), H = Math.max(1, h - 2 * e), f = n => (+n).toFixed(2);
  if (form === 'kreis')
    return '<ellipse cx="' + f(w / 2) + '" cy="' + f(h / 2) + '" rx="' + f(W / 2) + '" ry="' + f(H / 2) + '" ' + attr + '/>';
  if (form === 'bogen'){
    const rx = W / 2, ry = Math.min(W / 2, H);
    return '<path d="M' + f(e) + ',' + f(e + H) + ' L' + f(e) + ',' + f(e + ry) + ' A' + f(rx) + ',' + f(ry) +
           ' 0 0 1 ' + f(e + W) + ',' + f(e + ry) + ' L' + f(e + W) + ',' + f(e + H) + ' Z" ' + attr + '/>';
  }
  const roh = Object.prototype.hasOwnProperty.call(MASKE_PFAD, form) ? MASKE_PFAD[form] : '';
  if (!roh) return '';
  let i = 0;                                   // Zahlen abwechselnd als x und y skalieren
  const d = roh.replace(/-?\d+(\.\d+)?/g, z => (i++ % 2 === 0 ? f(e + z / 100 * W) : f(e + z / 100 * H)));
  return '<path d="' + d + '" ' + attr + '/>';
}
// Als CSS-Maske. Ohne Klammern und Hochkommas, damit url(...) ueberall sauber bleibt.
function maskeUrl(form, w, h, e){
  if (!e && form !== 'bogen'){ w = 100; h = 100; }   // gestreckt identisch, der Browser teilt sie sich
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + w.toFixed(2) + ' ' + h.toFixed(2) +
              '" preserveAspectRatio="none">' + maskeForm(form, w, h, 'fill="#fff"', e) + '</svg>';
  return 'url("data:image/svg+xml,' + encodeURIComponent(svg).replace(/\(/g, '%28').replace(/\)/g, '%29')
                                                               .replace(/'/g, '%27') + '")';
}
function maskeAnwenden(el, b, w, h){
  const sp = el.querySelector('.spiegel');
  if (!sp || !w || !h) return;
  const r = b.rahmen || {}, s = Math.max(0, Math.min(60, +r.breite || 0));
  const u = maskeUrl(b.maske, w, h, s / 2);
  sp.style.webkitMaskImage = u; sp.style.maskImage = u;
  sp.style.webkitMaskSize = sp.style.maskSize = '100% 100%';
  sp.style.webkitMaskRepeat = sp.style.maskRepeat = 'no-repeat';
  if (s){                                       // Rand folgt der Form
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'maskenrand');
    svg.setAttribute('viewBox', '0 0 ' + w.toFixed(2) + ' ' + h.toFixed(2));
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.innerHTML = maskeForm(b.maske, w, h, 'fill="none" stroke="' + farbeOder(r.farbe, '#ffffff') +
                              '" stroke-width="' + s + '" stroke-linejoin="round" vector-effect="non-scaling-stroke"', s / 2);
    el.appendChild(svg);
  }
}

function farbeHell(hex){
  const h = String(hex).replace('#', ''), v = h.length < 6 ? h.split('').map(c => c + c).join('') : h.slice(0, 6);
  const n = parseInt(v, 16) || 0;
  return (0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255 > 0.6;
}
// Geraet in Box-Pixeln: Koerper (unter dem Bild), Bildschirm-Rechteck, Teile ueber dem Bild.
// Passt die Box nicht zum Geraet, sitzt es mittig darin.
function geraetTeile(typ, W, H, farbe){
  const r = GERAETE[typ];
  let w = W, h = H, ox = 0, oy = 0;
  if (r){ if (W / H > r){ w = H * r; ox = (W - w) / 2; } else { h = W / r; oy = (H - h) / 2; } }
  const f = n => (+n).toFixed(2), hell = farbeHell(farbe);
  const kante = hell ? 'rgba(0,0,0,0.16)' : 'rgba(255,255,255,0.22)';
  const R = (x, y, ww, hh, rr, fuell, extra) => '<rect x="' + f(ox + x) + '" y="' + f(oy + y) + '" width="' +
    f(Math.max(0, ww)) + '" height="' + f(Math.max(0, hh)) + '" rx="' + f(Math.max(0, rr)) + '" fill="' + fuell + '"' + (extra || '') + '/>';
  const rand = (rr, x, y, ww, hh) => R((x || 0) + 0.75, (y || 0) + 0.75, (ww || w) - 1.5, (hh || h) - 1.5, rr - 0.75, 'none',
                                       ' stroke="' + kante + '" stroke-width="1.5"');
  let k = '', o = '', s;
  if (typ === 'handy'){
    const rad = w * 0.15, b = w * 0.042, iw = w * 0.3, ih = w * 0.088;
    k = R(0, 0, w, h, rad, farbe) + rand(rad);
    s = {x: b, y: b, w: w - 2 * b, h: h - 2 * b, r: f(rad - b) + 'px', grund: '#0b0b0c'};
    o = R((w - iw) / 2, b + w * 0.032, iw, ih, ih / 2, '#050505');
  } else if (typ === 'tablet'){
    const rad = w * 0.06, b = w * 0.048;
    k = R(0, 0, w, h, rad, farbe) + rand(rad);
    s = {x: b, y: b, w: w - 2 * b, h: h - 2 * b, r: f(rad * 0.45) + 'px', grund: '#0b0b0c'};
    o = '<circle cx="' + f(ox + w / 2) + '" cy="' + f(oy + b / 2) + '" r="' + f(w * 0.009) + '" fill="' +
        (hell ? '#9aa0a6' : '#3a3a3c') + '"/>';
  } else if (typ === 'laptop'){
    const dx = w * 0.075, dw = w - 2 * dx, dh = h * 0.915, rad = w * 0.022, b = w * 0.02, kinn = w * 0.032;
    const fh = h - dh, rr = fh * 0.7;
    k = R(dx, 0, dw, dh + rad, rad, farbe) + rand(rad, dx, 0, dw, dh + rad) +
        '<path d="M' + f(ox) + ',' + f(oy + dh) + ' L' + f(ox + w) + ',' + f(oy + dh) + ' L' + f(ox + w) + ',' +
        f(oy + h - rr) + ' Q' + f(ox + w) + ',' + f(oy + h) + ' ' + f(ox + w - rr) + ',' + f(oy + h) + ' L' +
        f(ox + rr) + ',' + f(oy + h) + ' Q' + f(ox) + ',' + f(oy + h) + ' ' + f(ox) + ',' + f(oy + h - rr) + ' Z" fill="' +
        farbe + '" stroke="' + kante + '" stroke-width="1.5"/>' +
        R(w * 0.43, dh, w * 0.14, fh * 0.32, fh * 0.16, hell ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.35)');
    s = {x: dx + b, y: b, w: dw - 2 * b, h: dh - b - kinn, r: f(rad * 0.35) + 'px', grund: '#0b0b0c'};
    o = '<circle cx="' + f(ox + w / 2) + '" cy="' + f(oy + b / 2) + '" r="' + f(w * 0.004) + '" fill="#3a3a3c"/>';
  } else {                                       // browser
    const rad = Math.min(w, h) * 0.025, l = Math.min(h * 0.16, Math.max(w * 0.06, 26));
    k = R(0, 0, w, h, rad, farbe) + rand(rad);
    ['#ff5f57', '#febc2e', '#28c840'].forEach((c, i) => {
      k += '<circle cx="' + f(ox + l * 0.55 + i * l * 0.5) + '" cy="' + f(oy + l / 2) + '" r="' + f(l * 0.14) + '" fill="' + c + '"/>';
    });
    k += R(l * 2.1, l * 0.22, w - l * 2.7, l * 0.56, l * 0.28, hell ? '#ffffff' : 'rgba(255,255,255,0.12)');
    s = {x: 0, y: l, w: w, h: h - l, r: '0 0 ' + f(rad) + 'px ' + f(rad) + 'px', grund: '#ffffff'};
  }
  s.x += ox; s.y += oy;
  return {koerper: k, schirm: s, oben: o};
}
function geraetBauen(el, b, w, h){
  const sp = el.querySelector('.spiegel');
  if (!sp || !w || !h) return;
  const t = geraetTeile(b.geraet, w, h, farbeOder(b.geraetfarbe, GERAET_FARBE[b.geraet]));
  const svg = (klasse, inhalt) => {
    const e = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    e.setAttribute('class', klasse);
    e.setAttribute('viewBox', '0 0 ' + w.toFixed(2) + ' ' + h.toFixed(2));
    e.setAttribute('preserveAspectRatio', 'none');
    e.innerHTML = inhalt;
    return e;
  };
  const s = t.schirm, schirm = document.createElement('div');
  schirm.className = 'bildschirm';
  // in Prozent, damit beim Ziehen im Cockpit alles mitwaechst
  schirm.style.left = (s.x / w * 100) + '%'; schirm.style.top = (s.y / h * 100) + '%';
  schirm.style.width = (s.w / w * 100) + '%'; schirm.style.height = (s.h / h * 100) + '%';
  schirm.style.borderRadius = s.r; schirm.style.background = s.grund;
  el.insertBefore(svg('geraetkoerper', t.koerper), sp);
  schirm.appendChild(sp);
  el.appendChild(schirm);
  if (t.oben) el.appendChild(svg('geraetoben', t.oben));
}
function rahmenZeichnen(el, b, w, h){
  if (b.typ !== 'bild') return;
  if (istGeraet(b)) geraetBauen(el, b, w, h);
  else if (istMaske(b)) maskeAnwenden(el, b, w, h);
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
  // Bild in der Schrift: das Foto fuellt die Buchstaben. Ein Schatten wirkt dann
  // als drop-shadow, text-shadow laege sonst ueber dem Bild. Flaeche entfaellt.
  const bf = typeof b.bildfuellung === 'string' && DATEI_OK.test(b.bildfuellung) ? b.bildfuellung : '';
  el.classList.toggle('bildschrift', !!bf);
  el.style.backgroundImage = bf ? 'url("' + BASIS + bf + '")' : '';
  el.style.webkitBackgroundClip = el.style.backgroundClip = bf ? 'text' : '';
  if (bf){
    el.style.webkitTextFillColor = 'transparent';
    el.style.backgroundColor = ''; el.style.borderRadius = ''; el.style.padding = '';
    el.style.textShadow = '';
    el.style.filter = b.schatten ? schattenCss(Object.assign({abstand: 6, weich: 10, deck: 50}, b.schatten)) : '';
  } else el.style.filter = '';
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
  const eigen = istMaske(b) || istGeraet(b);
  el.style.borderRadius = (b.ecken && !eigen) ? b.ecken + 'px' : '';
  const r = b.rahmen || {};
  el.style.border = (+r.breite && !eigen) ? r.breite + 'px solid ' + farbeOder(r.farbe, '#ffffff') : '';
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

  const bl = (slide.bloecke || []).slice(0, MAX_BLOECKE);   // fremde Dateien mit Tausenden Bloecken
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

  // Formen, Bild-Formen und Geraete zeichnen, jetzt steht ihre Groesse fest
  bl.forEach(b => {
    if (b.typ === 'form' && b.form !== 'icon' && layout[b.id])
      boxen[b.id].innerHTML = formSvg(b, layout[b.id].w, layout[b.id].h);
    if (b.typ === 'bild' && layout[b.id])
      rahmenZeichnen(boxen[b.id], b, +layout[b.id].w || boxen[b.id].offsetWidth,
                     +layout[b.id].h || boxen[b.id].offsetHeight);
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

// ------------------------------------------------------------ Nahtloses Karussell
// Ein frei gesetzter Block mit "nahtlos" darf ueber den Folienrand ragen und
// laeuft auf der Nachbarfolie weiter (dort als Gast, eine Kopie seiner Box).
// Wie eine durchgehende Leinwand von links nach rechts: Gaeste von frueheren
// Folien liegen unter den eigenen Bloecken, Gaeste von spaeteren darueber.
// Ohne "nahtlos" wird am Rand abgeschnitten wie bisher.
function nahtlosBloecke(slide){
  return (slide && slide.bloecke || []).filter(b => b && b.nahtlos && frei(b));
}
// Grenzen gegen fremde Dateien: Instagram erlaubt 20 Folien, mehr Gaeste braucht keine Folie
const NAHTLOS_REICHWEITE = 19, NAHTLOS_MAX_GAESTE = 200;
// cache: Map Folie -> ueberstehende Boxen, damit Minis und Buehne jede Nachbarfolie nur
// einmal je Zeichnen unsichtbar aufbauen.
function renderFolie(slides, i, stil, ziel, cache){
  const r = renderSlide(slides[i], stil, ziel);
  r.gaeste = [];
  if (!Array.isArray(slides) || slides.length < 2) return r;
  const B = +(Object.assign({}, STIL_STD, stil || {})).breite || 1080;
  const unten = [], oben = [];
  slides.forEach((s, m) => {
    if (m === i || Math.abs(m - i) > NAHTLOS_REICHWEITE || r.gaeste.length >= NAHTLOS_MAX_GAESTE) return;
    const abst = (m - i) * B;
    // Vorpruefung aus den Daten: kann ein nahtloser Block diese Folie ueberhaupt erreichen?
    const kandidat = nahtlosBloecke(s).some(b => {
      const w = +b.w || 0, pad = +b.dreh ? Math.max(w, +b.h || w) : 0;
      return +b.x + abst - pad < B && +b.x + w + abst + pad > 0;
    });
    if (!kandidat) return;
    let teile = cache && cache.get(m);
    if (!teile){
      teile = [];
      const tmp = document.createElement('div');
      tmp.style.cssText = 'position:absolute;left:-40000px;top:0;visibility:hidden;pointer-events:none';
      document.body.appendChild(tmp);
      try {
        const n = renderSlide(s, stil, tmp), s0 = n.el.getBoundingClientRect();
        Array.prototype.forEach.call(n.el.children, bx => {         // in Stapelreihenfolge
          if (!bx.classList || !bx.classList.contains('box') || bx.dataset.nahtlos !== '1') return;
          const rr = bx.getBoundingClientRect();
          teile.push({bx: bx, l: rr.left - s0.left, r: rr.right - s0.left});
        });
      } catch (e) { teile = []; }                // eine kaputte Nachbarfolie legt diese nicht lahm
      finally { tmp.remove(); }
      if (cache) cache.set(m, teile);
    }
    teile.forEach(o => {
      if (r.gaeste.length >= NAHTLOS_MAX_GAESTE || o.r + abst <= 0.5 || o.l + abst >= B - 0.5) return;
      const id = o.bx.dataset.art, g = o.bx.cloneNode(true);
      g.classList.add('gast');
      g.dataset.gast = (m + 1) + ':' + id;
      g.dataset.art = 'gast-' + (m + 1) + '-' + id;
      g.style.left = (parseFloat(o.bx.style.left) + abst) + 'px';
      (m < i ? unten : oben).push(g);
      r.gaeste.push({art: g.dataset.art, folie: m + 1, id: id, lage: m < i ? 'unten' : 'oben'});
    });
  });
  const erstes = Array.prototype.find.call(r.el.children, x => x.classList && x.classList.contains('box'));
  unten.forEach(g => r.el.insertBefore(g, erstes || null));
  oben.forEach(g => r.el.appendChild(g));
  return r;
}

// ------------------------------------------------------------ Instagram-Format
// Das Profilraster zeigt jedes Vorschaubild als 3:4-Kachel (gemessen 05.10.2026):
// was breiter ist (4:5), verliert links und rechts, was hoeher ist, oben und unten.
// In der Beitragsansicht bleibt alles sichtbar.
function profilAusschnitt(B, H){
  B = +B || STIL_STD.breite; H = +H || STIL_STD.hoehe;
  return {x: Math.max(0, (B - H * 3 / 4) / 2), y: Math.max(0, (H - B * 4 / 3) / 2)};
}

// Unsichtbar aufbauen und messen, danach ist der Platz wieder leer
function unsichtbar(f){
  const tmp = document.createElement('div');
  tmp.style.cssText = 'position:absolute;left:-40000px;top:0;visibility:hidden;pointer-events:none';
  document.body.appendChild(tmp);
  try { return f(tmp); } finally { tmp.remove(); }
}

// Welche Elemente der ersten Folie reichen in den Streifen, den das Profilraster
// abschneidet? Text zaehlt mit seinen Buchstaben, nicht mit der breiten Box.
// Was schon ueber den Folienrand ragt, ist gewollt angeschnitten und zaehlt nicht,
// ebenso Bilder und Formen bis an den Rand (Hintergrund) und Teile, die von der
// Nachbarfolie hereinlaufen.
function profilRandPruefen(slides, stil){
  const st = Object.assign({}, STIL_STD, stil || {});
  const B = +st.breite, H = +st.hoehe, a = profilAusschnitt(B, H);
  if (!Array.isArray(slides) || !slides.length || (a.x < 1 && a.y < 1)) return [];
  return unsichtbar(tmp => {
    const r = renderFolie(slides, 0, stil, tmp), s0 = r.el.getBoundingClientRect();
    const namen = [], bl = (slides[0].bloecke || []).slice(0, MAX_BLOECKE);
    Array.prototype.forEach.call(r.el.children, bx => {
      if (!bx.classList || !bx.classList.contains('box') || bx.classList.contains('gast')) return;
      const b = bl.find(x => x.id === bx.dataset.art);
      if (!b) return;
      const box = bx.getBoundingClientRect();
      const l0 = box.left - s0.left, r0 = box.right - s0.left, o0 = box.top - s0.top, u0 = box.bottom - s0.top;
      if (l0 < -1 || r0 > B + 1 || o0 < -1 || u0 > H + 1) return;       // gewollt angeschnitten
      const text = bx.classList.contains('text');
      if (!text && (l0 <= 1 || r0 >= B - 1 || o0 <= 1 || u0 >= H - 1)) return;   // Flaeche bis an den Rand
      let l = l0, r = r0, o = o0, u = u0;
      if (text){
        // nur die Buchstaben: Rechtecke der Textstuecke, nicht die der Absaetze (volle Breite)
        const teile = [], w = document.createTreeWalker(bx, NodeFilter.SHOW_TEXT);
        for (let t = w.nextNode(); t; t = w.nextNode()){
          if (!t.nodeValue.trim()) continue;
          const z = document.createRange(); z.selectNodeContents(t);
          Array.prototype.forEach.call(z.getClientRects(), q => { if (q.width > 0.5 && q.height > 0.5) teile.push(q); });
        }
        if (!teile.length) return;
        l = Math.min.apply(null, teile.map(q => q.left)) - s0.left;
        r = Math.max.apply(null, teile.map(q => q.right)) - s0.left;
        o = Math.min.apply(null, teile.map(q => q.top)) - s0.top;
        u = Math.max.apply(null, teile.map(q => q.bottom)) - s0.top;
      }
      const drin = l >= a.x - 0.5 && r <= B - a.x + 0.5 && o >= a.y - 0.5 && u <= H - a.y + 0.5;
      if (!drin && namen.indexOf(nameVon(b)) < 0) namen.push(nameVon(b));
    });
    return namen;
  });
}

// Format wechseln, z. B. 3:4 (1080 x 1440) und 4:5 (1080 x 1350). Die Breite bleibt.
// Fliessende Bloecke ordnet das Layout selbst neu (Raender wie bei einem neuen
// Karussell in diesem Format). Frei gesetzte Bloecke behalten Groesse und Schrift:
//  - Was sich in der Hoehe ueberschneidet, bildet eine Zeile und rueckt gemeinsam
//    (Text auf einer Karte, Bild neben Text, Gruppen). Nur der Freiraum ueber,
//    zwischen und unter den Zeilen wird gestaucht oder gedehnt, ueberall im
//    gleichen Verhaeltnis; enge Abstaende bleiben also eng.
//  - Am oberen Rand bleibt oben, am unteren Rand bleibt unten (dort ist kein Freiraum).
//  - Fotos, Rechtecke und Linien ueber die ganze Hoehe wachsen oder schrumpfen mit.
//    Alles andere behaelt seine Groesse, auch grosse Bilder und Karten.
// Hin und zurueck ergibt wieder das Original (bis auf 1 px Rundung).
// Gibt {daten, hinweise} zurueck, d selbst bleibt unveraendert. Cockpit und
// k.py (ueber vorlage.html) rechnen beide hier, damit beide dasselbe tun.
const AM_RAND = 2;                                   // px: so nah gilt als "am Rand"
const FORMAT_RAENDER = {1350: {randOben: 354, randUnten: 94}, 1440: {randOben: 377, randUnten: 100}};
function streckbar(b){
  if (b.h === undefined || b.h === null || b.h === '' || !isFinite(+b.h)) return false;
  if (b.typ === 'bild') return !istMaske(b) && !(istGeraet(b) && GERAETE[b.geraet] > 0);
  return b.typ === 'form' && (b.form === 'rechteck' || b.form === 'linie');
}
// Seitenverhaeltnis einer Bilddatei (0, wenn sie nicht oder nicht in 3 s laedt)
function bildVerhaeltnis(url){
  return new Promise(fertig => {
    const i = new Image(), uhr = setTimeout(() => fertig(0), 3000);
    i.onload = () => { clearTimeout(uhr); fertig(i.naturalWidth && i.naturalHeight ? i.naturalWidth / i.naturalHeight : 0); };
    i.onerror = () => { clearTimeout(uhr); fertig(0); };
    i.src = url;
  });
}
const MAX_FOLIEN_UMSTELLEN = 100;                // Instagram erlaubt 20; fremde Dateien bremsen sonst
async function formatUmstellen(d, hoeheNeu){
  const neu = JSON.parse(JSON.stringify(d || {}));
  const st = Object.assign({}, STIL_STD, neu.stil || {});
  const H0 = +st.hoehe, H1 = Math.round(+hoeheNeu), B = +st.breite;
  if (!(H1 >= 100 && H1 <= 8000) || !(H0 >= 100 && H0 <= 8000) || !(B >= 100 && B <= 5000))
    throw new Error('Format ungueltig');
  const hinweise = [], basis = BASIS;            // Ordner merken: unten wird noch gewartet
  if (H1 === H0) return {daten: neu, hinweise: hinweise};
  if (Array.isArray(neu.slides) && neu.slides.length > MAX_FOLIEN_UMSTELLEN)
    throw new Error('Zu viele Folien (hoechstens ' + MAX_FOLIEN_UMSTELLEN + ')');
  const k = H1 / H0, dH = H1 - H0;
  // Raender des fliessenden Layouts: Standardwerte des Zielformats, eigene im Verhaeltnis
  const stilNeu = Object.assign({}, neu.stil || {}, {hoehe: H1});
  ['randOben', 'randUnten'].forEach(f => {
    const v = +st[f], alt = FORMAT_RAENDER[H0], ziel = FORMAT_RAENDER[H1];
    stilNeu[f] = alt && ziel && v === alt[f] ? ziel[f] : Math.round(v * k);
  });
  const slides = Array.isArray(neu.slides) ? neu.slides : [];
  const flaeche = (L, b) => {
    const l = L.layout[b.id];
    if (!l) return null;
    const x = +l.x || 0, y = +l.y || 0;
    return {l: x, r: x + (+l.w || 0), o: y, u: y + (+l.hBox || 0)};
  };
  const ueber = (a, b) => Math.min(a.r, b.r) - Math.max(a.l, b.l) > 2 && Math.min(a.u, b.u) - Math.max(a.o, b.o) > 2;
  const grafiken = new Map();      // gestreckte SVG-Grafiken: Linien am Rand koennen wegfallen
  unsichtbar(tmp => {
    slides.forEach((s, i) => {
      if (!s || typeof s !== 'object') return;
      tmp.innerHTML = '';
      const L0 = renderSlide(s, neu.stil, tmp).masse;     // misst die Texthoehen, vergibt fehlende IDs
      const alle = (s.bloecke || []).slice(0, MAX_BLOECKE);
      const hoehe = b => streckbar(b) ? +b.h : (+(L0.layout[b.id] || {}).hBox || 0);
      const namen = new Map(), name = b => { if (!namen.has(b)) namen.set(b, nameVon(b)); return namen.get(b); };
      // Einheiten: eine Gruppe rueckt als Ganzes, sonst jeder Block fuer sich
      const einheiten = new Map();
      alle.forEach((b, j) => {
        if (!frei(b) || !L0.layout[b.id]) return;
        const key = b.gruppe ? 'g:' + String(b.gruppe).slice(0, 60) : 'b:' + j;
        const e = einheiten.get(key) || {bloecke: [], o: Infinity, u: -Infinity};
        const o = zahlOder(b.y, 0);
        e.bloecke.push(b); e.o = Math.min(e.o, o); e.u = Math.max(e.u, o + hoehe(b));
        einheiten.set(key, e);
      });
      const inhalt = [], flaechen = [], ganze = [];
      einheiten.forEach(e => {
        const ganz = e.o <= AM_RAND && e.u >= H0 - AM_RAND, b = e.bloecke.length === 1 ? e.bloecke[0] : null;
        if (ganz && b && streckbar(b)) flaechen.push(e);
        else if (ganz) ganze.push(e);          // z. B. Gruppe oder Kreis ueber die ganze Hoehe
        else inhalt.push(e);
      });
      const zeilen = [];
      inhalt.map(e => ({e: e, o: Math.max(0, Math.min(H0, e.o)), u: Math.max(0, Math.min(H0, e.u))}))
        .sort((a, b) => a.o - b.o)
        .forEach(x => {
          const z = zeilen[zeilen.length - 1];
          if (z && x.o < z.u){ z.u = Math.max(z.u, x.u); z.teile.push(x.e); }
          else zeilen.push({o: x.o, u: x.u, teile: [x.e]});
        });
      let luft = 0, vor = 0;
      zeilen.forEach(z => { luft += z.o - vor; vor = z.u; });
      luft += H0 - vor;
      const f = luft > 0 ? Math.max(0, (luft + dH) / luft) : 1;
      // Hoehe vorher -> nachher als Kurve durch die Zeilenkanten, dazwischen gleichmaessig
      const punkte = [[0, 0]];
      let y = 0; vor = 0;
      zeilen.forEach(z => {
        y += (z.o - vor) * f;
        z.schub = y - z.o;
        punkte.push([z.o, y], [z.u, y + z.u - z.o]);
        y += z.u - z.o; vor = z.u;
      });
      punkte.push([H0, H1]);
      const M = v => {
        if (v <= 0) return v;
        if (v >= H0) return v + dH;
        for (let p = 1; p < punkte.length; p++){
          const a = punkte[p - 1], b = punkte[p];
          if (v <= b[0]) return b[0] > a[0] ? a[1] + (v - a[0]) * (b[1] - a[1]) / (b[0] - a[0]) : b[1];
        }
        return v + dH;
      };
      zeilen.forEach(z => z.teile.forEach(e => e.bloecke.forEach(b => {
        if (Math.round(z.schub)) b.y = Math.round(zahlOder(b.y, 0) + z.schub);
      })));
      flaechen.forEach(e => {
        const b = e.bloecke[0], o = M(e.o), u = M(e.u);
        b.y = Math.round(o); b.h = Math.max(1, Math.round(u - o));
        if (b.typ === 'bild' && DATEI_OK.test(String(b.datei || '')) && /\.svg$/i.test(b.datei))
          grafiken.set(b.datei, (grafiken.get(b.datei) || []).concat({nr: i + 1, v: (+b.w || 0) / b.h}));
      });
      ganze.forEach(e => {
        const m = (e.o + e.u) / 2, schub = M(m) - m;
        if (Math.round(schub)) e.bloecke.forEach(b => { b.y = Math.round(zahlOder(b.y, 0) + schub); });
      });
      // Nachher messen: was ist kleiner geworden, was ragt hinaus, was stoesst neu zusammen?
      tmp.innerHTML = '';
      const L1 = renderSlide(s, stilNeu, tmp).masse;
      const nr = 'Folie ' + (i + 1) + ': ';
      if (L1.faktor < L0.faktor - 0.005)
        hinweise.push(nr + 'Text wird auf ' + Math.round(L1.faktor / L0.faktor * 100) + ' % verkleinert, damit er passt');
      if (hinweise.length >= 40) return;                 // mehr liest niemand
      alle.forEach(b => {
        const a = flaeche(L0, b), n = flaeche(L1, b);
        if (a && n && a.o >= -1 && a.u <= H0 + 1 && (n.o < -1 || n.u > H1 + 1))
          hinweise.push(nr + '„' + name(b) + '“ ragt ' + (n.o < -1 ? 'oben' : 'unten') + ' ueber den Rand');
      });
      for (let x = 0; x < alle.length && hinweise.length < 40; x++){
        const a0 = flaeche(L0, alle[x]), a1 = flaeche(L1, alle[x]);
        if (!a0 || !a1) continue;
        for (let y = x + 1; y < alle.length; y++){
          const b0 = flaeche(L0, alle[y]), b1 = flaeche(L1, alle[y]);
          if (b0 && b1 && !ueber(a0, b0) && ueber(a1, b1))
            hinweise.push(nr + '„' + name(alle[x]) + '“ und „' + name(alle[y]) + '“ ueberlappen jetzt');
        }
      }
    });
  });
  neu.stil = stilNeu;
  // Bilder fuellen ihre Flaeche wie ein Foto. Passt eine Grafik ueber die ganze Hoehe
  // nicht mehr zu ihrem eigenen Seitenverhaeltnis, faellt am Rand etwas weg
  // (z. B. die Rahmenlinie eines Hintergrunds).
  let gemessen = 0;
  for (const [datei, stellen] of grafiken){
    if (++gemessen > 20) break;
    const v = await bildVerhaeltnis(basis + datei);
    const nummern = stellen.filter(x => v > 0 && Math.abs(x.v / v - 1) > 0.01).map(x => x.nr);
    if (!nummern.length) continue;
    const folien = nummern.length > 2 && nummern[nummern.length - 1] - nummern[0] === nummern.length - 1
      ? nummern[0] + ' bis ' + nummern[nummern.length - 1] : nummern.join(', ');
    hinweise.push('Folie ' + folien + ': Grafik „' + datei.slice(0, 40) + '“ passt nicht mehr ganz hinein, am Rand faellt etwas weg (Linien ansehen)');
  }
  profilRandPruefen(slides, stilNeu).forEach(n =>
    hinweise.push('Folie 1: „' + n + '“ reicht in den Rand, der im Profil wegfaellt'));
  return {daten: neu, hinweise: hinweise.slice(0, 40)};
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
