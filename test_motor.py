"""
Pruebas unitarias del motor de TileUp.

Cubren, como mínimo, los cuatro casos exigidos por el enunciado:
    - fusión de dos fichas
    - fusión de una componente de tres o más
    - colocación sin fusión
    - detección de derrota
Y además: detección de victoria, fusión con forma no lineal (L/U), el
invariante de conservación de la suma, y validación de instancias mal
formadas.

Ejecutar con:  python -m pytest tests/ -v
"""

import os
import tempfile
import pytest

from tileup.motor import (
    Instancia,
    Estado,
    estado_inicial,
    acciones_legales,
    aplicar_accion,
    es_meta,
    es_derrota,
    celdas_ocupadas,
    ficha_mayor,
    suma_total,
    leer_instancia,
    escribir_solucion,
    InstanciaInvalidaError,
    AccionInvalidaError,
)


def instancia_simple(n=3, k=2, secuencia=None):
    """Instancia auxiliar de pruebas; se puede pasar una secuencia custom."""
    if secuencia is None:
        secuencia = ((1, 1), (1, 2))
    return Instancia(n=n, k=k, m=len(secuencia), secuencia=tuple(secuencia))


# ---------------------------------------------------------------------------
# Colocación sin fusión
# ---------------------------------------------------------------------------

def test_colocacion_sin_fusion():
    """Una ficha colocada sin vecinos del mismo color queda tal cual."""
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 5), (2, 3)])
    s0 = estado_inicial(inst)

    s1 = aplicar_accion(s0, inst, (0, 0))
    assert s1.tablero[0][0] == (1, 5)
    assert s1.indice_siguiente == 1

    # Colocar la segunda ficha lejos y de otro color: tampoco debe fusionar.
    s2 = aplicar_accion(s1, inst, (2, 2))
    assert s2.tablero[2][2] == (2, 3)
    assert s2.tablero[0][0] == (1, 5)  # la primera ficha sigue intacta
    assert celdas_ocupadas(s2) == 2


def test_estado_original_no_se_modifica():
    """El motor es inmutable: aplicar_accion no debe tocar el estado recibido."""
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 1)])
    s0 = estado_inicial(inst)
    tablero_original = s0.tablero

    aplicar_accion(s0, inst, (1, 1))

    assert s0.tablero == tablero_original
    assert s0.indice_siguiente == 0


# ---------------------------------------------------------------------------
# Fusión de dos fichas
# ---------------------------------------------------------------------------

def test_fusion_de_dos_fichas():
    """Dos fichas del mismo color, adyacentes, se fusionan sumando valores."""
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 2), (1, 3)])
    s0 = estado_inicial(inst)

    s1 = aplicar_accion(s0, inst, (0, 0))  # ficha (1,2) en (0,0)
    s2 = aplicar_accion(s1, inst, (0, 1))  # ficha (1,3) adyacente -> fusiona

    # Tras la fusión debe quedar UNA sola ficha con valor 2+3=5
    assert s2.tablero[0][1] == (1, 5)
    assert s2.tablero[0][0] is None
    assert celdas_ocupadas(s2) == 1
    assert suma_total(s2) == 5


# ---------------------------------------------------------------------------
# Fusión de una componente de tres o más fichas
# ---------------------------------------------------------------------------

def test_fusion_de_componente_de_tres():
    """Tres fichas del mismo color en línea se fusionan en una sola."""
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 1), (1, 1), (1, 1)])
    s0 = estado_inicial(inst)

    s1 = aplicar_accion(s0, inst, (0, 0))
    s2 = aplicar_accion(s1, inst, (0, 1))  # fusiona con (0,0) -> valor 2 en (0,1)
    s3 = aplicar_accion(s2, inst, (0, 2))  # adyacente a (0,1) -> fusiona de nuevo

    assert celdas_ocupadas(s3) == 1
    assert s3.tablero[0][2] == (1, 3)
    assert suma_total(s3) == 3


