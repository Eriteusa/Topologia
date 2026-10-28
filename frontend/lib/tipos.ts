// Formas de los JSON que devuelve la API (CONTEXTO §10).

export type TipoNodo = "Servidor" | "PC" | "IoT";
export type EstadoNodo = "Normal" | "Anómalo" | "Bloqueado";
export type NivelAlerta = "Normal" | "Alerta temprana" | "Anómalo" | "Bloqueado";

export type Nodo = {
  id: string;
  tipo: TipoNodo;
  subtipo: string;
  trafico: number;
  cpu: number;
  bloqueado: boolean;
  clase_umbral: string;
  clase_extendida: string | null;
  p_anomalo: number | null;
  estado: EstadoNodo;
  nivel_alerta: NivelAlerta;
  secuencia: string;
  secuencia_valida: boolean;
  delta_p: number | null;
  x: number;
  y: number;
};

export type Arista = {
  id: string;
  origen: string;
  destino: string;
  latencia_ms: number;
  rol: "Troncal" | "Principal" | "Redundante";
  bloqueada: boolean;
  activa: boolean;
};

export type Bloqueo = {
  orden: number;
  tipo: "nodo" | "arista";
  elemento: string;
  modo: "inicial" | "aleatorio" | "manual";
};

export type Red = {
  semilla: number;
  parametros: { bloqueo_inicial: boolean; atributos: string; latencias: string };
  fuente: "gnn" | "umbral";
  nodos: Nodo[];
  aristas: Arista[];
  bloqueos: Bloqueo[];
  cambiaron: string[];
  ruta_vigente: [string, string] | null;
};

export type Ruta = {
  origen: string;
  destino: string;
  existe: boolean;
  nodos: string[];
  aristas: { id: string; latencia_ms: number }[];
  latencia_total: number | null;
  verificacion: string | null;
  empates: string[][];
};

export type DefinicionAutomata = {
  Q: string[];
  sigma: string[];
  q0: string;
  F: string[];
  delta: Record<string, Record<string, string>>;
};

export type ResultadoAutomata = {
  aceptada: boolean;
  recorrido: string[];
  estado_final: string;
  error?: string;
};

export type Seleccion = { tipo: "nodo" | "arista"; id: string } | null;

export type ParametrosSesion = {
  semilla: number;
  bloqueo_inicial: boolean;
  atributos: "base" | "aleatorios";
  latencias: "base" | "aleatorias";
};
