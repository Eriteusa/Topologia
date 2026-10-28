import pytest

from softcast.datos_base import ARISTAS, RANGOS_LATENCIA
from softcast.generador import categoria
from softcast.sesion import Sesion


def nodo(red, id):
    return next(n for n in red["nodos"] if n["id"] == id)


def test_la_sesion_bloquea_2_nodos_al_azar_y_es_reproducible():
    a, b = Sesion(7), Sesion(7)
    assert len(a.bloqueos) == 2
    assert [x["modo"] for x in a.bloqueos] == ["inicial", "inicial"]
    assert [x["tipo"] for x in a.bloqueos] == ["nodo", "nodo"]
    assert a.bloqueos == b.bloqueos
    assert len({tuple(x["elemento"] for x in Sesion(s).bloqueos) for s in range(30)}) > 5


def test_sin_bloqueo_inicial_no_hay_bloqueos():
    assert Sesion(7, bloqueo_inicial=False).bloqueos == []


def test_los_bloqueados_no_se_clasifican_y_tienen_prioridad_en_el_estado():
    s = Sesion(7)
    red = s.red()
    bloqueados = {b["elemento"] for b in s.bloqueos}
    for n in red["nodos"]:
        if n["id"] in bloqueados:
            assert n["estado"] == "Bloqueado" and n["nivel_alerta"] == "Bloqueado"
            assert n["p_anomalo"] is None and n["bloqueado"] is True
        else:
            assert n["estado"] in ("Normal", "Anómalo") and n["p_anomalo"] is not None
    assert len(s.clasificacion) == 13


def test_las_aristas_de_un_nodo_bloqueado_quedan_inactivas_sin_marcarse_bloqueadas():
    s = Sesion(7, bloqueo_inicial=False)
    s.bloquear("nodo", "S1")
    aristas = {a["id"]: a for a in s.red()["aristas"]}
    assert aristas["S1-S2"]["activa"] is False and aristas["S1-S2"]["bloqueada"] is False
    assert aristas["S2-PC1"]["activa"] is True


def test_bloquear_una_arista_la_marca_bloqueada_con_cualquier_orden_de_extremos():
    s = Sesion(7, bloqueo_inicial=False)
    s.bloquear("arista", "S2-S1")
    arista = next(a for a in s.red()["aristas"] if a["id"] == "S1-S2")
    assert arista["bloqueada"] is True and arista["activa"] is False
    assert s.bloqueos[-1] == {"orden": 1, "tipo": "arista", "elemento": "S1-S2", "modo": "manual"}


@pytest.mark.parametrize("tipo, elemento", [("nodo", "X9"), ("arista", "S1-PC3"), ("arista", "S1"), ("otro", "S1")])
def test_bloqueos_invalidos_lanzan_error(tipo, elemento):
    with pytest.raises(ValueError):
        Sesion(7, bloqueo_inicial=False).bloquear(tipo, elemento)


def test_no_se_puede_bloquear_dos_veces():
    s = Sesion(7, bloqueo_inicial=False)
    s.bloquear("nodo", "S1")
    with pytest.raises(ValueError):
        s.bloquear("nodo", "S1")


def test_bloquear_un_nodo_cambia_a_sus_vecinos():
    s = Sesion(7, bloqueo_inicial=False)
    s.bloquear("nodo", "S1")
    assert s.cambios
    assert "S1" not in s.cambios
    assert any(n["delta_p"] is not None for n in s.red()["nodos"])


def test_origen_o_destino_bloqueados_no_dan_ruta():
    s = Sesion(7, bloqueo_inicial=False)
    s.bloquear("nodo", "PC3")
    with pytest.raises(ValueError):
        s.ruta("PC3", "IoT4")
    with pytest.raises(ValueError):
        s.ruta("IoT4", "PC3")


def test_bloquear_el_origen_a_mano_deja_la_ruta_sin_camino_y_la_limpia():
    s = Sesion(7, bloqueo_inicial=False)
    assert s.ruta("PC3", "IoT4")["existe"]
    s.bloquear("nodo", "PC3")
    assert s.ruta_actual()["existe"] is False
    assert s.ruta_actual() is None


