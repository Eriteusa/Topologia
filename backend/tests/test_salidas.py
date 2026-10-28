import csv

from softcast import figuras, validacion
from softcast.tablas import coma, tabla_md, variacion


def test_formatos_numericos():
    assert coma(0.4567) == "0,46"
    assert variacion(0.12) == "+0,12" and variacion(-0.06) == "−0,06"
    assert tabla_md(["a", "b"], [[1, "x|y"]]) == "| a | b |\n| --- | --- |\n| 1 | x\\|y |\n"


def test_tabla_de_rutas_reproduce_la_tabla_9(tmp_path):
    figuras.escribir_tabla_rutas(tmp_path)
    with open(tmp_path / "tabla_rutas.csv", encoding="utf-8") as f:
        filas = list(csv.reader(f))
    cuerpo = filas[1:]
    assert len(cuerpo) == 6
    assert [f[3] for f in cuerpo] == ["26", "30", "34", "54", "54", "—"]
    assert cuerpo[0][4] == "4 + 2 + 20 = 26 ms"
    assert cuerpo[3][5] == "PC3 → PC4 → PC5 → PC6 → IoT6 → S1 → IoT4"  # el empate descartado
    assert cuerpo[5][2] == "Sin camino disponible"
    assert "Sin camino disponible" in (tmp_path / "tabla_rutas.md").read_text(encoding="utf-8")


def test_figura_del_grafo(tmp_path):
    figuras.dibujar_grafo(tmp_path)
    imagen = (tmp_path / "grafo_red.png").read_bytes()
    assert imagen[:8] == b"\x89PNG\r\n\x1a\n" and len(imagen) > 50_000


def test_tabla_del_automata(tmp_path):
    validacion.tabla_automata(tmp_path)
    with open(tmp_path / "tabla_automata.csv", encoding="utf-8") as f:
        filas = {f_[0]: f_ for f_ in csv.reader(f)}
    assert filas["abcde"][3] == "Aceptada" and filas["abcccde"][3] == "Aceptada"
    assert all(filas[c][3] == "Rechazada" for c in ["ac", "abde", "abcdef", "abcfde", "aabcde", "(vacía)", "abz"])
    assert "fuera del alfabeto" in filas["abz"][4]


def test_validacion_completa_escribe_todos_los_archivos(tmp_path):
    validacion.main(tmp_path)
    nombres = {p.name for p in tmp_path.iterdir()}
    assert nombres == {
        "tabla_automata.csv", "tabla_automata.md", "tabla_clasificacion.md",
        "metricas_gnn.md", "efecto_bloqueo.md", "efecto_falla.md",
    }
    clasificacion = (tmp_path / "tabla_clasificacion.md").read_text(encoding="utf-8")
    assert "coincide con la clase por umbral de la Tabla 3 en 15 de 15 nodos" in clasificacion
    metricas = (tmp_path / "metricas_gnn.md").read_text(encoding="utf-8")
    assert "266" in metricas and "Lectura" in metricas and "Matrices de confusión" in metricas
    falla = (tmp_path / "efecto_falla.md").read_text(encoding="utf-8")
    assert "| PC1 | 35 → 35 | 42 → 95 | Normal → Anómalo |" in falla
    bloqueo = (tmp_path / "efecto_bloqueo.md").read_text(encoding="utf-8")
    assert bloqueo.count("\n| ") >= 16 and "La etiqueta cambia en" in bloqueo
