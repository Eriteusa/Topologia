"use client";

import { useEffect, useState } from "react";
import { clasesBoton } from "@/components/Panel";
import { coma } from "@/lib/formato";
import type { Arista, NivelAlerta, Nodo, Red, Ruta, Seleccion } from "@/lib/tipos";

const VISTA = { x: 150, y: 220, w: 650, h: 420 };
// Semáforo: el color indica el estado; el tipo de dispositivo se distingue por la forma
const COLOR_NIVEL: Record<Exclude<NivelAlerta, "Bloqueado">, { fondo: string; texto: string }> = {
  Normal: { fondo: "#1e8449", texto: "#ffffff" },
  "Alerta temprana": { fondo: "#f5b301", texto: "#2a1f00" },
  Anómalo: { fondo: "#d1352b", texto: "#ffffff" },
};
const TINTA = "#2b2f36";
const PELIGRO = "#d1352b";
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

/** Trazo de una arista recorrida desde un extremo dado, para animar la ruta en su sentido. */
function trazoRuta(a: Arista, desde: string, pos: Record<string, Punto>): string {
  const inicio = pos[desde];
  const fin = pos[desde === a.origen ? a.destino : a.origen];
  const c = CURVAS[a.id];
  return c
    ? `M${inicio.x} ${inicio.y} Q${c[0]} ${c[1]} ${fin.x} ${fin.y}`
    : `M${inicio.x} ${inicio.y} L${fin.x} ${fin.y}`;
}

const radio = (n: Nodo) => (n.tipo === "Servidor" ? 23 : n.tipo === "IoT" ? 21 : 17);

type Props = {
  red: Red;
  ruta: Ruta | null;
  seleccion: Seleccion;
  ocupado: boolean;
  onSeleccionar: (s: Seleccion) => void;
  onBloquear: (tipo: "nodo" | "arista", elemento: string) => void;
};

