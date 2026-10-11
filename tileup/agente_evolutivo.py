"""
Agente evolutivo para TileUp (algoritmo genético generacional con elitismo).

Idea general:
  - Cada individuo (cromosoma) es una lista de m enteros, uno por cada ficha
    de la secuencia. El entero i decide en qué celda vacía se coloca la ficha i
    (usando módulo sobre la cantidad de celdas vacías en ese momento).
  - Se simula la partida con el motor, se calcula la aptitud y se evoluciona
    la población con selección por torneo, cruce de dos puntos y mutación.
"""
import random
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional

from tileup.motor import (
    Instancia, Estado, estado_inicial, aplicar_accion,
    celdas_vacias, ficha_mayor,
)

#  tipos
Cromosoma = list[int]                       # lista de m enteros
Fitness = tuple[int, int, float]            # (colocadas, -ocupadas_final, -ocupacion_media)
Jugadas = list[tuple[int, int, int]]        # (indice_ficha, fila, columna)

# Tamaño máximo de la caché de aptitudes
MAX_CACHE = 50_000


@dataclass
class Params:
    poblacion: int = 100
    generaciones: int = 400
    torneo: int = 3
    p_cruce: float = 0.9
    mut_factor: float = 2.0      # p_mut = mut_factor / m  (≈ 2 mutaciones por hijo)
    elitismo: int = 3
    estancamiento: int = 100     # generaciones seguidas sin mejora para parar
    margen_tiempo: float = 0.9   # usamos solo el 90% del tiempo límite


@dataclass
class Resultado:
    jugadas: Jugadas
    estado_final: Estado
    colocadas: int
    ocupadas: int
    mayor: int
    victoria: bool
    tiempo: float = 0.0
    evaluaciones: int = 0
    generaciones: int = 0
    motivo_paro: str = ""
    historial: list = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Representación del individuo: cromosoma, simulación y aptitud
# --------------------------------------------------------------------------- #
def cromosoma_aleatorio(generador: random.Random, instancia: Instancia) -> Cromosoma:
    """Crea un cromosoma con m genes aleatorios en [0, n*n)."""
    rango = instancia.n * instancia.n
    return [generador.randrange(rango) for _ in range(instancia.m)]


def simular(instancia: Instancia, cromosoma: Cromosoma,
            con_jugadas: bool = False) -> tuple[Estado, Jugadas, int, int, float]:
    """
    Simula la partida que describe el cromosoma.
    Devuelve: (estado_final, jugadas, colocadas, ocupadas_final, ocupacion_media)
    """
    total_celdas = instancia.n * instancia.n
    estado = estado_inicial(instancia)
    jugadas: Jugadas = []
    colocadas = 0
    suma_ocupadas = 0

    # Calcula las vacías una vez por paso y las reutiliza en la siguiente iteración
    vacias = celdas_vacias(estado)

    for i in range(instancia.m):
        if not vacias:          # tablero lleno, para
            break
        celda = vacias[cromosoma[i] % len(vacias)]
        estado = aplicar_accion(estado, instancia, celda)
        colocadas += 1
        if con_jugadas:
            jugadas.append((i, celda[0], celda[1]))

        # Estado resultante (se recalcula después de aplicar la acción).
        vacias = celdas_vacias(estado)
        suma_ocupadas += total_celdas - len(vacias)   # ocupadas = N*N - vacías

    ocupadas_final = total_celdas - len(vacias)
    ocupacion_media = suma_ocupadas / colocadas if colocadas > 0 else 0.0
    return estado, jugadas, colocadas, ocupadas_final, ocupacion_media


def decodificar(instancia: Instancia, cromosoma: Cromosoma,
                con_jugadas: bool = False) -> tuple[Estado, Jugadas, int]:
    """Devuelve el estado final, las jugadas y cuántas fichas se colocaron."""
    estado, jugadas, colocadas, _, _ = simular(instancia, cromosoma, con_jugadas)
    return estado, jugadas, colocadas


