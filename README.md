# SoftCast

Prototipo de la Experiencia Final de Lenguajes y Autómatas: la red de la empresa SoftCast modelada como grafo, una GNN que clasifica cada nodo como Normal o Anómalo, un autómata finito que valida la secuencia de eventos de cada dispositivo y bloqueo de nodos o enlaces con recálculo de la ruta óptima (Dijkstra).

- **`backend/`**: Python 3.12 con NetworkX, PyTorch y PyTorch Geometric. Expone una API REST (FastAPI).
- **`frontend/`**: Next.js con TypeScript y Tailwind. El grafo se dibuja en SVG propio.
- Especificación completa en `CONTEXTO.md`; instrucciones de construcción en `CLAUDE.md`.

## Requisitos

Probado en Ubuntu 26.04.

- `git` y `curl`
- [`uv`](https://docs.astral.sh/uv/) para el entorno de Python
- Node.js LTS con `npm` (por ejemplo con [nvm](https://github.com/nvm-sh/nvm))

## Instalación

### Backend

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # instala uv; abre una terminal nueva después
cd backend
uv python install 3.12
uv venv --python 3.12
uv pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
uv pip install -e . pytest httpx
```

PyTorch se instala primero y en su versión CPU para no descargar la build con CUDA. Los comandos siguientes usan `uv run --no-sync`, que ejecuta dentro de este entorno sin volver a resolver dependencias.

### Frontend

```bash
cd frontend
npm install
```

## Entrenar la GNN

El repositorio ya incluye los modelos entrenados en `backend/modelos/`. Para reentrenar (unos segundos en CPU):

```bash
cd backend
uv run --no-sync python -m softcast.entrenar
```

Genera 1.000 grafos sintéticos con semilla 42, entrena la GCN y el MLP de comparación y guarda en `backend/modelos/` los modelos y `metricas.json`, y en `backend/salidas/` la curva de pérdida y las matrices de confusión.

## Ejecutar

Se necesitan dos terminales.

```bash
# 1. API (puerto 8000)
cd backend
uv run --no-sync uvicorn softcast.api:app --port 8000

# 2. Interfaz (puerto 3000)
cd frontend
npm run dev
```

Abre <http://localhost:3000>. La documentación de la API está en <http://localhost:8000/docs>.

- El CORS de la API solo admite el origen `http://localhost:3000`, así que la interfaz debe correr en ese puerto.
- Si el puerto 8000 está ocupado por otro programa, levanta la API en otro (por ejemplo `--port 8010`) y arranca la interfaz con `NEXT_PUBLIC_API_URL=http://localhost:8010 npm run dev`.

## Pruebas

```bash
cd backend
uv run --no-sync pytest
```

Cubren el grafo y las rutas, el autómata y el archivo `.jff`, las secuencias, el dataset, los modelos, las alertas, la sesión, la API y los scripts de salidas.

## Reproducir la Tabla 9

Origen PC3, destino IoT4, sin bloqueo inicial; en cada paso se bloquea una arista de la ruta vigente.

**Por la interfaz:**

1. Desmarca **Bloqueo inicial** y pulsa **Nueva sesión**.
2. Elige origen `PC3` y destino `IoT4`, y pulsa **Calcular ruta**: `4 + 2 + 20 = 26 ms`.
3. Haz clic en cada arista y pulsa **Bloquear arista**, en este orden: `S1–S2`, `S2–PC3`, `IoT4–IoT5`, `PC2–PC3`, `PC3–PC4`.
4. Las latencias sucesivas son 30, 34, 54 y 54 ms, y al final aparece «Sin camino disponible». En la cuarta ruta se avisa el empate a 54 ms con la ruta de 6 saltos que se descartó.

**Por línea de comandos:**

```bash
cd backend
uv run --no-sync python -m softcast.figuras     # escribe salidas/tabla_rutas.csv y .md
```

## Salidas para el documento

Todas se escriben en `backend/salidas/`.

```bash
cd backend
uv run --no-sync python -m softcast.figuras       # grafo_red.png, tabla_rutas.csv, tabla_rutas.md
uv run --no-sync python -m softcast.validacion    # tablas de validación (necesita backend/modelos/)
```

| archivo | contenido |
|---|---|
| `grafo_red.png` | topología de 15 nodos y 26 aristas con latencias |
| `tabla_rutas.csv` / `.md` | corrida de la Tabla 9 con la verificación de latencias |
| `tabla_automata.csv` / `.md` | cadenas de prueba con recorrido, resultado y motivo |
| `tabla_clasificacion.md` | clase por umbral, clase extendida y resultado de la GNN para los 15 nodos |
| `metricas_gnn.md` | precisión, recall y F1 de la GCN frente al MLP, con matrices de confusión |
| `efecto_bloqueo.md` | por cada nodo bloqueado, qué nodos cambian de probabilidad y si cambia la etiqueta |
| `efecto_falla.md` | simulaciones de falla y sus efectos |
| `curva_perdida.png`, `matriz_confusion.png` | las genera `softcast.entrenar` |

## Autómata en JFLAP

`backend/jflap/automata_softcast.jff` se abre con JFLAP y contiene los 7 estados y las 42 transiciones. Para regenerarlo:

```bash
cd backend
uv run --no-sync python -m softcast.automata
```

## Estructura

```
softcast/
├── CONTEXTO.md, CLAUDE.md       especificación y guía de construcción
├── backend/
│   ├── softcast/                datos_base, umbral, grafo, automata, secuencias, generador,
│   │                            gnn, entrenar, alertas, sesion, api, figuras, validacion
│   ├── tests/
│   ├── modelos/                 modelos entrenados y metricas.json
│   ├── salidas/                 figuras y tablas generadas
│   └── jflap/                   automata_softcast.jff
└── frontend/                    interfaz Next.js
```
