"""Punto de entrada CLI unificado para TileUp.

Uso:
    python -m tileup.cli --instancia RUTA --agente AGENTE \
                         --semilla N --tiempo SEGUNDOS [--salida RUTA]
"""
import argparse
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
    parser.add_argument("--agente", required=True,
                        choices=["evolutivo", "busqueda"],
                        help="Agente a usar.")
    parser.add_argument("--semilla", type=int, required=True,
                        help="Semilla (ignorada por búsqueda).")
    parser.add_argument("--tiempo", type=float, required=True,
                        help="Límite de tiempo en segundos.")
    parser.add_argument("--salida", default="solucion.txt",
                        help="Ruta del archivo de solución.")

    # --- Parámetros del evolutivo ---
    grupo_evo = parser.add_argument_group("Parámetros del evolutivo (opcionales)")
    for nombre, valor in asdict(Params()).items():
        flag = f"--{nombre.replace('_', '-')}"
        grupo_evo.add_argument(flag, type=type(valor), default=valor,
                               help=f"(default: {valor})")

    # --- Parámetros de búsqueda ---
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


def main(argv=None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)

    try:
        instancia = leer_instancia(args.instancia)
    except InstanciaInvalidaError as e:
        print(f"ERROR: instancia inválida: {e}", file=sys.stderr)
        return 2

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