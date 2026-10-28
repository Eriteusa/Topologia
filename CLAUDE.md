# CLAUDE.md — Instrucciones de construcción del prototipo SoftCast

Lee primero **`CONTEXTO.md`**: es la especificación completa, con datos exactos, reglas y casos de prueba. Este archivo dice **cómo** construirlo. `IMPLEMENTACION_CORRECTA.md` explica el porqué de los ajustes (criterio de vecindad, latencias aleatorias, validación).

## Reglas de trabajo

- **Trabaja por fases**, en el orden de abajo. Al terminar cada fase, corre sus pruebas, muestra un resumen corto (qué quedó, qué pruebas pasaron) y **espera confirmación** antes de seguir.
- Los datos de `CONTEXTO.md` (latencias, umbrales, δ, arquitectura) son fijos porque ya están en un documento entregado. **No los cambies.** Si algo parece inconsistente, pregunta. La única extensión es el criterio de vecindad de §3.1, que conserva el umbral original y la Tabla 2.1.
- Proyecto local; todavía no hay repositorio remoto. Inicializa git y haz commits pequeños por fase, pero **no hagas push**.
- Idioma: identificadores de dominio en español (`latencia_ms`, `bloqueado`, `recorrido`), textos de interfaz en español y comentarios en español, breves.
- Usa siempre "sustentación", nunca "exposición".
- **Estilo de interfaz** (el que el profesor aprobó en el proyecto de la pinza): minimalista y funcional; **sin texto narrativo, subtítulos ni frases de tutorial** en la UI; modo claro; mensajes solo cuando hay un resultado que mostrar. Los textos de interfaz nombran cosas (paneles, campos, resultados), no explican cómo usarlas.

## Entorno

- **Sistema:** Ubuntu 26.04 (paquetes del sistema con `apt`, no `dnf`). El Python del sistema es 3.14, que puede no ser compatible con PyTorch, así que **usa `uv` con Python 3.12** para el backend. `uv` puede no estar instalado: `curl -LsSf https://astral.sh/uv/install.sh | sh`, luego `uv python install 3.12` y `uv venv --python 3.12`.
- **PyTorch:** versión CPU (`uv pip install torch --index-url https://download.pytorch.org/whl/cpu`). **PyTorch Geometric:** solo `torch_geometric`, sin extensiones compiladas (no hacen falta para `GCNConv`).
- **Otras dependencias del backend:** `networkx numpy scipy scikit-learn fastapi uvicorn pydantic pytest httpx matplotlib` (`httpx` para `TestClient`, `matplotlib` para las figuras).
- **Frontend:** Node ya está instalado vía nvm (v24). Si falta: `sudo apt install nodejs npm`.

## Stack

| capa | tecnología |
|---|---|
| Interfaz | Next.js (App Router) + TypeScript + Tailwind CSS; el grafo se dibuja en **SVG propio** (sin librerías de grafos en el frontend) |
| API | FastAPI + Pydantic + Uvicorn |
| Lógica | Python 3.12: NetworkX, NumPy, SciPy (`truncnorm`), PyTorch, PyTorch Geometric, scikit-learn |
| Pruebas | pytest |

## Estructura

```
softcast/
├── CLAUDE.md
├── CONTEXTO.md
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── softcast/
│   │   ├── __init__.py
│   │   ├── datos_base.py     # nodos, aristas y posiciones de CONTEXTO §2 (única fuente de verdad)
│   │   ├── umbral.py         # criterio §3: umbral_propio y clase_extendida (§3.1)
│   │   ├── grafo.py          # construcción NetworkX, bloqueos, Dijkstra con desempate, verificación
│   │   ├── automata.py       # AFD §6: δ como diccionario, validar(cadena), exportar .jff
│   │   ├── secuencias.py     # generador de cadenas por nodo §6.3
│   │   ├── generador.py      # dataset sintético §7.2
│   │   ├── gnn.py            # modelo GCN, MLP baseline, construcción de Data, inferencia
│   │   ├── entrenar.py       # script: genera dataset, entrena, evalúa, guarda artefactos
│   │   ├── alertas.py        # reglas §8
│   │   ├── sesion.py         # estado en memoria: semilla, bloqueos, atributos, historial
│   │   ├── api.py            # FastAPI
│   │   ├── figuras.py        # grafo_red.png y tabla_rutas
│   │   └── validacion.py     # tablas de validación para el documento
│   ├── modelos/              # modelo_gcn.pt, metricas.json (generados)
│   ├── salidas/              # figuras y tablas generadas (curva, matriz, grafo)
│   ├── jflap/automata_softcast.jff
│   └── tests/
└── frontend/
    └── (proyecto Next.js)
```

