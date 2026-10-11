"""
Agente de búsqueda para TileUp: beam search con una heurística de lookahead.
"""
import time
from typing import List, Tuple
from tileup.motor import (
    Instancia, Estado, Ficha, Tablero,
    estado_inicial, acciones_legales, aplicar_accion,
    es_meta, es_derrota, celdas_ocupadas, leer_instancia, escribir_solucion,
)
W_Global = 50
Beta_Global = 1.0
# Parámetros del beam search:
#   W    = ancho del beam, cuántos estados se conservan en cada nivel.
#          Más W explora más alternativas, pero cada nivel tarda más.
#   Beta = peso del término de lookahead en la heurística: cuánto se premia
#          tener espacios libres junto a fichas del mismo color que vendrán.


def _vecinos(fila: int, col: int, n: int) -> List[Tuple[int, int]]:
    """Vecinos ortogonales (arriba, abajo, izquierda, derecha) dentro del tablero."""

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

def completado_desorden (estado: Estado, plan: list, instancia: Instancia,
                     tiempo_ok):
    """
    Respaldo desordenado para ayudar a beam si ya no hay tiempo
    """
    n = instancia.n
    plan = list(plan)

    # Alistar rapidamente las listas que faltan
    while not es_meta(estado, instancia) and not es_derrota(estado, instancia): #Revisa si ya termino o si pierde
        if not tiempo_ok():
            break
        color = instancia.secuencia[estado.indice_siguiente][0]
        mejor_celda, mejor_afinidad = None, -1
        for f, c in acciones_legales(estado, instancia):
            afinidad = sum(
                1 for vf, vc in _vecinos(f, c, n)
                if estado.tablero[vf][vc] is not None
                and estado.tablero[vf][vc][0] == color
                # hace algo rapido para ver si hay vecinos, y si es asi suma 1 y de ahi la afinidad
            )
            if afinidad > mejor_afinidad:
                mejor_celda, mejor_afinidad = (f, c), afinidad
        plan.append((estado.indice_siguiente, mejor_celda[0], mejor_celda[1]))
        estado = aplicar_accion(estado, instancia, mejor_celda)
        # Lo hace rapidamente hasta que ya termine
    return plan


def beam_search(instancia: Instancia, W: int, beta: float,
                tiempo_max: float = None):
    """
    Parámetros:
        W: ancho del beam
        beta: peso del término lookahead
        tiempo_max: si se supera, corta y devuelve el mejor plan parcial
    """
    t0 = time.perf_counter()

    # Funcion para llevar control del tiempo
    def tiempo_ok():
        return tiempo_max is None or (time.perf_counter() - t0) <= tiempo_max

    beam = [(estado_inicial(instancia), [])]
    nodos = 0
    # Estado inicial 

    for nivel in range(instancia.m):

        candidatos = []
        corte = False

        
        for estado, plan in beam:
            # Recorre los estados del beam
            if not tiempo_ok():
                corte = True
                break
            if es_meta(estado, instancia) or es_derrota(estado, instancia): #Revisa si ya termina o si pierde
                candidatos.append((estado, plan))
                continue
            for celda in acciones_legales(estado, instancia):
                nuevo = aplicar_accion(estado, instancia, celda)
                jugada = (estado.indice_siguiente, celda[0], celda[1])
                candidatos.append((nuevo, plan + [jugada]))
                nodos += 1
                # Aca si crea los nodos nuevos
        if corte:
            break

        
        unicos = {}
        for estado, plan in candidatos:
            if estado not in unicos:
                unicos[estado] = (estado, plan)
                # Se manda los duplicados, entonces si encuentra uno duplicado solo guarda el primero 

        
        con_clave = []
        for estado, plan in unicos.values():
            if not tiempo_ok():
                corte = True
                break
            con_clave.append((_clave_orden(estado, instancia, beta), (estado, plan)))
            # Guarda la clave para ya despues ordenarlo
        if corte:
            break

        # Ordena los candidatos de menor a mayor
        con_clave.sort(key=lambda x: x[0])
        beam = [par for _, par in con_clave[:W]]
        # Toma el valor mas bajo

    # Mejor estado del beam: más fichas colocadas y menos celdas ocupadas
    beam.sort(key=lambda par: (-par[0].indice_siguiente,
                               celdas_ocupadas(par[0]),
                               _tablero_ordenable(par[0].tablero)))
    mejor_estado, mejor_plan = beam[0]

    # Si el beam no llegó al final, terminar las fichas que faltan
    if not es_meta(mejor_estado, instancia) and not es_derrota(mejor_estado, instancia):
        mejor_plan = completado_desorden(mejor_estado, mejor_plan, instancia,
                                      lambda: tiempo_max is None
                                      or (time.perf_counter() - t0) <= tiempo_max * 1.1)
    return mejor_plan, nodos


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
    plan, nodos = beam_search(inst, W=W, beta=beta)
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
    print(f"Nodos generados: {nodos}")
    print(f"Tiempo: {t1 - t0:.4f}s")
if __name__ == "__main__":
    import sys
    argumentos_validos = [
        arg for arg in sys.argv[1:]
        if not arg.startswith("-") and not arg.endswith(".json")
    ]
    ruta = argumentos_validos[0] if argumentos_validos else "instancias/mediana.txt"
    main(ruta)