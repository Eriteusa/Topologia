import xml.etree.ElementTree as ET

import pytest

from softcast.automata import DELTA, F, Q, Q0, SIGMA, definicion, exportar_jff, validar

# (cadena, aceptada, recorrido) — CONTEXTO §6.2 y Tabla 17 del documento
CASOS = [
    ("abcde", True, ["q0", "q1", "q2", "q3", "q4", "q5"]),
    ("abcccde", True, ["q0", "q1", "q2", "q3", "q3", "q3", "q4", "q5"]),
    ("ac", False, ["q0", "q1", "qNP"]),
    ("abde", False, ["q0", "q1", "q2", "qNP", "qNP"]),
    ("abcdef", False, ["q0", "q1", "q2", "q3", "q4", "q5", "qNP"]),
    ("abcfde", False, ["q0", "q1", "q2", "q3", "qNP", "qNP", "qNP"]),
    ("aabcde", False, ["q0", "q1", "qNP", "qNP", "qNP", "qNP", "qNP"]),
    ("", False, ["q0"]),
]


@pytest.mark.parametrize("cadena, aceptada, recorrido", CASOS)
def test_cadenas_de_prueba(cadena, aceptada, recorrido):
    resultado = validar(cadena)
    assert resultado["aceptada"] is aceptada
    assert resultado["recorrido"] == recorrido
    assert resultado["estado_final"] == recorrido[-1]
    assert "error" not in resultado


def test_simbolo_fuera_del_alfabeto():
    resultado = validar("abz")
    assert resultado["aceptada"] is False
    assert "fuera del alfabeto" in resultado["error"]
    assert resultado["recorrido"] == ["q0", "q1", "q2"]


def test_los_cinco_parametros():
    assert Q == ["q0", "q1", "q2", "q3", "q4", "q5", "qNP"]
    assert SIGMA == ["a", "b", "c", "d", "e", "f"]
    assert Q0 == "q0"
    assert F == ["q5"]


def test_delta_tiene_las_42_entradas():
    assert len(DELTA) == 42
    assert set(DELTA) == {(q, s) for q in Q for s in SIGMA}
    assert set(DELTA.values()) <= set(Q)


def test_delta_solo_tiene_las_transiciones_del_lenguaje():
    validas = {k: v for k, v in DELTA.items() if v != "qNP"}
    assert validas == {
        ("q0", "a"): "q1", ("q1", "b"): "q2", ("q2", "c"): "q3",
        ("q3", "c"): "q3", ("q3", "d"): "q4", ("q4", "e"): "q5",
    }


def test_definicion_para_la_interfaz():
    d = definicion()
    assert d["Q"] == Q and d["sigma"] == SIGMA and d["q0"] == "q0" and d["F"] == ["q5"]
    assert d["delta"]["q3"]["d"] == "q4"
    assert sum(len(fila) for fila in d["delta"].values()) == 42


def test_jff_es_xml_valido_con_7_estados(tmp_path):
    ruta = exportar_jff(tmp_path / "automata.jff")
    raiz = ET.parse(ruta).getroot()

    assert raiz.tag == "structure"
    assert raiz.find("type").text == "fa"
    estados = raiz.findall("automaton/state")
    assert [e.get("name") for e in estados] == Q
    assert [e.get("name") for e in estados if e.find("initial") is not None] == ["q0"]
    assert [e.get("name") for e in estados if e.find("final") is not None] == ["q5"]

    transiciones = raiz.findall("automaton/transition")
    assert len(transiciones) == 42
    leidas = {
        (Q[int(t.find("from").text)], t.find("read").text): Q[int(t.find("to").text)]
        for t in transiciones
    }
    assert leidas == DELTA


def test_jff_pone_los_estados_en_linea_y_qnp_debajo(tmp_path):
    raiz = ET.parse(exportar_jff(tmp_path / "automata.jff")).getroot()
    y = {e.get("name"): float(e.find("y").text) for e in raiz.findall("automaton/state")}
    assert len({y[q] for q in Q if q != "qNP"}) == 1
    assert y["qNP"] > y["q0"]