export default function Grafo({ red, ruta, seleccion, ocupado, onSeleccionar, onBloquear }: Props) {
  // Versión de la ruta: al cambiar, el trazo vuelve a dibujarse
  const [rutaVista, setRutaVista] = useState(ruta);
  const [version, setVersion] = useState(0);
  if (rutaVista !== ruta) {
    setRutaVista(ruta);
    setVersion((v) => v + 1);
  }

  useEffect(() => {
    const cerrar = (e: KeyboardEvent) => e.key === "Escape" && onSeleccionar(null);
    window.addEventListener("keydown", cerrar);
    return () => window.removeEventListener("keydown", cerrar);
  }, [onSeleccionar]);

  const pos: Record<string, Punto> = Object.fromEntries(red.nodos.map((n) => [n.id, { x: n.x, y: n.y }]));
  const enRuta = new Set(ruta?.existe ? ruta.aristas.map((a) => a.id) : []);
  const geo = Object.fromEntries(red.aristas.map((a) => [a.id, geometria(a, pos)]));

  // Tramos de la ruta en el orden del recorrido
  const tramos: { arista: Arista; d: string }[] = [];
  if (ruta?.existe) {
    for (let i = 0; i < ruta.nodos.length - 1; i++) {
      const u = ruta.nodos[i];
      const v = ruta.nodos[i + 1];
      const arista = red.aristas.find(
        (a) => (a.origen === u && a.destino === v) || (a.origen === v && a.destino === u),
      );
      if (arista) tramos.push({ arista, d: trazoRuta(arista, u, pos) });
    }
  }

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
        fontFamily="var(--font-sans)"
        onClick={() => onSeleccionar(null)}
      >
        <g fill="none" stroke="#b4bac3" strokeWidth={1.5} strokeDasharray="2 5" opacity={0.6}>
          {retiradas.map((a) => (
            <path key={a.id} d={geo[a.id].d} />
          ))}
        </g>

        {activas.map((a) => (
          <path
            key={a.id}
            d={geo[a.id].d}
            fill="none"
            stroke="#a9b0ba"
            strokeWidth={2.4}
            strokeLinecap="round"
            strokeDasharray={a.rol === "Redundante" ? "8 6" : undefined}
          />
        ))}

        {bloqueadas.map((a) => (
          <path
            key={a.id}
            d={geo[a.id].d}
            fill="none"
            stroke={PELIGRO}
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeDasharray="3 5"
          />
        ))}

        <g fill="none" stroke={TINTA} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round">
          {tramos.map(({ arista, d }, i) => (
            <path
              key={`${version}-${arista.id}`}
              d={d}
              pathLength={1}
              className="trazo"
              style={{ animationDelay: `${i * 130}ms` }}
            />
          ))}
        </g>

        {red.aristas.map((a) => (
          <path
            key={`area-${a.id}`}
            d={geo[a.id].d}
            fill="none"
            stroke="transparent"
            strokeWidth={16}
            strokeLinecap="round"
            className="area-arista cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              onSeleccionar({ tipo: "arista", id: a.id });
            }}
          >
            <title>{`${a.origen}–${a.destino}`}</title>
          </path>
        ))}

        <g
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
              fill={enRuta.has(a.id) ? TINTA : "#4a525d"}
              fontWeight={enRuta.has(a.id) ? 700 : 500}
            >
              {a.latencia_ms}
            </text>
          ))}
        </g>

        {bloqueadas.map((a) => (
          <g key={`x-${a.id}`} pointerEvents="none" className="animate-fundir">
            <circle cx={geo[a.id].mx} cy={geo[a.id].my} r={9} fill="#ffffff" stroke={PELIGRO} strokeWidth={1.5} />
            <path
              d={`M${geo[a.id].mx - 4} ${geo[a.id].my - 4} l8 8 M${geo[a.id].mx + 4} ${geo[a.id].my - 4} l-8 8`}
              stroke={PELIGRO}
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
          <g fontSize={11} fontWeight={700} textAnchor="middle" pointerEvents="none">
            {[
              { id: ruta.origen, texto: "origen" },
              { id: ruta.destino, texto: "destino" },
            ].map(({ id, texto }, i) => {
              const n = red.nodos.find((m) => m.id === id);
              if (!n || n.bloqueado) return null;
              return (
                <g key={`${version}-${texto}`} className="animate-fundir" style={{ animationDelay: `${i * 160}ms` }}>
                  <rect x={n.x - 27} y={n.y - radio(n) - 27} width={54} height={19} rx={9.5} fill={TINTA} />
                  <text x={n.x} y={n.y - radio(n) - 14} fill="#ffffff">
                    {texto}
                  </text>
                </g>
              );
            })}
          </g>
        )}
      </svg>

      {nodoSel && (
        <Popover key={`n-${nodoSel.id}`} x={nodoSel.x} y={nodoSel.y} desplazamiento={radio(nodoSel) + 12}>
          <DetalleNodo nodo={nodoSel} ocupado={ocupado} onBloquear={() => onBloquear("nodo", nodoSel.id)} />
        </Popover>
      )}
      {aristaSel && (
        <Popover key={`a-${aristaSel.id}`} x={geo[aristaSel.id].mx} y={geo[aristaSel.id].my} desplazamiento={16}>
          <DetalleArista arista={aristaSel} ocupado={ocupado} onBloquear={() => onBloquear("arista", aristaSel.id)} />
        </Popover>
      )}
    </div>
  );
}

