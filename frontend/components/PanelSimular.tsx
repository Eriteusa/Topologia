"use client";

import { useState } from "react";
import Panel, { clasesBoton, clasesCampo } from "@/components/Panel";
import type { Nodo } from "@/lib/tipos";

type Props = {
  nodos: Nodo[];
  nodoId: string;
  ocupado: boolean;
  onCambiarNodo: (id: string) => void;
  onAplicar: (id: string, trafico: number, cpu: number) => void;
};

function Deslizador({
  id,
  etiqueta,
  valor,
  sufijo,
  onCambiar,
}: {
  id: string;
  etiqueta: string;
  valor: number;
  sufijo?: string;
  onCambiar: (v: number) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-[13px]">
        <label htmlFor={id}>{etiqueta}</label>
        <span className="font-mono">
          {valor}
          {sufijo}
        </span>
      </div>
      <input
        id={id}
        type="range"
        min={0}
        max={100}
        value={valor}
        onChange={(e) => onCambiar(Number(e.target.value))}
        className="min-h-8 w-full accent-primario"
      />
    </div>
  );
}

export default function PanelSimular({ nodos, nodoId, ocupado, onCambiarNodo, onAplicar }: Props) {
  // Mientras el usuario no mueve un deslizador se muestran los valores reales del nodo.
  const [edicion, setEdicion] = useState<{ nodo: string; trafico: number; cpu: number } | null>(null);
  const libres = nodos.filter((n) => !n.bloqueado);
  const nodo = libres.find((n) => n.id === nodoId);
  const actual = edicion?.nodo === nodoId ? edicion : nodo ? { nodo: nodoId, trafico: nodo.trafico, cpu: nodo.cpu } : null;

  return (
    <Panel titulo="Simular falla">
      <div className="flex flex-col gap-1">
        <label htmlFor="nodo-falla" className="text-xs text-suave">
          Nodo
        </label>
        <select
          id="nodo-falla"
          value={nodo ? nodoId : ""}
          onChange={(e) => onCambiarNodo(e.target.value)}
          className={clasesCampo}
        >
          <option value="">—</option>
          {libres.map((n) => (
            <option key={n.id} value={n.id}>
              {n.id}
            </option>
          ))}
        </select>
      </div>

      <Deslizador
        id="trafico"
        etiqueta="Tráfico"
        valor={actual?.trafico ?? 0}
        onCambiar={(v) => actual && setEdicion({ ...actual, trafico: v })}
      />
      <Deslizador
        id="cpu"
        etiqueta="CPU"
        valor={actual?.cpu ?? 0}
        sufijo=" %"
        onCambiar={(v) => actual && setEdicion({ ...actual, cpu: v })}
      />

      <button
        type="button"
        disabled={ocupado || !actual}
        onClick={() => {
          if (!actual) return;
          onAplicar(actual.nodo, actual.trafico, actual.cpu);
          setEdicion(null);
        }}
        className={`${clasesBoton} bg-primario text-white`}
      >
        Aplicar y reclasificar
      </button>
    </Panel>
  );
}
