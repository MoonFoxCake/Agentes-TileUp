"""Generador de instancias de TileUp parametrizado por N, K, M y semilla."""
import random


def generar_instancia(n: int, k: int, m: int, semilla: int) -> str:
    rng = random.Random(semilla)
    lineas = [f"{n} {k}", str(m)]
    for _ in range(m):
        lineas.append(f"{rng.randint(1, k)} {rng.randint(1, 9)}")
    return "\n".join(lineas) + "\n"


def escribir_instancia(ruta: str, n: int, k: int, m: int, semilla: int) -> None:
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(generar_instancia(n, k, m, semilla))