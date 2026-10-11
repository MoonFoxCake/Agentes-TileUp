"""Pruebas de los dos agentes, ejecutados a través del CLI (caja negra).

Comprueban lo que exige el enunciado del programa: soluciones legales según el
validador, determinismo con la misma semilla, respeto del límite de tiempo y
escritura de la solución aunque la partida termine en derrota.
"""
import os
import subprocess
import sys
import time

import pytest

from tileup.generador_instancias import generar_instancia
from tileup.motor import leer_instancia
from tileup.validador import validar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTES = ["busqueda", "evolutivo"]

# Instancia pequeña del proyecto (3x3, 2 colores, 4 fichas)
INSTANCIA_PEQUENA = "3 2\n4\n1 5\n1 7\n2 3\n2 4\n"


def correr_cli(instancia, salida, agente, semilla=42, tiempo=5):
    return subprocess.run(
        [sys.executable, "-m", "tileup.cli",
         "--instancia", str(instancia), "--agente", agente,
         "--semilla", str(semilla), "--tiempo", str(tiempo),
         "--salida", str(salida)],
        capture_output=True, text=True, cwd=ROOT,
    )


def escribir_instancia(tmp_path, texto, nombre="inst.txt"):
    ruta = tmp_path / nombre
    ruta.write_text(texto)
    return ruta


def metricas_de(stdout):
    """Lee las líneas clave=valor que el CLI imprime por salida estándar."""
    datos = {}
    for linea in stdout.splitlines():
        if "=" in linea:
            clave, valor = linea.split("=", 1)
            datos[clave.strip()] = valor.strip()
    return datos


# --- Legalidad ---------------------------------------------------------------

@pytest.mark.parametrize("agente", AGENTES)
def test_solucion_es_legal_y_completa(tmp_path, agente):
    ruta_inst = escribir_instancia(tmp_path, generar_instancia(5, 3, 10, 1))
    sol = tmp_path / "sol.txt"
    r = correr_cli(ruta_inst, sol, agente)
    assert r.returncode == 0, r.stderr
    ok, msg, met = validar(leer_instancia(str(ruta_inst)), str(sol))
    assert ok, msg
    assert met["colocadas"] == 10          # hay espacio de sobra: gana la partida
    assert met["meta"] is True


@pytest.mark.parametrize("agente", AGENTES)
def test_ocupadas_respeta_la_cota_inferior(tmp_path, agente):
    """Al final quedan al menos tantas celdas ocupadas como colores distintos."""
    ruta_inst = escribir_instancia(tmp_path, generar_instancia(5, 3, 10, 1))
    inst = leer_instancia(str(ruta_inst))
    sol = tmp_path / "sol.txt"
    correr_cli(ruta_inst, sol, agente)
    ok, msg, met = validar(inst, str(sol))
    assert ok, msg
    assert met["ocupadas"] >= len({color for color, _ in inst.secuencia})


@pytest.mark.parametrize("agente", AGENTES)
def test_metricas_del_cli_coinciden_con_el_validador(tmp_path, agente):
    ruta_inst = escribir_instancia(tmp_path, INSTANCIA_PEQUENA)
    sol = tmp_path / "sol.txt"
    r = correr_cli(ruta_inst, sol, agente)
    assert r.returncode == 0, r.stderr
    informado = metricas_de(r.stdout)
    ok, msg, met = validar(leer_instancia(str(ruta_inst)), str(sol))
    assert ok, msg
    assert int(informado["colocadas"]) == met["colocadas"]
    assert int(informado["ocupadas"]) == met["ocupadas"]
    assert int(informado["mayor"]) == met["mayor"]


# --- Determinismo ------------------------------------------------------------

@pytest.mark.parametrize("agente", AGENTES)
def test_misma_semilla_misma_solucion(tmp_path, agente):
    ruta_inst = escribir_instancia(tmp_path, INSTANCIA_PEQUENA)
    sol_a, sol_b = tmp_path / "a.txt", tmp_path / "b.txt"
    assert correr_cli(ruta_inst, sol_a, agente, semilla=7).returncode == 0
    assert correr_cli(ruta_inst, sol_b, agente, semilla=7).returncode == 0
    assert sol_a.read_text() == sol_b.read_text()


# --- Derrota -----------------------------------------------------------------

@pytest.mark.parametrize("agente", AGENTES)
def test_escribe_solucion_aunque_la_partida_se_pierda(tmp_path, agente):
    """Tablero 1x1 con dos fichas: solo cabe la primera, es derrota inevitable."""
    ruta_inst = escribir_instancia(tmp_path, "1 2\n2\n1 1\n2 1\n")
    sol = tmp_path / "sol.txt"
    r = correr_cli(ruta_inst, sol, agente, tiempo=3)
    assert r.returncode == 0, r.stderr
    assert sol.exists()
    ok, msg, met = validar(leer_instancia(str(ruta_inst)), str(sol))
    assert ok, msg
    assert met["colocadas"] == 1
    assert met["derrota"] is True


# --- Límite de tiempo --------------------------------------------------------

@pytest.mark.parametrize("agente", AGENTES)
def test_respeta_el_limite_de_tiempo(tmp_path, agente):
    """Instancia grande con límite corto: debe terminar cerca del límite."""
    ruta_inst = escribir_instancia(tmp_path, generar_instancia(10, 5, 150, 3))
    sol = tmp_path / "sol.txt"
    limite = 2
    t0 = time.monotonic()
    r = correr_cli(ruta_inst, sol, agente, tiempo=limite)
    transcurrido = time.monotonic() - t0
    assert r.returncode == 0, r.stderr
    assert transcurrido < limite + 3, f"tardó {transcurrido:.1f}s con límite {limite}s"
    ok, msg, _ = validar(leer_instancia(str(ruta_inst)), str(sol))
    assert ok, msg


# --- Errores de entrada ------------------------------------------------------

@pytest.mark.parametrize("agente", AGENTES)
def test_instancia_mal_formada_da_error_legible(tmp_path, agente):
    ruta_inst = escribir_instancia(tmp_path, "esto no es una instancia\n")
    r = correr_cli(ruta_inst, tmp_path / "sol.txt", agente)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr