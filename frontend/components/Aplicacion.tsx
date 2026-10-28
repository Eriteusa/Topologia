"use client";

import { useCallback, useEffect, useState } from "react";
import Grafo from "@/components/Grafo";
import Panel, { clasesBoton } from "@/components/Panel";
import PanelAutomata from "@/components/PanelAutomata";
import PanelClasificacion from "@/components/PanelClasificacion";
import PanelControles, { type Controles } from "@/components/PanelControles";
import PanelHistorial from "@/components/PanelHistorial";
import PanelRuta from "@/components/PanelRuta";
import PanelSimular from "@/components/PanelSimular";
import {
  ErrorApi,
  bloquear,
  bloquearAlAzar,
  calcularRuta,
  crearSesion,
  obtenerAutomata,
  obtenerRed,
  reiniciar,
  simularFalla,
} from "@/lib/api";
import type { DefinicionAutomata, Red, Ruta, Seleccion } from "@/lib/tipos";

/** Origen y destino de la Tabla 9 si están libres; si no, el primero y el último nodo libres. */
function elegirExtremos(red: Red) {
  const libres = red.nodos.filter((n) => !n.bloqueado).map((n) => n.id);
  const origen = libres.includes("PC3") ? "PC3" : (libres[0] ?? "");
  const destino = libres.includes("IoT4") ? "IoT4" : (libres.filter((i) => i !== origen).at(-1) ?? "");
  return { origen, destino };
}

const mensaje = (e: unknown) => (e instanceof ErrorApi ? e.message : "No se pudo completar la acción");