# --------------------------------------------------------------------------- #
# Función de aptitud
# --------------------------------------------------------------------------- #
def evaluar(instancia: Instancia, cromosoma: Cromosoma,
            con_jugadas: bool = False) -> tuple[Fitness, Estado, Jugadas]:
    """
    aptitud es una tupla que se compara de forma lexicográfica:
      1) más fichas colocadas es mejor,
      2) menos celdas ocupadas al final es mejor (por eso el signo negativo),
      3) menor ocupación media durante la partida es mejor.
    """
    estado, jugadas, colocadas, ocupadas_final, ocupacion_media = simular(
        instancia, cromosoma, con_jugadas)
    fitness: Fitness = (colocadas, -ocupadas_final, -ocupacion_media)
    return fitness, estado, jugadas


# --------------------------------------------------------------------------- #
# Población inicial
# --------------------------------------------------------------------------- #
def poblacion_inicial(instancia: Instancia, generador: random.Random,
                      tamano: int) -> list[Cromosoma]:
    #tamaño obligatorio: se le pasa Params.poblacion desde resolver().
    return [cromosoma_aleatorio(generador, instancia) for _ in range(tamano)]


# --------------------------------------------------------------------------- #
# Selección
# --------------------------------------------------------------------------- #
def seleccion_torneo(aptitudes: list[Fitness], k: int,
                     generador: random.Random) -> int:
    """
    Torneo de tamaño k: se eligen k individuos al azar y gana el de mayor
    aptitud. Devuelve el ÍNDICE del ganador. Solo se necesita la lista de
    aptitudes (su largo es el tamaño de la población).
    """
    mejor_i = generador.randrange(len(aptitudes))
    for _ in range(k - 1):
        i = generador.randrange(len(aptitudes))
        if aptitudes[i] > aptitudes[mejor_i]:
            mejor_i = i
    return mejor_i


# --------------------------------------------------------------------------- #
# Crossover
# --------------------------------------------------------------------------- #
def cruzar(padre: Cromosoma, madre: Cromosoma, generador: random.Random,
           p_cruce: float = 0.9) -> tuple[Cromosoma, Cromosoma]:
    #Cruce en dos puntos. Siempre devuelve copias, nunca los padres.
    m = len(padre)
    if m < 3 or generador.random() >= p_cruce:
        return padre[:], madre[:]
    i, j = sorted(generador.sample(range(m + 1), 2))
    hijo1 = padre[:i] + madre[i:j] + padre[j:]
    hijo2 = madre[:i] + padre[i:j] + madre[j:]
    return hijo1, hijo2


def mutar(cromosoma: Cromosoma, p_mut: float, rango: int,
          generador: random.Random) -> Cromosoma:
    #Mutación gen a gen.
    nuevo = cromosoma[:]
    for k in range(len(nuevo)):
        if generador.random() < p_mut:
            nuevo[k] = generador.randrange(rango)
    return nuevo


