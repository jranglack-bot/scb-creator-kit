// Vorschau ohne Server, zweiter Teil: laeuft nach dem Cockpit-Skript. Begruessung,
// Hinweis "in der Vollversion" an allem, was einen Rechner braucht.
(() => {
'use strict';
const $ = id => document.getElementById(id);
let zuletzt = null;

function zeigen(el){
  zuletzt = document.activeElement;
  el.style.display = 'flex';
  const k = el.querySelector('button.haupt');
  if (k) k.focus();
}
function zu(el){
  el.style.display = 'none';
  if (zuletzt && zuletzt.focus) try { zuletzt.focus(); } catch (e) {}
}
function hinweis(text){
  $('demoHText').textContent = text;
  zeigen($('demoHinweis'));
}
window.demoHinweis = hinweis;

$('demoLos').onclick = () => zu($('demoWillkommen'));
$('demoHOk').onclick = () => zu($('demoHinweis'));
['demoWillkommen', 'demoHinweis'].forEach(id => {
  $(id).addEventListener('mousedown', e => { if (e.target.id === id) zu($(id)); });
});
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  ['demoHinweis', 'demoWillkommen'].forEach(id => { if ($(id).style.display === 'flex') zu($(id)); });
}, true);
setTimeout(() => { if ($('demoWillkommen').style.display === 'flex') $('demoLos').focus(); }, 0);

// Kennzeichen im Kopf, holt die Begruessung zurueck
const h1 = document.querySelector('header h1');
if (h1){
  const b = document.createElement('button');
  b.id = 'demoMarke'; b.type = 'button'; b.textContent = 'Vorschau';
  b.title = 'Was diese Vorschau kann und was nur die Vollversion';
  b.onclick = () => zeigen($('demoWillkommen'));
  h1.insertAdjacentElement('afterend', b);
}

// Was einen Rechner braucht: freundlich sagen statt Fehler zeigen
const AUSGABE = 'Bilder für Instagram, PDF und Canva-Datei baut das Cockpit auf deinem Rechner, ' +
                'eine Datei je Folie, bereit zum Posten.';
['rBilder', 'rPptx', 'rPdf'].forEach(id => { if ($(id)) $(id).onclick = () => hinweis(AUSGABE); });
window.freistellen = () => hinweis('Hintergrund entfernen läuft auf deinem Rechner, ' +
                                   'mit einem Klick, ohne Upload ins Internet.');
window.modellLaden = async () => false;
window.videoHochladen = async () => {
  hinweis('Videos als Folie: Das Cockpit wandelt das Video passend für Instagram um und schneidet es zu.');
  return null;
};
window.auftragAuf = () => hinweis('An Claude: Elemente markieren, Wunsch dazuschreiben, ' +
                                  'Claude liest beides mit und setzt es im Karussell um.');
if ($('pClaude')) $('pClaude').onclick = window.auftragAuf;
window.schriftHolen = async () => hinweis('Über 1.800 Google-Schriften mit einem Klick laden, ' +
                                          'danach funktionieren sie auch ohne Internet.');
window.schriftDateiHochladen = async () => {
  hinweis('Eigene Schriftdateien (TTF, OTF, WOFF) einmal ablegen, danach stehen sie in jeder Schriftauswahl.');
  return null;
};
if ($('mAnwenden')) $('mAnwenden').onclick = () =>
  hinweis('Markenpaket anwenden: deine Farben, Schriften und dein Logo mit einem Klick aufs ganze Karussell.');
if ($('mLogoDatei')) $('mLogoDatei').onchange = e => {
  e.target.value = '';
  hinweis('Logos ablegen und mit einem Klick ins Karussell setzen.');
};

// Im eingebetteten Fenster (Link-Fassung) zeigt der Browser keine Rueckfragen:
// confirm() kaeme sofort mit "nein" zurueck und Loeschen im Papierkorb ginge nie.
// In der Vorschau ist nichts endgueltig, darum dort ohne Rueckfrage.
let eingebettet = true;
try { eingebettet = window.top !== window; } catch (e) {}
if (eingebettet) window.confirm = () => true;

// Nichts geht still verloren: vor dem Schliessen fragen, sobald etwas geaendert ist
window.addEventListener('beforeunload', e => {
  if (!window.demoVeraendert) return;
  e.preventDefault();
  e.returnValue = '';
});
})();
