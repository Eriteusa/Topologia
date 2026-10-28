"use client";

import Panel, { clasesBoton, clasesCampo } from "@/components/Panel";
import type { Nodo } from "@/lib/tipos";

export type Controles = {
  semilla: string;
  atributos: "base" | "aleatorios";
  latencias: "base" | "aleatorias";
  bloqueoInicial: boolean;
  origen: string;
  destino: string;
};

type Props = {
  valores: Controles;
  nodos: Nodo[];
  ocupado: boolean;
  error: string | null;
  onCambiar: (cambios: Partial<Controles>) => void;
  onNuevaSesion: () => void;
  onCalcular: () => void;
  onAzar: () => void;
  onReiniciar: () => void;
};

function Selector({
  id,
  etiqueta,
  valor,
  opciones,
  onCambiar,
}: {
  id: string;
  etiqueta: string;
  valor: string;
  opciones: { valor: string; texto: string }[];
  onCambiar: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs text-suave">
        {etiqueta}
      </label>
      <select id={id} value={valor} onChange={(e) => onCambiar(e.target.value)} className={clasesCampo}>
        {opciones.map((o) => (
          <option key={o.valor} value={o.valor}>
            {o.texto}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function PanelControles({
  valores,
  nodos,
  ocupado,
  error,
  onCambiar,
  onNuevaSesion,
  onCalcular,
  onAzar,
  onReiniciar,
}: Props) {
  const libres = nodos.filter((n) => !n.bloqueado).map((n) => ({ valor: n.id, texto: n.id }));
  const conVacio = [{ valor: "", texto: "—" }, ...libres];
  const listo = valores.origen !== "" && valores.destino !== "" && valores.origen !== valores.destino;

  return (
    <Panel titulo="Controles">
      <div className="flex items-end gap-2">
        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <label htmlFor="semilla" className="text-xs text-suave">
            Semilla
          </label>
          <input
            id="semilla"
            type="text"
            inputMode="numeric"
            value={valores.semilla}
            onChange={(e) => onCambiar({ semilla: e.target.value })}
            onKeyDown={(e) => e.key === "Enter" && onNuevaSesion()}
            className={`${clasesCampo} w-full font-mono text-base`}
          />
        </div>
        <button
          type="button"
          disabled={ocupado}
          onClick={onNuevaSesion}
          className={`${clasesBoton} whitespace-nowrap border border-primario bg-white text-primario`}
        >
          Nueva sesión
        </button>
      </div>

      <div className="grid grid-cols-2 gap-[10px]">
        <Selector
          id="atributos"
          etiqueta="Atributos"
          valor={valores.atributos}
          opciones={[
            { valor: "base", texto: "base" },
            { valor: "aleatorios", texto: "aleatorios" },
          ]}
          onCambiar={(v) => onCambiar({ atributos: v as Controles["atributos"] })}
        />
        <Selector
          id="latencias"
          etiqueta="Latencias"
          valor={valores.latencias}
          opciones={[
            { valor: "base", texto: "base" },
            { valor: "aleatorias", texto: "aleatorias" },
          ]}
          onCambiar={(v) => onCambiar({ latencias: v as Controles["latencias"] })}
        />
        <Selector
          id="origen"
          etiqueta="Origen"
          valor={valores.origen}
          opciones={conVacio}
          onCambiar={(v) => onCambiar({ origen: v })}
        />
        <Selector
          id="destino"
          etiqueta="Destino"
          valor={valores.destino}
          opciones={conVacio}
          onCambiar={(v) => onCambiar({ destino: v })}
        />
      </div>

      <label className="flex min-h-11 items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={valores.bloqueoInicial}
          onChange={(e) => onCambiar({ bloqueoInicial: e.target.checked })}
          className="size-4 accent-primario"
        />
        Bloqueo inicial
      </label>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={ocupado || !listo}
          onClick={onCalcular}
          className={`${clasesBoton} flex-auto bg-primario text-white`}
        >
          Calcular ruta
        </button>
        <button
          type="button"
          disabled={ocupado || !listo}
          onClick={onAzar}
          className={`${clasesBoton} flex-auto border border-peligro bg-white text-[#8c2520]`}
        >
          Bloqueo aleatorio
        </button>
        <button
          type="button"
          disabled={ocupado}
          onClick={onReiniciar}
          className={`${clasesBoton} flex-auto border border-borde-fuerte bg-white font-medium`}
        >
          Reiniciar
        </button>
      </div>

      {error && (
        <p role="alert" className="m-0 rounded-md bg-[#fdecea] px-3 py-2 text-[13px] text-[#8c2520]">
          {error}
        </p>
      )}
    </Panel>
  );
}