def test_fusion_forma_no_lineal_en_L():
    """
    Verifica que la componente conexa se calcula por BFS real y no asume
    una línea recta: coloca fichas formando una L y confirma que todas se
    fusionan en un solo grupo.

        (0,0)=color1  (0,1)=color1
        (1,0)=color1
    """
    inst = instancia_simple(n=3, k=2, secuencia=[(1, 1), (1, 1), (1, 1)])
    s0 = estado_inicial(inst)

    s1 = aplicar_accion(s0, inst, (0, 0))
    s2 = aplicar_accion(s1, inst, (1, 0))  # adyacente vertical a (0,0) -> fusiona
    s3 = aplicar_accion(s2, inst, (0, 1))  # adyacente a (0,0)... pero (0,0) ya se vació

    # Tras colocar en (1,0), la ficha fusionada queda en (1,0) con valor 2,
    # y (0,0) vuelve a estar vacía. Colocar en (0,1) NO es adyacente a (1,0),
    # así que no debería fusionar de nuevo.
    assert s2.tablero[1][0] == (1, 2)
    assert s2.tablero[0][0] is None
    assert s3.tablero[0][1] == (1, 1)  # ficha nueva, sin fusión
    assert celdas_ocupadas(s3) == 2


def test_fusion_no_encadena_mas_alla_de_la_componente():
    """
    La ficha resultante de una fusión no debe "seguir fusionando" con fichas
    que no formaban parte de la componente original en el momento de colocar.
    """
    inst = instancia_simple(n=4, k=2, secuencia=[(1, 1), (2, 9), (1, 1)])
    s0 = estado_inicial(inst)

    # Ficha de color 2 (valor 9) separando dos zonas de color 1.
    s1 = aplicar_accion(s0, inst, (0, 0))   # color1 en (0,0)
    s2 = aplicar_accion(s1, inst, (0, 1))   # color2 en (0,1): no fusiona con (0,0)
    s3 = aplicar_accion(s2, inst, (0, 2))   # color1 en (0,2), NO adyacente a (0,0)

    assert s3.tablero[0][0] == (1, 1)
    assert s3.tablero[0][1] == (2, 9)
    assert s3.tablero[0][2] == (1, 1)  # sigue siendo dos fichas de color1 separadas
    assert celdas_ocupadas(s3) == 3


# ---------------------------------------------------------------------------
# Detección de victoria
# ---------------------------------------------------------------------------

def test_victoria_al_colocar_todas_las_fichas():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1), (2, 1)])
    s0 = estado_inicial(inst)
    assert not es_meta(s0, inst)

    s1 = aplicar_accion(s0, inst, (0, 0))
    assert not es_meta(s1, inst)

    s2 = aplicar_accion(s1, inst, (0, 1))
    assert es_meta(s2, inst)
    assert acciones_legales(s2, inst) == []


# ---------------------------------------------------------------------------
# Detección de derrota
# ---------------------------------------------------------------------------

def test_derrota_tablero_lleno_con_fichas_pendientes():
    """
    Tablero 2x2 que se llena en patrón de "tablero de ajedrez" (colores
    alternados en diagonal, nunca dos iguales adyacentes) para garantizar
    que ninguna colocación dispare una fusión: así el tablero termina
    ocupado en sus 4 celdas y queda 1 ficha pendiente de una secuencia de 5.

        (0,0)=color1  (0,1)=color2
        (1,0)=color2  (1,1)=color1
    """
    secuencia = [(1, 1), (2, 1), (2, 2), (1, 2), (1, 3)]  # 5 fichas, tablero de 4 celdas
    inst = instancia_simple(n=2, k=2, secuencia=secuencia)
    s = estado_inicial(inst)

    assert not es_derrota(s, inst)
    s = aplicar_accion(s, inst, (0, 0))  # color1
    s = aplicar_accion(s, inst, (0, 1))  # color2, adyacente a color1: no fusiona
    s = aplicar_accion(s, inst, (1, 0))  # color2, adyacente a (0,0)=color1: no fusiona
    s = aplicar_accion(s, inst, (1, 1))  # color1, adyacente a color2 en ambos lados: no fusiona

    assert not es_meta(s, inst)      # queda 1 ficha pendiente (índice 4)
    assert celdas_ocupadas(s) == 4   # las 4 celdas siguen ocupadas, sin fusiones
    assert es_derrota(s, inst)       # y no hay celdas vacías
    assert acciones_legales(s, inst) == []


