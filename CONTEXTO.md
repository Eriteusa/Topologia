# CONTEXTO — Proyecto SoftCast (Experiencia Final, Lenguajes y Autómatas)

Este archivo es la **especificación funcional y técnica** del prototipo. Todos los datos numéricos que aparecen aquí (nodos, aristas, latencias, umbrales, autómata, arquitectura de la GNN) están en el documento académico ya entregado al docente. **El código debe reproducirlos exactamente.** Si algo no cuadra, se pregunta; no se "corrige" por cuenta propia.

**Única extensión sobre lo entregado:** el criterio de clase de §3 añade una regla de vecindad (§3.1) para que la GNN analice relaciones entre nodos, como pide el enunciado. La regla 1 es el umbral original y la Tabla 2.1 se sigue reproduciendo. Ver también `IMPLEMENTACION_CORRECTA.md`.

---

## 1. El problema en una frase

La empresa ficticia SoftCast tiene una red de servidores, PC y dispositivos IoT. El sistema:

- modela esa red como un grafo;
- clasifica cada nodo como Normal o Anómalo con una GNN;
- valida con un autómata finito la secuencia de eventos de comunicación de cada dispositivo;
- permite bloquear nodos o enlaces y recalcula la ruta óptima con Dijkstra hasta que no quede camino.

---

## 2. Topología fija (escenario base)

Es un grafo **no dirigido y ponderado** G = (V, E) con 15 nodos y 26 aristas. El peso de cada arista es la latencia en ms; a menor latencia, mejor camino.

### 2.1 Nodos y atributos del escenario base (Tabla 3 del documento)

| id | tipo | subtipo | tráfico | cpu (%) | clase por umbral |
|---|---|---|---|---|---|
| S1 | Servidor | BD/IoT | 58 | 63 | Normal |
| S2 | Servidor | Web/Core | 71 | 68 | Normal |
| PC1 | PC | Workstation | 35 | 42 | Normal |
| PC2 | PC | Workstation | 82 | 91 | Anómalo |
| PC3 | PC | Workstation | 40 | 38 | Normal |
| PC4 | PC | Workstation | 65 | 72 | Normal |
| PC5 | PC | Workstation | 28 | 30 | Normal |
| PC6 | PC | Workstation | 55 | 60 | Normal |
| IoT1 | IoT | Cámara IP | 48 | 55 | Normal |
| IoT2 | IoT | Cámara IP | 95 | 98 | Anómalo |
| IoT3 | IoT | Sensor de temperatura | 20 | 25 | Normal |
| IoT4 | IoT | Sensor de humo | 18 | 20 | Normal |
| IoT5 | IoT | Sensor de humedad | 22 | 28 | Normal |
| IoT6 | IoT | Impresora de red | 30 | 33 | Normal |
| IoT7 | IoT | Impresora de red | 85 | 88 | Anómalo |

### 2.2 Aristas y latencias (Tabla 4 del documento)

| # | origen | destino | latencia (ms) | rol |
|---|---|---|---|---|
| 1 | S1 | S2 | 2 | Troncal |
| 2 | S2 | PC1 | 5 | Principal |
| 3 | S2 | PC2 | 6 | Principal |
| 4 | S2 | PC3 | 4 | Principal |
| 5 | S2 | PC4 | 5 | Principal |
| 6 | S2 | PC5 | 7 | Principal |
| 7 | S2 | PC6 | 6 | Principal |
| 8 | S1 | IoT1 | 12 | Principal |
| 9 | S1 | IoT2 | 15 | Principal |
| 10 | S1 | IoT3 | 18 | Principal |
| 11 | S1 | IoT4 | 20 | Principal |
| 12 | S1 | IoT5 | 19 | Principal |
| 13 | S1 | IoT6 | 10 | Principal |
| 14 | S1 | IoT7 | 11 | Principal |
| 15 | PC1 | PC2 | 3 | Redundante |
| 16 | PC2 | PC3 | 4 | Redundante |
| 17 | PC3 | PC4 | 3 | Redundante |
| 18 | PC4 | PC5 | 4 | Redundante |
| 19 | PC5 | PC6 | 3 | Redundante |
| 20 | IoT1 | IoT2 | 6 | Redundante |
| 21 | IoT3 | IoT4 | 5 | Redundante |
| 22 | IoT4 | IoT5 | 5 | Redundante |
| 23 | IoT6 | IoT7 | 4 | Redundante |
| 24 | PC1 | IoT1 | 15 | Redundante |
| 25 | PC6 | IoT6 | 14 | Redundante |
| 26 | S2 | IoT5 | 21 | Redundante |

