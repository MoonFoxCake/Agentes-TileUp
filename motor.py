"""
Motor del juego TileUp.

Diseño: estado INMUTABLE. Cada función que "juega" una ficha recibe un
estado y retorna un estado NUEVO; el original nunca se modifica. Esto
permite que los agentes de búsqueda guarden estados en conjuntos/diccionarios
(para detectar repetidos) sin preocuparse de que cambien por debajo, y que
el agente evolutivo simule un cromosoma completo sin necesidad de deshacer
jugadas.

El tablero se representa como una tupla de tuplas (inmutable y hashable).
Cada celda es:
    None                -> celda vacía
    (color, valor)       -> ficha presente, color en 1..K, valor entero > 0

El motor NO usa aleatoriedad en ningún punto: las reglas de TileUp son
deterministas. La semilla es responsabilidad exclusiva de los agentes.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List


Ficha = Tuple[int, int]  # (color, valor)
Tablero = Tuple[Tuple[Optional[Ficha], ...], ...]


@dataclass(frozen=True)
class Instancia:
    """Datos fijos de una partida: no cambian durante la ejecución."""
    n: int
    k: int
    m: int
    secuencia: Tuple[Ficha, ...]  # las M fichas, en el orden en que se colocan


@dataclass(frozen=True)
class Estado:
    """
    Estado inmutable del juego.

    tablero: contenido actual de la cuadrícula N x N.
    indice_siguiente: índice (0-based) de la próxima ficha de la secuencia
        que falta por colocar. Si indice_siguiente == instancia.m, la
        partida terminó en victoria (todas las fichas fueron colocadas).
    """
    tablero: Tablero
    indice_siguiente: int


class InstanciaInvalidaError(Exception):
    """Se lanza cuando el archivo de instancia está mal formado."""
    pass


class AccionInvalidaError(Exception):
    """Se lanza cuando se intenta aplicar una acción ilegal sobre un estado."""
    pass


# ---------------------------------------------------------------------------
# Construcción de estados
# ---------------------------------------------------------------------------

def estado_inicial(instancia: Instancia) -> Estado:
    """Tablero N x N completamente vacío, apuntando a la primera ficha."""
    fila_vacia = tuple(None for _ in range(instancia.n))
    tablero_vacio = tuple(fila_vacia for _ in range(instancia.n))
    return Estado(tablero=tablero_vacio, indice_siguiente=0)


# ---------------------------------------------------------------------------
# Consultas sobre un estado
# ---------------------------------------------------------------------------

def celdas_vacias(estado: Estado) -> List[Tuple[int, int]]:
    """Lista de coordenadas (fila, columna) de celdas vacías, en orden de lectura."""
    n = len(estado.tablero)
    return [
        (f, c)
        for f in range(n)
        for c in range(n)
        if estado.tablero[f][c] is None
    ]


def acciones_legales(estado: Estado, instancia: Instancia) -> List[Tuple[int, int]]:
    """
    Acciones disponibles en este estado: una por cada celda vacía.
    Si la partida ya terminó (victoria), no hay acciones legales.
    """
    if es_meta(estado, instancia):
        return []
    return celdas_vacias(estado)


def es_meta(estado: Estado, instancia: Instancia) -> bool:
    """Victoria: se colocaron las M fichas de la secuencia."""
    return estado.indice_siguiente >= instancia.m


def es_derrota(estado: Estado, instancia: Instancia) -> bool:
    """
    Derrota: queda al menos una ficha pendiente y no hay ninguna celda vacía.
    Nótese que es_meta y es_derrota son mutuamente excluyentes: si ya se
    colocaron todas las fichas, es_meta es True y es_derrota es False aunque
    el tablero esté lleno.
    """
    if es_meta(estado, instancia):
        return False
    return len(celdas_vacias(estado)) == 0


def celdas_ocupadas(estado: Estado) -> int:
    """Cantidad de celdas con ficha en el estado actual."""
    n = len(estado.tablero)
    return sum(
        1
        for f in range(n)
        for c in range(n)
        if estado.tablero[f][c] is not None
    )


def ficha_mayor(estado: Estado) -> int:
    """Valor de la ficha más grande presente en el tablero (0 si está vacío)."""
    n = len(estado.tablero)
    mayor = 0
    for f in range(n):
        for c in range(n):
            ficha = estado.tablero[f][c]
            if ficha is not None and ficha[1] > mayor:
                mayor = ficha[1]
    return mayor


def suma_total(estado: Estado) -> int:
    """
    Suma de todos los valores presentes en el tablero. Se usa como
    invariante en las pruebas: la fusión conserva la suma, así que esta
    cantidad solo debería cambiar cuando se coloca una ficha nueva (se le
    suma su valor), nunca por una fusión en sí misma.
    """
    n = len(estado.tablero)
    return sum(
        estado.tablero[f][c][1]
        for f in range(n)
        for c in range(n)
        if estado.tablero[f][c] is not None
    )


# ---------------------------------------------------------------------------
# Fusión (componente conexa por adyacencia ortogonal)
# ---------------------------------------------------------------------------

def _componente_conexa(tablero: Tablero, origen: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    BFS sobre vecinos ortogonales (arriba, abajo, izquierda, derecha) que
    comparten el mismo color que la ficha en `origen`. Retorna la lista de
    coordenadas de la componente completa (incluye a `origen`).

    No hay fusión en cadena: esta función se llama UNA sola vez, sobre el
    color de la ficha recién colocada, y su resultado se usa para construir
    la ficha fusionada. No se vuelve a invocar sobre el resultado.
    """
    n = len(tablero)
    f0, c0 = origen
    color_objetivo = tablero[f0][c0][0]

    visitados = {origen}
    pendientes = [origen]
    componente = []

    while pendientes:
        f, c = pendientes.pop()
        componente.append((f, c))
        for df, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nf, nc = f + df, c + dc
            if 0 <= nf < n and 0 <= nc < n and (nf, nc) not in visitados:
                vecino = tablero[nf][nc]
                if vecino is not None and vecino[0] == color_objetivo:
                    visitados.add((nf, nc))
                    pendientes.append((nf, nc))

    return componente


