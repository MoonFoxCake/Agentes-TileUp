import argparse
import os
import sys
import time
from dataclasses import asdict

from tileup.motor import (
    leer_instancia, escribir_solucion, estado_inicial, aplicar_accion,
    celdas_ocupadas, ficha_mayor, InstanciaInvalidaError,
)
from tileup.agente_evolutivo import Params, resolver as resolver_evolutivo
from tileup.agente_busqueda import beam_search, W_Global, Beta_Global



def construir_parser():
    parser = argparse.ArgumentParser(
        prog="tileup",
        description="Agentes para TileUp (Tarea Corta 1).",
    )
    parser.add_argument("--instancia", required=True,
                        help="Ruta del archivo de instancia.")
    parser.add_argument("--agente", choices=["evolutivo", "busqueda"],
                        help="Agente a usar (ignorado si se pasa --full).")
    parser.add_argument("--full", action="store_true",
                        help="Corre ambos agentes sobre la instancia y luego "
                             "la batería experimental completa.")
    parser.add_argument("--semilla", type=int, required=True,
                        help="Semilla (ignorada por búsqueda).")
    parser.add_argument("--tiempo", type=float, required=True,
                        help="Límite de tiempo en segundos.")
    parser.add_argument("--salida", default="solucion.txt",
                        help="Ruta base del archivo de solución.")

    # --- Parámetros del evolutivo (opcionales) ---
    grupo_evo = parser.add_argument_group("Parámetros del evolutivo (opcionales)")
    for nombre, valor in asdict(Params()).items():
        flag = f"--{nombre.replace('_', '-')}"
        grupo_evo.add_argument(flag, type=type(valor), default=valor,
                               help=f"(default: {valor})")

    # --- Parámetros de búsqueda (opcionales) ---
    grupo_bus = parser.add_argument_group("Parámetros de búsqueda (opcionales)")
    grupo_bus.add_argument("--w", type=int, default=W_Global,
                           help=f"Ancho del beam (default: {W_Global})")
    grupo_bus.add_argument("--beta", type=float, default=Beta_Global,
                           help=f"Peso del lookahead (default: {Beta_Global})")

    return parser



def _resolver_busqueda(instancia, tiempo, args):
    """Ejecuta beam search y devuelve (jugadas, estado_final, nodos)."""
    plan, nodos = beam_search(instancia, W=args.w, beta=args.beta,
                              tiempo_max=tiempo * 0.8)

    estado = estado_inicial(instancia)
    for _, f, c in plan:
        estado = aplicar_accion(estado, instancia, (f, c))

    return plan, estado, nodos

def _ruta_variante(ruta_base, sufijo):
    """'sol.txt' → 'sol_busqueda.txt' o 'sol_evolutivo.txt'."""
    base, ext = os.path.splitext(ruta_base)
    return f"{base}_{sufijo}{ext or '.txt'}"