Propiedades verificadas que deben cumplirse:

- grado medio 3,47;
- sin nodos de articulación ni aristas puente;
- conectividad por nodos y por aristas = 2.

### 2.3 Posiciones para dibujar el grafo (SVG)

Son coordenadas aproximadas tomadas de la figura del documento, con viewBox sugerido `150 220 650 420`. Se pueden ajustar un poco, pero hay que conservar la forma: PC a la izquierda alrededor de S2, IoT a la derecha alrededor de S1 y troncal horizontal al centro.

```
S2 (335,435)   S1 (600,435)
PC1 (413,283)  PC2 (335,265)  PC3 (255,308)  PC4 (218,393)  PC5 (225,500)  PC6 (318,583)
IoT1 (520,283) IoT2 (617,263) IoT3 (712,308) IoT4 (742,400) IoT5 (683,510) IoT6 (580,580) IoT7 (675,608)
```

Las aristas redundantes se dibujan punteadas y las principales y la troncal, sólidas. Cada arista muestra su latencia.

### 2.4 Rangos de latencia por categoría (Tabla 8)

Se usan para generar el dataset aleatorio de la GNN y para las sesiones con `latencias: "aleatorias"` (§10), nunca para el escenario base. La topología (qué nodo se conecta con cuál) es siempre la de §2.2.

| categoría | latencia (ms) | n.º aristas |
|---|---|---|
| Servidor–Servidor | 1 a 3 | 1 |
| Servidor–PC | 3 a 8 | 6 |
| Servidor–IoT | 8 a 22 | 8 |
| PC–PC | 2 a 5 | 5 |
| IoT–IoT | 3 a 8 | 4 |
| PC–IoT | 12 a 18 | 2 |

---

## 3. Criterio de umbral (etiqueta / ground truth)

Un nodo es **Anómalo** si cumple al menos una de estas condiciones; si no cumple ninguna, es Normal:

1. `cpu >= 85`, o
2. `trafico >= 80`, o
3. `cpu >= 70 and trafico >= 70`.

Este criterio (`umbral_propio`) debe reproducir la columna "clase por umbral" de la tabla 2.1.

### 3.1 Criterio extendido con vecindad (etiqueta que aprende la GNN)

El enunciado pide que la GNN analice las relaciones entre nodos y que se vea cómo cambia el comportamiento de la red al bloquear. Con el umbral propio la clase depende solo del nodo, y una GNN no aportaría nada sobre un MLP. Por eso la etiqueta es:

```
fraccion_vecinos(v) = (vecinos activos con umbral_propio) / (vecinos activos)
                      0 si no tiene vecinos activos

Anómalo(v) = umbral_propio(v)
          o ( fraccion_vecinos(v) >= 0.5  y  (cpu >= 60 o trafico >= 60) )
```

- "Vecinos activos" son los no bloqueados, con arista no bloqueada.
- En el escenario base la mayor fracción de vecinos anómalos es 1/3, así que la Tabla 2.1 no cambia: PC2, IoT2 e IoT7 siguen siendo los únicos Anómalos. **Debe haber una prueba automática que lo confirme.**
- Se implementa en `umbral.py` con dos funciones: `umbral_propio(cpu, trafico)` y `clase_extendida(nodo, vecinos_activos)`.
- La columna "clase por umbral" de la interfaz y de la API usa `umbral_propio`; el entrenamiento y las métricas usan `clase_extendida`.

---

## 4. Estados del nodo (ajuste pedido por el docente)

Cada nodo tiene un **estado** con tres valores posibles:

| estado | cuándo | color en la interfaz |
|---|---|---|
| Normal | la GNN predice clase 0 y el nodo no está bloqueado | color por tipo (servidor azul oscuro, PC azul, IoT verde) |
| Anómalo | la GNN predice clase 1 y el nodo no está bloqueado | borde rojo grueso |
| Bloqueado | el nodo fue bloqueado (inicial, aleatorio o manual) | relleno gris con una ✕; tiene prioridad sobre lo anterior |

Reglas:

- La GNN sigue siendo un **clasificador binario** (Normal/Anómalo). "Bloqueado" no se aprende: es una acción del sistema o del usuario.
- **Antes de clasificar, los nodos bloqueados se retiran de los datos que recibe la GNN**, junto con todas sus aristas. No se clasifican y no influyen en sus vecinos. En la interfaz siguen visibles en gris.
- Como consecuencia, bloquear un nodo puede cambiar la clasificación de sus vecinos. Esto es intencional ("cómo cambia el comportamiento de la red") y la interfaz debe hacerlo visible, por ejemplo resaltando los nodos cuya probabilidad cambió.

---

