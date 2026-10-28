import itertools

import networkx as nx
import pytest

from softcast.datos_base import ARISTAS, NODOS, id_arista
from softcast.grafo import aplicar_bloqueos, construir_grafo, ruta_optima

PARES_DESCONECTANTES = {
    frozenset(p)
    for p in [
        ("S1", "S2"), ("S1", "PC1"), ("S1", "PC6"), ("S1", "IoT1"),
        ("S1", "IoT4"), ("S1", "IoT5"), ("S1", "IoT6"),
    ]
}

# Tabla 9 (CONTEXTO §5.6): arista bloqueada en cada iteración (acumulativa),
# ruta esperada y latencia.
TABLA_9 = [
    (None, ["PC3", "S2", "S1", "IoT4"], 26),
    ("S2-S1", ["PC3", "S2", "IoT5", "IoT4"], 30),
    ("PC3-S2", ["PC3", "PC4", "S2", "IoT5", "IoT4"], 34),
    ("IoT5-IoT4", ["PC3", "PC2", "PC1", "IoT1", "S1", "IoT4"], 54),
    ("PC3-PC2", ["PC3", "PC4", "PC5", "PC6", "IoT6", "S1", "IoT4"], 54),
    ("PC3-PC4", None, None),
]


@pytest.fixture
def G():
    return construir_grafo()


def test_tamano_y_grado_medio(G):
    assert G.number_of_nodes() == 15
    assert G.number_of_edges() == 26
    grado_medio = 2 * G.number_of_edges() / G.number_of_nodes()
    assert grado_medio == pytest.approx(3.47, abs=0.01)


def test_conectividad_sin_puentes_ni_articulacion(G):
    assert nx.node_connectivity(G) == 2
    assert nx.edge_connectivity(G) == 2
    assert list(nx.bridges(G)) == []
    assert list(nx.articulation_points(G)) == []


def test_siete_pares_desconectantes(G):
    desconectan = {
        frozenset(par)
        for par in itertools.combinations(G.nodes, 2)
        if not nx.is_connected(aplicar_bloqueos(G, [{"tipo": "nodo", "elemento": n} for n in par]))
    }
    assert desconectan == PARES_DESCONECTANTES


def test_tabla_9_completa(G):
    bloqueos = []
    for arista, esperada, latencia in TABLA_9:
        if arista:
            bloqueos.append({"tipo": "arista", "elemento": arista})
        ruta = ruta_optima(aplicar_bloqueos(G, bloqueos), "PC3", "IoT4")

        if esperada is None:
            assert ruta["existe"] is False
            assert ruta["latencia_total"] is None
        else:
            assert ruta["existe"] is True
            assert ruta["nodos"] == esperada
            assert ruta["latencia_total"] == latencia


def test_iteracion_4_empate_a_54_con_ruta_de_6_saltos(G):
    bloqueos = [{"tipo": "arista", "elemento": e} for e in ["S2-S1", "PC3-S2", "IoT5-IoT4"]]
    ruta = ruta_optima(aplicar_bloqueos(G, bloqueos), "PC3", "IoT4")

    assert len(ruta["nodos"]) - 1 == 5
    assert ["PC3", "PC4", "PC5", "PC6", "IoT6", "S1", "IoT4"] in ruta["empates"]


def test_desglose_suma_total_y_coincide_con_tabla_4(G):
    latencia_tabla = {id_arista(o, d): lat for o, d, lat, _ in ARISTAS}
    bloqueos = []
    for arista, _, _ in TABLA_9:
        if arista:
            bloqueos.append({"tipo": "arista", "elemento": arista})
        ruta = ruta_optima(aplicar_bloqueos(G, bloqueos), "PC3", "IoT4")
        if not ruta["existe"]:
            continue
        assert sum(a["latencia_ms"] for a in ruta["aristas"]) == ruta["latencia_total"]
        assert all(a["latencia_ms"] == latencia_tabla[a["id"]] for a in ruta["aristas"])
        assert ruta["verificacion"] == (
            " + ".join(str(a["latencia_ms"]) for a in ruta["aristas"]) + f" = {ruta['latencia_total']} ms"
        )


def test_verificacion_del_ejemplo_base(G):
    ruta = ruta_optima(G, "PC3", "IoT4")
    assert ruta["verificacion"] == "4 + 2 + 20 = 26 ms"


def test_bloquear_nodo_retira_sus_aristas(G):
    activo = aplicar_bloqueos(G, [{"tipo": "nodo", "elemento": "S1"}])
    assert "S1" not in activo
    assert activo.number_of_nodes() == 14
    assert activo.number_of_edges() == 26 - 8
    assert G.number_of_nodes() == 15  # el grafo original no cambia


def test_bloquear_arista_no_depende_del_orden_de_extremos(G):
    activo = aplicar_bloqueos(G, [{"tipo": "arista", "elemento": "S1-S2"}])
    assert not activo.has_edge("S2", "S1")
    assert activo.number_of_edges() == 25


def test_sin_camino_no_lanza_error(G):
    activo = aplicar_bloqueos(G, [{"tipo": "nodo", "elemento": "S1"}, {"tipo": "nodo", "elemento": "S2"}])
    ruta = ruta_optima(activo, "PC3", "IoT4")
    assert ruta["existe"] is False


def test_origen_bloqueado_deja_la_ruta_sin_camino(G):
    activo = aplicar_bloqueos(G, [{"tipo": "nodo", "elemento": "PC3"}])
    assert ruta_optima(activo, "PC3", "IoT4")["existe"] is False


def test_nodos_traen_atributos_de_la_tabla_3(G):
    assert G.number_of_nodes() == len(NODOS)
    assert G.nodes["IoT2"]["cpu"] == 98
    assert G.nodes["S2"]["subtipo"] == "Web/Core"
