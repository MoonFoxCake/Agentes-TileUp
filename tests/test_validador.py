"""Pruebas del validador independiente.

Cubren: aceptación de soluciones legales, rechazo de cada tipo de ilegalidad,
la regla de fusión aclarada por el profesor (p pertenece a G y la ficha
resultante queda en p), el comportamiento por línea de comandos y la
concordancia entre el validador y el motor sobre partidas aleatorias.
"""
import os
import random
import subprocess
import sys

import pytest

from tileup.motor import (
    Instancia, estado_inicial, aplicar_accion, acciones_legales,
    es_meta, celdas_ocupadas, ficha_mayor, escribir_solucion,
)
from tileup.validador import validar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Instancia y solución del ejemplo del enunciado
INST_PDF = Instancia(
    n=4, k=3, m=6,
    secuencia=((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4)),
)
SOL_PDF = "0 0 0\n1 1 1\n2 0 1\n3 2 2\n4 0 2\n5 1 2\n# colocadas=6 ocupadas=3 mayor=6\n"


def escribir(tmp_path, texto, nombre="sol.txt"):
    ruta = tmp_path / nombre
    ruta.write_text(texto)
    return str(ruta)


# --- Aceptación ------------------------------------------------------------

def test_acepta_ejemplo_del_enunciado(tmp_path):
    ok, msg, met = validar(INST_PDF, escribir(tmp_path, SOL_PDF))
    assert ok, msg
    assert met["colocadas"] == 6
    assert met["ocupadas"] == 3
    assert met["mayor"] == 6
    assert met["meta"] is True
    assert met["derrota"] is False


def test_acepta_solucion_sin_linea_resumen(tmp_path):
    sin_resumen = "\n".join(SOL_PDF.splitlines()[:-1]) + "\n"
    ok, msg, met = validar(INST_PDF, escribir(tmp_path, sin_resumen))
    assert ok, msg
    assert met["colocadas"] == 6


def test_acepta_solucion_parcial_con_derrota(tmp_path):
    # Tablero 2x2, 5 fichas; en patrón de ajedrez no hay fusiones y se llena.
    inst = Instancia(n=2, k=2, m=5,
                     secuencia=((1, 1), (2, 1), (2, 2), (1, 2), (1, 3)))
    sol = "0 0 0\n1 0 1\n2 1 0\n3 1 1\n# colocadas=4 ocupadas=4 mayor=2\n"
    ok, msg, met = validar(inst, escribir(tmp_path, sol))
    assert ok, msg
    assert met["colocadas"] == 4
    assert met["meta"] is False
    assert met["derrota"] is True


# --- Regla de fusión (aclaración del profesor) -----------------------------

def test_fusion_queda_en_la_celda_de_la_ultima_ficha(tmp_path):
    """Dos fichas del mismo color: la fusionada queda en p, no en el vecino.
    Se comprueba con una tercera ficha: si la fusión hubiera quedado en (0,0),
    la celda (0,1) estaría libre y la jugada sería legal; no lo es."""
    inst = Instancia(n=3, k=2, m=3, secuencia=((1, 2), (1, 3), (2, 1)))
    # (0,1) debe estar ocupada tras la fusión, así que repetirla es ilegal
    ok, msg, _ = validar(inst, escribir(tmp_path, "0 0 0\n1 0 1\n2 0 1\n"))
    assert not ok
    assert "ocupada" in msg
    # y (0,0) debe haber quedado libre, así que usarla es legal
    ok, msg, met = validar(inst, escribir(tmp_path, "0 0 0\n1 0 1\n2 0 0\n"))
    assert ok, msg
    assert met["ocupadas"] == 2


def test_fusion_en_L_une_tres_fichas_con_p_en_el_grupo(tmp_path):
    inst = Instancia(n=3, k=2, m=3, secuencia=((1, 1), (1, 2), (1, 4)))
    sol = "0 0 0\n1 1 1\n2 0 1\n"          # (0,0) y (1,1) se unen por (0,1)
    ok, msg, met = validar(inst, escribir(tmp_path, sol))
    assert ok, msg
    assert met["ocupadas"] == 1
    assert met["mayor"] == 7


def test_fusion_no_encadena(tmp_path):
    """Colores distintos separan los grupos: no hay fusión entre ellos."""
    inst = Instancia(n=4, k=2, m=3, secuencia=((1, 1), (2, 9), (1, 1)))
    ok, msg, met = validar(inst, escribir(tmp_path, "0 0 0\n1 0 1\n2 0 2\n"))
    assert ok, msg
    assert met["ocupadas"] == 3


# --- Rechazos --------------------------------------------------------------

def test_rechaza_celda_ocupada(tmp_path):
    ok, msg, met = validar(INST_PDF, escribir(tmp_path, "0 0 0\n1 0 0\n"))
    assert not ok and "ocupada" in msg and met is None


def test_rechaza_indice_fuera_de_orden(tmp_path):
    ok, msg, _ = validar(INST_PDF, escribir(tmp_path, "0 0 0\n2 1 1\n"))
    assert not ok and "índice" in msg


def test_rechaza_indice_que_no_empieza_en_cero(tmp_path):
    ok, msg, _ = validar(INST_PDF, escribir(tmp_path, "1 0 0\n"))
    assert not ok and "índice" in msg


