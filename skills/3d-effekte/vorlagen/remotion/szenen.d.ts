export type Szene = {
  bereit: Promise<unknown>;
  render: (t: number) => void;
  dispose: () => void;
};
export const EBENEN_SCHILDER: string[];
export function dauerGesamt(szenen: {dauer: number}[]): number;
export function logoEbene(t: number, optionen?: object): "hinten" | "vorne";
export function logoWackeln(t: number, optionen?: object): {x: number; y: number};
export function ebenenLage(t: number): {
  drehY: number;
  drehX: number;
  massstab: number;
  tiefe: {wand: number; objekt: number; person: number};
  rahmen: number;
  schild: number;
};
export function erstelleSzene(
  name: string,
  canvas: HTMLCanvasElement,
  optionen?: {
    breite?: number;
    hoehe?: number;
    pfad?: (datei: string) => string;
    optionen?: object;
  },
): Szene;
