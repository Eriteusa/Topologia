import pytest

from softcast.alertas import ALERTA, ANOMALO, BLOQUEADO, NORMAL, nivel


@pytest.mark.parametrize("p, valida, esperado", [
    (0.00, True, NORMAL),
    (0.39, True, NORMAL),
    (0.40, True, ALERTA),
    (0.49, True, ALERTA),
    (0.50, True, ANOMALO),
    (0.99, True, ANOMALO),
    (0.10, False, ALERTA),   # secuencia inválida con p < 0,50
    (0.49, False, ALERTA),
    (0.50, False, ANOMALO),  # p ≥ 0,50 manda sobre la secuencia
])
def test_niveles_de_la_tabla_12(p, valida, esperado):
    assert nivel(p, valida) == esperado


def test_un_nodo_bloqueado_no_tiene_nivel_de_alerta():
    assert nivel(0.9, False, bloqueado=True) == BLOQUEADO
    assert nivel(None, True, bloqueado=True) == BLOQUEADO
