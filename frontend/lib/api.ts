import type {
  DefinicionAutomata,
  ParametrosSesion,
  Red,
  ResultadoAutomata,
  Ruta,
} from "./tipos";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ErrorApi extends Error {}

async function llamar<T>(ruta: string, cuerpo?: unknown): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(BASE + ruta, {
      method: cuerpo === undefined ? "GET" : "POST",
      headers: cuerpo === undefined ? undefined : { "Content-Type": "application/json" },
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
  } catch {
    throw new ErrorApi("Sin conexión con la API");
  }
  if (!respuesta.ok) {
    const datos = await respuesta.json().catch(() => null);
    throw new ErrorApi(typeof datos?.detail === "string" ? datos.detail : `Respuesta ${respuesta.status}`);
  }
  return respuesta.json();
}

export const obtenerRed = () => llamar<Red>("/api/red");
export const crearSesion = (p: ParametrosSesion) => llamar<Red>("/api/sesion", p);
export const reiniciar = () => llamar<Red>("/api/reiniciar", {});
export const calcularRuta = (origen: string, destino: string) =>
  llamar<Ruta>("/api/ruta", { origen, destino });
export const bloquear = (tipo: "nodo" | "arista", elemento: string) =>
  llamar<{ red: Red; ruta: Ruta | null }>("/api/bloqueos", { tipo, elemento });
export const bloquearAlAzar = (origen: string, destino: string) =>
  llamar<{ red: Red; ruta: Ruta | null }>("/api/bloqueos/aleatorio", { origen, destino });
export const simularFalla = (nodo: string, trafico: number, cpu: number) =>
  llamar<{ red: Red; cambiaron: string[] }>(`/api/nodos/${nodo}/atributos`, { trafico, cpu });
export const obtenerAutomata = () => llamar<DefinicionAutomata>("/api/automata");
export const validarCadena = (cadena: string) =>
  llamar<ResultadoAutomata>("/api/automata/validar", { cadena });