def test_no_hay_falso_positivo_de_derrota_si_hay_celda_vacia():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1)])
    s = estado_inicial(inst)
    assert not es_derrota(s, inst)


# ---------------------------------------------------------------------------
# Acciones inválidas
# ---------------------------------------------------------------------------

def test_no_se_puede_colocar_en_celda_ocupada():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1), (2, 1)])
    s0 = estado_inicial(inst)
    s1 = aplicar_accion(s0, inst, (0, 0))
    with pytest.raises(AccionInvalidaError):
        aplicar_accion(s1, inst, (0, 0))


def test_no_se_puede_jugar_tras_victoria():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1)])
    s0 = estado_inicial(inst)
    s1 = aplicar_accion(s0, inst, (0, 0))
    assert es_meta(s1, inst)
    with pytest.raises(AccionInvalidaError):
        aplicar_accion(s1, inst, (0, 1))


def test_celda_fuera_de_rango():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 1)])
    s0 = estado_inicial(inst)
    with pytest.raises(AccionInvalidaError):
        aplicar_accion(s0, inst, (5, 5))


# ---------------------------------------------------------------------------
# Lectura de instancias
# ---------------------------------------------------------------------------

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
        assert inst.n == 4
        assert inst.k == 3
        assert inst.m == 6
        assert inst.secuencia == ((1, 2), (2, 1), (1, 3), (3, 1), (1, 1), (2, 4))
    finally:
        os.remove(ruta)


@pytest.mark.parametrize("contenido", [
    "4 3\n2\n1 1\n",                     # dice M=2 pero solo trae 1 ficha
    "4 3\n1\n9 1\n",                     # color fuera de rango 1..K
    "4 3\n1\n1 0\n",                     # valor no positivo
    "4\n1\n1 1\n",                       # falta K en la primera línea
    "0 3\n0\n",                          # N no positivo
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


# ---------------------------------------------------------------------------
# Escritura de soluciones
# ---------------------------------------------------------------------------

def test_escribir_solucion_formato_correcto():
    inst = instancia_simple(n=2, k=2, secuencia=[(1, 2), (1, 3)])
    s0 = estado_inicial(inst)
    s1 = aplicar_accion(s0, inst, (0, 0))
    s2 = aplicar_accion(s1, inst, (0, 1))  # fusiona -> valor 5

    jugadas = [(0, 0, 0), (1, 0, 1)]

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        ruta = f.name
    try:
        escribir_solucion(ruta, jugadas, s2)
        with open(ruta) as f:
            lineas = f.read().splitlines()
        assert lineas[0] == "0 0 0"
        assert lineas[1] == "1 0 1"
        assert lineas[2] == "# colocadas=2 ocupadas=1 mayor=5"
    finally:
        os.remove(ruta)


# ---------------------------------------------------------------------------
# Invariante: la fusión conserva la suma total de valores
# ---------------------------------------------------------------------------

def test_invariante_suma_se_conserva_tras_fusiones():
    """
    La suma total de valores en el tablero debe ser siempre igual a la suma
    de valores de las fichas colocadas hasta el momento, sin importar cuántas
    fusiones hayan ocurrido (la fusión solo agrupa, nunca crea ni destruye valor).
    """
    secuencia = [(1, 1), (1, 2), (1, 3), (2, 5), (1, 4)]
    inst = instancia_simple(n=3, k=2, secuencia=secuencia)
    s = estado_inicial(inst)

    suma_esperada = 0
    celdas = [(0, 0), (0, 1), (0, 2), (1, 1), (2, 2)]
    for (color, valor), celda in zip(secuencia, celdas):
        s = aplicar_accion(s, inst, celda)
        suma_esperada += valor
        assert suma_total(s) == suma_esperada
