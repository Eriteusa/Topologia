# Clasificación del escenario base (semilla 42, sin bloqueos)

| Nodo | Tipo | Tráfico | CPU | Clase por umbral (Tabla 3) | Clase extendida | p anómalo (GNN) | Estado (GNN) | Nivel de alerta | Secuencia |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | Servidor | 58 | 63 | Normal | Normal | 0,48 | Normal | Alerta temprana | abcde (aceptada) |
| S2 | Servidor | 71 | 68 | Normal | Normal | 0,33 | Normal | Normal | abcde (aceptada) |
| PC1 | PC | 35 | 42 | Normal | Normal | 0,17 | Normal | Normal | abcccde (aceptada) |
| PC2 | PC | 82 | 91 | Anómalo | Anómalo | 0,52 | Anómalo | Anómalo | abcccde (aceptada) |
| PC3 | PC | 40 | 38 | Normal | Normal | 0,18 | Normal | Alerta temprana | abced (rechazada) |
| PC4 | PC | 65 | 72 | Normal | Normal | 0,10 | Normal | Normal | abcde (aceptada) |
| PC5 | PC | 28 | 30 | Normal | Normal | 0,02 | Normal | Normal | abcccde (aceptada) |
| PC6 | PC | 55 | 60 | Normal | Normal | 0,03 | Normal | Normal | abcccde (aceptada) |
| IoT1 | IoT | 48 | 55 | Normal | Normal | 0,45 | Normal | Alerta temprana | abcccde (aceptada) |
| IoT2 | IoT | 95 | 98 | Anómalo | Anómalo | 1,00 | Anómalo | Anómalo | abccde (aceptada) |
| IoT3 | IoT | 20 | 25 | Normal | Normal | 0,00 | Normal | Normal | abcccde (aceptada) |
| IoT4 | IoT | 18 | 20 | Normal | Normal | 0,00 | Normal | Normal | abcde (aceptada) |
| IoT5 | IoT | 22 | 28 | Normal | Normal | 0,00 | Normal | Normal | abcde (aceptada) |
| IoT6 | IoT | 30 | 33 | Normal | Normal | 0,19 | Normal | Normal | abccde (aceptada) |
| IoT7 | IoT | 85 | 88 | Anómalo | Anómalo | 0,93 | Anómalo | Anómalo | abcde (aceptada) |

El estado de la GNN coincide con la clase por umbral de la Tabla 3 en 15 de 15 nodos.