def _tablero_con_cambios(tablero: Tablero, cambios: dict) -> Tablero:
    """
    Retorna un nuevo tablero (tupla de tuplas) aplicando `cambios`, un
    diccionario {(fila, columna): nuevo_valor_o_None}. No modifica `tablero`.
    """
    n = len(tablero)
    filas_nuevas = []
    for f in range(n):
        if not any(f == cf for cf, _ in cambios):
            filas_nuevas.append(tablero[f])
            continue
        fila = list(tablero[f])
        for (cf, cc), valor in cambios.items():
            if cf == f:
                fila[cc] = valor
        filas_nuevas.append(tuple(fila))
    return tuple(filas_nuevas)


# ---------------------------------------------------------------------------
# Aplicar una acción (colocar la ficha pendiente en una celda)
# ---------------------------------------------------------------------------

def aplicar_accion(estado: Estado, instancia: Instancia,
                    celda: Tuple[int, int]) -> Estado:
    """
    Coloca la próxima ficha pendiente de la secuencia en `celda` y resuelve
    la fusión si corresponde. Retorna un ESTADO NUEVO; `estado` no se toca.

    Lanza AccionInvalidaError si la partida ya terminó, la celda está fuera
    de rango o la celda ya está ocupada.
    """
    if es_meta(estado, instancia):
        raise AccionInvalidaError("La partida ya terminó (todas las fichas colocadas).")

    f, c = celda
    n = len(estado.tablero)
    if not (0 <= f < n and 0 <= c < n):
        raise AccionInvalidaError(f"Celda fuera de rango: {celda}")
    if estado.tablero[f][c] is not None:
        raise AccionInvalidaError(f"Celda ya ocupada: {celda}")

    color, valor = instancia.secuencia[estado.indice_siguiente]

    # 1. Colocar la ficha tal cual, en un tablero temporal.
    tablero_tras_colocar = _tablero_con_cambios(estado.tablero, {celda: (color, valor)})

    # 2. Calcular la componente conexa de ese color que contiene a `celda`.
    componente = _componente_conexa(tablero_tras_colocar, celda)

    if len(componente) >= 2:
        # Fusión: se retira toda la componente y queda una sola ficha en
        # `celda` con el valor sumado. La suma total se conserva.
        valor_fusionado = sum(tablero_tras_colocar[cf][cc][1] for cf, cc in componente)
        cambios = {pos: None for pos in componente}
        cambios[celda] = (color, valor_fusionado)
        tablero_final = _tablero_con_cambios(tablero_tras_colocar, cambios)
    else:
        # |componente| == 1: no hay fusión, el tablero temporal ya es el final.
        tablero_final = tablero_tras_colocar

    return Estado(tablero=tablero_final, indice_siguiente=estado.indice_siguiente + 1)