## Fases

### Fase 1 — Núcleo de grafo y rutas

1. `datos_base.py` con los datos exactos de CONTEXTO §2.1–2.3.
2. `grafo.py`:
   - `construir_grafo()`
   - `aplicar_bloqueos(G, bloqueos)`
   - `ruta_optima(G, origen, destino)`, con el desempate de §5.4; devuelve el objeto `Ruta` de §10 con `verificacion` y `empates`.
3. **Pruebas** (`tests/test_grafo.py`):
   - 15 nodos y 26 aristas; grado medio 3,47 (±0,01).
   - Conectividad por nodos = 2 y por aristas = 2; sin puentes ni nodos de articulación.
   - Exactamente los 7 pares desconectantes de §5.1.
   - La Tabla 9 completa de §5.6, con rutas, latencias y "sin camino" en la iteración 6. En la iteración 4, `empates` debe contener la ruta de 6 saltos.
   - Para cada ruta, la suma del desglose es igual a `latencia_total` y cada latencia coincide con la tabla 2.2.

### Fase 2 — Autómata

1. `automata.py`:
   - los 5 parámetros declarados como datos **al inicio del archivo, antes de cualquier función**, cada uno con su nombre formal en un comentario: `Q`, `SIGMA` (Σ), `Q0` (q0), `F` y por último `DELTA` (δ);
   - la δ completa de §6.1 como diccionario;
   - `validar(cadena) -> {aceptada, recorrido, estado_final, error?}`.
2. `exportar_jff(ruta)`: genera el XML de JFLAP (`<structure><type>fa</type><automaton>…`) con los 7 estados, q0 inicial, q5 final y todas las transiciones. Coloca los estados en línea y qNP debajo. Guárdalo en `backend/jflap/automata_softcast.jff`.
3. `secuencias.py` según §6.3.
4. **Pruebas**:
   - todas las cadenas de §6.2;
   - que δ tenga las 42 entradas;
   - que el `.jff` sea XML válido con 7 estados.

### Fase 3 — Dataset y GNN

1. `umbral.py` con `umbral_propio` y `clase_extendida` según §3 y §3.1; `generador.py` según §7.2, etiquetando con `clase_extendida`.
2. `gnn.py`:
   - `GCNSoftCast` exactamente como en §7.5;
   - `MLPBase`;
   - `a_data(nodos, aristas)`, que construye el `torch_geometric.data.Data` con las features de §7.3 y los pesos 1/latencia;
   - `predecir(modelo, nodos_activos, aristas_activas)`.
3. `entrenar.py` (se ejecuta con `uv run python -m softcast.entrenar`), según §7.6–7.7. Guarda:
   - `modelos/modelo_gcn.pt`, `modelos/modelo_mlp.pt`;
   - `modelos/metricas.json`: % real de Anómalos del dataset (con el criterio extendido), métricas de GCN y MLP, matriz de confusión y número de épocas;
   - `salidas/curva_perdida.png` y `salidas/matriz_confusion.png`.
4. **Pruebas**:
   - `umbral_propio` reproduce la clase de la tabla 2.1;
   - `clase_extendida` también reproduce la tabla 2.1 en el escenario base (solo PC2, IoT2 e IoT7 son Anómalos);
   - un nodo con carga media (cpu o tráfico ≥ 60) y ≥ 50 % de vecinos anómalos es Anómalo, y deja de serlo si se bloquean esos vecinos;
   - la GCN tiene exactamente 266 parámetros entrenables;
   - `a_data` produce `x` de forma (15, 6) y `edge_index` con 52 columnas en el grafo completo;
   - con un nodo bloqueado, `x` es (14, 6) y se eliminan sus aristas.

