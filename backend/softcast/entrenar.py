# Entrenamiento y evaluación de la GCN y del MLP (CONTEXTO §7.6–7.7).
# Uso: uv run python -m softcast.entrenar [--escala-peso X]
import argparse
import copy
import json
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from torch import nn
from torch_geometric.loader import DataLoader

from softcast.generador import generar_dataset, particionar
from softcast.gnn import GCNSoftCast, MLPBase, calibrar, contar_parametros

RAIZ = Path(__file__).resolve().parent.parent
SEMILLA = 42
MAX_EPOCAS = 200
PACIENCIA = 20
LR = 0.01
TAMANO_LOTE = 32


def fijar_semillas(semilla=SEMILLA):
    random.seed(semilla)
    np.random.seed(semilla)
    torch.manual_seed(semilla)


def pesos_de_clase(entrenamiento):
    """Inversamente proporcionales a la frecuencia de cada clase en entrenamiento."""
    y = torch.cat([d.y for d in entrenamiento])
    conteo = torch.bincount(y, minlength=2).float()
    return len(y) / (2 * conteo)


def _perdida_media(modelo, lotes, criterio):
    modelo.eval()
    total, n = 0.0, 0
    with torch.no_grad():
        for lote in lotes:
            total += float(criterio(modelo(lote.x, lote.edge_index, lote.edge_weight), lote.y))
            n += 1
    return total / n


def entrenar_modelo(modelo, entrenamiento, validacion, pesos):
    """Adam, entropía cruzada ponderada y parada temprana sobre la pérdida de validación."""
    criterio = nn.CrossEntropyLoss(weight=pesos)
    optimizador = torch.optim.Adam(modelo.parameters(), lr=LR)
    generador = torch.Generator().manual_seed(SEMILLA)
    lotes_entrenamiento = DataLoader(entrenamiento, batch_size=TAMANO_LOTE, shuffle=True, generator=generador)
    lotes_validacion = list(DataLoader(validacion, batch_size=TAMANO_LOTE))

    historial = {"entrenamiento": [], "validacion": []}
    mejor, mejor_estado, mejor_epoca, sin_mejora = float("inf"), None, 0, 0

    for epoca in range(1, MAX_EPOCAS + 1):
        modelo.train()
        suma, n = 0.0, 0
        for lote in lotes_entrenamiento:
            optimizador.zero_grad()
            perdida = criterio(modelo(lote.x, lote.edge_index, lote.edge_weight), lote.y)
            perdida.backward()
            optimizador.step()
            suma += float(perdida)
            n += 1
        historial["entrenamiento"].append(suma / n)
        historial["validacion"].append(_perdida_media(modelo, lotes_validacion, criterio))

        if historial["validacion"][-1] < mejor:
            mejor, mejor_estado, mejor_epoca, sin_mejora = historial["validacion"][-1], copy.deepcopy(modelo.state_dict()), epoca, 0
        else:
            sin_mejora += 1
            if sin_mejora >= PACIENCIA:
                break

    modelo.load_state_dict(mejor_estado)
    return {"historial": historial, "epocas": len(historial["validacion"]), "mejor_epoca": mejor_epoca}


@torch.no_grad()
def probabilidades(modelo, datos):
    modelo.eval()
    ps, ys = [], []
    for lote in DataLoader(datos, batch_size=TAMANO_LOTE):
        ps.append(torch.softmax(modelo(lote.x, lote.edge_index, lote.edge_weight), dim=1)[:, 1])
        ys.append(lote.y)
    return torch.cat(ps), torch.cat(ys).numpy()


def metricas_de(y, p, corte=0.5):
    """Precisión, recall y F1 de la clase Anómalo y matriz de confusión con p ≥ corte."""
    y_hat = (p >= corte).numpy().astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y, y_hat, average="binary", pos_label=1, zero_division=0)
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "matriz_confusion": confusion_matrix(y, y_hat, labels=[0, 1]).tolist(),
    }


def evaluar(modelo, prueba, razon_pesos):
    """
    Métricas sobre los grafos de prueba en tres puntos de operación:
    calibrado con corte 0,50 (el que usa el prototipo para el estado Anómalo),
    calibrado con corte 0,40 (Alerta temprana o peor) y sin calibrar (argmax).
    """
    p, y = probabilidades(modelo, prueba)
    p_calibrada = calibrar(p, razon_pesos)
    return {
        "calibrado": metricas_de(y, p_calibrada, 0.5),
        "corte_0_40": metricas_de(y, p_calibrada, 0.4),
        "sin_calibrar": metricas_de(y, p, 0.5),
    }