## 5. Bloqueo de nodos y enlaces, y recálculo de rutas

### 5.1 Bloqueo inicial (ajuste pedido por el docente)

- Al iniciar una sesión, el sistema **bloquea 2 nodos al azar** entre los 15, usando la semilla de la sesión. Puede caer cualquier nodo, incluidos los servidores.
- Origen y destino **solo** se pueden elegir entre nodos no bloqueados.
- Hay 7 pares de nodos (de 105) que, bloqueados juntos, desconectan la red:
  - (S1, S2), (S1, PC1), (S1, PC6), (S1, IoT1), (S1, IoT4), (S1, IoT5), (S1, IoT6).
  - En ese caso algunos pares origen–destino no tienen camino y el sistema muestra "Sin camino disponible", sin error.

### 5.2 Bloqueos posteriores

- **Manual (clic):** el usuario (o el jurado durante la sustentación) hace clic sobre un nodo o una arista y lo bloquea.
- **Aleatorio:** se elige al azar, con la semilla, un elemento de la **ruta vigente**: una de sus aristas o uno de sus nodos intermedios, nunca el origen ni el destino. La elección es uniforme entre todos los candidatos (aristas y nodos intermedios juntos). Si la ruta es una sola arista, el único candidato es esa arista.
- **Manual sobre origen o destino:** está permitido. La ruta pasa a "Sin camino disponible" y los selectores de origen y destino se limpian.
- **Orden de recálculo tras cada cambio:** grafo activo → clasificación (GNN) → alertas → ruta.
- **Bloquear un nodo** retira el nodo y todas sus aristas.
- **Bloquear una arista** hace que su peso pase a infinito, es decir, se retira.
- Cada bloqueo queda registrado en un historial con: orden, tipo (nodo/arista), elemento y modo (inicial/aleatorio/manual).

### 5.3 Ciclo

```
G' ← G sin los elementos bloqueados
ruta ← Dijkstra(G', origen, destino)
si no hay ruta: "Sin camino disponible" y fin
mostrar ruta + latencia total + verificación por arista
esperar siguiente bloqueo (clic o aleatorio) y repetir
```

### 5.4 Desempate de Dijkstra (obligatorio)

Si hay varias rutas con la misma latencia mínima:

1. Gana la de **menos saltos** (menos aristas).
2. Si persiste el empate, gana la de menor orden lexicográfico de la lista de ids.

Implementación sugerida: `networkx.all_shortest_paths(G, o, d, weight="latencia_ms")` y luego `min(rutas, key=lambda r: (len(r), r))`.

### 5.5 Verificación de latencia (ajuste pedido por el docente)

Toda ruta devuelta debe incluir un **desglose arista por arista**, con cada latencia tomada de la tabla 2.2, y la suma. Por ejemplo: `PC3–S2 (4) + S2–S1 (2) + S1–IoT4 (20) = 26 ms`. La interfaz muestra este desglose.

### 5.6 Caso de prueba de referencia (Tabla 9 del documento)

Origen PC3, destino IoT4, **sin** bloqueo inicial de nodos, bloqueando aristas en este orden:

| iter. | aristas bloqueadas (acumuladas) | ruta esperada | latencia |
|---|---|---|---|
| 1 | — | PC3 → S2 → S1 → IoT4 | 26 |
| 2 | S2–S1 | PC3 → S2 → IoT5 → IoT4 | 30 |
| 3 | + PC3–S2 | PC3 → PC4 → S2 → IoT5 → IoT4 | 34 |
| 4 | + IoT5–IoT4 | PC3 → PC2 → PC1 → IoT1 → S1 → IoT4 | 54 |
| 5 | + PC3–PC2 | PC3 → PC4 → PC5 → PC6 → IoT6 → S1 → IoT4 | 54 |
| 6 | + PC3–PC4 | Sin camino disponible | — |

En la iteración 4 hay **empate a 54 ms**: la ruta de la iteración 5 (6 saltos) también estaba disponible. Gana la de 5 saltos por la regla 5.4.

---

## 6. Autómata finito determinista (AFD)

M = (Q, Σ, δ, q0, F)

- **Q** = {q0, q1, q2, q3, q4, q5, qNP}, que corresponden a Inactivo, Solicitud, Autenticación, Transmisión, Confirmación, Finalizado y No pertenece (estado trampa).
- **Σ** = {a, b, c, d, e, f}, con:
  - a = solicitar conexión
  - b = autenticar
  - c = transmitir datos
  - d = confirmar (ACK)
  - e = finalizar/cerrar sesión
  - f = timeout o evento inválido