export default function Aplicacion() {
  const [red, setRed] = useState<Red | null>(null);
  const [ruta, setRuta] = useState<Ruta | null>(null);
  const [definicion, setDefinicion] = useState<DefinicionAutomata | null>(null);
  const [seleccion, setSeleccion] = useState<Seleccion>(null);
  const [nodoSim, setNodoSim] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [controles, setControles] = useState<Controles>({
    semilla: "42",
    atributos: "base",
    latencias: "base",
    bloqueoInicial: true,
    origen: "",
    destino: "",
  });

  const iniciar = useCallback(([r, a]: [Red, DefinicionAutomata]) => {
    setRed(r);
    setDefinicion(a);
    setControles({
      semilla: String(r.semilla),
      atributos: r.parametros.atributos as Controles["atributos"],
      latencias: r.parametros.latencias as Controles["latencias"],
      bloqueoInicial: r.parametros.bloqueo_inicial,
      ...elegirExtremos(r),
    });
    setError(null);
  }, []);

  useEffect(() => {
    let vigente = true;
    Promise.all([obtenerRed(), obtenerAutomata()])
      .then((datos) => vigente && iniciar(datos))
      .catch((e) => vigente && setError(mensaje(e)));
    return () => {
      vigente = false;
    };
  }, [iniciar]);

  const reintentar = () =>
    Promise.all([obtenerRed(), obtenerAutomata()])
      .then(iniciar)
      .catch((e) => setError(mensaje(e)));

  async function ejecutar(accion: () => Promise<void>) {
    setOcupado(true);
    setError(null);
    try {
      await accion();
    } catch (e) {
      setError(mensaje(e));
    } finally {
      setOcupado(false);
    }
  }

  /** Aplica una red nueva y limpia origen y destino si alguno quedó bloqueado. */
  function aplicarRed(nueva: Red) {
    setRed(nueva);
    setSeleccion(null);
    const bloqueados = new Set(nueva.nodos.filter((n) => n.bloqueado).map((n) => n.id));
    setControles((c) => ({
      ...c,
      origen: bloqueados.has(c.origen) ? "" : c.origen,
      destino: bloqueados.has(c.destino) ? "" : c.destino,
    }));
  }

  /** Sesión nueva o reiniciada: ruta limpia y extremos por defecto. */
  function aplicarSesion(nueva: Red) {
    setRed(nueva);
    setRuta(null);
    setSeleccion(null);
    setControles((c) => ({ ...c, semilla: String(nueva.semilla), ...elegirExtremos(nueva) }));
  }

  const seleccionar = useCallback(
    (s: Seleccion) => {
      setSeleccion(s);
      if (s?.tipo === "nodo") setNodoSim(s.id);
    },
    [],
  );

  const nuevaSesion = () =>
    ejecutar(async () => {
      const semilla = Number.parseInt(controles.semilla, 10);
      if (Number.isNaN(semilla)) throw new ErrorApi("Semilla no válida");
      aplicarSesion(
        await crearSesion({
          semilla,
          bloqueo_inicial: controles.bloqueoInicial,
          atributos: controles.atributos,
          latencias: controles.latencias,
        }),
      );
    });

  const calcular = () =>
    ejecutar(async () => {
      setRuta(await calcularRuta(controles.origen, controles.destino));
    });

  const bloquearElemento = (tipo: "nodo" | "arista", elemento: string) =>
    ejecutar(async () => {
      const respuesta = await bloquear(tipo, elemento);
      aplicarRed(respuesta.red);
      setRuta(respuesta.ruta);
    });

  const alAzar = () =>
    ejecutar(async () => {
      const respuesta = await bloquearAlAzar(controles.origen, controles.destino);
      aplicarRed(respuesta.red);
      setRuta(respuesta.ruta);
    });

  const reiniciarSesion = () => ejecutar(async () => aplicarSesion(await reiniciar()));

  const aplicarFalla = (nodo: string, trafico: number, cpu: number) =>
    ejecutar(async () => {
      const respuesta = await simularFalla(nodo, trafico, cpu);
      aplicarRed(respuesta.red);
    });

  if (!red) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-4 p-6">
        {error ? (
          <>
            <p role="alert" className="m-0 text-center text-[#8c2520]">
              {error}
            </p>
            <button type="button" onClick={() => void reintentar()} className={`${clasesBoton} bg-primario text-white`}>
              Reintentar
            </button>
          </>
        ) : (
          <span className="text-suave">—</span>
        )}
      </main>
    );
  }

  const bloqueados = red.nodos.filter((n) => n.bloqueado).length;
  const nodoSeleccionado = seleccion?.tipo === "nodo" ? red.nodos.find((n) => n.id === seleccion.id) : undefined;

  return (
    <main className="flex flex-col gap-5 px-7 pb-10 pt-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="m-0 text-[26px] font-bold tracking-tight text-primario">SoftCast</h1>
        <div className="flex flex-wrap gap-2 font-mono text-[13px]">
          {[`semilla ${red.semilla}`, `fuente: ${red.fuente === "gnn" ? "GNN" : "umbral"}`, `${bloqueados} de ${red.nodos.length} nodos bloqueados`].map(
            (texto) => (
              <span key={texto} className="rounded-md border border-borde bg-white px-2.5 py-1.5">
                {texto}
              </span>
            ),
          )}
        </div>
      </header>

      <div className="flex flex-wrap items-start gap-5">
        <div className="flex min-w-0 flex-[65_1_640px] flex-col gap-5">
          <Panel titulo="Topología de la red">
            <Grafo
              red={red}
              ruta={ruta}
              seleccion={seleccion}
              ocupado={ocupado}
              onSeleccionar={seleccionar}
              onBloquear={bloquearElemento}
            />
            <Leyenda />
          </Panel>
          <PanelRuta ruta={ruta} />
          <PanelAutomata
            definicion={definicion}
            secuenciaNodo={nodoSeleccionado ? { id: nodoSeleccionado.id, secuencia: nodoSeleccionado.secuencia } : null}
          />
        </div>

        <div className="flex min-w-0 flex-[35_1_360px] flex-col gap-5">
          <PanelControles
            valores={controles}
            nodos={red.nodos}
            ocupado={ocupado}
            error={error}
            onCambiar={(cambios) => setControles((c) => ({ ...c, ...cambios }))}
            onNuevaSesion={nuevaSesion}
            onCalcular={calcular}
            onAzar={alAzar}
            onReiniciar={reiniciarSesion}
          />
          <PanelHistorial bloqueos={red.bloqueos} />
          <PanelClasificacion red={red} />
          <PanelSimular
            nodos={red.nodos}
            nodoId={nodoSim}
            ocupado={ocupado}
            onCambiarNodo={setNodoSim}
            onAplicar={aplicarFalla}
          />
        </div>
      </div>
    </main>
  );
}

function Leyenda() {
  const punto = (estilo: React.CSSProperties) => <span className="size-3.5 rounded-full" style={estilo} />;
  const linea = (estilo: React.CSSProperties) => <span className="w-[22px]" style={estilo} />;
  const items: [React.ReactNode, string][] = [
    [punto({ background: "#14365e" }), "Servidor"],
    [punto({ background: "#3f7cb5" }), "PC"],
    [punto({ background: "#2f8a5f" }), "IoT"],
    [punto({ background: "#fff", border: "3px solid #d64545" }), "Anómalo"],
    [punto({ background: "#c3c9d1", border: "1px solid #8b95a3" }), "Bloqueado"],
    [linea({ borderTop: "3px dashed #7d8999" }), "Enlace redundante"],
    [linea({ borderTop: "5px solid #e8742a" }), "Ruta vigente"],
    [linea({ borderTop: "3px dotted #c0392b" }), "Arista bloqueada"],
    [punto({ border: "2px dashed #c48a00" }), "Cambió tras el bloqueo"],
  ];
  return (
    <ul className="m-0 flex list-none flex-wrap gap-x-[18px] gap-y-2 p-0 text-[13px] text-[#3d4755]">
      {items.map(([marca, texto]) => (
        <li key={texto} className="inline-flex items-center gap-1.5">
          {marca}
          {texto}
        </li>
      ))}
    </ul>
  );
}
