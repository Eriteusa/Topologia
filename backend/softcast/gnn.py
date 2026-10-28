# Modelos y conversión a PyTorch Geometric (CONTEXTO §7.3–7.5, §7.8).
from pathlib import Path

import torch
from torch import nn
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

TIPOS = ["Servidor", "PC", "IoT"]
LATENCIA_MAX = 22
N_FEATURES = 6


class GCNSoftCast(nn.Module):
    """GCNConv(6→16) + ReLU + Dropout(0.3), GCNConv(16→8) + ReLU, Linear(8→2): 266 parámetros."""

    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(N_FEATURES, 16)
        self.conv2 = GCNConv(16, 8)
        self.lineal = nn.Linear(8, 2)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x, edge_index, edge_weight=None):
        x = self.dropout(torch.relu(self.conv1(x, edge_index, edge_weight)))
        x = torch.relu(self.conv2(x, edge_index, edge_weight))
        return self.lineal(x)  # logits; el softmax se aplica solo en inferencia


class MLPBase(nn.Module):
    """Comparación sin estructura de grafo: 6 → 16 → 8 → 2 (mismo dropout)."""

    def __init__(self):
        super().__init__()
        self.capa1 = nn.Linear(N_FEATURES, 16)
        self.capa2 = nn.Linear(16, 8)
        self.lineal = nn.Linear(8, 2)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x, edge_index=None, edge_weight=None):
        x = self.dropout(torch.relu(self.capa1(x)))
        x = torch.relu(self.capa2(x))
        return self.lineal(x)


def a_data(nodos, aristas, clases=None, escala_peso=1.0):
    """
    Construye el Data de PyG con las features de §7.3 y los pesos de §7.4.
    nodos: dicts con id, tipo, trafico, cpu. aristas: dicts con origen, destino,
    latencia_ms. Las aristas con un extremo fuera de `nodos` (bloqueado) se ignoran.
    clases: {id: 0|1} opcional, se guarda en `y`.
    El peso de arista es min(1, escala_peso / latencia): con escala 1 es 1/latencia.
    """
    indice = {n["id"]: i for i, n in enumerate(nodos)}
    activas = [a for a in aristas if a["origen"] in indice and a["destino"] in indice]

    latencias = [[] for _ in nodos]
    origenes, destinos, pesos = [], [], []
    for a in activas:
        i, j = indice[a["origen"]], indice[a["destino"]]
        latencias[i].append(a["latencia_ms"])
        latencias[j].append(a["latencia_ms"])
        peso = min(1.0, escala_peso / a["latencia_ms"])
        origenes += [i, j]  # cada arista en ambos sentidos
        destinos += [j, i]
        pesos += [peso, peso]

    filas = []
    for n, lat in zip(nodos, latencias):
        tipo = [1.0 if n["tipo"] == t else 0.0 for t in TIPOS]
        media = sum(lat) / len(lat) / LATENCIA_MAX if lat else 1.0
        filas.append(tipo + [n["trafico"] / 100, n["cpu"] / 100, media])

    data = Data(
        x=torch.tensor(filas, dtype=torch.float).reshape(len(nodos), N_FEATURES),
        edge_index=torch.tensor([origenes, destinos], dtype=torch.long).reshape(2, -1),
        edge_weight=torch.tensor(pesos, dtype=torch.float),
    )
    if clases is not None:
        data.y = torch.tensor([clases[n["id"]] for n in nodos], dtype=torch.long)
    return data


def calibrar(p_anomalo, razon_pesos):
    """
    Corrige el sesgo de los pesos de clase. Entrenar con pesos inversos a la frecuencia
    multiplica por `razon_pesos` los odds a favor de Anómalo; aquí se deshace, de modo
    que p_anomalo vuelve a ser una probabilidad y los cortes 0,40 y 0,50 de §8 tienen sentido.
    """
    p = torch.as_tensor(p_anomalo, dtype=torch.float).clamp(1e-7, 1 - 1e-7)
    odds = p / (1 - p) / razon_pesos
    return odds / (1 + odds)


@torch.no_grad()
def predecir(modelo, nodos_activos, aristas_activas, escala_peso=1.0):
    """{id: p_anomalo} calibrada para los nodos activos, con softmax sobre los logits."""
    if not nodos_activos:
        return {}
    modelo.eval()
    data = a_data(nodos_activos, aristas_activas, escala_peso=escala_peso)
    probabilidades = torch.softmax(modelo(data.x, data.edge_index, data.edge_weight), dim=1)[:, 1]
    probabilidades = calibrar(probabilidades, getattr(modelo, "razon_pesos", 1.0))
    return {n["id"]: float(p) for n, p in zip(nodos_activos, probabilidades)}


def cargar_gcn(ruta):
    """(modelo, escala_peso) desde el archivo entrenado, o None si no existe (el backend usa el umbral)."""
    if not Path(ruta).exists():
        return None
    guardado = torch.load(ruta, map_location="cpu")
    modelo = GCNSoftCast()
    modelo.load_state_dict(guardado["estado"])
    modelo.razon_pesos = guardado.get("razon_pesos", 1.0)
    modelo.eval()
    return modelo, guardado["escala_peso"]


def contar_parametros(modelo):
    return sum(p.numel() for p in modelo.parameters() if p.requires_grad)
