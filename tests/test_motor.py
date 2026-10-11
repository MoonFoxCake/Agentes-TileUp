"""Pruebas unitarias del motor de TileUp."""
import os
import tempfile
import pytest

from tileup.motor import (
    Instancia, estado_inicial, acciones_legales, aplicar_accion,
    es_meta, es_derrota, celdas_ocupadas, ficha_mayor, suma_total,
    leer_instancia, escribir_solucion,
    InstanciaInvalidaError, AccionInvalidaError,
)


def instancia_simple(n=3, k=2, secuencia=None):
    if secuencia is None:
        secuencia = ((1, 1), (1, 2))
    return Instancia(n=n, k=k, m=len(secuencia), secuencia=tuple(secuencia))


# --- Colocación sin fusión -------------------------------------------------

def test_colocacion_sin_fusion():
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 5), (2, 3)])
    s = aplicar_accion(estado_inicial(inst), inst, (0, 0))
    assert s.tablero[0][0] == (1, 5)
    assert s.indice_siguiente == 1
    s = aplicar_accion(s, inst, (2, 2))
    assert s.tablero[2][2] == (2, 3)
    assert s.tablero[0][0] == (1, 5)
    assert celdas_ocupadas(s) == 2


def test_estado_original_no_se_modifica():
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 1)])
    s0 = estado_inicial(inst)
    tablero_original = s0.tablero
    aplicar_accion(s0, inst, (1, 1))
    assert s0.tablero == tablero_original
    assert s0.indice_siguiente == 0


# --- Fusión ----------------------------------------------------------------

def test_fusion_de_dos_fichas():
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 2), (1, 3)])
    s = aplicar_accion(estado_inicial(inst), inst, (0, 0))
    s = aplicar_accion(s, inst, (0, 1))
    assert s.tablero[0][1] == (1, 5)
    assert s.tablero[0][0] is None
    assert celdas_ocupadas(s) == 1
    assert suma_total(s) == 5


def test_fusion_de_componente_de_tres():
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 1), (1, 1), (1, 1)])
    s = estado_inicial(inst)
    for celda in [(0, 0), (0, 1), (0, 2)]:
        s = aplicar_accion(s, inst, celda)
    assert celdas_ocupadas(s) == 1
    assert s.tablero[0][2] == (1, 3)


def test_fusion_forma_L_se_combina_en_la_celda_colocada():
    """
    (0,0) y (1,1) son del mismo color pero NO son adyacentes entre sí.
    Al colocar en (0,1), la ficha toca a ambas: G = {(0,0),(1,1),(0,1)}
    (forma de L). p=(0,1) pertenece a G y la ficha resultante queda en p.
    """
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 1), (1, 2), (1, 4)])
    s = estado_inicial(inst)
    s = aplicar_accion(s, inst, (0, 0))
    s = aplicar_accion(s, inst, (1, 1))
    assert celdas_ocupadas(s) == 2
    s = aplicar_accion(s, inst, (0, 1))
    assert s.tablero[0][1] == (1, 7)
    assert s.tablero[0][0] is None
    assert s.tablero[1][1] is None
    assert celdas_ocupadas(s) == 1


def test_fusion_ocurre_en_p_y_no_en_el_vecino():
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 2), (1, 3)])
    s = aplicar_accion(estado_inicial(inst), inst, (0, 0))
    s = aplicar_accion(s, inst, (0, 1))
    assert s.tablero[0][1] == (1, 5)
    assert s.tablero[0][0] is None


def test_colores_separados_no_se_fusionan():
    inst = instancia_simple(n=4, k=2, secuencia=[(1, 1), (2, 9), (1, 1)])
    s = estado_inicial(inst)
    s = aplicar_accion(s, inst, (0, 0))
    s = aplicar_accion(s, inst, (0, 1))
    s = aplicar_accion(s, inst, (0, 2))
    assert s.tablero[0][0] == (1, 1)
    assert s.tablero[0][1] == (2, 9)
    assert s.tablero[0][2] == (1, 1)
    assert celdas_ocupadas(s) == 3


# --- Victoria y derrota ----------------------------------------------------

def test_victoria_al_colocar_todas_las_fichas():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1), (2, 1)])
    s = estado_inicial(inst)
    assert not es_meta(s, inst)
    s = aplicar_accion(s, inst, (0, 0))
    assert not es_meta(s, inst)
    s = aplicar_accion(s, inst, (0, 1))
    assert es_meta(s, inst)
    assert acciones_legales(s, inst) == []


