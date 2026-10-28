import pytest
from fastapi.testclient import TestClient

from softcast.api import app

TABLA_9 = [
    (None, ["PC3", "S2", "S1", "IoT4"], 26),
    ("S2-S1", ["PC3", "S2", "IoT5", "IoT4"], 30),
    ("PC3-S2", ["PC3", "PC4", "S2", "IoT5", "IoT4"], 34),
    ("IoT5-IoT4", ["PC3", "PC2", "PC1", "IoT1", "S1", "IoT4"], 54),
    ("PC3-PC2", ["PC3", "PC4", "PC5", "PC6", "IoT6", "S1", "IoT4"], 54),
    ("PC3-PC4", None, None),
]


@pytest.fixture
def cliente():
    return TestClient(app)


def crear(cliente, **datos):
    respuesta = cliente.post("/api/sesion", json=datos)
    assert respuesta.status_code == 200
    return respuesta.json()


def bloqueados(red):
    return sorted(n["id"] for n in red["nodos"] if n["bloqueado"])


def test_crear_sesion_bloquea_exactamente_2_nodos_reproducibles(cliente):
    red = crear(cliente, semilla=42)
    assert len(bloqueados(red)) == 2
    assert bloqueados(crear(cliente, semilla=42)) == bloqueados(red)
    assert red["semilla"] == 42 and len(red["nodos"]) == 15 and len(red["aristas"]) == 26
    assert [b["modo"] for b in red["bloqueos"]] == ["inicial", "inicial"]


def test_get_red_devuelve_la_sesion_actual(cliente):
    red = crear(cliente, semilla=9)
    assert cliente.get("/api/red").json() == red


def test_ruta_con_origen_o_destino_bloqueado_da_400(cliente):
    red = crear(cliente, semilla=42)
    bloqueado = bloqueados(red)[0]
    libre = next(n["id"] for n in red["nodos"] if not n["bloqueado"])
    assert cliente.post("/api/ruta", json={"origen": bloqueado, "destino": libre}).status_code == 400
    assert cliente.post("/api/ruta", json={"origen": libre, "destino": bloqueado}).status_code == 400
    assert cliente.post("/api/ruta", json={"origen": "X9", "destino": libre}).status_code == 400


