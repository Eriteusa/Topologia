import Panel from "@/components/Panel";
import type { Bloqueo } from "@/lib/tipos";

const COLUMNAS = "grid grid-cols-[40px_70px_minmax(0,1fr)_84px] items-center gap-x-2";

const ESTILO_MODO: Record<Bloqueo["modo"], string> = {
  inicial: "bg-[#e6eaef] text-[#2d3745]",
  aleatorio: "bg-[#fde8d8] text-[#7a3200]",
  manual: "bg-[#dbe8f7] text-primario",
};

export default function PanelHistorial({ bloqueos }: { bloqueos: Bloqueo[] }) {
  return (
    <Panel titulo="Historial de bloqueos">
      <div className={`${COLUMNAS} border-b border-borde pb-1.5 text-xs text-suave`}>
        <span>Orden</span>
        <span>Tipo</span>
        <span>Elemento</span>
        <span>Modo</span>
      </div>
      {bloqueos.length === 0 && <span className="text-suave">—</span>}
      {bloqueos.map((b) => (
        <div key={b.orden} className={`${COLUMNAS} py-0.5 text-sm`}>
          <span className="font-mono">{b.orden}</span>
          <span>{b.tipo}</span>
          <span className="font-mono font-semibold">{b.elemento}</span>
          <span className={`rounded px-2 py-[3px] text-center text-xs font-semibold ${ESTILO_MODO[b.modo]}`}>
            {b.modo}
          </span>
        </div>
      ))}
    </Panel>
  );
}
