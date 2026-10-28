import pytest
import torch

from softcast.datos_base import ARISTAS, NODOS, RANGOS_LATENCIA
from softcast.generador import categoria, generar_dataset, generar_grafos, particionar
from softcast.gnn import GCNSoftCast, MLPBase, a_data, calibrar, cargar_gcn, contar_parametros, predecir
from softcast.grafo import aplicar_bloqueos, construir_grafo

ARISTAS_BASE = [{"origen": o, "destino": d, "latencia_ms": lat} for o, d, lat, _ in ARISTAS]


def test_la_gcn_tiene_266_parametros():
    assert contar_parametros(GCNSoftCast()) == 266


def test_el_mlp_tiene_los_mismos_266_parametros():
    assert contar_parametros(MLPBase()) == 266


def test_a_data_del_grafo_completo():
    data = a_data(NODOS, ARISTAS_BASE)
    assert tuple(data.x.shape) == (15, 6)
    assert tuple(data.edge_index.shape) == (2, 52)
    assert data.edge_weight.shape == (52,)


def test_features_de_s2():
    data = a_data(NODOS, ARISTAS_BASE)
    i = [n["id"] for n in NODOS].index("S2")
    latencias_s2 = [a["latencia_ms"] for a in ARISTAS_BASE if "S2" in (a["origen"], a["destino"])]
    esperado = [1.0, 0.0, 0.0, 0.71, 0.68, sum(latencias_s2) / len(latencias_s2) / 22]
    assert data.x[i].tolist() == pytest.approx(esperado, abs=1e-6)


def test_peso_de_arista_es_uno_sobre_latencia_en_ambos_sentidos():
    data = a_data(NODOS, ARISTAS_BASE)
    assert sorted(data.edge_weight.tolist())[0] == pytest.approx(1 / 21, abs=1e-6)  # S2–IoT5, la más lenta
    assert data.edge_weight.tolist().count(pytest.approx(1 / 2, abs=1e-6)) == 2  # S1–S2 (2 ms), ida y vuelta


def test_con_un_nodo_bloqueado_x_es_14_y_se_eliminan_sus_aristas():
    G = aplicar_bloqueos(construir_grafo(), [{"tipo": "nodo", "elemento": "PC4"}])
    nodos = [{"id": n, **G.nodes[n]} for n in G.nodes]
    aristas = [{"origen": a, "destino": b, "latencia_ms": d["latencia_ms"]} for a, b, d in G.edges(data=True)]
    data = a_data(nodos, aristas)
    assert tuple(data.x.shape) == (14, 6)
    assert data.edge_index.shape[1] == 52 - 2 * 3  # PC4 tenía 3 aristas
    assert data.edge_index.max() == 13


def test_a_data_ignora_las_aristas_de_nodos_que_no_se_le_pasan():
    sin_pc4 = [n for n in NODOS if n["id"] != "PC4"]
    data = a_data(sin_pc4, ARISTAS_BASE)  # se le pasan todas las aristas
    assert tuple(data.x.shape) == (14, 6)
    assert data.edge_index.shape[1] == 46


def test_latencia_media_es_1_si_no_hay_aristas_activas():
    # IoT2 queda aislado al retirar S1 y IoT1
    nodos = [n for n in NODOS if n["id"] not in ("S1", "IoT1")]
    data = a_data(nodos, ARISTAS_BASE)
    i = [n["id"] for n in nodos].index("IoT2")
    assert data.x[i, 5].item() == 1.0


def test_predecir_devuelve_p_anomalo_por_nodo_activo():
    nodos = [n for n in NODOS if n["id"] != "S1"]
    p = predecir(GCNSoftCast(), nodos, ARISTAS_BASE)
    assert set(p) == {n["id"] for n in nodos}
    assert all(0.0 <= v <= 1.0 for v in p.values())
    assert predecir(GCNSoftCast(), [], []) == {}


def test_calibrar_deshace_el_sesgo_de_los_pesos_de_clase():
    assert calibrar(0.5, 1.0).item() == pytest.approx(0.5, abs=1e-6)
    assert calibrar(0.5, 3.37).item() == pytest.approx(1 / (1 + 3.37), abs=1e-6)  # odds 1 / 3,37
    assert calibrar(0.0, 3.37).item() == pytest.approx(0.0, abs=1e-5)
    assert calibrar(1.0, 3.37).item() == pytest.approx(1.0, abs=1e-5)
    p = torch.linspace(0.01, 0.99, 50)
    assert (calibrar(p, 3.37) < p).all() and (calibrar(p, 3.37).diff() > 0).all()  # monótona y más baja


def test_predecir_aplica_la_calibracion_del_modelo():
    modelo = GCNSoftCast()
    sin = predecir(modelo, NODOS, ARISTAS_BASE)
    modelo.razon_pesos = 3.37
    con = predecir(modelo, NODOS, ARISTAS_BASE)
    assert all(con[i] < sin[i] for i in sin)


def test_cargar_gcn_recupera_la_razon_de_pesos(tmp_path):
    torch.save({"estado": GCNSoftCast().state_dict(), "escala_peso": 1.0, "razon_pesos": 3.37}, tmp_path / "m.pt")
    modelo, _ = cargar_gcn(tmp_path / "m.pt")
    assert modelo.razon_pesos == 3.37


def test_cargar_gcn_sin_archivo_devuelve_none(tmp_path):
    assert cargar_gcn(tmp_path / "no_existe.pt") is None


def test_guardar_y_cargar_gcn_da_las_mismas_probabilidades(tmp_path):
    modelo = GCNSoftCast()
    torch.save({"estado": modelo.state_dict(), "escala_peso": 1.0}, tmp_path / "m.pt")
    cargado, escala = cargar_gcn(tmp_path / "m.pt")
    assert escala == 1.0
    assert predecir(cargado, NODOS, ARISTAS_BASE) == predecir(modelo, NODOS, ARISTAS_BASE)


# ---------- dataset ----------

def test_las_latencias_base_caen_en_los_rangos_de_la_tabla_8():
    for o, d, lat, _ in ARISTAS:
        minimo, maximo = RANGOS_LATENCIA[categoria(o, d)]
        assert minimo <= lat <= maximo, (o, d)


def test_el_dataset_tiene_1000_grafos_con_atributos_y_latencias_en_rango():
    grafos = generar_grafos(1000, 42)
    assert len(grafos) == 1000
    for nodos, aristas in grafos[:100]:
        assert all(0 <= n["trafico"] <= 100 and 0 <= n["cpu"] <= 100 for n in nodos)
        for a in aristas:
            minimo, maximo = RANGOS_LATENCIA[categoria(a["origen"], a["destino"])]
            assert minimo <= a["latencia_ms"] <= maximo


def test_el_dataset_es_reproducible_con_la_semilla():
    a = generar_grafos(20, 42)
    assert a == generar_grafos(20, 42)
    assert a != generar_grafos(20, 43)


def test_el_dataset_etiquetado_y_la_particion_700_150_150():
    dataset = generar_dataset(1000, 42)
    assert all(tuple(d.x.shape) == (15, 6) and tuple(d.y.shape) == (15,) for d in dataset)
    anomalos = torch.cat([d.y for d in dataset]).float().mean().item()
    assert 0.10 < anomalos < 0.35

    entrenamiento, validacion, prueba = particionar(dataset, 42)
    assert (len(entrenamiento), len(validacion), len(prueba)) == (700, 150, 150)
    ids = [id(d) for d in entrenamiento + validacion + prueba]
    assert len(set(ids)) == 1000  # ningún grafo se repite entre particiones
