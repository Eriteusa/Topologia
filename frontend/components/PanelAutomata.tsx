"use client";

import { useEffect, useState } from "react";
import Panel, { clasesBoton, clasesCampo } from "@/components/Panel";
import { ErrorApi, validarCadena } from "@/lib/api";
import type { DefinicionAutomata, ResultadoAutomata } from "@/lib/tipos";

const MS_POR_SIMBOLO = 450;
const EJEMPLOS = ["abcde", "abcccde", "ac", "abde", "abcfde"];
const NOMBRES: Record<string, string> = {
  q0: "Inactivo",
  q1: "Solicitud",
  q2: "Autenticación",
  q3: "Transmisión",
  q4: "Confirmación",
  q5: "Finalizado",
};

// Geometría del diagrama: estados en línea y qNP debajo
const Y = 78;
const R = 26;
const NP = { x: 335, y: 190 };
const posX = (i: number) => 58 + 110 * i;

const GRIS = "#8b95a3";
const VERDE = "#1f7a4d";
const NARANJA = "#e8742a";
const ROJO = "#c0392b";

type Corrida = { cadena: string; resultado: ResultadoAutomata; paso: number };

function Marcador({ id, color }: { id: string; color: string }) {
  return (
    <marker id={id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0 0 L10 5 L0 10 z" fill={color} />
    </marker>
  );
}

export default function PanelAutomata({
  definicion,
  secuenciaNodo,
}: {
  definicion: DefinicionAutomata | null;
  secuenciaNodo: { id: string; secuencia: string } | null;
}) {
  const [cadena, setCadena] = useState("abcde");
  const [corrida, setCorrida] = useState<Corrida | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);

  // Avanza un símbolo cada MS_POR_SIMBOLO hasta llegar al final del recorrido
  useEffect(() => {
    if (!corrida || corrida.paso >= corrida.resultado.recorrido.length - 1) return;
    const temporizador = setTimeout(
      () => setCorrida((c) => (c ? { ...c, paso: c.paso + 1 } : c)),
      MS_POR_SIMBOLO,
    );
    return () => clearTimeout(temporizador);
  }, [corrida]);

  async function validar(texto: string) {
    setOcupado(true);
    setAviso(null);
    try {
      const resultado = await validarCadena(texto);
      setCorrida({ cadena: texto, resultado, paso: 0 });
    } catch (e) {
      setAviso(e instanceof ErrorApi ? e.message : "No se pudo validar");
    } finally {
      setOcupado(false);
    }
  }

  function usar(texto: string) {
    setCadena(texto);
    void validar(texto);
  }

  if (!definicion) {
    return (
      <Panel titulo="Autómata de comunicación">
        <span className="text-suave">—</span>
      </Panel>
    );
  }

  const { Q, sigma, q0, F, delta } = definicion;
  const estados = Q.filter((q) => q !== "qNP");
  const recorrido = corrida?.resultado.recorrido ?? [];
  const paso = corrida?.paso ?? 0;
  const activo = corrida ? recorrido[paso] : q0;
  const terminada = corrida !== null && paso >= recorrido.length - 1;

  // Transiciones tomadas hasta el paso actual: clave "desde>hasta" y celda "estado,símbolo"
  const tomadas = new Set<string>();
  const celdas = new Set<string>();
  let actual = "";
  let celdaActual = "";
  if (corrida) {
    for (let i = 1; i <= paso; i++) {
      const clave = `${recorrido[i - 1]}>${recorrido[i]}`;
      const celda = `${recorrido[i - 1]},${corrida.cadena[i - 1]}`;
      tomadas.add(clave);
      celdas.add(celda);
      if (i === paso) {
        actual = clave;
        celdaActual = celda;
      }
    }
  }
  const visitados = new Set(recorrido.slice(0, paso + 1));

  // Transiciones del lenguaje (las que no van a qNP), agrupadas por par de estados
  const lenguaje = new Map<string, { desde: string; hasta: string; simbolos: string[] }>();
  for (const q of estados) {
    for (const s of sigma) {
      const hasta = delta[q][s];
      if (hasta === "qNP") continue;
      const clave = `${q}>${hasta}`;
      const previa = lenguaje.get(clave);
      if (previa) previa.simbolos.push(s);
      else lenguaje.set(clave, { desde: q, hasta, simbolos: [s] });
    }
  }

  const colorTransicion = (clave: string, base: string) =>
    actual === clave ? NARANJA : tomadas.has(clave) ? VERDE : base;
  const anchoTransicion = (clave: string) => (actual === clave ? 4 : tomadas.has(clave) ? 3 : 2);
  const marcador = (clave: string) =>
    actual === clave ? "url(#flecha-naranja)" : tomadas.has(clave) ? "url(#flecha-verde)" : "url(#flecha-gris)";

  return (
    <Panel
      titulo="Autómata de comunicación"
      derecha={<span className="font-mono text-[13px] text-suave">L(M) = {"{ a b c⁺ d e }"}</span>}
    >
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex min-w-[200px] flex-1 flex-col gap-1">
          <label htmlFor="cadena" className="text-xs text-suave">
            Cadena de eventos
          </label>
          <input
            id="cadena"
            type="text"
            value={cadena}
            autoComplete="off"
            spellCheck={false}
            onChange={(e) => setCadena(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && validar(cadena)}
            className={`${clasesCampo} font-mono text-base`}
          />
        </div>
        <button
          type="button"
          disabled={ocupado}
          onClick={() => validar(cadena)}
          className={`${clasesBoton} bg-primario text-white`}
        >
          Validar
        </button>
        {secuenciaNodo && (
          <button
            type="button"
            disabled={ocupado}
            onClick={() => usar(secuenciaNodo.secuencia)}
            className={`${clasesBoton} border border-borde-fuerte bg-white font-medium`}
          >
            Secuencia de {secuenciaNodo.id}
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-suave">Ejemplos</span>
        {EJEMPLOS.map((e) => (
          <button
            key={e}
            type="button"
            disabled={ocupado}
            onClick={() => usar(e)}
            className="min-h-11 cursor-pointer rounded-md border border-[#c3cad4] bg-fondo px-3.5 font-mono text-sm disabled:opacity-50"
          >
            {e}
          </button>
        ))}
      </div>

      {corrida && corrida.cadena !== "" && (
        <div className="font-mono text-lg tracking-widest" aria-label={`Cadena ${corrida.cadena}`}>
          {[...corrida.cadena].map((simbolo, i) => (
            <span
              key={i}
              className={i === paso - 1 ? "rounded bg-[#ffe3cc] px-0.5 text-[#7a3200]" : i < paso - 1 ? "text-suave" : ""}
            >
              {simbolo}
            </span>
          ))}
        </div>
      )}

      <svg viewBox="0 0 760 262" className="block h-auto w-full" role="img" aria-label="Diagrama del autómata">
        <defs>
          <Marcador id="flecha-gris" color={GRIS} />
          <Marcador id="flecha-verde" color={VERDE} />
          <Marcador id="flecha-naranja" color={NARANJA} />
        </defs>

        {/* aristas hacia qNP desde cada estado: tenues */}
        {estados.map((q, i) => {
          const de = { x: posX(i), y: Y };
          const dx = NP.x - de.x;
          const dy = NP.y - de.y;
          const largo = Math.hypot(dx, dy);
          const clave = `${q}>qNP`;
          const resaltada = tomadas.has(clave);
          return (
            <line
              key={clave}
              x1={de.x + (dx / largo) * R}
              y1={de.y + (dy / largo) * R}
              x2={NP.x - (dx / largo) * R}
              y2={NP.y - (dy / largo) * R}
              stroke={actual === clave ? ROJO : resaltada ? "#c0605a" : "#d4aaa6"}
              strokeWidth={actual === clave ? 3 : resaltada ? 2 : 1.2}
              opacity={resaltada ? 1 : 0.8}
            />
          );
        })}
        <path
          d={`M${NP.x - 14} ${NP.y + 23} C${NP.x - 30} ${NP.y + 62}, ${NP.x + 30} ${NP.y + 62}, ${NP.x + 14} ${NP.y + 23}`}
          fill="none"
          stroke={actual === "qNP>qNP" ? ROJO : tomadas.has("qNP>qNP") ? "#c0605a" : "#d4aaa6"}
          strokeWidth={actual === "qNP>qNP" ? 3 : tomadas.has("qNP>qNP") ? 2 : 1.2}
        />

        {/* flecha de entrada a q0 */}
        <line x1={8} y1={Y} x2={posX(0) - R - 2} y2={Y} stroke={GRIS} strokeWidth={2} markerEnd="url(#flecha-gris)" />

        {/* transiciones del lenguaje */}
        {[...lenguaje.entries()].map(([clave, t]) => {
          const i = estados.indexOf(t.desde);
          const j = estados.indexOf(t.hasta);
          const color = colorTransicion(clave, "#6b7686");
          const texto = t.simbolos.join(", ");
          if (i === j) {
            const x = posX(i);
            return (
              <g key={clave}>
                <path
                  d={`M${x - 12} ${Y - R + 2} C${x - 26} ${Y - 74}, ${x + 26} ${Y - 74}, ${x + 12} ${Y - R + 2}`}
                  fill="none"
                  stroke={color}
                  strokeWidth={anchoTransicion(clave)}
                  markerEnd={marcador(clave)}
                />
                <text x={x} y={Y - 64} textAnchor="middle" className="font-mono" fontSize={15} fontWeight={600} fill={color}>
                  {texto}
                </text>
              </g>
            );
          }
          const sentido = j > i ? 1 : -1;
          const x1 = posX(i) + sentido * R;
          const x2 = posX(j) - sentido * (R + 2);
          return (
            <g key={clave}>
              <line x1={x1} y1={Y} x2={x2} y2={Y} stroke={color} strokeWidth={anchoTransicion(clave)} markerEnd={marcador(clave)} />
              <text x={(x1 + x2) / 2} y={Y - 12} textAnchor="middle" className="font-mono" fontSize={15} fontWeight={600} fill={color}>
                {texto}
              </text>
            </g>
          );
        })}

        {/* estados */}
        {estados.map((q, i) => {
          const esActivo = activo === q;
          const fondo = esActivo ? "#ffe3cc" : visitados.has(q) && corrida ? "#e3f3ea" : "#f4f6f8";
          const borde = esActivo ? NARANJA : visitados.has(q) && corrida ? VERDE : GRIS;
          return (
            <g key={q}>
              <circle cx={posX(i)} cy={Y} r={R} fill={fondo} stroke={borde} strokeWidth={esActivo ? 4 : 2.5} />
              {F.includes(q) && <circle cx={posX(i)} cy={Y} r={R + 5} fill="none" stroke={borde} strokeWidth={2.5} />}
              <text x={posX(i)} y={Y + 5} textAnchor="middle" className="font-mono" fontSize={15} fontWeight={600} fill="#1c2430">
                {q}
              </text>
              <text
                x={posX(i)}
                y={Y + R + 20}
                textAnchor="middle"
                fontSize={11}
                fill="#566171"
                stroke="#ffffff"
                strokeWidth={4}
                paintOrder="stroke"
                strokeLinejoin="round"
              >
                {NOMBRES[q]}
              </text>
            </g>
          );
        })}
        <g>
          <circle
            cx={NP.x}
            cy={NP.y}
            r={R - 1}
            fill={activo === "qNP" ? "#fde2e0" : "#f4f6f8"}
            stroke={activo === "qNP" ? ROJO : GRIS}
            strokeWidth={activo === "qNP" ? 4 : 2}
            strokeDasharray={activo === "qNP" ? undefined : "4 3"}
          />
          <text x={NP.x} y={NP.y + 5} textAnchor="middle" className="font-mono" fontSize={14} fontWeight={600} fill="#1c2430">
            qNP
          </text>
        </g>
      </svg>

      {aviso && (
        <p role="alert" className="m-0 rounded-md bg-[#fdecea] px-3 py-2 text-[13px] text-[#8c2520]">
          {aviso}
        </p>
      )}

      {terminada && corrida && (
        <div
          className={`flex flex-wrap items-center gap-x-4 gap-y-1 rounded-md border px-3 py-2.5 ${
            corrida.resultado.aceptada ? "border-[#1f7a4d] bg-[#e3f3ea] text-[#14532d]" : "border-[#c0392b] bg-[#fdecea] text-[#8c2520]"
          }`}
        >
          <strong className="text-[15px]">{corrida.resultado.aceptada ? "Aceptada" : "Rechazada"}</strong>
          <span className="font-mono text-sm">{recorrido.join(" → ")}</span>
          {corrida.resultado.error && <span className="text-sm">{corrida.resultado.error}</span>}
        </div>
      )}

      {/* Los 5 parámetros formales M = (Q, Σ, δ, q0, F) */}
      <div className="flex flex-col gap-2 border-t border-borde pt-3">
        <div className="grid grid-cols-[44px_minmax(0,1fr)] gap-x-2 gap-y-1 font-mono text-sm">
          <strong>Q</strong>
          <span>{`{ ${Q.join(", ")} }`}</span>
          <strong>Σ</strong>
          <span>{`{ ${sigma.join(", ")} }`}</span>
          <strong>q0</strong>
          <span>{q0}</span>
          <strong>F</strong>
          <span>{`{ ${F.join(", ")} }`}</span>
          <strong>δ</strong>
          <span />
        </div>
        <div
          className="grid overflow-hidden rounded-md border border-[#c3cad4] text-center font-mono text-[13px]"
          style={{ gridTemplateColumns: `64px repeat(${sigma.length}, minmax(0, 1fr))` }}
        >
          <span className="bg-[#e6eaef] px-1 py-1.5" />
          {sigma.map((s) => (
            <span key={s} className="border-l border-[#c3cad4] bg-[#e6eaef] px-1 py-1.5 font-semibold">
              {s}
            </span>
          ))}
          {Q.map((q) => (
            <FilaDelta
              key={q}
              etiqueta={(q === q0 ? "→" : "") + (F.includes(q) ? "*" : "") + q}
              q={q}
              sigma={sigma}
              delta={delta}
              celdas={celdas}
              celdaActual={celdaActual}
            />
          ))}
        </div>
      </div>
    </Panel>
  );
}

function FilaDelta({
  etiqueta,
  q,
  sigma,
  delta,
  celdas,
  celdaActual,
}: {
  etiqueta: string;
  q: string;
  sigma: string[];
  delta: Record<string, Record<string, string>>;
  celdas: Set<string>;
  celdaActual: string;
}) {
  return (
    <>
      <span className="border-t border-[#c3cad4] bg-fondo py-1.5 pl-2 text-left font-semibold">{etiqueta}</span>
      {sigma.map((s) => {
        const clave = `${q},${s}`;
        const destino = delta[q][s];
        const fondo = celdaActual === clave ? "bg-[#ffe3cc] font-bold" : celdas.has(clave) ? "bg-[#e3f3ea] font-bold" : "";
        return (
          <span
            key={s}
            className={`border-l border-t border-[#c3cad4] px-1 py-1.5 ${fondo} ${destino === "qNP" && !celdas.has(clave) ? "text-[#8a929e]" : ""}`}
          >
            {destino}
          </span>
        );
      })}
    </>
  );
}