# ---------------------------------------------------------------------------
# Lectura de instancias / escritura de soluciones
# ---------------------------------------------------------------------------

def leer_instancia(ruta: str) -> Instancia:
    """
    Lee el formato de instancia definido en el enunciado:
    - líneas en blanco y las que empiezan con '#' se ignoran
    - línea 1 (útil): N K
    - línea 2 (útil): M
    - siguientes M líneas (útiles): color valor

    Lanza InstanciaInvalidaError con un mensaje legible ante cualquier
    formato incorrecto (nunca deja escapar una excepción sin controlar).
    """
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas_crudas = f.readlines()
    except OSError as e:
        raise InstanciaInvalidaError(f"No se pudo abrir el archivo de instancia: {e}")

    lineas_utiles = []
    for lineano, linea in enumerate(lineas_crudas, start=1):
        limpia = linea.split("#", 1)[0].strip()
        if limpia == "":
            continue
        lineas_utiles.append((lineano, limpia))

    if len(lineas_utiles) < 2:
        raise InstanciaInvalidaError(
            "La instancia debe tener al menos la línea 'N K' y la línea 'M'."
        )

    # Línea 1: N K
    lineano, contenido = lineas_utiles[0]
    partes = contenido.split()
    if len(partes) != 2:
        raise InstanciaInvalidaError(
            f"Línea {lineano}: se esperaban dos enteros 'N K', se recibió: '{contenido}'"
        )
    try:
        n, k = int(partes[0]), int(partes[1])
    except ValueError:
        raise InstanciaInvalidaError(
            f"Línea {lineano}: N y K deben ser enteros, se recibió: '{contenido}'"
        )
    if n <= 0 or k <= 0:
        raise InstanciaInvalidaError(f"Línea {lineano}: N y K deben ser positivos.")

    # Línea 2: M
    lineano, contenido = lineas_utiles[1]
    try:
        m = int(contenido)
    except ValueError:
        raise InstanciaInvalidaError(
            f"Línea {lineano}: M debe ser un entero, se recibió: '{contenido}'"
        )
    if m < 0:
        raise InstanciaInvalidaError(f"Línea {lineano}: M no puede ser negativo.")

    # Siguientes M líneas: color valor
    lineas_fichas = lineas_utiles[2:]
    if len(lineas_fichas) != m:
        raise InstanciaInvalidaError(
            f"Se declararon M={m} fichas pero se encontraron {len(lineas_fichas)} líneas de ficha."
        )

    secuencia = []
    for lineano, contenido in lineas_fichas:
        partes = contenido.split()
        if len(partes) != 2:
            raise InstanciaInvalidaError(
                f"Línea {lineano}: se esperaban 'color valor', se recibió: '{contenido}'"
            )
        try:
            color, valor = int(partes[0]), int(partes[1])
        except ValueError:
            raise InstanciaInvalidaError(
                f"Línea {lineano}: color y valor deben ser enteros, se recibió: '{contenido}'"
            )
        if not (1 <= color <= k):
            raise InstanciaInvalidaError(
                f"Línea {lineano}: color {color} fuera de rango 1..{k}"
            )
        if valor <= 0:
            raise InstanciaInvalidaError(
                f"Línea {lineano}: el valor de la ficha debe ser positivo, se recibió {valor}"
            )
        secuencia.append((color, valor))

    return Instancia(n=n, k=k, m=m, secuencia=tuple(secuencia))


def escribir_solucion(ruta: str, jugadas: List[Tuple[int, int, int]],
                       estado_final: Estado) -> None:
    """
    Escribe el archivo de solución en el formato del enunciado.

    jugadas: lista de (indice_ficha, fila, columna) en el orden en que se
        jugaron (puede tener menos de M elementos si hubo derrota).
    estado_final: el estado alcanzado tras la última jugada; de aquí se
        calculan las métricas del resumen final.
    """
    with open(ruta, "w", encoding="utf-8") as f:
        for indice_ficha, fila, col in jugadas:
            f.write(f"{indice_ficha} {fila} {col}\n")
        colocadas = len(jugadas)
        ocupadas = celdas_ocupadas(estado_final)
        mayor = ficha_mayor(estado_final)
        f.write(f"# colocadas={colocadas} ocupadas={ocupadas} mayor={mayor}\n")
