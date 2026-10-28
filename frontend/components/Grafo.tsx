"use client";

import { useEffect } from "react";
import { clasesBoton } from "@/components/Panel";
import { coma } from "@/lib/formato";
import type { Arista, Nodo, Red, Ruta, Seleccion } from "@/lib/tipos";

const VISTA = { x: 150, y: 220, w: 650, h: 420 };
const COLOR_TIPO = { Servidor: "#14365e", PC: "#3f7cb5", IoT: "#2f8a5f" } as const;
// Aristas que se dibujan curvas, como en la Figura 1 del documento (punto de control)
const CURVAS: Record<string, [number, number]> = { "S2-IoT5": [520, 560] };

type Punto = { x: number; y: number };

function geometria(a: Arista, pos: Record<string, Punto>) {
  const p = pos[a.origen];
  const q = pos[a.destino];
  const c = CURVAS[a.id];
  if (c) {
    return {
      d: `M${p.x} ${p.y} Q${c[0]} ${c[1]} ${q.x} ${q.y}`,
      mx: 0.25 * p.x + 0.5 * c[0] + 0.25 * q.x,
      my: 0.25 * p.y + 0.5 * c[1] + 0.25 * q.y,
    };
  }
  return { d: `M${p.x} ${p.y} L${q.x} ${q.y}`, mx: (p.x + q.x) / 2, my: (p.y + q.y) / 2 };
}

const radio = (n: Nodo) => (n.tipo === "Servidor" ? 23 : 17);

type Props = {
  red: Red;
  ruta: Ruta | null;
  seleccion: Seleccion;
  ocupado: boolean;
  onSeleccionar: (s: Seleccion) => void;
  onBloquear: (tipo: "nodo" | "arista", elemento: string) => void;
};

