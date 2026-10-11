"""Validador independiente: reproduce una solución paso a paso.

No usa la lógica de juego del motor: reimplementa colocación y fusión.
Solo reutiliza leer_instancia (lectura de datos, no lógica de decisión).

Uso:
    python -m tileup.validador INSTANCIA SOLUCION
Códigos de salida: 0 = legal, 1 = ilegal, 2 = error de entrada.
"""
import sys
from tileup.motor import leer_instancia, InstanciaInvalidaError


def validar(instancia, ruta_solucion):
    """Devuelve (es_legal, mensaje, metricas)."""
    try:
        with open(ruta_solucion, encoding="utf-8") as fh:
            lineas = fh.read().splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return False, f"No se pudo leer la solución: {e}", None

    n = instancia.n
    tab = [[None] * n for _ in range(n)]
    colocadas = 0
    resumen = None

    for no, linea in enumerate(lineas, start=1):
        txt = linea.strip()
        if not txt:
            continue
        if txt.startswith("#"):
            resumen = txt
            continue
        partes = txt.split()
        if len(partes) != 3:
            return False, f"Línea {no}: se esperaban 3 enteros.", None
        try:
            i, f, c = (int(x) for x in partes)
        except ValueError:
            return False, f"Línea {no}: no son enteros.", None
        if colocadas >= instancia.m:
            return False, f"Línea {no}: hay más colocaciones que fichas.", None
        if i != colocadas:
            return False, f"Línea {no}: índice {i}, se esperaba {colocadas}.", None
        if not (0 <= f < n and 0 <= c < n):
            return False, f"Línea {no}: celda ({f},{c}) fuera del tablero.", None
        if tab[f][c] is not None:
            return False, f"Línea {no}: celda ({f},{c}) ya ocupada.", None

        # 1. Colocar la ficha en p = (f, c)
        color, valor = instancia.secuencia[i]
        tab[f][c] = (color, valor)

        # 2. Componente conexa G del mismo color que contiene a p
        comp, vistos, k = [(f, c)], {(f, c)}, 0
        while k < len(comp):
            r, q = comp[k]
            k += 1
            for dr, dq in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                a, b = r + dr, q + dq
                if (0 <= a < n and 0 <= b < n and (a, b) not in vistos
                        and tab[a][b] is not None and tab[a][b][0] == color):
                    vistos.add((a, b))
                    comp.append((a, b))

        # 3. Si |G| >= 2: se retira G y la ficha con la suma queda en p
        if len(comp) >= 2:
            total = sum(tab[r][q][1] for r, q in comp)
            for r, q in comp:
                tab[r][q] = None
            tab[f][c] = (color, total)
        colocadas += 1

    fichas = [x for fila in tab for x in fila if x is not None]
    ocupadas = len(fichas)
    mayor = max((x[1] for x in fichas), default=0)
    meta = colocadas == instancia.m
    metricas = {
        "colocadas": colocadas, "ocupadas": ocupadas, "mayor": mayor,
        "meta": meta, "derrota": (not meta) and ocupadas == n * n,
    }

    # La línea resumen del archivo debe coincidir con lo reproducido
    if resumen is not None:
        esperado = [f"colocadas={colocadas}", f"ocupadas={ocupadas}", f"mayor={mayor}"]
        if resumen.lstrip("#").split() != esperado:
            return False, (f"El resumen '{resumen}' no coincide con lo "
                           f"reproducido: {' '.join(esperado)}"), metricas
    return True, "OK", metricas


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python -m tileup.validador INSTANCIA SOLUCION")
        sys.exit(2)
    try:
        inst = leer_instancia(sys.argv[1])
    except InstanciaInvalidaError as e:
        print(f"ERROR: {e}")
        sys.exit(2)
    ok, msg, met = validar(inst, sys.argv[2])
    print("LEGAL" if ok else f"ILEGAL: {msg}")
    if met:
        print(met)
    sys.exit(0 if ok else 1)
