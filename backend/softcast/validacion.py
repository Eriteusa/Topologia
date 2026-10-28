# Evidencia para el documento de validación y resultados.
# Uso: uv run python -m softcast.validacion   (necesita modelos/ de `softcast.entrenar`)
import json

from softcast.automata import validar
from softcast.sesion import Sesion
from softcast.tablas import SALIDAS, coma, escribir_csv, tabla_md, variacion

SEMILLA = 42
RAIZ_MODELOS = SALIDAS.parent / "modelos"

# Cadenas de prueba del autómata (CONTEXTO §6.2, Tabla 17) y el motivo de cada resultado
CADENAS = [
    ("abcde", "Secuencia completa"),
    ("abcccde", "Varias transmisiones"),
    ("ac", "Transmite sin autenticar"),
    ("abde", "Falta al menos una c"),
    ("abcdef", "Evento después de finalizar"),
    ("abcfde", "Timeout en transmisión"),
    ("aabcde", "Solicitud repetida"),
    ("", "No inicia comunicación"),
    ("abz", "Símbolo fuera del alfabeto"),
]

# Simulaciones de falla: nodo, tráfico y CPU nuevos
FALLAS = [("PC1", 35, 95), ("IoT3", 90, 25), ("S2", 90, 95), ("PC4", 20, 25)]


def _sesion():
    sesion = Sesion(SEMILLA, bloqueo_inicial=False)
    if sesion.red()["fuente"] != "gnn":
        raise SystemExit("No hay modelo entrenado: ejecuta primero `uv run python -m softcast.entrenar`.")
    return sesion


def _estados(red):
    return {n["id"]: n for n in red["nodos"]}


def tabla_automata(destino):
    cabecera = ["Cadena", "Recorrido", "Estado final", "Resultado", "Motivo"]
    filas = []
    for cadena, motivo in CADENAS:
        r = validar(cadena)
        filas.append([
            cadena or "(vacía)",
            " → ".join(r["recorrido"]),
            r["estado_final"],
            "Aceptada" if r["aceptada"] else "Rechazada",
            r.get("error", motivo),
        ])
    escribir_csv(destino / "tabla_automata.csv", cabecera, filas)
    (destino / "tabla_automata.md").write_text("# Cadenas de prueba del autómata\n\n" + tabla_md(cabecera, filas), encoding="utf-8")


def tabla_clasificacion(destino):
    red = _sesion().red()
    cabecera = ["Nodo", "Tipo", "Tráfico", "CPU", "Clase por umbral (Tabla 3)", "Clase extendida", "p anómalo (GNN)", "Estado (GNN)", "Nivel de alerta", "Secuencia"]
    filas, coinciden = [], 0
    for n in red["nodos"]:
        coinciden += n["estado"] == n["clase_umbral"]
        filas.append([
            n["id"], n["tipo"], n["trafico"], n["cpu"], n["clase_umbral"], n["clase_extendida"],
            coma(n["p_anomalo"]), n["estado"], n["nivel_alerta"],
            f"{n['secuencia']} ({'aceptada' if n['secuencia_valida'] else 'rechazada'})",
        ])
    texto = (
        "# Clasificación del escenario base (semilla 42, sin bloqueos)\n\n"
        + tabla_md(cabecera, filas)
        + f"\nEl estado de la GNN coincide con la clase por umbral de la Tabla 3 en {coinciden} de {len(red['nodos'])} nodos.\n"
    )
    (destino / "tabla_clasificacion.md").write_text(texto, encoding="utf-8")


def metricas_gnn(destino):
    archivo = RAIZ_MODELOS / "metricas.json"
    if not archivo.exists():
        raise SystemExit("Falta modelos/metricas.json: ejecuta primero `uv run python -m softcast.entrenar`.")
    m = json.loads(archivo.read_text(encoding="utf-8"))

    puntos = [("calibrado", "calibrado, corte 0,50 (prototipo)"), ("corte_0_40", "calibrado, corte 0,40"), ("sin_calibrar", "sin calibrar")]
    cabecera = ["Modelo", "Punto de operación", "Precisión", "Recall", "F1"]
    filas = []
    for modelo in ("gcn", "mlp"):
        for clave, nombre in puntos:
            r = m[modelo] if clave == "calibrado" else m[modelo][clave]
            filas.append([modelo.upper(), nombre, coma(r["precision"], 3), coma(r["recall"], 3), coma(r["f1"], 3)])

    matrices = []
    for modelo in ("gcn", "mlp"):
        (tn, fp), (fn, tp) = m[modelo]["matriz_confusion"]
        matrices.append(f"**{modelo.upper()}** (calibrado, corte 0,50)\n\n" + tabla_md(
            ["Real \\ Predicha", "Normal", "Anómalo"], [["Normal", tn, fp], ["Anómalo", fn, tp]]))

    lecturas = []
    for clave, nombre in puntos:
        f1_gcn = (m["gcn"] if clave == "calibrado" else m["gcn"][clave])["f1"]
        f1_mlp = (m["mlp"] if clave == "calibrado" else m["mlp"][clave])["f1"]
        veredicto = "supera" if f1_gcn > f1_mlp else "no supera"
        lecturas.append(f"- {nombre}: F1 de la GCN {coma(f1_gcn, 3)} frente a {coma(f1_mlp, 3)} del MLP; la GCN {veredicto} al MLP.")

    texto = (
        "# Métricas de la GNN frente al MLP\n\n"
        f"- Dataset: {sum(m['grafos'].values())} grafos con la topología fija, particionados por grafos completos "
        f"({m['grafos']['entrenamiento']} entrenamiento, {m['grafos']['validacion']} validación, {m['grafos']['prueba']} prueba), semilla {m['semilla']}.\n"
        f"- Nodos de clase Anómalo en el dataset: {coma(m['porcentaje_anomalos'])} %.\n"
        f"- Pesos de clase inversos a la frecuencia: razón {coma(m['razon_pesos'])}. "
        "La probabilidad se calibra dividiendo los odds entre esa razón.\n"
        f"- Parámetros entrenables: GCN {m['gcn']['parametros']}, MLP {m['mlp']['parametros']}. "
        f"Épocas: GCN {m['gcn']['epocas']} (mejor {m['gcn']['mejor_epoca']}), MLP {m['mlp']['epocas']} (mejor {m['mlp']['mejor_epoca']}).\n\n"
        "## Métricas sobre los grafos de prueba (clase Anómalo)\n\n" + tabla_md(cabecera, filas)
        + "\n## Matrices de confusión\n\n" + "\n".join(matrices)
        + "\n## Lectura\n\n" + "\n".join(lecturas) + "\n"
    )
    (destino / "metricas_gnn.md").write_text(texto, encoding="utf-8")