export default function Grafo({ red, ruta, seleccion, ocupado, onSeleccionar, onBloquear }: Props) {
  useEffect(() => {
    const cerrar = (e: KeyboardEvent) => e.key === "Escape" && onSeleccionar(null);
    window.addEventListener("keydown", cerrar);
    return () => window.removeEventListener("keydown", cerrar);
  }, [onSeleccionar]);

  const pos: Record<string, Punto> = Object.fromEntries(red.nodos.map((n) => [n.id, { x: n.x, y: n.y }]));
  const enRuta = new Set(ruta?.existe ? ruta.aristas.map((a) => a.id) : []);
  const geo = Object.fromEntries(red.aristas.map((a) => [a.id, geometria(a, pos)]));

  const retiradas = red.aristas.filter((a) => !a.activa && !a.bloqueada);
  const bloqueadas = red.aristas.filter((a) => a.bloqueada);
  const activas = red.aristas.filter((a) => a.activa);

  const nodoSel = seleccion?.tipo === "nodo" ? red.nodos.find((n) => n.id === seleccion.id) : undefined;
  const aristaSel = seleccion?.tipo === "arista" ? red.aristas.find((a) => a.id === seleccion.id) : undefined;

  return (
    <div className="relative">
      <svg
        viewBox={`${VISTA.x} ${VISTA.y} ${VISTA.w} ${VISTA.h}`}
        className="block h-auto w-full"
        role="group"
        aria-label="Grafo de la red SoftCast"
        onClick={() => onSeleccionar(null)}
      >
        <g fill="none" stroke="#a3acb8" strokeWidth={1.5} strokeDasharray="2 5" opacity={0.55}>
          {retiradas.map((a) => (
            <path key={a.id} d={geo[a.id].d} />
          ))}
        </g>

        {activas.map((a) => (
          <path
            key={a.id}
            d={geo[a.id].d}
            fill="none"
            stroke="#7d8999"
            strokeWidth={2.5}
            strokeDasharray={a.rol === "Redundante" ? "8 6" : undefined}
          />
        ))}

        {bloqueadas.map((a) => (
          <path key={a.id} d={geo[a.id].d} fill="none" stroke="#c0392b" strokeWidth={2.5} strokeDasharray="3 5" />
        ))}

        <g fill="none" stroke="#e8742a" strokeWidth={6} strokeLinecap="round">
          {activas.filter((a) => enRuta.has(a.id)).map((a) => (
            <path key={a.id} d={geo[a.id].d} />
          ))}
        </g>

        {red.aristas.map((a) => (
          <path
            key={`area-${a.id}`}
            d={geo[a.id].d}
            fill="none"
            stroke="transparent"
            strokeWidth={16}
            className="cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              onSeleccionar({ tipo: "arista", id: a.id });
            }}
          >
            <title>{`${a.origen}–${a.destino}`}</title>
          </path>
        ))}

        <g
          fontFamily="var(--font-plex-mono), monospace"
          fontSize={12}
          fontWeight={500}
          textAnchor="middle"
          paintOrder="stroke"
          stroke="#ffffff"
          strokeWidth={4}
          strokeLinejoin="round"
          pointerEvents="none"
        >
          {activas.map((a) => (
            <text
              key={a.id}
              x={geo[a.id].mx}
              y={geo[a.id].my + 4}
              fill={enRuta.has(a.id) ? "#b24f10" : "#2d3745"}
              fontWeight={enRuta.has(a.id) ? 700 : 500}
            >
              {a.latencia_ms}
            </text>
          ))}
        </g>

        {bloqueadas.map((a) => (
          <g key={`x-${a.id}`} pointerEvents="none">
            <circle cx={geo[a.id].mx} cy={geo[a.id].my} r={9} fill="#ffffff" stroke="#c0392b" strokeWidth={1.5} />
            <path
              d={`M${geo[a.id].mx - 4} ${geo[a.id].my - 4} l8 8 M${geo[a.id].mx + 4} ${geo[a.id].my - 4} l-8 8`}
              stroke="#c0392b"
              strokeWidth={2.2}
              strokeLinecap="round"
            />
          </g>
        ))}

        {red.nodos.map((n) => (
          <NodoSvg
            key={n.id}
            nodo={n}
            seleccionado={seleccion?.tipo === "nodo" && seleccion.id === n.id}
            onSeleccionar={onSeleccionar}
          />
        ))}

        {ruta && (
          <g fontFamily="var(--font-plex-sans), sans-serif" fontSize={11} fontWeight={700} textAnchor="middle" pointerEvents="none">
            {[
              { id: ruta.origen, texto: "origen" },
              { id: ruta.destino, texto: "destino" },
            ].map(({ id, texto }) => {
              const n = red.nodos.find((m) => m.id === id);
              if (!n || n.bloqueado) return null;
              return (
                <g key={texto}>
                  <rect x={n.x - 26} y={n.y - radio(n) - 25} width={52} height={17} rx={4} fill="#e8742a" />
                  <text x={n.x} y={n.y - radio(n) - 13} fill="#2b1200">
                    {texto}
                  </text>
                </g>
              );
            })}
          </g>
        )}
      </svg>

      {nodoSel && (
        <Popover x={nodoSel.x} y={nodoSel.y} desplazamiento={radio(nodoSel) + 12}>
          <DetalleNodo nodo={nodoSel} ocupado={ocupado} onBloquear={() => onBloquear("nodo", nodoSel.id)} />
        </Popover>
      )}
      {aristaSel && (
        <Popover x={geo[aristaSel.id].mx} y={geo[aristaSel.id].my} desplazamiento={16}>
          <DetalleArista arista={aristaSel} ocupado={ocupado} onBloquear={() => onBloquear("arista", aristaSel.id)} />
        </Popover>
      )}
    </div>
  );
}

function NodoSvg({
  nodo: n,
  seleccionado,
  onSeleccionar,
}: {
  nodo: Nodo;
  seleccionado: boolean;
  onSeleccionar: (s: Seleccion) => void;
}) {
  const r = radio(n);
  const seleccionar = () => onSeleccionar({ tipo: "nodo", id: n.id });
  return (
    <g
      tabIndex={0}
      role="button"
      aria-label={`${n.id}, ${n.estado}`}
      className="group cursor-pointer outline-none"
      onClick={(e) => {
        e.stopPropagation();
        seleccionar();
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          seleccionar();
        }
      }}
    >
      {n.delta_p !== null && !n.bloqueado && (
        <circle cx={n.x} cy={n.y} r={r + 6} fill="none" stroke="#c48a00" strokeWidth={2.5} strokeDasharray="4 3" />
      )}
      {seleccionado && (
        <circle cx={n.x} cy={n.y} r={r + 8} fill="none" stroke="#1f4e8c" strokeWidth={2.5} strokeDasharray="5 3" />
      )}
      <circle
        cx={n.x}
        cy={n.y}
        r={r + 8}
        fill="none"
        strokeWidth={2.5}
        className="stroke-transparent group-focus-visible:stroke-[#1f4e8c]"
      />
      {n.bloqueado ? (
        <>
          <circle cx={n.x} cy={n.y} r={r} fill="#c3c9d1" stroke="#8b95a3" strokeWidth={2} />
          <path
            d={`M${n.x - 8} ${n.y - 8} l16 16 M${n.x + 8} ${n.y - 8} l-16 16`}
            stroke="#3d4755"
            strokeWidth={3}
            strokeLinecap="round"
          />
          <text x={n.x} y={n.y + r + 14} textAnchor="middle" fontSize={11} fontWeight={600} fill="#566171">
            {n.id}
          </text>
        </>
      ) : (
        <>
          <circle
            cx={n.x}
            cy={n.y}
            r={r}
            fill={COLOR_TIPO[n.tipo]}
            stroke={n.estado === "Anómalo" ? "#d64545" : "none"}
            strokeWidth={4}
          />
          <text
            x={n.x}
            y={n.y + 4}
            textAnchor="middle"
            fontSize={n.tipo === "Servidor" ? 12 : 10.5}
            fontWeight={700}
            fill="#ffffff"
          >
            {n.id}
          </text>
        </>
      )}
    </g>
  );
}

