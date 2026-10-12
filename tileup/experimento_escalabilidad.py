"""
Batería experimental del módulo de escalabilidad (sección 6).

Grid: 3 valores de N × 3 valores de K, con M proporcional y 3 semillas por
configuración. Corre ambos agentes (búsqueda y evolutivo) sobre cada instancia,
recolecta métricas y las escribe a un CSV para el informe.
"""
import argparse
import csv
import os
import time

from tileup.motor import (
    leer_instancia, escribir_solucion, estado_inicial, aplicar_accion,
    celdas_ocupadas, ficha_mayor,
)
from tileup.generador_instancias import escribir_instancia
from tileup.agente_evolutivo import resolver as resolver_evolutivo, Params
from tileup.agente_busqueda import beam_search, W_Global, Beta_Global


# --------------------------------------------------------------------------- #
# Configuración del grid
# --------------------------------------------------------------------------- #
N_VALORES = [5, 7, 10]               # 3 valores de N
K_VALORES = [3, 5, 8]                # 3 valores de K
M_PROPORCION = 2.0                   # M = round(N² · M_PROPORCION)
SEMILLAS_AGENTE = [0, 1, 2]          # 3 semillas por configuración
SEMILLAS_INSTANCIA = [100, 200, 300] # semillas distintas de las de ajuste
TIEMPO_LIMITE = 15.0                 # segundos por corrida

DIR_INSTANCIAS = "instancias/escalabilidad"
DIR_SALIDAS = "soluciones/escalabilidad"
CSV_SALIDA = "resultados/escalabilidad.csv"

# La versión de demostración (--rapido / --demo) escribe en carpetas aparte para
# no pisar los archivos de la batería completa.
DEMO_N_VALORES = [5, 7]
DEMO_K_VALORES = [3, 5]
DEMO_TIEMPO_LIMITE = 2.0
DEMO_DIR_INSTANCIAS = "instancias/demo"
DEMO_DIR_SALIDAS = "soluciones/demo"
DEMO_CSV_SALIDA = "resultados/demo/escalabilidad.csv"


# --------------------------------------------------------------------------- #
# Adaptadores de los agentes
# --------------------------------------------------------------------------- #
# Cada adaptador recibe (instancia, semilla, tiempo_limite) y devuelve
# (jugadas, estado_final, esfuerzo).
def correr_busqueda(instancia, semilla, tiempo_limite):
    """Beam search. La semilla se ignora: el algoritmo es determinista.
    Usa el mismo 80 % del límite de tiempo que el CLI."""
    plan, nodos = beam_search(instancia, W=W_Global, beta=Beta_Global,
                              tiempo_max=tiempo_limite * 0.8)
    estado = estado_inicial(instancia)
    for _, f, c in plan:
        estado = aplicar_accion(estado, instancia, (f, c))
    return plan, estado, nodos


def correr_evolutivo(instancia, semilla, tiempo_limite):
    r = resolver_evolutivo(instancia, semilla, tiempo_limite, Params())
    esfuerzo = r.evaluaciones
    return r.jugadas, r.estado_final, esfuerzo


# --------------------------------------------------------------------------- #
# Batería
# --------------------------------------------------------------------------- #
def asegurar_directorios(dir_instancias, dir_salidas):
    os.makedirs(dir_instancias, exist_ok=True)
    os.makedirs(dir_salidas, exist_ok=True)