def efecto_bloqueo(destino):
    base = _estados(_sesion().red())
    cabecera = ["Nodo bloqueado", "Vecinos directos que cambiaron", "Otros nodos que cambiaron", "Cambios de nivel de alerta", "Cambios de la clase extendida (etiqueta)"]
    filas, con_vecinos, con_etiqueta = [], 0, 0
    for id_bloqueado in base:
        sesion = _sesion()
        vecinos = set(sesion.G.neighbors(id_bloqueado))
        sesion.bloquear("nodo", id_bloqueado)
        despues = _estados(sesion.red())
        directos = [f"{i} ({variacion(d)})" for i, d in sesion.cambios.items() if i in vecinos]
        otros = [f"{i} ({variacion(d)})" for i, d in sesion.cambios.items() if i not in vecinos]
        niveles = [f"{i}: {base[i]['nivel_alerta']} → {despues[i]['nivel_alerta']}"
                   for i in sesion.cambios if base[i]["nivel_alerta"] != despues[i]["nivel_alerta"]]
        etiquetas = [f"{i}: {base[i]['clase_extendida']} → {n['clase_extendida']}"
                     for i, n in despues.items() if not n["bloqueado"] and n["clase_extendida"] != base[i]["clase_extendida"]]
        con_vecinos += bool(directos)
        con_etiqueta += bool(etiquetas)
        filas.append([id_bloqueado, ", ".join(directos) or "—", ", ".join(otros) or "—",
                      "; ".join(niveles) or "—", "; ".join(etiquetas) or "—"])
    texto = (
        "# Efecto de bloquear cada nodo sobre la clasificación (semilla 42, sin otros bloqueos)\n\n"
        "Se considera que un nodo cambió si su p anómalo varía 0,02 o más, o cruza 0,40 o 0,50. "
        "Entre paréntesis, la variación de p anómalo. Las cuatro primeras columnas describen la respuesta de la GCN; "
        "la última, si la etiqueta (clase extendida, §3.1) también cambia al retirar el nodo.\n\n"
        + tabla_md(cabecera, filas)
        + f"\nAl bloquear un nodo cambia la clasificación de al menos un vecino directo en {con_vecinos} de {len(base)} casos. "
        f"La etiqueta cambia en {con_etiqueta} de {len(base)} casos.\n"
    )
    (destino / "efecto_bloqueo.md").write_text(texto, encoding="utf-8")


def efecto_falla(destino):
    cabecera = ["Nodo", "Tráfico", "CPU", "Estado antes → después", "p anómalo antes → después", "Otros nodos que cambiaron"]
    filas = []
    for nodo, trafico, cpu in FALLAS:
        sesion = _sesion()
        antes = _estados(sesion.red())[nodo]
        sesion.simular_falla(nodo, trafico, cpu)
        despues = _estados(sesion.red())[nodo]
        otros = [f"{i} ({variacion(d)})" for i, d in sesion.cambios.items() if i != nodo]
        filas.append([
            nodo, f"{antes['trafico']} → {trafico}", f"{antes['cpu']} → {cpu}",
            f"{antes['estado']} → {despues['estado']}",
            f"{coma(antes['p_anomalo'])} → {coma(despues['p_anomalo'])}",
            ", ".join(otros) or "—",
        ])
    texto = "# Efecto de simular fallas (semilla 42, sin bloqueos)\n\n" + tabla_md(cabecera, filas)
    (destino / "efecto_falla.md").write_text(texto, encoding="utf-8")


def main(destino=SALIDAS):
    destino.mkdir(parents=True, exist_ok=True)
    for escribir in (tabla_automata, tabla_clasificacion, metricas_gnn, efecto_bloqueo, efecto_falla):
        escribir(destino)
    print(f"Escrito en {destino}: tabla_automata, tabla_clasificacion, metricas_gnn, efecto_bloqueo, efecto_falla")


if __name__ == "__main__":
    main()