def test_derrota_tablero_lleno_con_fichas_pendientes():
    """
    Tablero 2x2 en patrón de ajedrez (nunca dos colores iguales adyacentes)
    para que no haya fusiones: se llena con 4 fichas y queda 1 pendiente.
    """
    secuencia = [(1, 1), (2, 1), (2, 2), (1, 2), (1, 3)]
    inst = instancia_simple(n=2, k=2, secuencia=secuencia)
    s = estado_inicial(inst)
    assert not es_derrota(s, inst)
    s = aplicar_accion(s, inst, (0, 0))
    s = aplicar_accion(s, inst, (0, 1))
    s = aplicar_accion(s, inst, (1, 0))
    s = aplicar_accion(s, inst, (1, 1))
    assert not es_meta(s, inst)
    assert celdas_ocupadas(s) == 4
    assert es_derrota(s, inst)
    assert acciones_legales(s, inst) == []


def test_no_hay_falso_positivo_de_derrota_si_hay_celda_vacia():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1)])
    assert not es_derrota(estado_inicial(inst), inst)


# --- Acciones inválidas ----------------------------------------------------

def test_no_se_puede_colocar_en_celda_ocupada():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1), (2, 1)])
    s = aplicar_accion(estado_inicial(inst), inst, (0, 0))
    with pytest.raises(AccionInvalidaError):
        aplicar_accion(s, inst, (0, 0))


def test_no_se_puede_jugar_tras_victoria():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1)])
    s = aplicar_accion(estado_inicial(inst), inst, (0, 0))
    assert es_meta(s, inst)
    with pytest.raises(AccionInvalidaError):
        aplicar_accion(s, inst, (0, 1))


def test_celda_fuera_de_rango():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1)])
    with pytest.raises(AccionInvalidaError):
        aplicar_accion(estado_inicial(inst), inst, (5, 5))


# --- Lectura de instancias -------------------------------------------------

def test_leer_instancia_valida():
    contenido = """# comentario inicial
4 3 # tablero 4x4, 3 colores
6 # 6 fichas

1 2
2 1
1 3
3 1
1 1
2 4
"""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(contenido)
        ruta = f.name
    try:
        inst = leer_instancia(ruta)
        assert (inst.n, inst.k, inst.m) == (4, 3, 6)
        assert inst.secuencia == ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4))
    finally:
        os.remove(ruta)


@pytest.mark.parametrize("contenido", [
    "4 3\n2\n1 1\n",    # M=2 pero solo 1 ficha
    "4 3\n1\n9 1\n",    # color fuera de rango
    "4 3\n1\n1 0\n",    # valor no positivo
    "4\n1\n1 1\n",      # falta K
    "0 3\n0\n",         # N no positivo
])
def test_leer_instancia_invalida_lanza_error_legible(contenido):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(contenido)
        ruta = f.name
    try:
        with pytest.raises(InstanciaInvalidaError):
            leer_instancia(ruta)
    finally:
        os.remove(ruta)


# --- Escritura de soluciones -----------------------------------------------

def test_escribir_solucion_formato_correcto():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 2), (1, 3)])
    s = aplicar_accion(estado_inicial(inst), inst, (0, 0))
    s = aplicar_accion(s, inst, (0, 1))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        ruta = f.name
    try:
        escribir_solucion(ruta, [(0, 0, 0), (1, 0, 1)], s)
        with open(ruta) as f:
            lineas = f.read().splitlines()
        assert lineas[0] == "0 0 0"
        assert lineas[1] == "1 0 1"
        assert lineas[2] == "# colocadas=2 ocupadas=1 mayor=5"
    finally:
        os.remove(ruta)


# --- Invariante de suma ----------------------------------------------------

def test_invariante_suma_se_conserva_tras_fusiones():
    secuencia = [(1, 1), (1, 2), (1, 3), (2, 5), (1, 4)]
    inst = instancia_simple(n=3, k=2, secuencia=secuencia)
    s = estado_inicial(inst)
    esperada = 0
    for (color, valor), celda in zip(secuencia, [(0, 0), (0, 1), (0, 2), (1, 1), (2, 2)]):
        s = aplicar_accion(s, inst, celda)
        esperada += valor
        assert suma_total(s) == esperada


# --- Regresión: ejemplo del enunciado ---------------------------------------

def test_ejemplo_del_enunciado():
    """Ejemplo del PDF: debe terminar con 3 celdas ocupadas y ficha mayor 6."""
    secuencia = [(1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4)]
    celdas = [(0, 0), (1, 1), (0, 1), (2, 2), (0, 2), (1, 2)]
    inst = Instancia(n=4, k=3, m=6, secuencia=tuple(secuencia))
    s = estado_inicial(inst)
    for celda in celdas:
        s = aplicar_accion(s, inst, celda)
    assert es_meta(s, inst)
    assert celdas_ocupadas(s) == 3
    assert ficha_mayor(s) == 6
