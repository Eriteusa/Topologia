# Criterio de clase (CONTEXTO §3). Clase: 0 = Normal, 1 = Anómalo.
NOMBRES_CLASE = ["Normal", "Anómalo"]

# Umbral propio (§3)
CPU_ALTA = 85
TRAFICO_ALTO = 80
CARGA_COMBINADA = 70

# Contagio por vecindad (§3.1)
CARGA_MEDIA = 60
FRACCION_VECINOS = 0.5


def umbral_propio(cpu, trafico):
    """Regla 1: solo depende de los atributos del propio nodo."""
    return (
        cpu >= CPU_ALTA
        or trafico >= TRAFICO_ALTO
        or (cpu >= CARGA_COMBINADA and trafico >= CARGA_COMBINADA)
    )


def _supera_umbral(nodo):
    return umbral_propio(nodo["cpu"], nodo["trafico"])


def clase_umbral(nodo):
    return int(_supera_umbral(nodo))


def clase_extendida(nodo, vecinos_activos):
    """
    Anómalo si supera el umbral propio, o si tiene carga media y al menos la
    mitad de sus vecinos activos superan el umbral propio. Sin vecinos activos
    la fracción es 0.
    """
    if _supera_umbral(nodo):
        return 1
    if not vecinos_activos:
        return 0
    fraccion = sum(_supera_umbral(v) for v in vecinos_activos) / len(vecinos_activos)
    carga_media = nodo["cpu"] >= CARGA_MEDIA or nodo["trafico"] >= CARGA_MEDIA
    return int(carga_media and fraccion >= FRACCION_VECINOS)


def clases_extendidas(nodos, aristas):
    """
    {id: clase} para una lista de nodos y aristas activas.
    nodos: dicts con id, cpu, trafico. aristas: dicts con origen, destino.
    """
    por_id = {n["id"]: n for n in nodos}
    vecinos = {n["id"]: [] for n in nodos}
    for a in aristas:
        if a["origen"] in por_id and a["destino"] in por_id:
            vecinos[a["origen"]].append(por_id[a["destino"]])
            vecinos[a["destino"]].append(por_id[a["origen"]])
    return {i: clase_extendida(por_id[i], vecinos[i]) for i in por_id}