def test_flujo_de_bloqueos_reproduce_la_tabla_9(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    for arista, esperada, latencia in TABLA_9:
        if arista is None:
            ruta = cliente.post("/api/ruta", json={"origen": "PC3", "destino": "IoT4"}).json()
        else:
            respuesta = cliente.post("/api/bloqueos", json={"tipo": "arista", "elemento": arista})
            assert respuesta.status_code == 200
            ruta = respuesta.json()["ruta"]

        if esperada is None:
            assert ruta["existe"] is False
        else:
            assert ruta["nodos"] == esperada and ruta["latencia_total"] == latencia
            assert ruta["verificacion"].endswith(f"= {latencia} ms")


def test_bloquear_devuelve_la_red_actualizada_con_el_historial(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    cuerpo = cliente.post("/api/bloqueos", json={"tipo": "nodo", "elemento": "S1"}).json()
    assert cuerpo["ruta"] is None  # no había ruta activa
    assert bloqueados(cuerpo["red"]) == ["S1"]
    assert cuerpo["red"]["bloqueos"] == [{"orden": 1, "tipo": "nodo", "elemento": "S1", "modo": "manual"}]
    assert cuerpo["red"]["cambiaron"]


def test_bloqueo_invalido_da_400(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    assert cliente.post("/api/bloqueos", json={"tipo": "nodo", "elemento": "X9"}).status_code == 400
    assert cliente.post("/api/bloqueos", json={"tipo": "arista", "elemento": "S1-PC3"}).status_code == 400
    assert cliente.post("/api/bloqueos", json={"tipo": "planeta", "elemento": "S1"}).status_code == 422


def test_bloquear_el_origen_deja_la_ruta_sin_camino_sin_error(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    cliente.post("/api/ruta", json={"origen": "PC3", "destino": "IoT4"})
    respuesta = cliente.post("/api/bloqueos", json={"tipo": "nodo", "elemento": "PC3"})
    assert respuesta.status_code == 200
    assert respuesta.json()["ruta"]["existe"] is False


def test_bloqueo_aleatorio_toma_un_elemento_de_la_ruta_vigente(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    ruta = cliente.post("/api/ruta", json={"origen": "PC3", "destino": "IoT4"}).json()
    cuerpo = cliente.post("/api/bloqueos/aleatorio", json={"origen": "PC3", "destino": "IoT4"}).json()
    assert cuerpo["bloqueo"]["modo"] == "aleatorio"
    assert cuerpo["bloqueo"]["elemento"] in [a["id"] for a in ruta["aristas"]] + ruta["nodos"][1:-1]
    assert cuerpo["ruta"]["existe"] is True and cuerpo["ruta"]["latencia_total"] >= ruta["latencia_total"]


def test_bloqueo_aleatorio_hasta_agotar_los_caminos_da_400(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    cliente.post("/api/ruta", json={"origen": "PC3", "destino": "IoT4"})
    for _ in range(40):
        respuesta = cliente.post("/api/bloqueos/aleatorio", json={"origen": "PC3", "destino": "IoT4"})
        if respuesta.status_code == 400:
            return
        assert respuesta.status_code == 200
    pytest.fail("la red nunca se quedó sin camino")


def test_simular_falla_en_pc1_lo_vuelve_anomalo(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    cuerpo = cliente.post("/api/nodos/PC1/atributos", json={"trafico": 35, "cpu": 95}).json()
    pc1 = next(n for n in cuerpo["red"]["nodos"] if n["id"] == "PC1")
    assert pc1["estado"] == "Anómalo" and pc1["cpu"] == 95
    assert "PC1" in cuerpo["cambiaron"]


def test_simular_falla_valida_el_rango_y_el_nodo(cliente):
    crear(cliente, semilla=42, bloqueo_inicial=False)
    assert cliente.post("/api/nodos/PC1/atributos", json={"trafico": 120, "cpu": 50}).status_code == 422
    assert cliente.post("/api/nodos/X9/atributos", json={"trafico": 50, "cpu": 50}).status_code == 400


def test_latencias_aleatorias_por_api(cliente):
    base = crear(cliente, semilla=3)
    azar = crear(cliente, semilla=3, latencias="aleatorias")
    assert [a["latencia_ms"] for a in azar["aristas"]] != [a["latencia_ms"] for a in base["aristas"]]
    assert crear(cliente, semilla=3, latencias="aleatorias") == azar


def test_reiniciar_vuelve_a_la_misma_semilla_y_bloqueos_iniciales(cliente):
    inicial = crear(cliente, semilla=21)
    libre = next(n["id"] for n in inicial["nodos"] if not n["bloqueado"])
    cliente.post("/api/bloqueos", json={"tipo": "nodo", "elemento": libre})
    reiniciada = cliente.post("/api/reiniciar").json()
    assert reiniciada["semilla"] == 21
    assert reiniciada["bloqueos"] == inicial["bloqueos"]


def test_automata_validar_y_definicion(cliente):
    aceptada = cliente.post("/api/automata/validar", json={"cadena": "abcde"}).json()
    assert aceptada["aceptada"] is True and aceptada["recorrido"][-1] == "q5"
    rechazada = cliente.post("/api/automata/validar", json={"cadena": "ac"}).json()
    assert rechazada["aceptada"] is False and rechazada["estado_final"] == "qNP"
    assert "fuera del alfabeto" in cliente.post("/api/automata/validar", json={"cadena": "abz"}).json()["error"]

    definicion = cliente.get("/api/automata").json()
    assert definicion["q0"] == "q0" and definicion["F"] == ["q5"] and len(definicion["Q"]) == 7


def test_cors_permite_el_origen_del_frontend(cliente):
    respuesta = cliente.options(
        "/api/red",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert respuesta.headers["access-control-allow-origin"] == "http://localhost:3000"
