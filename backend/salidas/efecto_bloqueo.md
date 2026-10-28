# Efecto de bloquear cada nodo sobre la clasificación (semilla 42, sin otros bloqueos)

Se considera que un nodo cambió si su p anómalo varía 0,02 o más, o cruza 0,40 o 0,50. Entre paréntesis, la variación de p anómalo. Las cuatro primeras columnas describen la respuesta de la GCN; la última, si la etiqueta (clase extendida, §3.1) también cambia al retirar el nodo.

| Nodo bloqueado | Vecinos directos que cambiaron | Otros nodos que cambiaron | Cambios de nivel de alerta | Cambios de la clase extendida (etiqueta) |
| --- | --- | --- | --- | --- |
| S1 | S2 (−0,09), IoT1 (+0,10), IoT6 (+0,04), IoT7 (+0,04) | — | IoT1: Alerta temprana → Anómalo | — |
| S2 | S1 (−0,27), PC1 (−0,05), PC3 (−0,05), PC4 (−0,06) | — | S1: Alerta temprana → Normal | — |
| PC1 | S2 (+0,21), PC2 (+0,39), IoT1 (+0,08) | S1 (+0,08), PC3 (+0,15), PC4 (+0,03) | S1: Alerta temprana → Anómalo; S2: Normal → Anómalo; IoT1: Alerta temprana → Anómalo | — |
| PC2 | S2 (−0,14), PC1 (−0,16), PC3 (−0,13) | S1 (−0,04), PC4 (−0,03) | — | — |
| PC3 | S2 (+0,23), PC2 (+0,31), PC4 (+0,15) | S1 (+0,09), PC1 (+0,12) | S1: Alerta temprana → Anómalo; S2: Normal → Anómalo | — |
| PC4 | S2 (−0,04), PC3 (−0,03) | — | — | — |
| PC5 | S2 (+0,16), PC4 (+0,18), PC6 (+0,05) | S1 (+0,07), PC2 (+0,03), PC3 (+0,09) | S1: Alerta temprana → Anómalo; S2: Normal → Alerta temprana | — |
| PC6 | — | — | — | — |
| IoT1 | S1 (+0,04) | PC2 (+0,03) | S1: Alerta temprana → Anómalo | — |
| IoT2 | S1 (−0,23), IoT1 (−0,40) | S2 (−0,04) | S1: Alerta temprana → Normal; IoT1: Alerta temprana → Normal | — |
| IoT3 | S1 (+0,09) | S2 (+0,03) | S1: Alerta temprana → Anómalo | — |
| IoT4 | S1 (+0,08) | S2 (+0,03) | S1: Alerta temprana → Anómalo | — |
| IoT5 | S1 (+0,13), S2 (+0,10) | PC2 (+0,02) | S1: Alerta temprana → Anómalo; S2: Normal → Alerta temprana | — |
| IoT6 | S1 (+0,17), IoT7 (+0,07) | S2 (+0,04) | S1: Alerta temprana → Anómalo | — |
| IoT7 | S1 (−0,22), IoT6 (−0,18) | S2 (−0,05) | S1: Alerta temprana → Normal | — |

Al bloquear un nodo cambia la clasificación de al menos un vecino directo en 14 de 15 casos. La etiqueta cambia en 0 de 15 casos.
