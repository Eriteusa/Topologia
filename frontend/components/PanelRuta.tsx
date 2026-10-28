import Panel from "@/components/Panel";
import type { Ruta } from "@/lib/tipos";

export default function PanelRuta({ ruta }: { ruta: Ruta | null }) {
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
        <div className="rounded-md border border-peligro bg-[#fdecea] px-3 py-2.5 font-semibold text-[#8c2520]">
          Sin camino disponible
        </div>
      </Panel>
    );
  }

  return (
    <Panel titulo="Ruta óptima">
      <div className="flex flex-wrap items-center gap-2">
        {ruta.nodos.map((id, i) => (
          <span key={`${id}-${i}`} className="inline-flex items-center gap-2">
            <span className="rounded-md border border-naranja bg-[#fdeadc] px-3 py-1.5 font-mono text-sm font-semibold text-[#5b2605]">
              {id}
            </span>
            {i < ruta.nodos.length - 1 && <span className="text-suave">→</span>}
          </span>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-x-7 gap-y-3">
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-suave">Latencia total</span>
          <span className="text-[32px] font-bold leading-none text-primario">
            {ruta.latencia_total} <span className="text-base font-medium">ms</span>
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs text-suave">Verificación</span>
          <span className="font-mono text-[15px]">{ruta.verificacion}</span>
        </div>
      </div>

      {ruta.empates.map((empate) => (
        <div key={empate.join(">")} className="rounded-md bg-fondo px-3 py-2 text-[13px]">
          Empate a {ruta.latencia_total} ms · se descartó{" "}
          <span className="font-mono">{empate.join(" → ")}</span> ({empate.length - 1} saltos)
        </div>
      ))}
    </Panel>
  );
}