def test_bloqueo_aleatorio_elige_un_elemento_de_la_ruta_sin_tocar_origen_ni_destino():
    for semilla in range(40):
        s = Sesion(semilla, bloqueo_inicial=False)
        ruta = s.ruta("PC3", "IoT4")
        bloqueo = s.bloqueo_aleatorio("PC3", "IoT4")
        assert bloqueo["modo"] == "aleatorio"
        if bloqueo["tipo"] == "nodo":
            assert bloqueo["elemento"] in ruta["nodos"][1:-1]
        else:
            assert bloqueo["elemento"] in [a["id"] for a in ruta["aristas"]]


def test_bloqueo_aleatorio_es_reproducible_con_la_semilla():
    def corrida(semilla):
        s = Sesion(semilla, bloqueo_inicial=False)
        s.ruta("PC3", "IoT4")
        return [s.bloqueo_aleatorio("PC3", "IoT4")["elemento"] for _ in range(3)]

    assert corrida(5) == corrida(5)


def test_bloqueo_aleatorio_sin_camino_lanza_error():
    s = Sesion(7, bloqueo_inicial=False)
    for e in ["S2-S1", "PC3-S2", "IoT5-IoT4", "PC3-PC2", "PC3-PC4"]:
        s.bloquear("arista", e)
    with pytest.raises(ValueError):
        s.bloqueo_aleatorio("PC3", "IoT4")


def test_simular_falla_en_pc1_lo_vuelve_anomalo():
    s = Sesion(7, bloqueo_inicial=False)
    assert "PC1" in s.simular_falla("PC1", 35, 95)
    n = nodo(s.red(), "PC1")
    assert n["estado"] == "Anómalo" and n["cpu"] == 95 and n["nivel_alerta"] == "Anómalo"


def test_no_se_simula_falla_en_un_nodo_bloqueado():
    s = Sesion(7, bloqueo_inicial=False)
    s.bloquear("nodo", "PC1")
    with pytest.raises(ValueError):
        s.simular_falla("PC1", 35, 95)


def test_reiniciar_conserva_semilla_y_bloqueos_iniciales():
    s = Sesion(11)
    iniciales = list(s.bloqueos)
    libre = next(n for n in s.G.nodes if n not in {b["elemento"] for b in s.bloqueos})
    s.bloquear("nodo", libre)
    nueva = s.reiniciada()
    assert nueva.semilla == 11 and nueva.bloqueos == iniciales


def test_respaldo_por_umbral_si_no_hay_modelo():
    s = Sesion(7, bloqueo_inicial=False, usar_gnn=False)
    red = s.red()
    assert red["fuente"] == "umbral"
    assert {n["id"] for n in red["nodos"] if n["estado"] == "Anómalo"} == {"PC2", "IoT2", "IoT7"}


def test_latencias_aleatorias_caen_en_su_rango_y_repiten_con_la_semilla():
    a, b = Sesion(3, latencias="aleatorias"), Sesion(3, latencias="aleatorias")
    lat = lambda s: {x["id"]: x["latencia_ms"] for x in s.red()["aristas"]}
    assert lat(a) == lat(b)
    assert lat(a) != {f"{o}-{d}": l for o, d, l, _ in ARISTAS}
    for arista in a.red()["aristas"]:
        origen, destino = arista["id"].split("-")
        minimo, maximo = RANGOS_LATENCIA[categoria(origen, destino)]
        assert minimo <= arista["latencia_ms"] <= maximo


def test_atributos_aleatorios_son_reproducibles_y_distintos_del_escenario_base():
    atributos = lambda s: [(n["trafico"], n["cpu"]) for n in s.red()["nodos"]]
    base = Sesion(3)
    assert atributos(Sesion(3, atributos="aleatorios")) == atributos(Sesion(3, atributos="aleatorios"))
    assert atributos(Sesion(3, atributos="aleatorios")) != atributos(base)


def test_cada_nodo_trae_su_secuencia_y_su_validez():
    red = Sesion(7).red()
    assert all(n["secuencia"] and isinstance(n["secuencia_valida"], bool) for n in red["nodos"])
