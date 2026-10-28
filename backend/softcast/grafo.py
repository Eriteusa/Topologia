# Construcción del grafo, bloqueos y ruta óptima (CONTEXTO §2, §5).
import networkx as nx

from softcast.datos_base import ARISTAS, NODOS, POSICIONES, id_arista


def construir_grafo(latencias=None, atributos=None):
    """
    Grafo completo de CONTEXTO §2, sin bloqueos.
    latencias: {id_arista: ms} para reemplazar las de la Tabla 4 (sesiones aleatorias).
    atributos: {id_nodo: {"trafico": n, "cpu": n}} para reemplazar los del escenario base.
    """
    G = nx.Graph()
    for nodo in NODOS:
        datos = dict(nodo)
        datos.update((atributos or {}).get(nodo["id"], {}))
        x, y = POSICIONES[nodo["id"]]
        G.add_node(nodo["id"], **{k: v for k, v in datos.items() if k != "id"}, x=x, y=y)

    for origen, destino, latencia_ms, rol in ARISTAS:
        arista = id_arista(origen, destino)
        G.add_edge(
            origen,
            destino,
            id=arista,
            latencia_ms=(latencias or {}).get(arista, latencia_ms),
            rol=rol,
        )
    return G


def aplicar_bloqueos(G, bloqueos):
    """
    Devuelve G' sin los elementos bloqueados; G no se modifica.
    bloqueos: lista de {"tipo": "nodo"|"arista", "elemento": id}.
    Bloquear un nodo retira también sus aristas.
    """
    activo = G.copy()
    for bloqueo in bloqueos:
        if bloqueo["tipo"] == "nodo":
            if bloqueo["elemento"] in activo:
                activo.remove_node(bloqueo["elemento"])
        else:
            a, b = bloqueo["elemento"].split("-")
            if activo.has_edge(a, b):
                activo.remove_edge(a, b)
    return activo


def ruta_optima(G, origen, destino):
    """
    Dijkstra sobre latencia_ms con el desempate de §5.4: menos saltos y,
    si persiste, menor orden lexicográfico de la lista de ids.
    G es el grafo activo (ya sin bloqueos). Devuelve el objeto Ruta de §10.
    """
    ruta = {
        "origen": origen,
        "destino": destino,
        "existe": False,
        "nodos": [],
        "aristas": [],
        "latencia_total": None,
        "verificacion": None,
        "empates": [],
    }
    if origen not in G or destino not in G:
        return ruta

    try:
        candidatas = list(nx.all_shortest_paths(G, origen, destino, weight="latencia_ms"))
    except nx.NetworkXNoPath:
        return ruta

    candidatas.sort(key=lambda r: (len(r), r))
    nodos = candidatas[0]
    aristas = [
        {"id": G[a][b]["id"], "latencia_ms": G[a][b]["latencia_ms"]}
        for a, b in zip(nodos, nodos[1:])
    ]
    total = sum(a["latencia_ms"] for a in aristas)
    suma = " + ".join(str(a["latencia_ms"]) for a in aristas)

    ruta.update(
        existe=True,
        nodos=nodos,
        aristas=aristas,
        latencia_total=total,
        verificacion=f"{suma} = {total} ms" if aristas else f"{total} ms",
        empates=candidatas[1:],
    )
    return ruta
