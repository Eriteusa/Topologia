# Métricas de la GNN frente al MLP

- Dataset: 1000 grafos con la topología fija, particionados por grafos completos (700 entrenamiento, 150 validación, 150 prueba), semilla 42.
- Nodos de clase Anómalo en el dataset: 23,22 %.
- Pesos de clase inversos a la frecuencia: razón 3,37. La probabilidad se calibra dividiendo los odds entre esa razón.
- Parámetros entrenables: GCN 266, MLP 266. Épocas: GCN 98 (mejor 78), MLP 39 (mejor 19).

## Métricas sobre los grafos de prueba (clase Anómalo)

| Modelo | Punto de operación | Precisión | Recall | F1 |
| --- | --- | --- | --- | --- |
| GCN | calibrado, corte 0,50 (prototipo) | 0,775 | 0,584 | 0,666 |
| GCN | calibrado, corte 0,40 | 0,710 | 0,724 | 0,717 |
| GCN | sin calibrar | 0,585 | 0,884 | 0,704 |
| MLP | calibrado, corte 0,50 (prototipo) | 0,940 | 0,646 | 0,766 |
| MLP | calibrado, corte 0,40 | 0,882 | 0,708 | 0,786 |
| MLP | sin calibrar | 0,730 | 0,788 | 0,758 |

## Matrices de confusión

**GCN** (calibrado, corte 0,50)

| Real \ Predicha | Normal | Anómalo |
| --- | --- | --- |
| Normal | 1593 | 95 |
| Anómalo | 234 | 328 |

**MLP** (calibrado, corte 0,50)

| Real \ Predicha | Normal | Anómalo |
| --- | --- | --- |
| Normal | 1665 | 23 |
| Anómalo | 199 | 363 |

## Lectura

- calibrado, corte 0,50 (prototipo): F1 de la GCN 0,666 frente a 0,766 del MLP; la GCN no supera al MLP.
- calibrado, corte 0,40: F1 de la GCN 0,717 frente a 0,786 del MLP; la GCN no supera al MLP.
- sin calibrar: F1 de la GCN 0,704 frente a 0,758 del MLP; la GCN no supera al MLP.
