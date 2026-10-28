import pytest

from softcast.datos_base import ARISTAS, CLASE_UMBRAL_BASE, NODOS
from softcast.umbral import NOMBRES_CLASE, clase_extendida, clases_extendidas, umbral_propio

ARISTAS_BASE = [{"origen": o, "destino": d, "latencia_ms": lat} for o, d, lat, _ in ARISTAS]


def nodos_base(**cambios):
    """Copia de los nodos del escenario base con atributos cambiados: nodos_base(IoT3={"cpu": 60})."""
    return [{**n, **cambios.get(n["id"], {})} for n in NODOS]


def test_umbral_propio_reproduce_la_tabla_3():
    for n in NODOS:
        clase = "Anómalo" if umbral_propio(n["cpu"], n["trafico"]) else "Normal"
        assert clase == CLASE_UMBRAL_BASE[n["id"]], n["id"]


@pytest.mark.parametrize("cpu, trafico, esperado", [
    (85, 0, True), (84, 69, False), (84, 79, True), (0, 80, True), (70, 70, True), (70, 69, False), (69, 70, False),
])
def test_umbral_propio_en_los_bordes(cpu, trafico, esperado):
    assert umbral_propio(cpu, trafico) is esperado


def test_clase_extendida_reproduce_la_tabla_3_en_el_escenario_base():
    clases = clases_extendidas(nodos_base(), ARISTAS_BASE)
    anomalos = {i for i, c in clases.items() if c == 1}
    assert anomalos == {i for i, c in CLASE_UMBRAL_BASE.items() if c == "Anómalo"}
    assert anomalos == {"PC2", "IoT2", "IoT7"}


def test_carga_media_con_la_mitad_de_vecinos_anomalos_es_anomalo():
    # IoT3 tiene vecinos S1 y IoT4; con IoT4 saturado la fracción es 1/2
    nodos = nodos_base(IoT3={"cpu": 60}, IoT4={"cpu": 90})
    assert clases_extendidas(nodos, ARISTAS_BASE)["IoT3"] == 1


def test_deja_de_serlo_si_se_bloquea_el_vecino_anomalo():
    nodos = nodos_base(IoT3={"cpu": 60}, IoT4={"cpu": 90})
    sin_iot4 = [n for n in nodos if n["id"] != "IoT4"]
    aristas = [a for a in ARISTAS_BASE if "IoT4" not in (a["origen"], a["destino"])]
    assert clases_extendidas(sin_iot4, aristas)["IoT3"] == 0


def test_carga_baja_no_se_contagia():
    nodos = nodos_base(IoT3={"cpu": 50, "trafico": 50}, IoT4={"cpu": 90}, S1={"cpu": 90})
    assert clases_extendidas(nodos, ARISTAS_BASE)["IoT3"] == 0


def test_menos_de_la_mitad_de_vecinos_no_contagia():
    # PC1 (carga media) con 1 de 3 vecinos anómalos (PC2): 1/3 < 0,5
    nodos = nodos_base(PC1={"cpu": 65})
    assert clases_extendidas(nodos, ARISTAS_BASE)["PC1"] == 0


def test_sin_vecinos_activos_se_queda_normal():
    nodo = {"id": "X", "cpu": 65, "trafico": 65}
    assert clase_extendida(nodo, []) == 0


def test_nombres_de_clase():
    assert NOMBRES_CLASE == ["Normal", "Anómalo"]
