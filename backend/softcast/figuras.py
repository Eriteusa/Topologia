# Figuras y tabla de rutas para el documento (CONTEXTO §5.6).
# Uso: uv run python -m softcast.figuras
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path as RutaMpl

from softcast.datos_base import CLASE_UMBRAL_BASE
from softcast.grafo import aplicar_bloqueos, construir_grafo, ruta_optima
from softcast.tablas import SALIDAS, escribir_csv, tabla_md

COLOR_TIPO = {"Servidor": "#14365e", "PC": "#3f7cb5", "IoT": "#2f8a5f"}
CURVAS = {"S2-IoT5": (520, 560)}  # aristas curvas, como en la Figura 1 del documento

# Tabla 9: origen PC3, destino IoT4, sin bloqueo inicial; cada paso bloquea una arista de la ruta vigente
ORIGEN, DESTINO = "PC3", "IoT4"
ARISTAS_TABLA_9 = [None, "S2-S1", "PC3-S2", "IoT5-IoT4", "PC3-PC2", "PC3-PC4"]


def corrida_tabla_9():
    """Filas de la Tabla 9: iteración, aristas bloqueadas acumuladas, ruta, latencia, verificación y empate descartado."""
    G = construir_grafo()
    bloqueos, filas = [], []
    for i, arista in enumerate(ARISTAS_TABLA_9, start=1):
        if arista:
            bloqueos.append({"tipo": "arista", "elemento": arista})
        ruta = ruta_optima(aplicar_bloqueos(G, bloqueos), ORIGEN, DESTINO)
        acumuladas = ", ".join(b["elemento"].replace("-", "–") for b in bloqueos) or "Ninguna"
        if ruta["existe"]:
            empates = "; ".join(" → ".join(e) for e in ruta["empates"]) or "—"
            filas.append([i, acumuladas, " → ".join(ruta["nodos"]), ruta["latencia_total"], ruta["verificacion"], empates])
        else:
            filas.append([i, acumuladas, "Sin camino disponible", "—", "—", "—"])
    return filas


def escribir_tabla_rutas(destino=SALIDAS):
    cabecera = ["Iteración", "Aristas bloqueadas", "Ruta óptima (Dijkstra)", "Latencia (ms)", "Verificación de latencia", "Empate descartado"]
    filas = corrida_tabla_9()
    escribir_csv(destino / "tabla_rutas.csv", cabecera, filas)
    (destino / "tabla_rutas.md").write_text(
        f"# Bloqueo y recálculo de rutas ({ORIGEN} a {DESTINO})\n\n" + tabla_md(cabecera, filas),
        encoding="utf-8",
    )


def _arista_geometria(origen, destino, id_arista, pos):
    (x1, y1), (x2, y2) = pos[origen], pos[destino]
    if id_arista in CURVAS:
        cx, cy = CURVAS[id_arista]
        trazo = RutaMpl([(x1, y1), (cx, cy), (x2, y2)], [RutaMpl.MOVETO, RutaMpl.CURVE3, RutaMpl.CURVE3])
        return trazo, (0.25 * x1 + 0.5 * cx + 0.25 * x2, 0.25 * y1 + 0.5 * cy + 0.25 * y2)
    return RutaMpl([(x1, y1), (x2, y2)], [RutaMpl.MOVETO, RutaMpl.LINETO]), ((x1 + x2) / 2, (y1 + y2) / 2)


def dibujar_grafo(destino=SALIDAS):
    """Topología de la Figura 1: 15 nodos, 26 aristas, latencias y los nodos de clase Anómalo del escenario base."""
    G = construir_grafo()
    pos = {n: (d["x"], d["y"]) for n, d in G.nodes(data=True)}
    fig, ax = plt.subplots(figsize=(13, 8.6), facecolor="white")

    for a, b, d in G.edges(data=True):
        trazo, (mx, my) = _arista_geometria(*d["id"].split("-"), d["id"], pos)
        ax.add_patch(PathPatch(trazo, fill=False, edgecolor="#7d8999", linewidth=2.2, linestyle="--" if d["rol"] == "Redundante" else "-", zorder=1))
        ax.text(mx, my, str(d["latencia_ms"]), ha="center", va="center", fontsize=10, family="monospace", zorder=2,
                bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none"})

    for n, d in G.nodes(data=True):
        x, y = pos[n]
        radio = 23 if d["tipo"] == "Servidor" else 17
        anomalo = CLASE_UMBRAL_BASE[n] == "Anómalo"
        ax.add_patch(Circle((x, y), radio, facecolor=COLOR_TIPO[d["tipo"]], edgecolor="#d64545" if anomalo else "none", linewidth=3.5, zorder=3))
        ax.text(x, y, n, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold", zorder=4)

    ax.set_xlim(150, 800)
    ax.set_ylim(645, 215)  # y hacia abajo, como en la interfaz
    ax.set_aspect("equal")
    ax.axis("off")
    leyenda = [
        Line2D([], [], marker="o", color="none", markerfacecolor=COLOR_TIPO["Servidor"], markersize=11, label="Servidor"),
        Line2D([], [], marker="o", color="none", markerfacecolor=COLOR_TIPO["PC"], markersize=11, label="PC"),
        Line2D([], [], marker="o", color="none", markerfacecolor=COLOR_TIPO["IoT"], markersize=11, label="Dispositivo IoT"),
        Line2D([], [], marker="o", color="none", markerfacecolor="white", markeredgecolor="#d64545", markeredgewidth=2.5, markersize=11, label="Clase Anómalo"),
        Line2D([], [], color="#7d8999", linewidth=2.2, linestyle="--", label="Enlace redundante"),
        Line2D([], [], color="#7d8999", linewidth=2.2, label="Enlace principal o troncal"),
    ]
    ax.legend(handles=leyenda, loc="lower center", ncol=6, frameon=False, fontsize=10, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout()
    fig.savefig(destino / "grafo_red.png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main(destino=SALIDAS):
    destino.mkdir(parents=True, exist_ok=True)
    escribir_tabla_rutas(destino)
    dibujar_grafo(destino)
    print(f"Escrito en {destino}: grafo_red.png, tabla_rutas.csv, tabla_rutas.md")


if __name__ == "__main__":
    main()
