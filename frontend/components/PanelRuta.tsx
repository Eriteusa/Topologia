import Panel from "@/components/Panel";
import type { Ruta } from "@/lib/tipos";

/** Ruta que había antes del último bloqueo y el elemento que se bloqueó. */
export type RutaPrevia = { ruta: Ruta; causa: string };

const guion = (id: string) => id.replace("-", "–");

function Cadena({ nodos }: { nodos: string[] }) {
  return (
    <span className="inline-flex flex-wrap items-center gap-x-1.5">
      {nodos.map((id, i) => (
        <span key={`${id}-${i}`} className="inline-flex items-center gap-1.5">
          <span>{id}</span>
          {i < nodos.length - 1 && <span className="text-suave">→</span>}
        </span>
      ))}
    </span>
  );
}

export default function PanelRuta({ ruta, previa }: { ruta: Ruta | null; previa: RutaPrevia | null }) {
  if (!ruta) {
    return (
      <Panel titulo="Ruta óptima">
        <span className="text-suave">—</span>
      </Panel>
    );
  }

  if (!ruta.existe) {
    return (
      <Panel titulo="Ruta óptima">
        <div className="animate-aparecer rounded-xl border border-[#d1352b] bg-[#fdecea] px-4 py-3 font-semibold text-[#9b241b]">
          Sin camino disponible
        </div>
      </Panel>
    );
  }

  const total = ruta.latencia_total ?? 0;
  const cambio = previa && previa.ruta.nodos.join(">") !== ruta.nodos.join(">") ? previa : null;
  const diferencia = cambio ? total - (cambio.ruta.latencia_total ?? 0) : 0;

  return (
    <Panel titulo="Ruta óptima">
      {/* clave por ruta: la animación se repite al cambiar de camino */}
      <div key={ruta.nodos.join(">")} className="flex flex-wrap items-center gap-2">
        {ruta.nodos.map((id, i) => (
          <span
            key={`${id}-${i}`}
            className="inline-flex animate-aparecer items-center gap-2"
            style={{ animationDelay: `${i * 90}ms` }}
          >
            <span className="rounded-lg bg-[#2b2f36] px-3 py-1.5 text-sm font-semibold text-white">{id}</span>
            {i < ruta.nodos.length - 1 && <span className="text-suave">→</span>}
          </span>
        ))}
      </div>

      <div className="flex flex-wrap items-end gap-x-8 gap-y-3">
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-suave">Latencia total</span>
          <span className="text-[34px] font-bold leading-none">
            {total} <span className="text-base font-medium text-suave">ms</span>
          </span>
        </div>

        <div className="flex min-w-0 flex-1 basis-[320px] flex-col gap-1.5" title={ruta.verificacion ?? undefined}>
          <span className="text-xs text-suave">Verificación</span>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1.5 text-sm">
            {ruta.aristas.map((a, i) => (
              <span key={`${a.id}-${i}`} className="inline-flex items-center gap-2">
                {i > 0 && <span className="text-suave">+</span>}
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-borde bg-fondo px-2.5 py-1">
                  {ruta.nodos[i]}–{ruta.nodos[i + 1]}
                  <strong className="font-semibold">{a.latencia_ms}</strong>
                </span>
              </span>
            ))}
            <span className="text-suave">=</span>
            <strong className="text-base font-semibold">{total} ms</strong>
          </div>
        </div>
      </div>

      {cambio && (
        <div className="flex animate-aparecer flex-wrap items-center gap-x-4 gap-y-1 rounded-xl bg-fondo px-4 py-2.5 text-sm">
          <span className="text-suave">Anterior</span>
          <Cadena nodos={cambio.ruta.nodos} />
          <span>{cambio.ruta.latencia_total} ms</span>
          <strong className={diferencia > 0 ? "text-[#d1352b]" : diferencia < 0 ? "text-[#1e8449]" : ""}>
            {diferencia >= 0 ? "+" : "−"}
            {Math.abs(diferencia)} ms
          </strong>
          <span className="text-suave">{guion(cambio.causa)} bloqueado</span>
        </div>
      )}

      {ruta.empates.map((empate) => (
        <div key={empate.join(">")} className="rounded-xl bg-fondo px-4 py-2.5 text-[13px]">
          Empate a {total} ms · se descartó <span className="font-semibold">{empate.join(" → ")}</span> (
          {empate.length - 1} saltos)
        </div>
      ))}
    </Panel>
  );
}