def graficar_curvas(resultados, ruta):
    fig, ejes = plt.subplots(1, len(resultados), figsize=(5 * len(resultados), 3.8), facecolor="white")
    for eje, (nombre, r) in zip(ejes, resultados.items()):
        eje.plot(r["historial"]["entrenamiento"], label="entrenamiento", color="#1f4e8c")
        eje.plot(r["historial"]["validacion"], label="validación", color="#e8742a")
        eje.axvline(r["mejor_epoca"] - 1, color="#8b95a3", linestyle=":", label="mejor época")
        eje.set_title(nombre)
        eje.set_xlabel("época")
        eje.set_ylabel("pérdida")
        eje.legend()
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def graficar_matrices(resultados, ruta):
    fig, ejes = plt.subplots(1, len(resultados), figsize=(4.2 * len(resultados), 3.8), facecolor="white")
    for eje, (nombre, r) in zip(ejes, resultados.items()):
        matriz = np.array(r["metricas"]["matriz_confusion"])
        eje.imshow(matriz, cmap="Blues")
        for i in range(2):
            for j in range(2):
                eje.text(j, i, str(matriz[i, j]), ha="center", va="center",
                         color="white" if matriz[i, j] > matriz.max() / 2 else "black")
        eje.set_xticks([0, 1], ["Normal", "Anómalo"])
        eje.set_yticks([0, 1], ["Normal", "Anómalo"])
        eje.set_xlabel("predicha")
        eje.set_ylabel("real")
        eje.set_title(f"{nombre} (p calibrada ≥ 0,50)")
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def main(escala_peso=1.0):
    fijar_semillas()
    dataset = generar_dataset(semilla=SEMILLA, escala_peso=escala_peso)
    entrenamiento, validacion, prueba = particionar(dataset, SEMILLA)

    y = torch.cat([d.y for d in dataset])
    porcentaje_anomalos = float(y.float().mean()) * 100
    pesos = pesos_de_clase(entrenamiento)
    razon_pesos = float(pesos[1] / pesos[0])
    print(f"Anómalos en el dataset: {porcentaje_anomalos:.2f} %  (pesos de clase {pesos.tolist()}, razón {razon_pesos:.2f})")

    resultados = {}
    for nombre, clase in [("GCN", GCNSoftCast), ("MLP", MLPBase)]:
        fijar_semillas()
        modelo = clase()
        r = entrenar_modelo(modelo, entrenamiento, validacion, pesos)
        evaluacion = evaluar(modelo, prueba, razon_pesos)
        r["metricas"] = evaluacion["calibrado"]
        r["evaluacion"] = evaluacion
        r["parametros"] = contar_parametros(modelo)
        r["modelo"] = modelo
        resultados[nombre] = r
        print(f"{nombre}: {r['parametros']} parámetros, {r['epocas']} épocas (mejor {r['mejor_epoca']})")
        for punto, m in evaluacion.items():
            print(f"   {punto:>12}: precisión {m['precision']:.3f}, recall {m['recall']:.3f}, F1 {m['f1']:.3f}")

    (RAIZ / "modelos").mkdir(exist_ok=True)
    (RAIZ / "salidas").mkdir(exist_ok=True)
    for nombre, archivo in [("GCN", "modelo_gcn.pt"), ("MLP", "modelo_mlp.pt")]:
        torch.save({"estado": resultados[nombre]["modelo"].state_dict(), "escala_peso": escala_peso,
                    "razon_pesos": razon_pesos}, RAIZ / "modelos" / archivo)

    metricas = {
        "semilla": SEMILLA,
        "escala_peso": escala_peso,
        "grafos": {"entrenamiento": len(entrenamiento), "validacion": len(validacion), "prueba": len(prueba)},
        "porcentaje_anomalos": porcentaje_anomalos,
        "pesos_de_clase": pesos.tolist(),
        "razon_pesos": razon_pesos,
        **{
            nombre.lower(): {
                "parametros": r["parametros"],
                "epocas": r["epocas"],
                "mejor_epoca": r["mejor_epoca"],
                **r["metricas"],  # calibrado, corte 0,50: el punto de operación del prototipo
                "corte_0_40": r["evaluacion"]["corte_0_40"],
                "sin_calibrar": r["evaluacion"]["sin_calibrar"],
            }
            for nombre, r in resultados.items()
        },
    }
    (RAIZ / "modelos" / "metricas.json").write_text(json.dumps(metricas, indent=2, ensure_ascii=False), encoding="utf-8")
    graficar_curvas(resultados, RAIZ / "salidas" / "curva_perdida.png")
    graficar_matrices(resultados, RAIZ / "salidas" / "matriz_confusion.png")
    return metricas


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--escala-peso", type=float, default=1.0)
    main(parser.parse_args().escala_peso)
