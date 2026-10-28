import xml.etree.ElementTree as ET
from pathlib import Path

# ============================================================
# AFD de comunicación de un dispositivo (CONTEXTO §6)
# M = (Q, Σ, δ, q0, F)        L(M) = { a b c⁺ d e }
# ============================================================

# Q — conjunto de estados: Inactivo, Solicitud, Autenticación,
# Transmisión, Confirmación, Finalizado y No pertenece (trampa)
Q = ["q0", "q1", "q2", "q3", "q4", "q5", "qNP"]

# Σ — alfabeto: a solicitar, b autenticar, c transmitir, d confirmar (ACK),
# e finalizar, f timeout o evento inválido
SIGMA = ["a", "b", "c", "d", "e", "f"]

# q0 — estado inicial
Q0 = "q0"

# F — estados finales (de aceptación)
F = ["q5"]

# δ — función de transición, Q × Σ → Q: 7 × 6 = 42 pares (Tabla 11 del documento)
DELTA = {
    ("q0", "a"): "q1",  ("q0", "b"): "qNP", ("q0", "c"): "qNP", ("q0", "d"): "qNP", ("q0", "e"): "qNP", ("q0", "f"): "qNP",
    ("q1", "a"): "qNP", ("q1", "b"): "q2",  ("q1", "c"): "qNP", ("q1", "d"): "qNP", ("q1", "e"): "qNP", ("q1", "f"): "qNP",
    ("q2", "a"): "qNP", ("q2", "b"): "qNP", ("q2", "c"): "q3",  ("q2", "d"): "qNP", ("q2", "e"): "qNP", ("q2", "f"): "qNP",
    ("q3", "a"): "qNP", ("q3", "b"): "qNP", ("q3", "c"): "q3",  ("q3", "d"): "q4",  ("q3", "e"): "qNP", ("q3", "f"): "qNP",
    ("q4", "a"): "qNP", ("q4", "b"): "qNP", ("q4", "c"): "qNP", ("q4", "d"): "qNP", ("q4", "e"): "q5",  ("q4", "f"): "qNP",
    ("q5", "a"): "qNP", ("q5", "b"): "qNP", ("q5", "c"): "qNP", ("q5", "d"): "qNP", ("q5", "e"): "qNP", ("q5", "f"): "qNP",
    ("qNP", "a"): "qNP", ("qNP", "b"): "qNP", ("qNP", "c"): "qNP", ("qNP", "d"): "qNP", ("qNP", "e"): "qNP", ("qNP", "f"): "qNP",
}

RUTA_JFF = Path(__file__).resolve().parent.parent / "jflap" / "automata_softcast.jff"


def validar(cadena):
    """
    Recorre la cadena símbolo por símbolo desde q0 aplicando δ.
    Un símbolo fuera de Σ rechaza la cadena con un mensaje en `error`.
    """
    estado = Q0
    recorrido = [estado]
    for simbolo in cadena:
        if simbolo not in SIGMA:
            return {
                "aceptada": False,
                "recorrido": recorrido,
                "estado_final": estado,
                "error": f"símbolo fuera del alfabeto: {simbolo}",
            }
        estado = DELTA[(estado, simbolo)]
        recorrido.append(estado)
    return {"aceptada": estado in F, "recorrido": recorrido, "estado_final": estado}


def definicion():
    """Los 5 parámetros como JSON, para dibujar el diagrama y la tabla en la interfaz."""
    return {
        "Q": Q,
        "sigma": SIGMA,
        "q0": Q0,
        "F": F,
        "delta": {q: {s: DELTA[(q, s)] for s in SIGMA} for q in Q},
    }


def exportar_jff(ruta=RUTA_JFF):
    """Escribe el autómata en el formato XML de JFLAP: estados en línea y qNP debajo."""
    estructura = ET.Element("structure")
    ET.SubElement(estructura, "type").text = "fa"
    automata = ET.SubElement(estructura, "automaton")

    for i, nombre in enumerate(Q):
        estado = ET.SubElement(automata, "state", id=str(i), name=nombre)
        if nombre == "qNP":
            x, y = 100 + 120 * 2.5, 260
        else:
            x, y = 100 + 120 * i, 100
        ET.SubElement(estado, "x").text = str(x)
        ET.SubElement(estado, "y").text = str(y)
        if nombre == Q0:
            ET.SubElement(estado, "initial")
        if nombre in F:
            ET.SubElement(estado, "final")

    for (origen, simbolo), destino in DELTA.items():
        transicion = ET.SubElement(automata, "transition")
        ET.SubElement(transicion, "from").text = str(Q.index(origen))
        ET.SubElement(transicion, "to").text = str(Q.index(destino))
        ET.SubElement(transicion, "read").text = simbolo

    ET.indent(estructura)
    cabecera = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(cabecera + ET.tostring(estructura, encoding="unicode") + "\n", encoding="utf-8")
    return ruta


if __name__ == "__main__":
    print(exportar_jff())
