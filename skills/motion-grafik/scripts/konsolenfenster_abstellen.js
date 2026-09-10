/*
  Stellt die Konsolenfenster ab, die HyperFrames beim Bauen und Rendern aufblitzen
  laesst.

  Es sind DREI Verursacher, nicht einer (gemessen 01.09.2026):

    1. chrome-headless-shell.exe  - rendert die Bilder.        Issue #3430, offen.
    2. esbuild.exe                - baut die Komposition. Laeuft bei JEDEM
                                    Vorschau-Start, jedem Nachladen und vor
                                    jedem Render. Das ist die Quelle der kurzen
                                    Fenster, die sofort wieder verschwinden.
    3. ffmpeg.exe / ffprobe.exe   - WIRD ABSICHTLICH NICHT ANGEFASST, siehe unten.

  Die frueherere Fassung dieses Scripts hat nur die NEUESTE Chrome-Fassung
  umgestellt. Liegen mehrere im Cache, blieben die aelteren Konsolenprogramme.
  Diese Fassung nimmt alle.

  Warum ueberhaupt: Windows gibt jedem Programm, das im Programmkopf als
  "Konsolenprogramm" markiert ist, zwingend ein Fenster, sobald es aus einem
  Prozess ohne eigene Konsole gestartet wird. Genau das passiert bei
  `hyperframes preview --background`. Chrome und esbuild brauchen die Konsole
  nicht, beide reden ueber Pipes. Geaendert werden genau zwei Bytes: das
  Subsystem-Feld von 3 (CONSOLE) auf 2 (GUI).

  ffmpeg bleibt CONSOLE, mit Absicht: es wird vom ganzen SCB-Kit und von Julian
  im Terminal benutzt. Auf GUI umgestellt gaebe es dort keine Ausgabe mehr und
  jede Fehlersuche im Kit waere blind. Die ffmpeg-Fenster verschwinden
  stattdessen dadurch, dass die Vorschau mit einer versteckten Konsole
  gestartet wird - Kinder erben die dann und bekommen kein eigenes Fenster:

      powershell Start-Process -WindowStyle Hidden -FilePath "cmd" ^
        -ArgumentList "/c npx hyperframes preview"

  Aufruf:
    node konsolenfenster-abstellen.js            zeigt nur den Stand
    node konsolenfenster-abstellen.js --setzen   Sicherung anlegen und umstellen
    node konsolenfenster-abstellen.js --zurueck  Sicherungen zurueckspielen

  ACHTUNG: Jedes Update von HyperFrames ersetzt esbuild.exe, und
  `browser ensure` kann ein neues Chrome laden. Danach sind die Fenster zurueck
  und dieses Script muss erneut mit --setzen laufen. Vor jeder Sitzung
  einmal ohne Schalter aufrufen, das kostet nichts.

  Vorher alle Renders und Vorschauen beenden, sonst sind die Dateien gesperrt:
    hyperframes preview --kill-all
*/

const fs = require("fs");
const path = require("path");
const os = require("os");

// --- Kandidaten einsammeln ------------------------------------------------

function suchen(wurzel, muster, tiefe = 0, treffer = []) {
  if (tiefe > 6 || !fs.existsSync(wurzel)) return treffer;
  for (const e of fs.readdirSync(wurzel, { withFileTypes: true })) {
    const p = path.join(wurzel, e.name);
    if (e.isDirectory()) suchen(p, muster, tiefe + 1, treffer);
    else if (muster.test(e.name)) treffer.push(p);
  }
  return treffer;
}

function kandidaten() {
  const liste = [];

  // 1. ALLE Chrome-Fassungen im Cache, nicht nur die neueste
  liste.push(
    ...suchen(
      path.join(os.homedir(), ".cache", "hyperframes", "chrome"),
      /^chrome-headless-shell\.exe$/i,
    ),
  );

  // 2. esbuild aus der global installierten HyperFrames-Fassung
  const npmRoot = process.env.APPDATA
    ? path.join(process.env.APPDATA, "npm", "node_modules", "hyperframes")
    : null;
  if (npmRoot) {
    liste.push(...suchen(path.join(npmRoot, "node_modules"), /^esbuild\.exe$/i));
  }

  // 3. esbuild aus dem npx-Zwischenspeicher, falls das Projekt eine andere
  //    Fassung pinnt als die global installierte.
  //
  //    ACHTUNG: ~/.npm/_npx ist der Unix-Ort. Auf Windows liegt der Cache
  //    woanders (AppData/Local/npm-cache/_npx), und genau deshalb hat diese
  //    Stelle am 09.09.2026 zwei CONSOLE-Kopien uebersehen, waehrend der
  //    Bericht "alles auf GUI" meldete. npm selbst nach dem Ort fragen.
  const npxOrte = [path.join(os.homedir(), ".npm", "_npx")];
  try {
    const cache = require("child_process")
      .execSync("npm config get cache", { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] })
      .trim();
    if (cache && cache !== "undefined") npxOrte.push(path.join(cache, "_npx"));
  } catch {
    // npm nicht erreichbar - dann bleibt es beim Standardort
  }
  if (process.env.LOCALAPPDATA) {
    npxOrte.push(path.join(process.env.LOCALAPPDATA, "npm-cache", "_npx"));
  }
  for (const ort of [...new Set(npxOrte)]) {
    liste.push(...suchen(ort, /^esbuild\.exe$/i));
    // In den npx-Kopien liegt teils auch ein eigenes Chrome.
    liste.push(...suchen(ort, /^chrome-headless-shell\.exe$/i));
  }

  // 4. REMOTION. Gleiche Bauart, gleiches Problem (gemessen 09.09.2026:
  //    esbuild, chrome-headless-shell, remotion.exe, ffmpeg und ffprobe
  //    lagen alle fuenf auf CONSOLE). Remotion baut mit esbuild, rendert
  //    mit Headless Chrome und kodiert mit einem eigenen Rust-Programm.
  //
  //    ffmpeg/ffprobe werden hier ABSICHTLICH mitgenommen, anders als
  //    weiter unten beschrieben: das sind Remotions PRIVATE Kopien unter
  //    node_modules, nicht auf dem PATH. Der Nutzer ruft sie nie selbst
  //    auf, also nimmt ihm die Umstellung auch keine Ausgabe weg. Das
  //    ffmpeg des Kits und des Terminals bleibt unberuehrt.
  //
  //    Wurzeln: alles, was als Pfad uebergeben wurde, sonst der aktuelle
  //    Ordner und Julians Remotion-Projekt.
  const wurzeln = process.argv.slice(2).filter((a) => !a.startsWith("--"));
  if (wurzeln.length === 0) {
    wurzeln.push(process.cwd(), "D:/Instagram Content/remotion");
  }
  for (const w of wurzeln) {
    const nm = path.join(w, "node_modules");
    if (!fs.existsSync(nm)) continue;
    liste.push(...suchen(path.join(nm, "@esbuild"), /^esbuild\.exe$/i));
    liste.push(
      ...suchen(path.join(nm, ".remotion"), /^chrome-headless-shell\.exe$/i),
    );
    liste.push(
      ...suchen(path.join(nm, "@remotion"), /^(remotion|ffmpeg|ffprobe)\.exe$/i),
    );
  }

  return [...new Set(liste)];
}