# --------------------------------------------------------------------------- #
# Reemplazo, parada y loop principal
# --------------------------------------------------------------------------- #
def resolver(instancia: Instancia, semilla: int, tiempo_limite: float,
             params: Optional[Params] = None) -> Resultado:
    p = params or Params()
    generador = random.Random(semilla)
    inicio = time.monotonic()
    plazo = inicio + tiempo_limite * p.margen_tiempo
    m = instancia.m
    rango = instancia.n * instancia.n

    # no hay fichas para colocar
    if m == 0:
        e = estado_inicial(instancia)
        return Resultado([], e, 0, 0, 0, True, 0.0, 0, 0, "instancia vacía")

    # --- Caché de aptitudes con reemplazo progresivo (LRU) ---
    # OrderedDict: el primero es el menos usado recientemente. Cuando se
    # llena, se saca solo el más viejo en vez de vaciar toda la caché, así
    # no se pierden las evaluaciones de la generación actual.
    cache: OrderedDict[tuple, Fitness] = OrderedDict()
    evaluaciones_reales = 0

    def aptitud_de(cromosoma: Cromosoma) -> Fitness:
        nonlocal evaluaciones_reales
        clave = tuple(cromosoma)
        if clave in cache:
            cache.move_to_end(clave)        # lo marca como "recién usado"
            return cache[clave]
        fit, _, _ = evaluar(instancia, cromosoma, con_jugadas=False)
        cache[clave] = fit
        evaluaciones_reales += 1
        if len(cache) > MAX_CACHE:
            cache.popitem(last=False)       # borra solo el más antiguo
        return fit

    # --- Población inicial (con checkeo de tiempo) ---
    # evalúa uno por uno y corta si se acaba el plazo
    poblacion = poblacion_inicial(instancia, generador, p.poblacion)
    aptitudes: list[Fitness] = []
    for crom in poblacion:
        aptitudes.append(aptitud_de(crom))
        if time.monotonic() >= plazo:
            break
    poblacion = poblacion[:len(aptitudes)]   # se queda con los evaluados
    tiempo_agotado_inicial = len(poblacion) < p.poblacion

    mejor_i = max(range(len(poblacion)), key=lambda i: aptitudes[i])
    mejor_global_crom = poblacion[mejor_i][:]
    mejor_global_fit = aptitudes[mejor_i]

    # --- Cota inferior: el mínimo de celdas ocupadas posible ---
    cota = len({c for c, _ in instancia.secuencia})

    def es_optimo(fit: Fitness) -> bool:
        return fit[0] == m and -fit[1] == cota

    p_mut = min(1.0, p.mut_factor / m)
    sin_mejora = 0
    historial: list = []
    motivo = "tiempo" if tiempo_agotado_inicial else "generaciones"
    gen = 0

    # Si ya se acabó el tiempo en la evaluación inicial no entra al for
    generaciones_a_correr = 0 if tiempo_agotado_inicial else p.generaciones

    for gen in range(generaciones_a_correr):
        # --- Criterios de parada ---
        if es_optimo(mejor_global_fit):
            motivo = "optimo (cota inferior)"; break
        if sin_mejora >= p.estancamiento:
            motivo = "estancamiento"; break
        if time.monotonic() >= plazo:
            motivo = "tiempo"; break

        # --- Elitismo: los mejores pasan directo (copias) ---
        orden = sorted(range(len(poblacion)),
                       key=lambda i: aptitudes[i], reverse=True)
        nueva_pob = [poblacion[i][:] for i in orden[:p.elitismo]]
        cortado_por_tiempo = False

        # --- Generación de hijos ---
        while len(nueva_pob) < p.poblacion:
            if time.monotonic() >= plazo:
                cortado_por_tiempo = True
                break
            i_p = seleccion_torneo(aptitudes, p.torneo, generador)
            i_m = seleccion_torneo(aptitudes, p.torneo, generador)
            h1, h2 = cruzar(poblacion[i_p], poblacion[i_m], generador, p.p_cruce)
            h1 = mutar(h1, p_mut, rango, generador)
            h2 = mutar(h2, p_mut, rango, generador)
            nueva_pob.append(h1)
            if len(nueva_pob) < p.poblacion:
                nueva_pob.append(h2)

        # Si se acabó el tiempo a la miatd, la población queda incompleta
        # la descarta y se queda con la anterior (que está completa)
        if cortado_por_tiempo:
            motivo = "tiempo"
            break

        # --- Reemplazo generacional ---
        poblacion = nueva_pob
        aptitudes = [aptitud_de(c) for c in poblacion]

        # --- Actualizar mejor global y contador de estancamiento ---
        mejor_i = max(range(len(poblacion)), key=lambda i: aptitudes[i])
        if aptitudes[mejor_i] > mejor_global_fit:
            mejor_global_fit = aptitudes[mejor_i]
            mejor_global_crom = poblacion[mejor_i][:]
            sin_mejora = 0
        else:
            sin_mejora += 1

        historial.append((mejor_global_fit[0], -mejor_global_fit[1]))

    # --- Reconstruir la mejor solución con las jugadas ---
    _, estado_final, jugadas = evaluar(instancia, mejor_global_crom, con_jugadas=True)
    return Resultado(
        jugadas=jugadas,
        estado_final=estado_final,
        colocadas=mejor_global_fit[0],
        ocupadas=-mejor_global_fit[1],
        mayor=ficha_mayor(estado_final),
        victoria=(mejor_global_fit[0] == m),
        tiempo=time.monotonic() - inicio,
        evaluaciones=evaluaciones_reales,
        generaciones=gen,
        motivo_paro=motivo,
        historial=historial,
    )