def correr_grid(agentes=("busqueda", "evolutivo"), n_valores=None, k_valores=None,
                semillas_instancia=None, semillas_agente=None, tiempo_limite=None,
                dir_instancias=None, dir_salidas=None):
    """
    agentes: iterable de strings, subconjunto de {"busqueda", "evolutivo"}.
    Los demás parámetros, si no se indican, toman los valores de la
    configuración del grid definida arriba.
    """
    n_valores = n_valores or N_VALORES
    k_valores = k_valores or K_VALORES
    semillas_instancia = semillas_instancia or SEMILLAS_INSTANCIA
    semillas_agente = semillas_agente or SEMILLAS_AGENTE
    tiempo_limite = tiempo_limite or TIEMPO_LIMITE
    dir_instancias = dir_instancias or DIR_INSTANCIAS
    dir_salidas = dir_salidas or DIR_SALIDAS
    asegurar_directorios(dir_instancias, dir_salidas)
    filas = []

    for n in n_valores:
        for k in k_valores:
            m = int(round(n * n * M_PROPORCION))
            for si in semillas_instancia:
                ruta_inst = f"{dir_instancias}/n{n}_k{k}_m{m}_si{si}.txt"
                escribir_instancia(ruta_inst, n, k, m, si)
                instancia = leer_instancia(ruta_inst)

                for agente in agentes:
                    for sa in semillas_agente:
                        ruta_sol = (
                            f"{dir_salidas}/"
                            f"{agente}_n{n}_k{k}_m{m}_si{si}_sa{sa}.txt"
                        )
                        t0 = time.monotonic()
                        try:
                            if agente == "evolutivo":
                                jugadas, estado, esfuerzo = correr_evolutivo(
                                    instancia, sa, tiempo_limite
                                )
                            elif agente == "busqueda":
                                jugadas, estado, esfuerzo = correr_busqueda(
                                    instancia, sa, tiempo_limite
                                )
                            else:
                                raise ValueError(f"Agente desconocido: {agente}")
                        except NotImplementedError as e:
                            print(f"[omitido] {e}")
                            continue
                        transcurrido = time.monotonic() - t0

                        escribir_solucion(ruta_sol, jugadas, estado)
                        filas.append({
                            "agente": agente,
                            "n": n, "k": k, "m": m,
                            "semilla_instancia": si,
                            "semilla_agente": sa,
                            "colocadas": len(jugadas),
                            "ocupadas": celdas_ocupadas(estado),
                            "mayor": ficha_mayor(estado),
                            "tiempo": round(transcurrido, 4),
                            "esfuerzo": esfuerzo,
                        })
                        print(f"[{agente}] n={n} k={k} m={m} si={si} "
                              f"sa={sa} → colocadas={len(jugadas)} "
                              f"ocupadas={celdas_ocupadas(estado)} "
                              f"t={transcurrido:.2f}s")
    return filas


def escribir_csv(filas, ruta=CSV_SALIDA):
    if not filas:
        print("Sin filas para escribir.")
        return
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"\nCSV escrito en {ruta} ({len(filas)} filas)")


def main():
    parser = argparse.ArgumentParser(description="Batería de escalabilidad de TileUp.")
    parser.add_argument("--rapido", "--demo", dest="rapido", action="store_true",
                        help="Versión reducida para probar o demostrar (N=5,7; K=3,5; "
                             "1 semilla; 2 s por corrida). Escribe en carpetas aparte "
                             "(instancias/demo, soluciones/demo, resultados/demo) para no "
                             "pisar la batería completa.")
    parser.add_argument("--agentes", nargs="+", default=["busqueda", "evolutivo"],
                        choices=["busqueda", "evolutivo"], help="Agentes a ejecutar.")
    parser.add_argument("--salida", default=None,
                        help="Ruta del CSV de resultados (por defecto resultados/escalabilidad.csv, "
                             "o resultados/demo/escalabilidad.csv con --rapido).")
    args = parser.parse_args()

    if args.rapido:
        filas = correr_grid(agentes=args.agentes,
                            n_valores=DEMO_N_VALORES, k_valores=DEMO_K_VALORES,
                            semillas_instancia=[100], semillas_agente=[0],
                            tiempo_limite=DEMO_TIEMPO_LIMITE,
                            dir_instancias=DEMO_DIR_INSTANCIAS,
                            dir_salidas=DEMO_DIR_SALIDAS)
        escribir_csv(filas, args.salida or DEMO_CSV_SALIDA)
    else:
        filas = correr_grid(agentes=args.agentes)
        escribir_csv(filas, args.salida or CSV_SALIDA)


if __name__ == "__main__":
    main()