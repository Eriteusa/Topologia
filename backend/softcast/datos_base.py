# Única fuente de verdad de la topología (CONTEXTO §2).
# Grafo no dirigido y ponderado: 15 nodos, 26 aristas, peso = latencia en ms.

# Nodos del escenario base (Tabla 3 del documento): id, tipo, subtipo, tráfico, cpu
NODOS = [
    {"id": "S1", "tipo": "Servidor", "subtipo": "BD/IoT", "trafico": 58, "cpu": 63},
    {"id": "S2", "tipo": "Servidor", "subtipo": "Web/Core", "trafico": 71, "cpu": 68},
    {"id": "PC1", "tipo": "PC", "subtipo": "Workstation", "trafico": 35, "cpu": 42},
    {"id": "PC2", "tipo": "PC", "subtipo": "Workstation", "trafico": 82, "cpu": 91},
    {"id": "PC3", "tipo": "PC", "subtipo": "Workstation", "trafico": 40, "cpu": 38},
    {"id": "PC4", "tipo": "PC", "subtipo": "Workstation", "trafico": 65, "cpu": 72},
    {"id": "PC5", "tipo": "PC", "subtipo": "Workstation", "trafico": 28, "cpu": 30},
    {"id": "PC6", "tipo": "PC", "subtipo": "Workstation", "trafico": 55, "cpu": 60},
    {"id": "IoT1", "tipo": "IoT", "subtipo": "Cámara IP", "trafico": 48, "cpu": 55},
    {"id": "IoT2", "tipo": "IoT", "subtipo": "Cámara IP", "trafico": 95, "cpu": 98},
    {"id": "IoT3", "tipo": "IoT", "subtipo": "Sensor de temperatura", "trafico": 20, "cpu": 25},
    {"id": "IoT4", "tipo": "IoT", "subtipo": "Sensor de humo", "trafico": 18, "cpu": 20},
    {"id": "IoT5", "tipo": "IoT", "subtipo": "Sensor de humedad", "trafico": 22, "cpu": 28},
    {"id": "IoT6", "tipo": "IoT", "subtipo": "Impresora de red", "trafico": 30, "cpu": 33},
    {"id": "IoT7", "tipo": "IoT", "subtipo": "Impresora de red", "trafico": 85, "cpu": 88},
]

# Clase por umbral de la Tabla 3 (solo para comprobar que el criterio la reproduce)
CLASE_UMBRAL_BASE = {n["id"]: "Normal" for n in NODOS}
CLASE_UMBRAL_BASE.update({"PC2": "Anómalo", "IoT2": "Anómalo", "IoT7": "Anómalo"})

# Aristas (Tabla 4): origen, destino, latencia_ms, rol. El orden es el de la tabla.
ARISTAS = [
    ("S1", "S2", 2, "Troncal"),
    ("S2", "PC1", 5, "Principal"),
    ("S2", "PC2", 6, "Principal"),
    ("S2", "PC3", 4, "Principal"),
    ("S2", "PC4", 5, "Principal"),
    ("S2", "PC5", 7, "Principal"),
    ("S2", "PC6", 6, "Principal"),
    ("S1", "IoT1", 12, "Principal"),
    ("S1", "IoT2", 15, "Principal"),
    ("S1", "IoT3", 18, "Principal"),
    ("S1", "IoT4", 20, "Principal"),
    ("S1", "IoT5", 19, "Principal"),
    ("S1", "IoT6", 10, "Principal"),
    ("S1", "IoT7", 11, "Principal"),
    ("PC1", "PC2", 3, "Redundante"),
    ("PC2", "PC3", 4, "Redundante"),
    ("PC3", "PC4", 3, "Redundante"),
    ("PC4", "PC5", 4, "Redundante"),
    ("PC5", "PC6", 3, "Redundante"),
    ("IoT1", "IoT2", 6, "Redundante"),
    ("IoT3", "IoT4", 5, "Redundante"),
    ("IoT4", "IoT5", 5, "Redundante"),
    ("IoT6", "IoT7", 4, "Redundante"),
    ("PC1", "IoT1", 15, "Redundante"),
    ("PC6", "IoT6", 14, "Redundante"),
    ("S2", "IoT5", 21, "Redundante"),
]

# Posiciones para dibujar el grafo (viewBox 150 220 650 420)
POSICIONES = {
    "S2": (335, 435), "S1": (600, 435),
    "PC1": (413, 283), "PC2": (335, 265), "PC3": (255, 308),
    "PC4": (218, 393), "PC5": (225, 500), "PC6": (318, 583),
    "IoT1": (520, 283), "IoT2": (617, 263), "IoT3": (712, 308),
    "IoT4": (742, 400), "IoT5": (683, 510), "IoT6": (580, 580), "IoT7": (675, 608),
}

# Rangos de latencia por categoría (Tabla 8), para el dataset y las sesiones aleatorias
RANGOS_LATENCIA = {
    ("Servidor", "Servidor"): (1, 3),
    ("PC", "Servidor"): (3, 8),
    ("IoT", "Servidor"): (8, 22),
    ("PC", "PC"): (2, 5),
    ("IoT", "IoT"): (3, 8),
    ("IoT", "PC"): (12, 18),
}


def id_arista(a, b):
    """Id canónico de una arista ("S1-S2"), sin importar el orden en que se den los extremos."""
    for origen, destino, _, _ in ARISTAS:
        if {origen, destino} == {a, b}:
            return f"{origen}-{destino}"
    raise KeyError(f"no existe la arista {a}-{b}")