def test_rechaza_celda_fuera_del_tablero(tmp_path):
    ok, msg, _ = validar(INST_PDF, escribir(tmp_path, "0 4 0\n"))
    assert not ok and "fuera" in msg
    ok, msg, _ = validar(INST_PDF, escribir(tmp_path, "0 -1 0\n"))
    assert not ok and "fuera" in msg


def test_rechaza_mas_colocaciones_que_fichas(tmp_path):
    inst = Instancia(n=3, k=1, m=1, secuencia=((1, 1),))
    ok, msg, _ = validar(inst, escribir(tmp_path, "0 0 0\n1 2 2\n"))
    assert not ok and "más colocaciones" in msg


def test_rechaza_linea_con_cantidad_incorrecta_de_enteros(tmp_path):
    ok, msg, _ = validar(INST_PDF, escribir(tmp_path, "0 0\n"))
    assert not ok and "3 enteros" in msg


def test_rechaza_valores_no_enteros(tmp_path):
    ok, msg, _ = validar(INST_PDF, escribir(tmp_path, "0 a 0\n"))
    assert not ok and "enteros" in msg


@pytest.mark.parametrize("resumen", [
    "# colocadas=6 ocupadas=9 mayor=6",
    "# colocadas=5 ocupadas=3 mayor=6",
    "# colocadas=6 ocupadas=3 mayor=99",
])
def test_rechaza_resumen_que_no_coincide(tmp_path, resumen):
    lineas = SOL_PDF.splitlines()[:-1] + [resumen]
    ok, msg, met = validar(INST_PDF, escribir(tmp_path, "\n".join(lineas) + "\n"))
    assert not ok
    assert "resumen" in msg
    assert met["ocupadas"] == 3          # devuelve lo realmente reproducido


def test_rechaza_archivo_inexistente():
    ok, msg, met = validar(INST_PDF, "/ruta/que/no/existe.txt")
    assert not ok and met is None


def test_rechaza_archivo_binario(tmp_path):
    ruta = tmp_path / "bin.txt"
    ruta.write_bytes(b"\xff\xfe\x00\x80\x81")
    ok, msg, met = validar(INST_PDF, str(ruta))
    assert not ok and met is None


# --- Independencia del motor ------------------------------------------------

def test_validador_no_reutiliza_la_logica_de_juego_del_motor():
    ruta = os.path.join(ROOT, "tileup", "validador.py")
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()
    for nombre in ("aplicar_accion", "_componente_conexa", "_tablero_con_cambios",
                   "es_derrota", "es_meta", "celdas_ocupadas", "ficha_mayor"):
        assert nombre not in codigo, f"el validador usa {nombre} del motor"


# --- Concordancia motor / validador sobre partidas aleatorias ---------------

def _partida_aleatoria(rng):
    n = rng.randint(1, 5)
    k = rng.randint(1, 4)
    m = rng.randint(1, 3 * n * n)
    secuencia = tuple((rng.randint(1, k), rng.randint(1, 9)) for _ in range(m))
    inst = Instancia(n=n, k=k, m=m, secuencia=secuencia)
    estado = estado_inicial(inst)
    jugadas = []
    while not es_meta(estado, inst):
        libres = acciones_legales(estado, inst)
        if not libres:
            break
        celda = rng.choice(libres)
        jugadas.append((estado.indice_siguiente, celda[0], celda[1]))
        estado = aplicar_accion(estado, inst, celda)
    return inst, jugadas, estado


def test_validador_y_motor_coinciden_en_300_partidas_aleatorias(tmp_path):
    rng = random.Random(2026)
    derrotas = 0
    for _ in range(300):
        inst, jugadas, estado = _partida_aleatoria(rng)
        ruta = str(tmp_path / "sol.txt")
        escribir_solucion(ruta, jugadas, estado)
        ok, msg, met = validar(inst, ruta)
        assert ok, msg
        assert met["colocadas"] == len(jugadas)
        assert met["ocupadas"] == celdas_ocupadas(estado)
        assert met["mayor"] == ficha_mayor(estado)
        assert met["meta"] == es_meta(estado, inst)
        derrotas += not met["meta"]
    assert derrotas > 0                   # el muestreo incluyó derrotas


# --- Línea de comandos -------------------------------------------------------

def _cli(*args):
    return subprocess.run([sys.executable, "-m", "tileup.validador", *args],
                          capture_output=True, text=True, cwd=ROOT)


def test_cli_legal_devuelve_0(tmp_path):
    inst = tmp_path / "i.txt"
    inst.write_text("4 3\n6\n1 2\n2 1\n1 3\n3 1\n1 1\n2 4\n")
    r = _cli(str(inst), escribir(tmp_path, SOL_PDF))
    assert r.returncode == 0
    assert r.stdout.startswith("LEGAL")


def test_cli_ilegal_devuelve_1(tmp_path):
    inst = tmp_path / "i.txt"
    inst.write_text("4 3\n6\n1 2\n2 1\n1 3\n3 1\n1 1\n2 4\n")
    r = _cli(str(inst), escribir(tmp_path, "0 0 0\n1 0 0\n"))
    assert r.returncode == 1
    assert "ILEGAL" in r.stdout


def test_cli_instancia_mal_formada_devuelve_2_sin_traceback(tmp_path):
    inst = tmp_path / "i.txt"
    inst.write_text("esto no es una instancia\n")
    r = _cli(str(inst), escribir(tmp_path, SOL_PDF))
    assert r.returncode == 2
    assert "Traceback" not in r.stderr + r.stdout


def test_cli_argumentos_incorrectos_devuelve_2():
    assert _cli().returncode == 2
