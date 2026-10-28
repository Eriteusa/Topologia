# API REST (FastAPI). Solo expone la lógica; no sabe nada de la interfaz.
# Uso: uv run uvicorn softcast.api:app --port 8000
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from softcast.automata import definicion, validar
from softcast.sesion import Sesion

app = FastAPI(title="SoftCast")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

estado = {"sesion": None}


class SesionIn(BaseModel):
    semilla: int = 42
    bloqueo_inicial: bool = True
    atributos: Literal["base", "aleatorios"] = "base"
    latencias: Literal["base", "aleatorias"] = "base"


class RutaIn(BaseModel):
    origen: str
    destino: str


class BloqueoIn(BaseModel):
    tipo: Literal["nodo", "arista"]
    elemento: str


class AtributosIn(BaseModel):
    trafico: int = Field(ge=0, le=100)
    cpu: int = Field(ge=0, le=100)


class CadenaIn(BaseModel):
    cadena: str


def sesion_actual():
    if estado["sesion"] is None:
        estado["sesion"] = Sesion()
    return estado["sesion"]


def o_400(funcion, *args):
    try:
        return funcion(*args)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/api/sesion")
def crear_sesion(datos: SesionIn):
    estado["sesion"] = Sesion(datos.semilla, datos.bloqueo_inicial, datos.atributos, datos.latencias)
    return estado["sesion"].red()


@app.get("/api/red")
def obtener_red():
    return sesion_actual().red()


@app.post("/api/ruta")
def calcular_ruta(datos: RutaIn):
    return o_400(sesion_actual().ruta, datos.origen, datos.destino)


@app.post("/api/bloqueos")
def bloquear(datos: BloqueoIn):
    sesion = sesion_actual()
    o_400(sesion.bloquear, datos.tipo, datos.elemento)
    return {"red": sesion.red(), "ruta": sesion.ruta_actual()}


@app.post("/api/bloqueos/aleatorio")
def bloquear_al_azar(datos: RutaIn):
    sesion = sesion_actual()
    bloqueo = o_400(sesion.bloqueo_aleatorio, datos.origen, datos.destino)
    return {"bloqueo": bloqueo, "red": sesion.red(), "ruta": sesion.ruta_actual()}


@app.post("/api/nodos/{nodo}/atributos")
def simular_falla(nodo: str, datos: AtributosIn):
    sesion = sesion_actual()
    cambiaron = o_400(sesion.simular_falla, nodo, datos.trafico, datos.cpu)
    return {"red": sesion.red(), "cambiaron": cambiaron}


@app.post("/api/automata/validar")
def validar_cadena(datos: CadenaIn):
    return validar(datos.cadena)


@app.get("/api/automata")
def obtener_automata():
    return definicion()


@app.post("/api/reiniciar")
def reiniciar():
    estado["sesion"] = sesion_actual().reiniciada()
    return estado["sesion"].red()
