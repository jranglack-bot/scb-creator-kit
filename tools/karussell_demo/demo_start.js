// Karussell-Cockpit als Vorschau ohne Server: ersetzt bauen.py im Browser.
// Laeuft nach render.js und vor dem Cockpit-Skript. Alles liegt nur im Speicher
// dieses Tabs; nichts verlaesst den Rechner. Gebaut von tools/karussell_demo/bauen.py.
(() => {
'use strict';
const echtFetch = window.fetch.bind(window);
const DATEN = JSON.parse(document.getElementById('demoDaten').textContent);
document.getElementById('demoDaten').remove();

const VOLL = 'Das geht in der Vollversion auf deinem Rechner.';
const BILDARTEN = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'];
const STIL_STD = {breite: 1080, hoehe: 1350, bg: '#dee3e7', text: '#313538', akzent: '#718d81',
                  schrift: 'Montserrat', randX: 132, randOben: 354, randUnten: 94,
                  titel: 84, textgroesse: 40, titelAbstand: 1.17, textAbstand: 1.42};
const FORMATE = {'45': {hoehe: 1350, randOben: 354, randUnten: 94},
                 '34': {hoehe: 1440, randOben: 377, randUnten: 100},
                 '916': {hoehe: 1920, randOben: 420, randUnten: 330}};
const SERIE_MAX = 30;

// ---------------------------------------------------------------- Zustand
const PROJEKTE = new Map();      // name -> {inhalt: Text, version, geaendert}
const VORLAGEN = new Map();      // name -> {inhalt: Text, eigen}
const DATEIEN = new Map();       // 'projekte/<name>/<datei>' oder 'vorlagen/<name>/<datei>' -> blob:-Adresse
let KORB = [];                   // {eintrag, name, slides, geloescht, projekt, dateien}
let AKTUELL = '';
let MARKE = {name: '', farben: [], titel: '', text: '', logos: []};
let ICONS = {}, TEXTE = {};
const iconCache = new Map();
const GROESSE = new Map();      // blob:-Adresse -> Bytes, fuer die MB im Papierkorb
window.demoVeraendert = false;

function bytes(b64){
  const s = atob(b64), u = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  return u;
}
async function entpacken(b64){
  const strom = new Blob([bytes(b64)]).stream().pipeThrough(new DecompressionStream('gzip'));
  return new Uint8Array(await new Response(strom).arrayBuffer());
}
function blobUrl(teil, art){
  const b = teil instanceof Blob ? teil : new Blob([teil], {type: art}), u = URL.createObjectURL(b);
  GROESSE.set(u, b.size);
  return u;
}

const bereit = (async () => {
  const dec = new TextDecoder();
  const gz = DATEN.gz || {};
  for (const pfad of Object.keys(gz)){
    const u8 = await entpacken(gz[pfad]);
    if (pfad === 'bib/icons.json') ICONS = JSON.parse(dec.decode(u8));
    else TEXTE[pfad] = dec.decode(u8);
  }
  // Schriften direkt ins Dokument, ohne Adresse
  for (const f of DATEN.schriften || []){
    try {
      const u8 = await entpacken(f.daten);
      const ff = new FontFace(f.family, u8.buffer, {weight: f.weight || '400', style: 'normal', display: 'block'});
      document.fonts.add(await ff.load());
    } catch (e) { console.warn('Schrift fehlt in der Vorschau: ' + f.family); }
  }
  for (const v of DATEN.vorlagen || []){
    VORLAGEN.set(v.name, {inhalt: v.inhalt, eigen: false});
    if (v.vorschau) DATEIEN.set('vorlagen/' + v.name + '/.vorschau.png', blobUrl(bytes(v.vorschau), 'image/png'));
    if (v.folien) DATEIEN.set('vorlagen/' + v.name + '/.folien.png', blobUrl(bytes(v.folien), 'image/png'));
  }
  const s = DATEN.start;
  if (s && VORLAGEN.has(s.vorlage)){
    projektAnlegen(s.name, ohneVorlagenInfo(VORLAGEN.get(s.vorlage).inhalt));
    AKTUELL = s.name;
  }
})();
bereit.catch(e => console.error('Vorschau konnte nicht starten', e));

// ---------------------------------------------------------------- Helfer wie projekt.py
function slug(roh){
  let s = String(roh || '').normalize('NFC').trim().toLowerCase();
  s = s.replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss');
  s = s.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return s.slice(0, 60).replace(/^-+|-+$/g, '');
}
function frei(name){
  const n = slug(name);
  if (!n) throw new Error('Bitte einen Namen eingeben.');
  if (PROJEKTE.has(n)) throw new Error('Den Namen „' + n + '“ gibt es schon. Nimm einen anderen.');
  return n;
}
function freiName(name){
  const basis = slug(name).slice(0, 55).replace(/-+$/, '');
  if (!basis) throw new Error('Bitte einen Namen eingeben.');
  for (let i = 1; i < 1000; i++){
    const n = i === 1 ? basis : basis + '-' + i;
    if (!PROJEKTE.has(n)) return n;
  }
  throw new Error('Kein freier Name fuer ' + basis);
}
function projekt(name){
  const n = name || AKTUELL;
  if (!PROJEKTE.has(n)) throw new Error('Projekt gibt es nicht: ' + (n || '(keins)'));
  return n;
}
function lesen(name){ return JSON.parse(PROJEKTE.get(projekt(name)).inhalt); }
function stil(d){ return Object.assign({}, STIL_STD, (d && d.stil) || {}); }
function standVon(name){
  const p = PROJEKTE.get(name);
  return (name || '') + '|' + (p ? ('0000000' + p.version.toString(16)).slice(-8) : '0');
}
function projektAnlegen(name, inhalt){
  PROJEKTE.set(name, {inhalt: inhalt, version: 1, geaendert: Math.floor(Date.now() / 1000)});
}
function ohneVorlagenInfo(text){
  try {
    const d = JSON.parse(text);
    if (d && typeof d === 'object' && ('vorlage' in d || 'serie' in d)){
      delete d.vorlage; delete d.serie;
      return JSON.stringify(d, null, 2);
    }
  } catch (e) {}
  return text;
}
// Dateien eines Ordners mitkopieren (nur die, die `nimm` zulaesst)
function dateienKopieren(von, nach, nimm){
  for (const [pfad, url] of Array.from(DATEIEN)){
    if (pfad.indexOf(von) !== 0) continue;
    const rel = pfad.slice(von.length);
    if (!nimm || nimm(rel)) DATEIEN.set(nach + rel, url);
  }
}
function dateienWeg(praefix){
  const weg = {};
  for (const pfad of Array.from(DATEIEN.keys()))
    if (pfad.indexOf(praefix) === 0){ weg[pfad.slice(praefix.length)] = DATEIEN.get(pfad); DATEIEN.delete(pfad); }
  return weg;
}
function texteIn(o, aus, tiefe){
  if ((tiefe || 0) > 40) return;
  if (typeof o === 'string') aus.add(o);
  else if (Array.isArray(o)) o.forEach(v => texteIn(v, aus, (tiefe || 0) + 1));
  else if (o && typeof o === 'object') Object.keys(o).forEach(k => texteIn(o[k], aus, (tiefe || 0) + 1));
}
function zeit(){
  const d = new Date(), z = n => String(n).padStart(2, '0');
  return {stempel: '' + d.getFullYear() + z(d.getMonth() + 1) + z(d.getDate()) + '-' + z(d.getHours()) + z(d.getMinutes()) + z(d.getSeconds()),
          lesbar: d.getFullYear() + '-' + z(d.getMonth() + 1) + '-' + z(d.getDate()) + ' ' + z(d.getHours()) + ':' + z(d.getMinutes())};
}

// ---------------------------------------------------------------- Datei-Adressen
function iconUrl(name){
  if (!iconCache.has(name)){
    const svg = ICONS[name];
    iconCache.set(name, svg ? 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg) : 'data:,');
  }
  return iconCache.get(name);
}
dateiUrl = p => {
  let pfad = String(p || '').split('#')[0].split('?')[0];
  if (/^(data|blob):/.test(pfad)) return p;
  try { pfad = decodeURIComponent(pfad); } catch (e) { return 'data:,'; }
  const m = /^bib\/((?:lucide|tabler|tabler-voll)\/[a-z0-9-]{1,80})\.svg$/.exec(pfad);
  if (m) return iconUrl(m[1]);
  return DATEIEN.get(pfad) || 'data:,';
};

// ---------------------------------------------------------------- Antworten
function antwort(text, code, art){
  return new Response(text, {status: code || 200, headers: {'Content-Type': (art || 'text/plain') + '; charset=utf-8'}});
}
const json = (o, code) => antwort(JSON.stringify(o), code, 'application/json');

function projekteListe(){
  return {aktuell: AKTUELL, projekte: Array.from(PROJEKTE.keys()).sort().map(n => {
    const p = PROJEKTE.get(n);
    try {
      const d = JSON.parse(p.inhalt), st = stil(d);
      return {name: n, slides: (d.slides || []).length, breite: +st.breite, hoehe: +st.hoehe,
              geaendert: p.geaendert, groesse: p.inhalt.length};
    } catch (e) { return {name: n, slides: 0, breite: 0, hoehe: 0}; }
  })};
}
function vorlagenListe(){
  return Array.from(VORLAGEN.keys()).sort().map(n => {
    const v = VORLAGEN.get(n);
    try {
      const d = JSON.parse(v.inhalt), st = stil(d), i = (!v.eigen && d.vorlage) || {};
      return {name: n, slides: (d.slides || []).length, breite: +st.breite, hoehe: +st.hoehe,
              vorschau: DATEIEN.has('vorlagen/' + n + '/.vorschau.png'),
              folien: DATEIEN.has('vorlagen/' + n + '/.folien.png'),
              titel: String(i.titel || '').slice(0, 40), beschreibung: String(i.beschreibung || '').slice(0, 140),
              eigen: v.eigen};
    } catch (e) { return null; }
  }).filter(Boolean);
}

async function get(weg){
  if (weg === 'stand') return antwort(standVon(AKTUELL));
  if (weg === 'projekte') return json(projekteListe());
  if (weg === 'vorlagen') return json(vorlagenListe());
  if (weg === 'papierkorb') return json(KORB.map(e => {
    const bytes = Object.keys(e.dateien).reduce((s, k) => s + (GROESSE.get(e.dateien[k]) || 0), e.projekt.inhalt.length);
    return {eintrag: e.eintrag, name: e.name, slides: e.slides, geloescht: e.geloescht, mb: Math.round(bytes / 1e5) / 10};
  }));
  if (weg === 'codestand') return antwort('vorschau');
  if (weg === 'modelle') return json({da: [], mb: {}, laden: {}});
  if (weg === 'marke') return json(MARKE);
  if (weg === 'fonts/google.json') return json([]);
  if (TEXTE[weg] !== undefined) return antwort(TEXTE[weg], 200, 'application/json');
  if (weg === 'inhalt.json') return antwort(PROJEKTE.get(projekt()).inhalt, 200, 'application/json');
  const m = /^projekte\/([^/]+)\/inhalt\.json$/.exec(weg);
  if (m){
    if (!PROJEKTE.has(m[1])) return antwort('Fehler: unbekannt', 404);
    return antwort(PROJEKTE.get(m[1]).inhalt, 200, 'application/json');
  }
  if (DATEIEN.has(weg)) return echtFetch(DATEIEN.get(weg));
  return antwort('unbekannt', 404);
}

// Grosse Fotos verkleinern wie bauen.py (laengste Kante 3200 px)
async function bildAufbereiten(blob, endung){
  if (endung === '.svg'){
    const kopf = (await blob.slice(0, 2048).text()).toLowerCase();
    if (kopf.indexOf('<svg') < 0) throw new Error('keine SVG-Grafik');
    return new Blob([blob], {type: 'image/svg+xml'});
  }
  let bild;
  try { bild = await createImageBitmap(blob); }
  catch (e) { throw new Error('keine lesbare Bilddatei'); }
  const kante = Math.max(bild.width, bild.height);
  const art = {'.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif'}[endung] || 'image/jpeg';
  if (kante <= 3200 || endung === '.gif'){ bild.close(); return new Blob([blob], {type: art}); }
  const f = 3200 / kante, c = document.createElement('canvas');
  c.width = Math.round(bild.width * f); c.height = Math.round(bild.height * f);
  c.getContext('2d').drawImage(bild, 0, 0, c.width, c.height);
  bild.close();
  return await new Promise(fertig => c.toBlob(b => fertig(b || blob), art, 0.92));
}

async function post(weg, qs, koerper){
  const name = qs.projekt || AKTUELL;
  const text = async () => (typeof koerper === 'string' ? koerper : koerper ? await new Response(koerper).text() : '');
  if (weg === 'speichern'){
    const t = await text();
    let d;
    try { d = JSON.parse(t); if (!Array.isArray(d.slides)) throw 0; }
    catch (e) { return antwort('Fehler: keine gueltigen Karusselldaten', 400); }
    const p = PROJEKTE.get(projekt(name));
    if (p.inhalt !== t){ p.inhalt = t; p.version++; p.geaendert = Math.floor(Date.now() / 1000); window.demoVeraendert = true; }
    return antwort(standVon(name));
  }
  if (weg === 'bild'){
    projekt(name);
    const roh = String(qs.name || 'bild.png').split(/[\\/]/).pop();
    let datei = roh.replace(/[^A-Za-z0-9_.\-]/g, '_').replace(/^[. -]+|[. -]+$/g, '') || 'bild.png';
    const punkt = datei.lastIndexOf('.'), endung = punkt > 0 ? datei.slice(punkt).toLowerCase() : '';
    if (['.heic', '.heif', '.tif', '.tiff'].indexOf(endung) >= 0)
      return antwort('Fehler: HEIC- und TIFF-Bilder bitte vorher als JPG oder PNG speichern', 400);
    if (BILDARTEN.indexOf(endung) < 0) return antwort('Fehler: nur Bilddateien (' + BILDARTEN.join(', ') + ')', 400);
    if (!(koerper instanceof Blob)) return antwort('Fehler: keine Bilddatei', 400);
    if (koerper.size > 50e6) return antwort('Fehler: zu gross', 413);
    let blob;
    try { blob = await bildAufbereiten(koerper, endung); }
    catch (e) { return antwort('Fehler: ' + e.message, 400); }
    const stamm = datei.slice(0, punkt), basis = 'projekte/' + name + '/';
    for (let n = 2; DATEIEN.has(basis + datei); n++) datei = stamm + '_' + n + endung;
    DATEIEN.set(basis + datei, blobUrl(blob));
    window.demoVeraendert = true;
    return antwort(datei);
  }
  if (weg === 'bildkopie'){
    try {
      const a = JSON.parse(await text()), q = 'projekte/' + projekt(a.von) + '/' + a.datei;
      if (!DATEIEN.has(q)) throw 0;
      const z = 'projekte/' + projekt(name) + '/' + a.datei;
      if (!DATEIEN.has(z)) DATEIEN.set(z, DATEIEN.get(q));
      return antwort('ok');
    } catch (e) { return antwort('Fehler: Bild nicht gefunden', 400); }
  }
  if (weg === 'marke'){
    let a = {};
    try { a = JSON.parse(await text() || '{}'); } catch (e) {}
    if (a.aktion === 'speichern' && a.marke && typeof a.marke === 'object'){
      const m = a.marke;
      const farben = [];
      (Array.isArray(m.farben) ? m.farben : []).slice(0, 12).forEach(f => {
        const n = String(f).toLowerCase();
        if (/^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/.test(n) && farben.indexOf(n) < 0) farben.push(n);
      });
      const schrift = s => (typeof s === 'string' && /^[A-Za-z0-9 ]{1,60}$/.test(s) ? s : '');
      MARKE = {name: String(m.name || '').replace(/[^A-Za-z0-9._]/g, '').slice(0, 30), farben: farben,
               titel: schrift(m.titel), text: schrift(m.text), logos: []};
      return json({ok: true, marke: MARKE});
    }
    if (a.aktion === 'logo-weg') return json({ok: true, marke: MARKE});
    return json({ok: false, fehler: 'Logos und Anwenden gehen in der Vollversion.'});
  }
  if (weg === 'projekt') return json(await projektAktion(JSON.parse(await text() || '{}')));
  if (weg === 'markelogo') return json({ok: false, fehler: 'Logos gehen in der Vollversion.'});
  if (['schrift', 'schriftdatei', 'modell', 'freistellen', 'video'].indexOf(weg) >= 0)
    return json({ok: false, fehler: VOLL});
  if (weg === 'rendern') return antwort('In der Vorschau baut das Cockpit keine Dateien. ' + VOLL);
  return antwort('Fehler: ' + VOLL, 400);
}

async function projektAktion(a){
  try {
    const aktion = a.aktion;
    if (aktion === 'oeffnen'){ AKTUELL = projekt(String(a.name || '')); }
    else if (aktion === 'neu' && a.vorlage){
      const v = VORLAGEN.get(String(a.vorlage));
      if (!v) throw new Error('Vorlage gibt es nicht: ' + a.vorlage);
      const n = frei(a.name);
      projektAnlegen(n, ohneVorlagenInfo(v.inhalt));
      dateienKopieren('vorlagen/' + a.vorlage + '/', 'projekte/' + n + '/', rel => rel !== '.vorschau.png' && rel !== '.folien.png');
      AKTUELL = n;
    }
    else if (aktion === 'neu'){
      const n = frei(a.name);
      const st = Object.assign({}, STIL_STD, FORMATE[a.format] || FORMATE['45']);
      projektAnlegen(n, JSON.stringify({stil: st, slides: [{bloecke: [
        {id: 'b1', typ: 'text', rolle: 'titel', text: '<b>Neues Karussell</b>'}]}]}, null, 2));
      AKTUELL = n;
    }
    else if (aktion === 'vorlage'){
      const q = projekt(a.von), n = slug(a.name);
      if (!n) throw new Error('Bitte einen Namen eingeben.');
      if (VORLAGEN.has(n)) throw new Error('Eine Vorlage „' + n + '“ gibt es schon. Nimm einen anderen Namen.');
      VORLAGEN.set(n, {inhalt: ohneVorlagenInfo(PROJEKTE.get(q).inhalt), eigen: true});
      dateienKopieren('projekte/' + q + '/', 'vorlagen/' + n + '/');
      window.demoVeraendert = true;
      return {ok: true, vorlage: n};
    }
    else if (aktion === 'duplizieren'){
      const q = projekt(a.von), n = frei(a.name);
      projektAnlegen(n, PROJEKTE.get(q).inhalt);
      dateienKopieren('projekte/' + q + '/', 'projekte/' + n + '/');
      AKTUELL = n;
    }
    else if (aktion === 'loeschen'){
      const namen = Array.isArray(a.namen) ? a.namen : [];
      if (namen.length < 1 || namen.length > 200) throw new Error('Nichts ausgewaehlt');
      const weg = namen.map(x => {
        const n = projekt(String(x)), t = zeit();
        let eintrag = n + '__' + t.stempel;
        for (let i = 2; KORB.some(e => e.eintrag === eintrag); i++) eintrag = n + '__' + t.stempel + '-' + i;
        let slides = 0;
        try { slides = (lesen(n).slides || []).length; } catch (e) {}
        KORB.unshift({eintrag: eintrag, name: n, slides: slides, geloescht: t.lesbar,
                      projekt: PROJEKTE.get(n), dateien: dateienWeg('projekte/' + n + '/')});
        PROJEKTE.delete(n);
        return eintrag;
      });
      if (!PROJEKTE.has(AKTUELL)) AKTUELL = Array.from(PROJEKTE.keys()).sort()[0] || '';
      window.demoVeraendert = true;
      return {ok: true, eintraege: weg, aktuell: AKTUELL};
    }
    else if (aktion === 'zurueckholen'){
      const e = KORB.find(x => x.eintrag === a.eintrag);
      if (!e) throw new Error('Eintrag gibt es nicht mehr');
      const n = freiName(e.name);
      PROJEKTE.set(n, e.projekt);
      Object.keys(e.dateien).forEach(rel => DATEIEN.set('projekte/' + n + '/' + rel, e.dateien[rel]));
      KORB = KORB.filter(x => x !== e);
      AKTUELL = n;
    }
    else if (aktion === 'leeren'){
      const liste = Array.isArray(a.eintraege) && a.eintraege.length ? a.eintraege : KORB.map(e => e.eintrag);
      liste.forEach(x => { if (!KORB.some(e => e.eintrag === x)) throw new Error('Eintrag gibt es nicht mehr'); });
      KORB = KORB.filter(e => liste.indexOf(e.eintrag) < 0);
      return {ok: true, anzahl: liste.length};
    }
    else if (aktion === 'serie'){
      const ks = a.karussells;
      if (!Array.isArray(ks) || ks.length < 1 || ks.length > SERIE_MAX) throw new Error('1 bis ' + SERIE_MAX + ' Karussells je Serie');
      ks.forEach(k => {
        if (!(k && typeof k.name === 'string' && Array.isArray(k.slides) && k.slides.length >= 1 && k.slides.length <= 100))
          throw new Error('ungueltige Serie');
      });
      const q = projekt(a.von), kopf = lesen(q);
      delete kopf.slides; delete kopf.serie; delete kopf.vorlage;
      const namen = [];
      ks.forEach(k => {
        const n = freiName(k.name), daten = Object.assign({}, kopf, {slides: k.slides}), benutzt = new Set();
        texteIn(daten, benutzt);
        projektAnlegen(n, JSON.stringify(daten, null, 2));
        dateienKopieren('projekte/' + q + '/', 'projekte/' + n + '/',
                        rel => benutzt.has(rel) || (/\.mp4\.jpg$/.test(rel) && benutzt.has(rel.slice(0, -4))));
        namen.push(n);
      });
      AKTUELL = namen[0];
      window.demoVeraendert = true;
      return {ok: true, name: AKTUELL, namen: namen, stand: standVon(AKTUELL)};
    }
    else throw new Error('unbekannte Aktion');
    if (aktion !== 'oeffnen') window.demoVeraendert = true;
    return {ok: true, name: AKTUELL, stand: standVon(AKTUELL)};
  } catch (e) {
    return {ok: false, fehler: e && e.message ? e.message : String(e)};
  }
}

window.fetch = async function(eingabe, opt){
  const url = typeof eingabe === 'string' ? eingabe : (eingabe && eingabe.url) || String(eingabe);
  if (/^(data|blob):/.test(url)) return echtFetch(eingabe, opt);
  await bereit;
  const u = new URL(url, 'http://vorschau.invalid/');
  let weg = u.pathname.replace(/^\/+/, '');
  try { weg = decodeURIComponent(weg); } catch (e) {}
  const qs = {};
  u.searchParams.forEach((v, k) => { qs[k] = v; });
  const methode = String((opt && opt.method) || 'GET').toUpperCase();
  try { return methode === 'POST' ? await post(weg, qs, opt.body) : await get(weg, qs); }
  catch (e) { return antwort('Fehler: ' + (e && e.message ? e.message : e), 404); }
};
})();
