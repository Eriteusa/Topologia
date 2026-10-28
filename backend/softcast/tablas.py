# Utilidades comunes de los scripts que escriben en salidas/.
import csv
from pathlib import Path

SALIDAS = Path(__file__).resolve().parent.parent / "salidas"


def coma(x, decimales=2):
    """0.4567 → "0,46"."""
    return f"{x:.{decimales}f}".replace(".", ",")


def variacion(x):
    """0.12 → "+0,12", -0.06 → "−0,06"."""
    return ("+" if x >= 0 else "−") + coma(abs(x))


def tabla_md(cabecera, filas):
    """Tabla en Markdown; las celdas se convierten a texto y se escapa la barra vertical."""
    def fila(celdas):
        return "| " + " | ".join(str(c).replace("|", "\\|") for c in celdas) + " |"

    return "\n".join([fila(cabecera), fila(["---"] * len(cabecera))] + [fila(f) for f in filas]) + "\n"


def escribir_csv(ruta, cabecera, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(cabecera)
        escritor.writerows(filas)