/** Figura del nodo según su tipo: cuadrado (servidor), círculo (PC) o rombo (IoT). */
function Figura({ nodo: n, fondo, borde }: { nodo: Nodo; fondo: string; borde: string }) {
  const comunes = { fill: fondo, stroke: borde, strokeWidth: 2, className: "nodo-figura" };
  if (n.tipo === "Servidor") {
    return <rect x={n.x - 21} y={n.y - 21} width={42} height={42} rx={11} {...comunes} />;
  }
  if (n.tipo === "IoT") {
    return (
      <rect
        x={n.x - 15}
        y={n.y - 15}
        width={30}
        height={30}
        rx={6}
        transform={`rotate(45 ${n.x} ${n.y})`}
        {...comunes}
      />
    );
  }
  return <circle cx={n.x} cy={n.y} r={17} {...comunes} />;
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
  const color = n.bloqueado ? null : COLOR_NIVEL[n.nivel_alerta as keyof typeof COLOR_NIVEL] ?? COLOR_NIVEL.Normal;
  return (
    <g
      tabIndex={0}
      role="button"
      aria-label={`${n.id}, ${n.nivel_alerta}`}
      className="nodo group cursor-pointer outline-none"
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
        <circle cx={n.x} cy={n.y} r={r + 5} fill="none" stroke={TINTA} strokeWidth={2} className="halo" />
      )}
      {seleccionado && (
        <circle
          cx={n.x}
          cy={n.y}
          r={r + 8}
          fill="none"
          stroke={TINTA}
          strokeWidth={2.5}
          strokeDasharray="5 3"
          className="animate-fundir"
        />
      )}
      <circle
        cx={n.x}
        cy={n.y}
        r={r + 8}
        fill="none"
        strokeWidth={2.5}
        className="stroke-transparent group-focus-visible:stroke-[#2b2f36]"
      />
      {color ? (
        <>
          <Figura nodo={n} fondo={color.fondo} borde="#ffffff" />
          <text
            x={n.x}
            y={n.y + 4}
            textAnchor="middle"
            fontSize={n.tipo === "Servidor" ? 12 : 10.5}
            fontWeight={700}
            fill={color.texto}
            pointerEvents="none"
          >
            {n.id}
          </text>
        </>
      ) : (
        <>
          <Figura nodo={n} fondo="#d5d9df" borde="#9aa1ab" />
          <path
            d={`M${n.x - 7} ${n.y - 7} l14 14 M${n.x + 7} ${n.y - 7} l-14 14`}
            stroke="#4a525d"
            strokeWidth={2.6}
            strokeLinecap="round"
            pointerEvents="none"
          />
          <text x={n.x} y={n.y + r + 15} textAnchor="middle" fontSize={11} fontWeight={600} fill="#5f6773">
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
      className="absolute z-10 w-[250px]"
      style={{
        left: `${px}%`,
        top: `${Math.min(Math.max(py, 24), 76)}%`,
        transform: `translate(${aLaIzquierda ? `calc(-100% - ${desplazamiento}px)` : `${desplazamiento}px`}, -50%)`,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <div
        role="dialog"
        className="flex animate-aparecer flex-col gap-2 rounded-2xl border border-borde bg-white p-3.5 shadow-[0_10px_30px_rgba(16,24,40,0.16)]"
        style={{ transformOrigin: aLaIzquierda ? "right center" : "left center" }}
      >
        {children}
      </div>
    </div>
  );
}

function Fila({ nombre, valor }: { nombre: string; valor: React.ReactNode }) {
  return (
    <>
      <span className="text-suave">{nombre}</span>
      <span className="text-right">{valor}</span>
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
        <Fila nombre="Nivel" valor={n.nivel_alerta} />
      </div>
      <div className="text-xs text-suave">
        Secuencia <span className="font-semibold text-tinta">{n.secuencia}</span> ·{" "}
        {n.secuencia_valida ? "aceptada" : "rechazada"}
      </div>
      {!n.bloqueado && (
        <button
          type="button"
          disabled={ocupado}
          onClick={onBloquear}
          className={`${clasesBoton} bg-peligro text-white hover:bg-[#b82d24]`}
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
        <strong className="text-[15px]">
          {a.origen}–{a.destino}
        </strong>
        <span className="text-xs text-suave">{a.rol}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[13px]">
        <Fila nombre="Origen" valor={a.origen} />
        <Fila nombre="Destino" valor={a.destino} />
        <Fila nombre="Latencia" valor={`${a.latencia_ms} ms`} />
        <Fila nombre="Estado" valor={estado} />
      </div>
      {a.activa && (
        <button
          type="button"
          disabled={ocupado}
          onClick={onBloquear}
          className={`${clasesBoton} bg-peligro text-white hover:bg-[#b82d24]`}
        >
          Bloquear arista
        </button>
      )}
    </>
  );
}
