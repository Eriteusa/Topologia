import random

from softcast.automata import validar
from softcast.secuencias import cadena_invalida, cadena_valida, secuencias_por_nodo

NODOS = ["S1", "S2", "PC1", "PC2", "PC3", "PC4", "PC5", "PC6",
         "IoT1", "IoT2", "IoT3", "IoT4", "IoT5", "IoT6", "IoT7"]


def test_las_validas_tienen_la_forma_abc_k_de_y_el_afd_las_acepta():
    rng = random.Random(1)
    for _ in range(200):
        cadena = cadena_valida(rng)
        assert cadena.startswith("ab") and cadena.endswith("de")
        assert 1 <= cadena.count("c") <= 3
        assert validar(cadena)["aceptada"]


def test_las_invalidas_siempre_las_rechaza_el_afd():
    rng = random.Random(2)
    for _ in range(500):
        assert not validar(cadena_invalida(rng))["aceptada"]


def test_misma_semilla_misma_secuencia_por_nodo():
    assert secuencias_por_nodo(NODOS, 42) == secuencias_por_nodo(NODOS, 42)
    assert secuencias_por_nodo(NODOS, 42) != secuencias_por_nodo(NODOS, 43)
    assert set(secuencias_por_nodo(NODOS, 42)) == set(NODOS)


def test_cerca_del_80_por_ciento_son_validas():
    cadenas = [c for semilla in range(100) for c in secuencias_por_nodo(NODOS, semilla).values()]
    validas = sum(validar(c)["aceptada"] for c in cadenas)
    assert 0.76 <= validas / len(cadenas) <= 0.84
