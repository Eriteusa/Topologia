import Panel from "@/components/Panel";
import Semaforo, { type LuzSemaforo } from "@/components/Semaforo";
import { coma, conSigno } from "@/lib/formato";
import type { NivelAlerta, Red } from "@/lib/tipos";

const COLUMNAS = "grid grid-cols-[50px_minmax(0,1fr)_40px_150px] items-center gap-x-2";

/** Colores de semáforo por nivel de alerta (barra y texto con contraste suficiente). */
export const COLOR_NIVEL: Record<NivelAlerta, { barra: string; texto: string }> = {
  Normal: { barra: "#1e8449", texto: "#176b3a" },
  "Alerta temprana": { barra: "#f5b301", texto: "#8a6100" },
  Anómalo: { barra: "#d1352b", texto: "#b02a21" },
  Bloqueado: { barra: "#9aa1ab", texto: "#5f6773" },
};

export default function PanelClasificacion({ red }: { red: Red }) {
  const conteo = (nivel: NivelAlerta) => red.nodos.filter((n) => n.nivel_alerta === nivel).length;
  const luz: LuzSemaforo = conteo("Anómalo") > 0 ? "rojo" : conteo("Alerta temprana") > 0 ? "ambar" : "verde";
  return (
    <Panel
      titulo="Clasificación y alertas"
      derecha={
        <span className="flex items-center gap-3">
          <span className="text-xs text-suave">fuente: {red.fuente === "gnn" ? "GNN" : "umbral"}</span>
          <Semaforo activa={luz} />
        </span>
      }
    >
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[13px]" aria-label="Nodos por nivel">
        {(["Normal", "Alerta temprana", "Anómalo"] as const).map((nivel) => (
          <span key={nivel} className="inline-flex items-center gap-1.5">
            <span className="size-2.5 rounded-full" style={{ background: COLOR_NIVEL[nivel].barra }} />
            <strong className="font-semibold">{conteo(nivel)}</strong>
            <span className="text-suave">{nivel === "Normal" ? "normales" : nivel === "Anómalo" ? "anómalos" : "en alerta"}</span>
          </span>
        ))}
      </div>
      <div className={`${COLUMNAS} border-b border-borde pb-1.5 text-xs text-suave`}>
        <span>Nodo</span>
        <span>p anómalo</span>
        <span className="text-right">p</span>
        <span>Nivel</span>
      </div>
      {red.nodos.map((n) => {
        const color = COLOR_NIVEL[n.nivel_alerta];
        const cambio = n.delta_p !== null && !n.bloqueado;
        return (
          <div
            key={n.id}
            className={`${COLUMNAS} rounded-lg px-1.5 py-[3px] text-[13px] transition-colors duration-500 ${cambio ? "bg-fondo" : ""}`}
          >
            <span className="font-semibold">{n.id}</span>
            <span className="block h-2 overflow-hidden rounded-full bg-[#e8ebef]">
              {n.p_anomalo !== null && (
                <span
                  className="block h-2 rounded-full transition-[width,background-color] duration-500 ease-out"
                  style={{ width: `${Math.round(n.p_anomalo * 100)}%`, background: color.barra }}
                />
              )}
            </span>
            <span className="text-right">{n.p_anomalo === null ? "—" : coma(n.p_anomalo)}</span>
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold" style={{ color: color.texto }}>
              <span className="size-2 shrink-0 rounded-full" style={{ background: color.barra }} />
              {n.nivel_alerta}
              {cambio && n.delta_p !== null && (
                <span className="font-medium text-suave">{conSigno(n.delta_p)}</span>
              )}
            </span>
          </div>
        );
      })}
    </Panel>
  );
}
