import Panel from "@/components/Panel";
import { coma, conSigno } from "@/lib/formato";
import type { NivelAlerta, Red } from "@/lib/tipos";

const COLUMNAS = "grid grid-cols-[50px_minmax(0,1fr)_40px_156px] items-center gap-x-2";

const COLOR_NIVEL: Record<NivelAlerta, { barra: string; texto: string }> = {
  Normal: { barra: "#3f7cb5", texto: "#2f6a3f" },
  "Alerta temprana": { barra: "#c48a00", texto: "#7a5600" },
  Anómalo: { barra: "#c93b3b", texto: "#a12a2a" },
  Bloqueado: { barra: "#8b95a3", texto: "#566171" },
};

export default function PanelClasificacion({ red }: { red: Red }) {
  return (
    <Panel
      titulo="Clasificación y alertas"
      derecha={<span className="font-mono text-xs text-suave">fuente: {red.fuente === "gnn" ? "GNN" : "umbral"}</span>}
    >
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
            className={`${COLUMNAS} rounded px-1 py-[3px] text-[13px] ${cambio ? "bg-ambar" : ""}`}
          >
            <span className="font-mono font-semibold">{n.id}</span>
            <span className="block h-2 overflow-hidden rounded bg-[#e6eaef]">
              {n.p_anomalo !== null && (
                <span
                  className="block h-2"
                  style={{ width: `${Math.round(n.p_anomalo * 100)}%`, background: color.barra }}
                />
              )}
            </span>
            <span className="text-right font-mono">{n.p_anomalo === null ? "—" : coma(n.p_anomalo)}</span>
            <span className="text-xs font-semibold" style={{ color: color.texto }}>
              {n.nivel_alerta}
              {cambio && n.delta_p !== null && (
                <span className="ml-1 font-mono font-medium text-[#7a5600]">{conSigno(n.delta_p)}</span>
              )}
            </span>
          </div>
        );
      })}
    </Panel>
  );
}
