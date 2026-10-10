import time
from typing import List, Tuple
from tileup.motor import (
    Instancia, Estado, Ficha, Tablero,
    estado_inicial, acciones_legales, aplicar_accion,
    es_meta, es_derrota, celdas_ocupadas, leer_instancia, escribir_solucion,
)
W_Global = 50
Beta_Global = 1.0
# Estos son parametros que usa el beam search, mientras mas W mas se fija en los detalles, mientras mas Beta mas profundo y detallado se pone




def _vecinos(fila: int, col: int, n: int) -> List[Tuple[int, int]]:
    """Revisa los vecinos, izquierda, derecha"""

    resultado = []
    if fila > 0:
        resultado.append((fila-1, col))
    if fila < n-1:
        resultado.append((fila+1, col))
    if col > 0:
        resultado.append((fila, col-1))
    if col < n-1:
        resultado.append((fila, col+1))
    return resultado

def _slots_color(estado: Estado, color: int) -> int:
    """
    Busca por color las celdas que esten vacias junto a sus vecinos

    """
    n = len(estado.tablero)
    slots = set() # fila, columna, sin duplicados

    for f in range(n):
      for c in range(n):
        ficha = estado.tablero[f][c]
        # si no hay color igual se ignora
        if ficha is None or ficha[0] != color:
            continue
        for fila, col in _vecinos(f,c,n):
            if estado.tablero[fila][col] is None:
                slots.add((fila, col))
    return len(slots)




def h_look(estado: Estado, instancia: Instancia, beta: float) -> float:
    """Es la Heuristica"""
    T = celdas_ocupadas(estado) #Estado actual

    # Colores en tablero
    en_tablero = set()

    for fila in estado.tablero:
      for ficha in fila:
        if ficha is not None:
          en_tablero.add(ficha[0])
          # Recorre el tablero, como es set no se duplica


    frecuencia = {}

    for color, _ in instancia.secuencia[estado.indice_siguiente:]:
      # Va desde como esta en el i actual hasta el final
      frecuencia[color] = frecuencia.get(color, 0) + 1


    potencial = 0
    for c in en_tablero:
      sigma_c = _slots_color(estado, c)
      # Ve los vecinos vacios a alguno de color
      f_c = frecuencia.get(c, 0)
      potencial += min(sigma_c, f_c)
      # Calcula el minimo de espacios y fichas futuras

    return T - beta * potencial

    # Ya aca completa la heuristica



def _tablero_ordenable(tablero: Tablero):
    """Convierte None → (0,0) para que los tableros se puedan comparar."""
    return tuple(
        tuple(celda if celda is not None else (0, 0) for celda in fila)
        for fila in tablero
    )


def _clave_orden(estado: Estado, instancia: Instancia, beta: float):
    """
    Se encarga de ordenar en caso de que haya empates en el tablero, corre la heuristica y el que de el numero menor gana
    """
    return(
      h_look(estado, instancia, beta),
      -estado.indice_siguiente,
      celdas_ocupadas(estado),
      _tablero_ordenable(estado.tablero),
  )

def beam_search(instancia: Instancia, W: int, beta: float,
                tiempo_max: float = None) -> List[Tuple[int, int, int]]:
    """

    Parámetros:
        W: ancho del beam
        beta: peso del término lookahead
        tiempo_max: si se supera, corta y devuelve el mejor plan parcial

    Estructura:
        1. Inicializa beam = [(estado_inicial, [])]
        2. Para cada nivel i in 0..M-1:
            a. Genera candidatos expandiendo cada estado del beam
            b. Deduplica por (tablero, indice_siguiente) conservando el mejor h
            c. Ordena con _clave_orden
            d. Conserva los top W
        3. Del beam final, elige el mejor por (placed DESC, -occupied ASC)
        4. Retorna el plan (lista de jugadas)
    """

    t0 = time.perf_counter()
    s0 = estado_inicial(instancia)
    beam = [(s0, [])]
    #Estado inicial del beam

    for nivel in range(instancia.m):
      if tiempo_max is not None and (time.perf_counter() - t0) > tiempo_max:
        # Por tiempo para evitar atascos
          break

      candidatos = []

      for estado, plan in beam:
        if es_meta(estado, instancia) or es_derrota(estado, instancia):
          candidatos.append((estado, plan))
          continue
        for celda in acciones_legales(estado, instancia):

          nuevo = aplicar_accion(estado, instancia, celda)
          jugada = (estado.indice_siguiente, celda[0], celda[1])
          candidatos.append((nuevo, plan + [jugada]))
          #

        # Revisa si es jugada legal

      unicos = {}
      for estado, plan in candidatos:
        if estado not in unicos:
            unicos[estado] = (estado, plan)

      lista = list(unicos.values())
      lista.sort(key=lambda par: _clave_orden(par[0], instancia, beta))
      beam = lista[:W]

    beam.sort(key=lambda par: (-par[0].indice_siguiente, celdas_ocupadas(par[0]), _tablero_ordenable(par[0].tablero),))

    mejor_estado, mejor_plan = beam[0]
    return mejor_plan


def _imprimir_tablero(estado: Estado) -> str:
    """Devuelve una representación ASCII legible del tablero."""
    n = len(estado.tablero)
    lineas = []
    for f in range(n):
        celdas = []
        for c in range(n):
            ficha = estado.tablero[f][c]
            if ficha is None:
                celdas.append(" ·  ")
            else:
                color, valor = ficha
                celdas.append(f"c{color}v{valor:<2}")
        lineas.append(" │ ".join(celdas))
    return "\n".join(lineas)



def main(ruta_instancia: str,
         W: int = W_Global,
         beta: float = Beta_Global,
         verbose: bool = True):
    inst = leer_instancia(ruta_instancia)

    print(f"Instancia: N={inst.n}, K={inst.k}, M={inst.m}")
    print(f"Parámetros: W={W}, beta={beta}")
    print()

    t0 = time.perf_counter()
    plan = beam_search(inst, W=W, beta=beta)
    t1 = time.perf_counter()

    estado = estado_inicial(inst)

    if verbose:
        print("=== Plan paso a paso ===")
        print(f"[inicio] T=0")
        print(_imprimir_tablero(estado))

    T_anterior = 0
    for idx, (indice, f, c) in enumerate(plan):
        estado = aplicar_accion(estado, inst, (f, c))
        T = celdas_ocupadas(estado)

        if verbose:
            color, valor = inst.secuencia[indice]
            evento = "FUSIÓN" if T < T_anterior + 1 else "coloca"
            print(f"\n[paso {idx+1}] ficha #{indice} = c{color}v{valor} en ({f},{c})  |  {evento}  |  T={T}")
            print(_imprimir_tablero(estado))

        T_anterior = T

    print()
    print("=== Resumen ===")
    print(f"Plan: {len(plan)} jugadas")
    print(f"Colocadas: {len(plan)} / {inst.m}")
    print(f"Ocupadas: {celdas_ocupadas(estado)}")
    print(f"Tiempo: {t1 - t0:.4f}s")
if __name__ == "__main__":
    import sys
    argumentos_validos = [
        arg for arg in sys.argv[1:]
        if not arg.startswith("-") and not arg.endswith(".json")
    ]
    ruta = argumentos_validos[0] if argumentos_validos else "instancias/mediana.txt"
    main(ruta)
