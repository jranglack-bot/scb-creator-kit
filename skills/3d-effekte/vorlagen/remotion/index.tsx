import React, {useLayoutEffect, useRef, useState} from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  continueRender,
  delayRender,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  EBENEN_SCHILDER,
  dauerGesamt,
  ebenenLage,
  erstelleSzene,
  logoEbene,
  logoWackeln,
  type Szene,
} from "./szenen.js";
import plan from "./plan.json";

/* ------------------------------------------------------------------
   3D-Effekte (SCB Creator Kit, Skill 3d-effekte) - Remotion-Huelle.
   Der 3D-Code steckt in szenen.js und ist mit HyperFrames geteilt.
   Was gezeigt wird, steht in plan.json. Dateien liegen in public/3d/.
------------------------------------------------------------------- */

type Eintrag = {name: string; dauer: number; [k: string]: unknown};
const SZENEN = plan.szenen as Eintrag[];
const datei = (d: unknown) => staticFile(`3d/${String(d)}`);

export const DREI_D_FPS = 30;
export const DREI_D_FRAMES = Math.round(dauerGesamt(SZENEN) * DREI_D_FPS);

const Leinwand: React.FC<{eintrag: Eintrag; style?: React.CSSProperties}> = ({eintrag, style}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const ref = useRef<HTMLCanvasElement>(null);
  const szene = useRef<Szene | null>(null);
  const zeit = useRef(frame / fps);
  zeit.current = frame / fps;
  const [warten] = useState(() => delayRender(`3D-Szene ${eintrag.name}`));
  const erledigt = useRef(false);

  useLayoutEffect(() => {
    let aktiv = true;
    const s = erstelleSzene(eintrag.name, ref.current!, {
      breite: width,
      hoehe: height,
      pfad: (d) => datei(d),
      optionen: eintrag,
    });
    szene.current = s;
    s.render(zeit.current);
    s.bereit.then(() => {
      if (!aktiv) return;
      s.render(zeit.current);
      if (!erledigt.current) {
        erledigt.current = true;
        continueRender(warten);
      }
    });
    return () => {
      aktiv = false;
      s.dispose();
    };
  }, [eintrag, width, height, warten]);

  useLayoutEffect(() => {
    szene.current?.render(frame / fps);
  }, [frame, fps]);

  return (
    <canvas
      ref={ref}
      width={width}
      height={height}
      style={{position: "absolute", left: 0, top: 0, width: "100%", height: "100%", ...style}}
    />
  );
};

// Logo-Wurf: Video, Logo (hinter oder vor der Person), Freisteller.
// Die Person existiert nur EINMAL im Bild: der Freisteller stammt aus
// demselben Video und liegt bildgenau darueber.
const LogoSzene: React.FC<{eintrag: Eintrag}> = ({eintrag}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const w = logoWackeln(t, eintrag);
  const aufprall = typeof eintrag.aufprall === "number" ? eintrag.aufprall : 4.3;
  const bewegt: React.CSSProperties =
    t >= aufprall ? {transform: `translate(${w.x}px, ${w.y}px) scale(1.05)`} : {};
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{...bewegt, zIndex: 0}}>
        <OffthreadVideo src={datei(eintrag.video)} muted />
      </AbsoluteFill>
      <AbsoluteFill style={{...bewegt, zIndex: 2}}>
        <OffthreadVideo src={datei(eintrag.person)} muted transparent />
      </AbsoluteFill>
      <Leinwand eintrag={eintrag} style={{zIndex: logoEbene(t, eintrag) === "hinten" ? 1 : 3}} />
    </AbsoluteFill>
  );
};

// Eine Karte im Raum: Inhalt, leuchtender Rahmen, Schild oben rechts
const Ebene: React.FC<{
  z: number;
  rahmen: number;
  schild: string;
  schildSicht: number;
  children: React.ReactNode;
}> = ({z, rahmen, schild, schildSicht, children}) => (
  <AbsoluteFill style={{transform: `translateZ(${z}px)`}}>
    {children}
    <AbsoluteFill
      style={{
        opacity: rahmen,
        border: "6px solid rgba(150,178,255,0.95)",
        borderRadius: 28,
        boxShadow: "0 0 48px rgba(89,127,217,0.65)",
      }}
    />
    <div
      style={{
        position: "absolute",
        right: 44,
        top: 200,
        opacity: schildSicht > 0.001 ? 1 : 0,
        transform: `scale(${0.4 + 0.6 * schildSicht})`,
        transformOrigin: "100% 0",
        font: '700 58px "Arial Rounded MT Bold", "Arial Rounded MT", Arial, sans-serif',
        color: "#fff",
        padding: "14px 34px",
        background: "rgba(8,12,28,0.86)",
        border: "4px solid #597fd9",
        borderRadius: 60,
      }}
    >
      {schild}
    </div>
  </AbsoluteFill>
);

// Drei Ebenen: Wand, 3D-Objekt, Person faechern sich im Raum auf
const EbenenSzene: React.FC<{eintrag: Eintrag}> = ({eintrag}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const L = ebenenLage(frame / fps);
  const schilder = (eintrag.schilder as string[] | undefined) ?? EBENEN_SCHILDER;
  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(ellipse at 50% 45%, #16204a 0%, #04050c 75%)",
        perspective: "2600px",
      }}
    >
      <AbsoluteFill
        style={{
          transformStyle: "preserve-3d",
          transform: `scale(${L.massstab}) rotateX(${L.drehX}deg) rotateY(${L.drehY}deg)`,
        }}
      >
        <Ebene z={L.tiefe.wand} rahmen={L.rahmen} schild={schilder[0]} schildSicht={L.schild}>
          <Img src={datei(eintrag.wand)} style={{width: "100%", height: "100%"}} />
        </Ebene>
        <Ebene z={L.tiefe.objekt} rahmen={L.rahmen} schild={schilder[1]} schildSicht={L.schild}>
          <Leinwand eintrag={eintrag} />
        </Ebene>
        <Ebene z={L.tiefe.person} rahmen={L.rahmen} schild={schilder[2]} schildSicht={L.schild}>
          <OffthreadVideo src={datei(eintrag.person)} muted transparent />
        </Ebene>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const DreiDEffekte: React.FC = () => {
  const {fps} = useVideoConfig();
  let von = 0;
  return (
    <AbsoluteFill style={{backgroundColor: "#000"}}>
      {SZENEN.map((s, i) => {
        const start = Math.round(von * fps);
        von += s.dauer;
        return (
          <Sequence key={i} from={start} durationInFrames={Math.round(s.dauer * fps)} name={s.name}>
            {s.name === "logo" ? (
              <LogoSzene eintrag={s} />
            ) : s.name === "ebenen" ? (
              <EbenenSzene eintrag={s} />
            ) : (
              <Leinwand eintrag={s} />
            )}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