// --- Subsystem lesen und schreiben ---------------------------------------

const NAMEN = { 2: "GUI (kein Fenster)", 3: "CONSOLE (Fenster!)" };

function subsystem(datei, neu) {
  const fd = fs.openSync(datei, neu === undefined ? "r" : "r+");
  try {
    const b4 = Buffer.alloc(4);
    fs.readSync(fd, b4, 0, 4, 0x3c);
    const peOff = b4.readUInt32LE(0);

    const sig = Buffer.alloc(4);
    fs.readSync(fd, sig, 0, 4, peOff);
    if (sig.toString("latin1") !== "PE\0\0") throw new Error("keine gueltige PE-Datei");

    // PE-Signatur (4) + COFF-Header (20) + Offset 68 im Optional Header
    const off = peOff + 4 + 20 + 68;
    const b2 = Buffer.alloc(2);
    fs.readSync(fd, b2, 0, 2, off);
    const alt = b2.readUInt16LE(0);

    if (neu !== undefined && alt !== neu) {
      b2.writeUInt16LE(neu, 0);
      fs.writeSync(fd, b2, 0, 2, off);
    }
    return alt;
  } finally {
    fs.closeSync(fd);
  }
}

function kurz(p) {
  return p.split(path.sep).slice(-3).join(path.sep);
}

// --- Ablauf ---------------------------------------------------------------

const modus = process.argv[2];
const dateien = kandidaten();

if (!dateien.length) {
  console.log("Nichts gefunden. Erst holen mit:  hyperframes browser ensure");
  process.exit(1);
}

let offen = 0;
const gesperrt = [];

for (const datei of dateien) {
  const sicherung = datei + ".original";

  if (modus === "--zurueck") {
    if (fs.existsSync(sicherung)) {
      fs.copyFileSync(sicherung, datei);
      console.log("zurueckgespielt      ", kurz(datei));
    } else {
      console.log("keine Sicherung      ", kurz(datei));
    }
    continue;
  }

  let jetzt;
  try {
    jetzt = subsystem(datei);
  } catch (e) {
    console.log("nicht lesbar         ", kurz(datei), e.message);
    continue;
  }

  if (modus !== "--setzen") {
    if (jetzt === 3) offen++;
    console.log((NAMEN[jetzt] ?? "unbekannt").padEnd(21), kurz(datei));
    continue;
  }

  if (jetzt === 2) {
    console.log("war schon GUI        ", kurz(datei));
    continue;
  }

  // Laeuft gerade ein Studio oder eine Vorschau, ist die Datei gesperrt
  // (EBUSY). Frueher ist das Script daran hart abgebrochen und die
  // restlichen Programme blieben unbehandelt — jetzt wird die eine Datei
  // uebersprungen und am Ende benannt.
  try {
    if (!fs.existsSync(sicherung)) fs.copyFileSync(datei, sicherung);
    subsystem(datei, 2);
    console.log("umgestellt auf GUI   ", kurz(datei));
  } catch (e) {
    if (e.code === "EBUSY" || e.code === "EPERM") {
      gesperrt.push(datei);
      console.log("IN BENUTZUNG         ", kurz(datei));
    } else {
      throw e;
    }
  }
}

if (gesperrt.length) {
  console.log(
    "\n" +
      gesperrt.length +
      " Datei(en) waren gesperrt. Studio bzw. Vorschau beenden\n" +
      "(remotion: Fenster schliessen; hyperframes preview --stop) und\n" +
      "dieses Script danach noch einmal mit --setzen laufen lassen.",
  );
}

if (modus !== "--setzen" && modus !== "--zurueck") {
  console.log(
    offen
      ? "\n" + offen + " Programm(e) machen noch Fenster auf." +
        "\nUmstellen mit:  node konsolenfenster-abstellen.js --setzen"
      : "\nAlles auf GUI, es geht kein Fenster mehr auf.",
  );
}