### Fase 4 — Alertas, sesión y API

1. `alertas.py` según §8.
2. `sesion.py`: estado en memoria de una sola sesión.
   - Al crearla con una semilla: atributos del escenario base (tabla 2.1), **2 nodos bloqueados al azar** (§5.1) y secuencias por nodo.
   - Debe permitir crear la sesión **sin** bloqueo inicial (flag `bloqueo_inicial=false`), que se usa para reproducir la Tabla 9.
   - Con `latencias="aleatorias"`, cada arista se muestrea como entero uniforme en el rango de su categoría (§2.4) con la semilla; con `"base"` usa la Tabla 2.2.
3. `api.py`, con CORS para `http://localhost:3000`:

| método | ruta | descripción |
|---|---|---|
| POST | `/api/sesion` | `{semilla, bloqueo_inicial: bool=true, atributos: "base"|"aleatorios", latencias: "base"|"aleatorias"}` → red completa |
| GET | `/api/red` | nodos (con estado, p, nivel), aristas, historial de bloqueos, semilla |
| POST | `/api/ruta` | `{origen, destino}` → Ruta (§10); error 400 si origen o destino están bloqueados |
| POST | `/api/bloqueos` | `{tipo, elemento}` → bloqueo manual; devuelve la red actualizada y la nueva ruta si hay una ruta activa |
| POST | `/api/bloqueos/aleatorio` | `{origen, destino}` → bloquea un elemento de la ruta vigente (§5.2) |
| POST | `/api/nodos/{id}/atributos` | `{trafico, cpu}` → simular falla (§9); devuelve la red y la lista de nodos que cambiaron |
| POST | `/api/automata/validar` | `{cadena}` → resultado de §6.2 |
| GET | `/api/automata` | definición formal (Q, Σ, δ, q0, F) para dibujar el diagrama |
| POST | `/api/reiniciar` | vuelve a crear la sesión con la misma semilla |

   Cada respuesta que cambia la red recalcula la clasificación (GNN sin nodos bloqueados, §7.8) y las alertas.
4. **Pruebas** con `TestClient`:
   - crear sesión → exactamente 2 nodos bloqueados y reproducibles con la misma semilla;
   - pedir una ruta con origen bloqueado → 400;
   - flujo de bloqueos que reproduce la Tabla 9 usando `bloqueo_inicial=false`;
   - la simulación de falla en PC1 (cpu 95) lo vuelve Anómalo;
   - con `latencias="aleatorias"` cada latencia cae en el rango de su categoría y la misma semilla repite los valores;
   - bloquear manualmente el origen o el destino deja la ruta en "Sin camino disponible" sin error.

### Fase 5 — Interfaz (Next.js)

Es una sola página con dos columnas: a la izquierda el grafo (≈65 %) y a la derecha los paneles. Debe verse limpia y académica, con fondo claro y tipografía legible para proyectar en la sustentación.

1. **Grafo SVG**:
   - posiciones de §2.3, latencia sobre cada arista y redundantes punteadas;
   - colores de §4;
   - ruta vigente resaltada (aristas gruesas en naranja);
   - aristas bloqueadas en rojo punteado con una ✕ en el punto medio;
   - leyenda abajo.
   - **Clic en nodo o arista** → popover junto al elemento con sus detalles (nodo: tipo, tráfico, CPU, p_anomalo, nivel, secuencia; arista: origen, destino, latencia, rol) y botón **"Bloquear"**, que llama a `POST /api/bloqueos` con modo manual.
   - Cada arista lleva encima una línea transparente más gruesa (≈ 16 px) como área de clic; los nodos son enfocables con el teclado (Tab y Enter).
   - No hay desbloqueo individual: el único camino es "Reiniciar".