- **q0** es el estado inicial y **F** = {q5}.
- El lenguaje reconocido es L(M) = { a b c⁺ d e }.

### 6.1 Función de transición δ completa (42 pares)

| estado | a | b | c | d | e | f |
|---|---|---|---|---|---|---|
| →q0 | q1 | qNP | qNP | qNP | qNP | qNP |
| q1 | qNP | q2 | qNP | qNP | qNP | qNP |
| q2 | qNP | qNP | q3 | qNP | qNP | qNP |
| q3 | qNP | qNP | q3 | q4 | qNP | qNP |
| q4 | qNP | qNP | qNP | qNP | q5 | qNP |
| q5 (F) | qNP | qNP | qNP | qNP | qNP | qNP |
| qNP | qNP | qNP | qNP | qNP | qNP | qNP |

### 6.2 Comportamiento esperado

- Cualquier símbolo fuera de Σ hace que la cadena se rechace con un mensaje claro de "símbolo fuera del alfabeto".
- La salida incluye `aceptada` (bool), `recorrido` (lista de estados, por ejemplo `q0→q1→q2→q3→q4→q5`) y el estado final.

Cadenas de prueba:

| cadena | resultado |
|---|---|
| `abcde` | aceptada |
| `abcccde` | aceptada |
| `ac` | rechazada (q1 –c→ qNP) |
| `abde` | rechazada (falta al menos una c) |
| `abcdef` | rechazada (q5 –f→ qNP) |
| `abcfde` | rechazada (timeout en transmisión) |
| `aabcde` | rechazada |
| `""` (vacía) | rechazada (termina en q0) |

### 6.3 Secuencias de eventos por nodo

Al crear la sesión, cada nodo recibe una cadena de eventos generada con la semilla:

- **~80 % válidas**: `ab` + `c`×k + `de`, con k entre 1 y 3.
- **~20 % inválidas**: una cadena válida con una mutación (insertar `f`, eliminar un símbolo o intercambiar dos símbolos adyacentes).

El autómata las valida y el resultado alimenta el motor de alertas.

---

## 7. GNN

### 7.1 Problema

Clasificación binaria **a nivel de nodo**: ŷ ∈ {0 = Normal, 1 = Anómalo}.

### 7.2 Dataset sintético

- **1.000 grafos**, todos con la topología de la sección 2.
- **Atributos por nodo:** tráfico y cpu se generan de forma independiente con una normal truncada en [0, 100], media 62 para servidores, 52 para PC y 42 para IoT, y desviación estándar 25. Se redondean a entero.
  - Con el umbral propio solo, semilla 42 da alrededor de 16 % de nodos Anómalos. Con el criterio extendido el porcentaje será mayor; **hay que medir y reportar el valor real que salga**, y actualizar el documento ("Características de los datos" y "Diseño de la GNN").
- **Latencias:** en cada grafo del dataset se muestrean como enteros uniformes dentro de los rangos de la sección 2.4.
- **Etiqueta:** el criterio extendido de la sección 3.1, calculado sobre la topología completa de cada grafo.
- **Partición por grafos completos:** 700 para entrenamiento, 150 para validación y 150 para prueba, con semilla 42.

### 7.3 Features (6 por nodo)

| feature | valor |
|---|---|
| tipo (one-hot, 3 valores) | [servidor, pc, iot] |
| tráfico | trafico / 100 |
| cpu | cpu / 100 |
| latencia media | promedio de las latencias de sus aristas activas / 22 (si no tiene aristas activas: 1.0) |

### 7.4 Pesos de arista

`edge_weight = 1 / latencia`. El grafo se trata como no dirigido, así que cada arista va en ambos sentidos en `edge_index`.

Nota: `GCNConv` añade un self-loop de peso 1, y con `1/latencia` las aristas lentas (IoT, ≈ 0,05) casi no aportan en la agregación. Se entrena primero así. **Si la GCN no supera al MLP**, se prueba un escalado como `min(1, 5/latencia)` y se documenta como decisión de diseño; no cambia el número de parámetros.

### 7.5 Arquitectura (debe dar exactamente 266 parámetros entrenables)

```
GCNConv(6 → 16) + ReLU + Dropout(0.3)
GCNConv(16 → 8) + ReLU
Linear(8 → 2)
Softmax (solo en inferencia, para obtener p(Normal), p(Anómalo))
```

Conteo: 112 + 136 + 18 = 266.

### 7.6 Entrenamiento

