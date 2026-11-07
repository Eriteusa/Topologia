"use client";

import { useCallback, useEffect, useState } from "react";
import Grafo from "@/components/Grafo";
import Panel, { botonPrimario, clasesBoton } from "@/components/Panel";
import PanelAutomata from "@/components/PanelAutomata";
import PanelClasificacion from "@/components/PanelClasificacion";
import PanelControles, { type Controles } from "@/components/PanelControles";
import PanelRuta, { type RutaPrevia } from "@/components/PanelRuta";
import PanelSimular from "@/components/PanelSimular";
import Semaforo, { type LuzSemaforo } from "@/components/Semaforo";
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
  const [previa, setPrevia] = useState<RutaPrevia | null>(null);
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
    setPrevia(null);
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
      setPrevia(null);
      setRuta(await calcularRuta(controles.origen, controles.destino));
    });

  const bloquearElemento = (tipo: "nodo" | "arista", elemento: string) =>
    ejecutar(async () => {
      const respuesta = await bloquear(tipo, elemento);
      aplicarRed(respuesta.red);
      setPrevia(ruta?.existe ? { ruta, causa: elemento } : null);
      setRuta(respuesta.ruta);
    });

  const alAzar = () =>
    ejecutar(async () => {
      const respuesta = await bloquearAlAzar(controles.origen, controles.destino);
      aplicarRed(respuesta.red);
      setPrevia(ruta?.existe ? { ruta, causa: respuesta.red.bloqueos.at(-1)?.elemento ?? "" } : null);
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
            <p role="alert" className="m-0 text-center text-[#9b241b]">
              {error}
            </p>
            <button type="button" onClick={() => void reintentar()} className={`${clasesBoton} ${botonPrimario}`}>
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
  const conteo = {
    Normal: red.nodos.filter((n) => n.nivel_alerta === "Normal").length,
    "Alerta temprana": red.nodos.filter((n) => n.nivel_alerta === "Alerta temprana").length,
    Anómalo: red.nodos.filter((n) => n.nivel_alerta === "Anómalo").length,
  };
  const luz: LuzSemaforo = conteo.Anómalo > 0 ? "rojo" : conteo["Alerta temprana"] > 0 ? "ambar" : "verde";
  const nodoSeleccionado = seleccion?.tipo === "nodo" ? red.nodos.find((n) => n.id === seleccion.id) : undefined;

  return (
    <main className="flex flex-col gap-5 px-7 pb-10 pt-6">
      <header className="flex animate-entrar flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <div className="flex items-center gap-3">
          <Semaforo activa={luz} />
          <h1 className="m-0 text-[26px] font-bold tracking-tight">SoftCast</h1>
        </div>
        <dl className="m-0 flex flex-wrap items-center gap-x-7 gap-y-2 text-sm">
          <Dato nombre="Semilla" valor={String(red.semilla)} />
          <Dato nombre="Fuente" valor={red.fuente === "gnn" ? "GNN" : "umbral"} />
          <Dato nombre="Bloqueados" valor={`${bloqueados} de ${red.nodos.length}`} />
          <div className="flex items-center gap-4" aria-label="Nodos por nivel">
            {RESUMEN.map(({ nivel, color, nombre }) => (
              <span key={nivel} className="inline-flex items-center gap-1.5" title={nombre}>
                <span className="size-2.5 rounded-full" style={{ background: color }} />
                <strong className="font-semibold">{conteo[nivel]}</strong>
                <span className="text-suave">{nombre}</span>
              </span>
            ))}
          </div>
        </dl>
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
          <PanelRuta ruta={ruta} previa={previa} />
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

const RESUMEN = [
  { nivel: "Normal", color: "#1e8449", nombre: "normales" },
  { nivel: "Alerta temprana", color: "#f5b301", nombre: "en alerta" },
  { nivel: "Anómalo", color: "#d1352b", nombre: "anómalos" },
] as const;

function Dato({ nombre, valor }: { nombre: string; valor: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <dt className="text-suave">{nombre}</dt>
      <dd className="m-0 font-semibold">{valor}</dd>
    </div>
  );
}

function Leyenda() {
  const icono = (hijo: React.ReactNode, ancho = 16) => (
    <svg width={ancho} height={16} viewBox={`0 0 ${ancho} 16`} aria-hidden="true">
      {hijo}
    </svg>
  );
  const gris = { fill: "#c7ccd3", stroke: "#8b929c", strokeWidth: 1.5 };
  const items: [React.ReactNode, string][] = [
    [icono(<circle cx="8" cy="8" r="6" fill="#1e8449" />), "Normal"],
    [icono(<circle cx="8" cy="8" r="6" fill="#f5b301" />), "Alerta temprana"],
    [icono(<circle cx="8" cy="8" r="6" fill="#d1352b" />), "Anómalo"],
    [icono(<circle cx="8" cy="8" r="5.5" fill="#d5d9df" stroke="#9aa1ab" strokeWidth="1.5" />), "Bloqueado"],
    [icono(<rect x="2" y="2" width="12" height="12" rx="3.5" {...gris} />), "Servidor"],
    [icono(<circle cx="8" cy="8" r="6" {...gris} />), "PC"],
    [icono(<rect x="3.5" y="3.5" width="9" height="9" rx="2" transform="rotate(45 8 8)" {...gris} />), "IoT"],
    [icono(<line x1="0" y1="8" x2="26" y2="8" stroke="#a9b0ba" strokeWidth="2.4" strokeDasharray="7 5" />, 26), "Enlace redundante"],
    [icono(<line x1="1" y1="8" x2="25" y2="8" stroke="#2b2f36" strokeWidth="5" strokeLinecap="round" />, 26), "Ruta vigente"],
    [icono(<line x1="0" y1="8" x2="26" y2="8" stroke="#d1352b" strokeWidth="2.5" strokeDasharray="3 5" />, 26), "Arista bloqueada"],
  ];
  return (
    <ul className="m-0 flex list-none flex-wrap gap-x-[18px] gap-y-2 p-0 text-[13px] text-suave">
      {items.map(([marca, texto]) => (
        <li key={texto} className="inline-flex items-center gap-1.5">
          {marca}
          {texto}
        </li>
      ))}
    </ul>
  );
}
