# Dataset sintético para la GNN (CONTEXTO §7.2).
import numpy as np
from scipy.stats import truncnorm

from softcast.datos_base import ARISTAS, NODOS, RANGOS_LATENCIA
from softcast.gnn import a_data
from softcast.umbral import clases_extendidas

MEDIA_POR_TIPO = {"Servidor": 62, "PC": 52, "IoT": 42}
DESVIACION = 25
TIPO_POR_NODO = {n["id"]: n["tipo"] for n in NODOS}


def categoria(origen, destino):
    return tuple(sorted((TIPO_POR_NODO[origen], TIPO_POR_NODO[destino])))


def _normal_truncada(media, tamano, rng):
    a, b = (0 - media) / DESVIACION, (100 - media) / DESVIACION
    muestras = truncnorm.rvs(a, b, loc=media, scale=DESVIACION, size=tamano, random_state=rng)
    return np.rint(muestras).astype(int)


def generar_grafos(n_grafos=1000, semilla=42):
    """
    Lista de (nodos, aristas) con la topología fija: tráfico y cpu de cada nodo
    como normal truncada en [0, 100] redondeada, y latencias enteras uniformes
    dentro del rango de su categoría (Tabla 8).
    """
    rng = np.random.default_rng(semilla)
    trafico = {n["id"]: _normal_truncada(MEDIA_POR_TIPO[n["tipo"]], n_grafos, rng) for n in NODOS}
    cpu = {n["id"]: _normal_truncada(MEDIA_POR_TIPO[n["tipo"]], n_grafos, rng) for n in NODOS}
    latencia = {}
    for origen, destino, _, _ in ARISTAS:
        minimo, maximo = RANGOS_LATENCIA[categoria(origen, destino)]
        latencia[(origen, destino)] = rng.integers(minimo, maximo + 1, size=n_grafos)

    grafos = []
    for g in range(n_grafos):
        nodos = [
            {"id": n["id"], "tipo": n["tipo"], "trafico": int(trafico[n["id"]][g]), "cpu": int(cpu[n["id"]][g])}
            for n in NODOS
        ]
        aristas = [
            {"origen": o, "destino": d, "latencia_ms": int(latencia[(o, d)][g])}
            for o, d, _, _ in ARISTAS
        ]
        grafos.append((nodos, aristas))
    return grafos


def generar_dataset(n_grafos=1000, semilla=42, escala_peso=1.0):
    """Lista de Data de PyG, uno por grafo, etiquetados con la clase extendida (§3.1)."""
    dataset = []
    for nodos, aristas in generar_grafos(n_grafos, semilla):
        clases = clases_extendidas(nodos, aristas)
        dataset.append(a_data(nodos, aristas, clases, escala_peso))
    return dataset


def particionar(dataset, semilla=42, n_entrenamiento=700, n_validacion=150):
    """Partición por grafos completos: 700 / 150 / 150."""
    orden = np.random.default_rng(semilla).permutation(len(dataset))
    a, b = n_entrenamiento, n_entrenamiento + n_validacion
    return (
        [dataset[i] for i in orden[:a]],
        [dataset[i] for i in orden[a:b]],
        [dataset[i] for i in orden[b:]],
    )
