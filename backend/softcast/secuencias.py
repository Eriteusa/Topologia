# Secuencias de eventos por nodo (CONTEXTO §6.3).
import random

from softcast.automata import validar

PROBABILIDAD_VALIDA = 0.8


def cadena_valida(rng):
    """a b c^k d e, con k entre 1 y 3."""
    return "ab" + "c" * rng.randint(1, 3) + "de"


def mutar(cadena, rng):
    """Una mutación: insertar f, eliminar un símbolo o intercambiar dos adyacentes."""
    tipo = rng.choice(["insertar", "eliminar", "intercambiar"])
    if tipo == "insertar":
        i = rng.randint(0, len(cadena))
        return cadena[:i] + "f" + cadena[i:]
    if tipo == "eliminar":
        i = rng.randrange(len(cadena))
        return cadena[:i] + cadena[i + 1:]
    i = rng.randrange(len(cadena) - 1)
    return cadena[:i] + cadena[i + 1] + cadena[i] + cadena[i + 2:]


def cadena_invalida(rng):
    """Una cadena válida mutada; se repite si la mutación dejó una cadena que el AFD acepta (p. ej. quitar una c de ccc)."""
    while True:
        cadena = mutar(cadena_valida(rng), rng)
        if not validar(cadena)["aceptada"]:
            return cadena


def generar_secuencia(rng):
    if rng.random() < PROBABILIDAD_VALIDA:
        return cadena_valida(rng)
    return cadena_invalida(rng)


def secuencias_por_nodo(ids_nodos, semilla):
    """{id_nodo: cadena}, reproducible con la semilla de la sesión."""
    rng = random.Random(semilla)
    return {nodo: generar_secuencia(rng) for nodo in ids_nodos}