- Entropía cruzada con pesos de clase (inversamente proporcionales a la frecuencia).
- Adam con lr = 0.01.
- Máximo 200 épocas, con parada temprana (paciencia 20, monitoreando la pérdida de validación).
- Semillas fijas: torch, numpy y random = 42.
- **Calibración de p (añadida tras medir el escenario base):** los pesos de clase inversos a la frecuencia multiplican por `razon_pesos` (≈ 3,37) los odds a favor de Anómalo, y con `p ≥ 0,5` sin corregir la GCN marcaba como Anómalos a S1, S2 e IoT1, que la Tabla 2.1 da como Normales. Al guardar el modelo se guarda `razon_pesos`, y la inferencia divide los odds entre ese valor (`calibrar` en `gnn.py`). No usa datos de prueba ni cambia la arquitectura ni el entrenamiento.

### 7.7 Evaluación (se guarda, no se exige mostrarla en la interfaz)

- Precisión, recall y F1 de la clase Anómalo, más la matriz de confusión, sobre los 150 grafos de prueba.
- Baseline: un MLP sin estructura de grafo (6 → 16 → 8 → 2) con el mismo protocolo.
- Las métricas se reportan en tres puntos de operación: calibrado con corte 0,50 (el del prototipo), calibrado con corte 0,40 (Alerta temprana o peor) y sin calibrar.
- Se reportan las métricas de GCN y MLP **tal como salgan**. Se espera que la GCN supere al MLP en recall de Anómalo por la regla de vecindad, pero no se asume: si no lo supera, se explica por qué.

### 7.8 Inferencia en el prototipo

1. Se construye el subgrafo de nodos **no bloqueados** y aristas **no bloqueadas**.
2. Se recalculan las features (la latencia media cambia si se bloquearon aristas).
3. Se ejecuta la GCN.
4. Para cada nodo activo se devuelve `p_anomalo`, ya calibrada (§7.6). Con ella, el escenario base marca como Anómalos exactamente PC2, IoT2 e IoT7; S1 e IoT1 quedan en Alerta temprana.

Si el archivo del modelo entrenado no existe, el backend usa el criterio de umbral como respaldo y lo indica en la respuesta con `fuente: "umbral"`; en el caso normal es `fuente: "gnn"`.

---

## 8. Motor de alertas tempranas (Tabla 12)

p = probabilidad de Anómalo que da la GNN.

| nivel | condición |
|---|---|
| Normal | p < 0,40 **y** secuencia válida |
| Alerta temprana | 0,40 ≤ p < 0,50, **o** secuencia inválida con p < 0,50 |
| Anómalo | p ≥ 0,50 |

Los nodos bloqueados no tienen nivel de alerta: su nivel es "Bloqueado".

---

## 9. Simular fallas

El enunciado pide simular fallas y cambios en los nodos. Desde la interfaz se puede seleccionar un nodo y modificar su tráfico y CPU con sliders de 0 a 100.

Al aplicar el cambio:

- se re-clasifica toda la red con la GNN;
- se recalculan las alertas;
- se muestra qué nodos cambiaron de estado o de nivel.

---

## 10. Modelo de datos (JSON entre API e interfaz)

- **Sesión (entrada):** `semilla, bloqueo_inicial (bool, true), atributos ("base"|"aleatorios"), latencias ("base"|"aleatorias")`. Con `latencias="base"` se usa la Tabla 2.2 (necesario para la Tabla 9); con `"aleatorias"`, cada arista se muestrea como entero uniforme en el rango de su categoría (§2.4) con la semilla.
- **Nodo:** `id, tipo, subtipo, trafico, cpu, bloqueado, clase_umbral (umbral propio), clase_extendida, p_anomalo, estado, nivel_alerta, secuencia, secuencia_valida, x, y`
- **Arista:** `id ("S1-S2"), origen, destino, latencia_ms, rol, bloqueada`
- **Bloqueo:** `orden, tipo ("nodo"|"arista"), elemento, modo ("inicial"|"aleatorio"|"manual")`
- **SecuenciaEventos:** `nodo, cadena, aceptada, recorrido`
- **Clasificacion:** `nodo, clase, p_anomalo, nivel_alerta, fuente`
- **Ruta:** `origen, destino, existe, nodos[], aristas[{id, latencia_ms}], latencia_total, verificacion ("4 + 2 + 20 = 26 ms"), empates[]`

La semilla de la sesión se guarda junto con el historial de bloqueos, de modo que cualquier corrida se pueda reproducir.

---

## 11. Vocabulario obligatorio

- En textos de interfaz, README y comentarios se dice **"sustentación"**, nunca "exposición".
- **"Clase"** es la salida binaria (Normal/Anómalo).
- **"Estado del nodo"** es Normal/Anómalo/Bloqueado.
- **"Estados del autómata"** son q0…q5 y qNP. No se mezclan los términos.