2. **Panel Controles**:
   - campo de semilla y botón "Nueva sesión";
   - selector de atributos (base/aleatorios);
   - selects de origen y destino, solo con nodos no bloqueados;
   - botones "Calcular ruta", "Bloqueo aleatorio" y "Reiniciar".
3. **Panel Ruta**:
   - ruta como cadena de ids;
   - latencia total;
   - **verificación** `4 + 2 + 20 = 26 ms`;
   - aviso si hubo empate y cuál se descartó;
   - mensaje claro de "Sin camino disponible".
4. **Panel Historial de bloqueos**: tabla con orden, tipo, elemento y modo; los 2 iniciales aparecen marcados como "inicial".
5. **Panel Clasificación y alertas**:
   - lista de nodos con estado, p_anomalo (barra) y nivel;
   - resalta los que cambiaron tras el último bloqueo o la última simulación;
   - indicador de `fuente` (GNN/umbral).
6. **Panel Simular falla**: con un nodo seleccionado, sliders de tráfico y CPU y botón "Aplicar".
7. **Panel Autómata**:
   - input de cadena, botones con ejemplos (`abcde`, `abcccde`, `ac`, `abde`, `abcfde`);
   - diagrama SVG de los 7 estados: q0 con flecha de entrada, q5 con doble círculo, aristas hacia qNP tenues (líneas finas desde cada estado, no 42 flechas);
   - el recorrido se anima paso a paso (≈ 450 ms por símbolo), iluminando el estado activo y la transición tomada, y termina con el resultado aceptada/rechazada;
   - **los 5 parámetros visibles en la interfaz** (se leen de `GET /api/automata`): Q, Σ, q0, F y la tabla δ de 7 × 6, con las celdas recorridas resaltadas;
   - al seleccionar un nodo, opción de validar su secuencia.
8. URL de la API en `NEXT_PUBLIC_API_URL` (por defecto `http://localhost:8000`).

### Fase 6 — Cierre

1. **`README.md`**: requisitos, instalación en Ubuntu (uv, Node), cómo entrenar, cómo correr backend y frontend, cómo correr pruebas y cómo reproducir la Tabla 9.
2. **Script `salidas`** (`uv run python -m softcast.figuras`), que genera:
   - `salidas/grafo_red.png`: la topología con la misma estética de la interfaz;
   - `salidas/tabla_rutas.csv` y `salidas/tabla_rutas.md`: corrida de la Tabla 9 con la columna de verificación de latencias.
2. **Script de validación** (`uv run python -m softcast.validacion`), con la evidencia para el documento de validación y resultados:
   - `salidas/tabla_automata.csv` y `.md`: cadenas de §6.2 con recorrido, resultado y motivo;
   - `salidas/tabla_clasificacion.md`: atributos y clase de los 15 nodos (umbral propio, clase extendida y GNN);
   - `salidas/metricas_gnn.md`: precisión, recall y F1 de Anómalo, GCN vs. MLP, matriz de confusión;
   - `salidas/efecto_bloqueo.md`: por cada bloqueo de nodo, qué vecinos cambiaron `p_anomalo` y si cambió su clase;
   - `salidas/efecto_falla.md`: simulaciones de falla (por ejemplo PC1 con cpu 95) y la red resultante.
3. **`.gitignore`**: `.venv`, `node_modules`, `.next`, `__pycache__`. **No ignorar** `modelos/` ni `salidas/`.
4. Corre todas las pruebas y reporta el resultado final.

## Criterios de aceptación

- `pytest` pasa completo.
- Al abrir la app aparecen exactamente 2 nodos grises bloqueados. Con la misma semilla se obtienen siempre los mismos 2.
- El jurado puede bloquear cualquier nodo o arista con un clic, y la ruta se recalcula al instante (< 3 s).
- Toda ruta muestra su verificación de latencia, y cada valor coincide con la tabla 2.2.
- El autómata acepta y rechaza exactamente lo indicado en §6.2 y el `.jff` abre en JFLAP.
- La clasificación excluye los nodos bloqueados y muestra cambios en los vecinos.