def _modo_full(instancia, args):
    """Corre en orden: búsqueda, evolutivo, comparación, y batería experimental."""
    resultados = []


    print("\n\n\n\n\n\n\n")
    print("PASO 1/3 — AGENTE DE BÚSQUEDA")


    t0 = time.monotonic()
    jugadas_b, estado_b, nodos = _resolver_busqueda(instancia, args.tiempo, args)
    tiempo_b = time.monotonic() - t0
    escribir_solucion(_ruta_variante(args.salida, "busqueda"), jugadas_b, estado_b)

    print(f"colocadas={len(jugadas_b)}")
    print(f"ocupadas={celdas_ocupadas(estado_b)}")
    print(f"mayor={ficha_mayor(estado_b)}")
    print(f"tiempo={tiempo_b:.3f}")
    print(f"nodos_expandidos={nodos}")
    resultados.append({
        "agente": "busqueda",
        "colocadas": len(jugadas_b),
        "ocupadas": celdas_ocupadas(estado_b),
        "tiempo": tiempo_b,
        "esfuerzo": nodos,
    })

    # ---------------- PASO 2/3: EVOLUTIVO ----------------
    print("\n\n\n\n\n\n\n")
    print("PASO 2/3 — AGENTE EVOLUTIVO")


    params = Params(**{k: getattr(args, k) for k in asdict(Params())})
    t0 = time.monotonic()
    r = resolver_evolutivo(instancia, args.semilla, args.tiempo, params)
    tiempo_e = time.monotonic() - t0
    escribir_solucion(_ruta_variante(args.salida, "evolutivo"),
                      r.jugadas, r.estado_final)

    print(f"colocadas={r.colocadas}")
    print(f"ocupadas={r.ocupadas}")
    print(f"mayor={r.mayor}")
    print(f"tiempo={tiempo_e:.3f}")
    print(f"evaluaciones_aptitud={r.evaluaciones}")
    print(f"generaciones={r.generaciones}")
    print(f"motivo_paro={r.motivo_paro}")
    resultados.append({
        "agente": "evolutivo",
        "colocadas": r.colocadas,
        "ocupadas": r.ocupadas,
        "tiempo": tiempo_e,
        "esfuerzo": r.evaluaciones,
    })


    print("\n\n\n\n\n\n")
    print("COMPARACIÓN DE ESTA INSTANCIA")

    print(f"{'agente':>10} | {'colocadas':>10} | {'ocupadas':>9} | "
          f"{'tiempo':>8} | {'esfuerzo':>10}")
    print("-" * 60)
    for x in resultados:
        print(f"{x['agente']:>10} | {x['colocadas']:>10} | {x['ocupadas']:>9} | "
              f"{x['tiempo']:>7.3f}s | {x['esfuerzo']:>10}")
    ganador = min(resultados,
                  key=lambda x: (-x["colocadas"], x["ocupadas"], x["tiempo"]))
    print(f"\nGanador (criterio del concurso): {ganador['agente']}")


    print("\n\n\n\n\n")
    print("PASO 3/3")
    

    from tileup.comparacion_experimental import main as correr_bateria
    correr_bateria()

    return 0



def main(argv=None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)

    # Validación: si no es --full, hace falta --agente.
    if not args.full and not args.agente:
        parser.error("Debe especificar --agente o --full.")

    try:
        instancia = leer_instancia(args.instancia)
    except InstanciaInvalidaError as e:
        print(f"ERROR: instancia inválida: {e}", file=sys.stderr)
        return 2

    # --- Modo extendido ---
    if args.full:
        return _modo_full(instancia, args)

    # --- Modo normal: un solo agente ---
    inicio = time.monotonic()

    if args.agente == "evolutivo":
        params = Params(**{k: getattr(args, k) for k in asdict(Params())})
        r = resolver_evolutivo(instancia, args.semilla, args.tiempo, params)
        jugadas = r.jugadas
        estado_final = r.estado_final
        extras = {
            "evaluaciones_aptitud": r.evaluaciones,
            "generaciones": r.generaciones,
            "motivo_paro": r.motivo_paro,
        }
    else:  # busqueda
        jugadas, estado_final, nodos = _resolver_busqueda(instancia, args.tiempo, args)
        extras = {
            "nodos_expandidos": nodos,
            "w": args.w,
            "beta": args.beta,
        }

    transcurrido = time.monotonic() - inicio
    escribir_solucion(args.salida, jugadas, estado_final)

    print(f"agente={args.agente}")
    print(f"instancia={args.instancia}")
    print(f"semilla={args.semilla}")
    print(f"colocadas={len(jugadas)}")
    print(f"ocupadas={celdas_ocupadas(estado_final)}")
    print(f"mayor={ficha_mayor(estado_final)}")
    print(f"tiempo={transcurrido:.3f}")
    for k, v in extras.items():
        print(f"{k}={v}")
    print(f"salida={args.salida}")
    return 0

if __name__ == "__main__":
    sys.exit(main())