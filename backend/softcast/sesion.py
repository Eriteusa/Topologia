# Estado en memoria de una sesión: semilla, atributos, bloqueos, clasificación (CONTEXTO §4, §5, §9).
import random
from pathlib import Path

from softcast import alertas
from softcast.automata import validar
from softcast.datos_base import id_arista
from softcast.generador import generar_grafos
from softcast.gnn import cargar_gcn, predecir
from softcast.grafo import aplicar_bloqueos, construir_grafo, ruta_optima
from softcast.secuencias import secuencias_por_nodo
from softcast.umbral import NOMBRES_CLASE, clase_umbral, clases_extendidas

RUTA_MODELO = Path(__file__).resolve().parent.parent / "modelos" / "modelo_gcn.pt"
CAMBIO_MINIMO_P = 0.02  # variación de p_anomalo que se considera "cambió" (también si cruza 0,40 o 0,50)


def _banda(p):
    return (p >= alertas.P_ALERTA, p >= alertas.P_ANOMALO)


class Sesion:
    def __init__(self, semilla=42, bloqueo_inicial=True, atributos="base", latencias="base", usar_gnn=True):
        self.semilla = semilla
        self.parametros = {
            "bloqueo_inicial": bloqueo_inicial,
            "atributos": atributos,
            "latencias": latencias,
        }
        self.usar_gnn = usar_gnn

        atributos_azar, latencias_azar = None, None
        if atributos == "aleatorios" or latencias == "aleatorias":
            nodos, aristas = generar_grafos(1, semilla)[0]
            if atributos == "aleatorios":
                atributos_azar = {n["id"]: {"trafico": n["trafico"], "cpu": n["cpu"]} for n in nodos}
            if latencias == "aleatorias":
                latencias_azar = {id_arista(a["origen"], a["destino"]): a["latencia_ms"] for a in aristas}
        self.G = construir_grafo(latencias_azar, atributos_azar)

        ids = list(self.G.nodes)
        self.secuencias = secuencias_por_nodo(ids, semilla)
        self.secuencia_valida = {n: validar(c)["aceptada"] for n, c in self.secuencias.items()}

        cargado = cargar_gcn(RUTA_MODELO) if usar_gnn else None
        self.modelo, self.escala_peso = cargado if cargado else (None, 1.0)

        self.bloqueos = []
        if bloqueo_inicial:
            for nodo in random.Random(f"{semilla}-inicial").sample(ids, 2):
                self._registrar("nodo", nodo, "inicial")

        self.ruta_vigente = None
        self.cambios = {}
        self.clasificacion = self._clasificar()

    # ---------- estado derivado ----------

    def _registrar(self, tipo, elemento, modo):
        self.bloqueos.append({"orden": len(self.bloqueos) + 1, "tipo": tipo, "elemento": elemento, "modo": modo})

    def _nodos_bloqueados(self):
        return {b["elemento"] for b in self.bloqueos if b["tipo"] == "nodo"}

    def _activo(self):
        return aplicar_bloqueos(self.G, self.bloqueos)

    def _listas_activas(self):
        activo = self._activo()
        nodos = [{"id": n, **activo.nodes[n]} for n in activo.nodes]
        aristas = [
            {"origen": a, "destino": b, "latencia_ms": d["latencia_ms"]}
            for a, b, d in activo.edges(data=True)
        ]
        return nodos, aristas

    def _clasificar(self):
        """{id: p_anomalo} de los nodos activos; sin nodos bloqueados ni sus aristas (§7.8)."""
        nodos, aristas = self._listas_activas()
        if self.modelo:
            return predecir(self.modelo, nodos, aristas, self.escala_peso)
        return {i: float(c) for i, c in clases_extendidas(nodos, aristas).items()}  # respaldo por umbral

    def _actualizar(self):
        """Reclasifica y guarda qué nodos cambiaron respecto de la clasificación anterior."""
        anterior = self.clasificacion
        nueva = self._clasificar()
        self.cambios = {
            n: round(p - anterior[n], 4)
            for n, p in nueva.items()
            if n in anterior and (abs(p - anterior[n]) >= CAMBIO_MINIMO_P or _banda(p) != _banda(anterior[n]))
        }
        self.clasificacion = nueva

    # ---------- acciones ----------

    def bloquear(self, tipo, elemento, modo="manual"):
        if tipo == "nodo":
            if elemento not in self.G:
                raise ValueError(f"nodo desconocido: {elemento}")
        elif tipo == "arista":
            try:
                a, b = elemento.split("-")
                elemento = id_arista(a, b)
            except (ValueError, KeyError):
                raise ValueError(f"arista desconocida: {elemento}")
        else:
            raise ValueError(f"tipo de bloqueo desconocido: {tipo}")

        if any(b["tipo"] == tipo and b["elemento"] == elemento for b in self.bloqueos):
            raise ValueError(f"ya está bloqueado: {elemento}")

        self._registrar(tipo, elemento, modo)
        self._actualizar()
        return self.bloqueos[-1]

    def ruta(self, origen, destino):
        bloqueados = self._nodos_bloqueados()
        for nodo in (origen, destino):
            if nodo not in self.G:
                raise ValueError(f"nodo desconocido: {nodo}")
            if nodo in bloqueados:
                raise ValueError(f"nodo bloqueado: {nodo}")
        self.ruta_vigente = (origen, destino)
        return ruta_optima(self._activo(), origen, destino)

    def ruta_actual(self):
        """Recalcula la ruta vigente; si se bloqueó su origen o destino queda sin camino y se limpia."""
        if not self.ruta_vigente:
            return None
        origen, destino = self.ruta_vigente
        ruta = ruta_optima(self._activo(), origen, destino)
        if {origen, destino} & self._nodos_bloqueados():
            self.ruta_vigente = None
        return ruta

    def bloqueo_aleatorio(self, origen, destino):
        """Bloquea una arista o un nodo intermedio de la ruta vigente, elegido con la semilla (§5.2)."""
        ruta = self.ruta(origen, destino)
        if not ruta["existe"]:
            raise ValueError("no hay ruta vigente")
        candidatos = [("arista", a["id"]) for a in ruta["aristas"]] + [("nodo", n) for n in ruta["nodos"][1:-1]]
        if not candidatos:
            raise ValueError("la ruta no tiene elementos que bloquear")
        tipo, elemento = random.Random(f"{self.semilla}-aleatorio-{len(self.bloqueos)}").choice(candidatos)
        return self.bloquear(tipo, elemento, "aleatorio")

    def simular_falla(self, nodo, trafico, cpu):
        if nodo not in self.G:
            raise ValueError(f"nodo desconocido: {nodo}")
        if nodo in self._nodos_bloqueados():
            raise ValueError(f"nodo bloqueado: {nodo}")
        self.G.nodes[nodo]["trafico"] = trafico
        self.G.nodes[nodo]["cpu"] = cpu
        self._actualizar()
        return list(self.cambios)

    def reiniciada(self):
        """Sesión nueva con la misma semilla y los mismos parámetros."""
        return Sesion(self.semilla, usar_gnn=self.usar_gnn, **self.parametros)

    # ---------- salida ----------

    def red(self):
        bloqueados = self._nodos_bloqueados()
        nodos_activos, aristas_activas = self._listas_activas()
        extendidas = clases_extendidas(nodos_activos, aristas_activas)

        nodos = []
        for n in self.G.nodes:
            datos = self.G.nodes[n]
            bloqueado = n in bloqueados
            p = None if bloqueado else self.clasificacion[n]
            valida = self.secuencia_valida[n]
            nodos.append({
                "id": n,
                "tipo": datos["tipo"],
                "subtipo": datos["subtipo"],
                "trafico": datos["trafico"],
                "cpu": datos["cpu"],
                "bloqueado": bloqueado,
                "clase_umbral": NOMBRES_CLASE[clase_umbral(datos)],
                "clase_extendida": None if bloqueado else NOMBRES_CLASE[extendidas[n]],
                "p_anomalo": p,
                "estado": "Bloqueado" if bloqueado else NOMBRES_CLASE[int(p >= alertas.P_ANOMALO)],
                "nivel_alerta": alertas.nivel(p, valida, bloqueado),
                "secuencia": self.secuencias[n],
                "secuencia_valida": valida,
                "delta_p": self.cambios.get(n),
                "x": datos["x"],
                "y": datos["y"],
            })

        aristas_bloqueadas = {b["elemento"] for b in self.bloqueos if b["tipo"] == "arista"}
        aristas = []
        for _, _, d in self.G.edges(data=True):
            origen, destino = d["id"].split("-")
            directa = d["id"] in aristas_bloqueadas
            aristas.append({
                "id": d["id"],
                "origen": origen,
                "destino": destino,
                "latencia_ms": d["latencia_ms"],
                "rol": d["rol"],
                "bloqueada": directa,
                "activa": not directa and origen not in bloqueados and destino not in bloqueados,
            })

        return {
            "semilla": self.semilla,
            "parametros": self.parametros,
            "fuente": "gnn" if self.modelo else "umbral",
            "nodos": nodos,
            "aristas": aristas,
            "bloqueos": self.bloqueos,
            "cambiaron": list(self.cambios),
            "ruta_vigente": list(self.ruta_vigente) if self.ruta_vigente else None,
        }