function Popover({
  x,
  y,
  desplazamiento,
  children,
}: {
  x: number;
  y: number;
  desplazamiento: number;
  children: React.ReactNode;
}) {
  const px = ((x - VISTA.x) / VISTA.w) * 100;
  const py = ((y - VISTA.y) / VISTA.h) * 100;
  const aLaIzquierda = px > 55;
  return (
    <div
      role="dialog"
      className="absolute z-10 flex w-[250px] flex-col gap-2 rounded-lg border border-[#b9c1cc] bg-white p-3 shadow-[0_6px_18px_rgba(20,54,94,0.18)]"
      style={{
        left: `${px}%`,
        top: `${Math.min(Math.max(py, 24), 76)}%`,
        transform: `translate(${aLaIzquierda ? `calc(-100% - ${desplazamiento}px)` : `${desplazamiento}px`}, -50%)`,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </div>
  );
}

function Fila({ nombre, valor }: { nombre: string; valor: React.ReactNode }) {
  return (
    <>
      <span className="text-suave">{nombre}</span>
      <span className="text-right font-mono">{valor}</span>
    </>
  );
}

function DetalleNodo({ nodo: n, ocupado, onBloquear }: { nodo: Nodo; ocupado: boolean; onBloquear: () => void }) {
  return (
    <>
      <div className="flex items-baseline justify-between gap-2">
        <strong className="text-[15px]">{n.id}</strong>
        <span className="text-right text-xs text-suave">
          {n.tipo} · {n.subtipo}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[13px]">
        <Fila nombre="Tráfico" valor={n.trafico} />
        <Fila nombre="CPU" valor={`${n.cpu} %`} />
        <Fila nombre="p anómalo" valor={n.p_anomalo === null ? "—" : coma(n.p_anomalo)} />
        <Fila nombre="Nivel" valor={<span className="font-sans">{n.nivel_alerta}</span>} />
      </div>
      <div className="text-xs text-suave">
        Secuencia <span className="font-mono text-tinta">{n.secuencia}</span> ·{" "}
        {n.secuencia_valida ? "aceptada" : "rechazada"}
      </div>
      {!n.bloqueado && (
        <button
          type="button"
          disabled={ocupado}
          onClick={onBloquear}
          className={`${clasesBoton} bg-peligro text-white`}
        >
          Bloquear nodo
        </button>
      )}
    </>
  );
}

function DetalleArista({
  arista: a,
  ocupado,
  onBloquear,
}: {
  arista: Arista;
  ocupado: boolean;
  onBloquear: () => void;
}) {
  const estado = a.bloqueada ? "Bloqueada" : a.activa ? "Activa" : "Retirada";
  return (
    <>
      <div className="flex items-baseline justify-between gap-2">
        <strong className="font-mono text-[15px]">
          {a.origen}–{a.destino}
        </strong>
        <span className="text-xs text-suave">{a.rol}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[13px]">
        <Fila nombre="Origen" valor={a.origen} />
        <Fila nombre="Destino" valor={a.destino} />
        <Fila nombre="Latencia" valor={`${a.latencia_ms} ms`} />
        <Fila nombre="Estado" valor={<span className="font-sans">{estado}</span>} />
      </div>
      {a.activa && (
        <button
          type="button"
          disabled={ocupado}
          onClick={onBloquear}
          className={`${clasesBoton} bg-peligro text-white`}
        >
          Bloquear arista
        </button>
      )}
    </>
  );
}
