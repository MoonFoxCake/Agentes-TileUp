"""
Comparacion de los agentes segun lo pedido, con los parametros dados
Uso:
    python experimento_comparacion.py
"""
import csv
import os
import subprocess
import sys
import time
from pathlib import Path

from tileup.generador_instancias import generar_instancia

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = PACKAGE_DIR.parent
INSTANCIAS_DIR = ROOT / "instancias_experimento"
RESULTADOS_DIR = ROOT / "resultados"
CSV_SALIDA = RESULTADOS_DIR / "Comparacion_experimental.csv"

#Configuraciones para usar
CONFIGURACIONES = [
    {"N": 4, "K": 2, "M": 6,  "semilla_gen": 1},
    {"N": 4, "K": 3, "M": 10, "semilla_gen": 2},
    {"N": 5, "K": 3, "M": 12, "semilla_gen": 3},
    {"N": 6, "K": 3, "M": 15, "semilla_gen": 4},
    {"N": 6, "K": 4, "M": 20, "semilla_gen": 5},
    {"N": 8, "K": 4, "M": 25, "semilla_gen": 6},
]

SEMILLAS = [1, 42, 123]      #3 semillas
AGENTES = ["busqueda", "evolutivo"]
TIEMPO_LIMITE = 10           # segundos maximos


def generar_todas_las_instancias():
    #Genera las instancias de prueba
    INSTANCIAS_DIR.mkdir(exist_ok=True)
    rutas = []
    for i, cfg in enumerate(CONFIGURACIONES):
        nombre = f"inst_{i}_N{cfg['N']}_K{cfg['K']}_M{cfg['M']}.txt"
        ruta = INSTANCIAS_DIR / nombre
        if not ruta.exists():
            contenido = generar_instancia(
                cfg["N"], cfg["K"], cfg["M"], cfg["semilla_gen"]
            )
            ruta.write_text(contenido, encoding="utf-8")
        rutas.append((ruta, cfg))
    return rutas



def parsear_salida_cli(stdout):
    # Parsea el output para poder guardar los resultados en un csv
    datos = {}
    for linea in stdout.splitlines():
        if "=" in linea:
            k, v = linea.split("=", 1)
            datos[k.strip()] = v.strip()
    return datos

def correr_una_vez(ruta_inst, agente, semilla, tiempo):
    # llama al cli para las instancias
    salida_tmp = ROOT / "sol_experimento.txt"
    cmd = [
        sys.executable, "-m", "tileup.cli",
        "--instancia", str(ruta_inst),
        "--agente", agente,
        "--semilla", str(semilla),
        "--tiempo", str(tiempo),
        "--salida", str(salida_tmp),
    ]
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
    # Esto es para que si encuentre los errores
    
    
    if r.returncode != 0:
        return None, r.stderr.strip()[:200]

    datos = parsear_salida_cli(r.stdout)
    esfuerzo = datos.get("nodos_expandidos") or datos.get("evaluaciones_aptitud", "")
    return {
        "colocadas": datos.get("colocadas", ""),
        "ocupadas": datos.get("ocupadas", ""),
        "tiempo": datos.get("tiempo", ""),
        "esfuerzo": esfuerzo,
    }, None



def main():
    RESULTADOS_DIR.mkdir(exist_ok=True)
    instancias = generar_todas_las_instancias()

    total = len(instancias) * len(AGENTES) * len(SEMILLAS)
    hechas = 0
    filas = []

    for ruta, cfg in instancias:
        print(f"\n=== N={cfg['N']}, K={cfg['K']}, M={cfg['M']} ===")
        for agente in AGENTES:
            for semilla in SEMILLAS:
                hechas += 1
                datos, err = correr_una_vez(ruta, agente, semilla, TIEMPO_LIMITE)
                if err:
                    print(f"  [{hechas}/{total}] {agente} s={semilla}: ERROR {err}")
                    continue

                fila = {
                    "agente": agente,
                    "n": cfg["N"],
                    "k": cfg["K"],
                    "m": cfg["M"],
                    "semilla": semilla,
                    "instancia": ruta.name,
                    "colocadas": datos["colocadas"],
                    "ocupadas": datos["ocupadas"],
                    "tiempo": datos["tiempo"],
                    "esfuerzo": datos["esfuerzo"],
                }
                filas.append(fila)
                print(f"  [{hechas}/{total}] {agente} semilla={semilla}: "
                      f"coloc={fila['colocadas']}, ocup={fila['ocupadas']}, "
                      f"t={fila['tiempo']}segundos, esfuerzo={fila['esfuerzo']}")

    if not filas:
        print("Sin resultados. Abortando.")
        return

    with open(CSV_SALIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas[0].keys())
        w.writeheader()
        w.writerows(filas)

    print(f"\nResultados guardados en {CSV_SALIDA}")
    print(f"Total de corridas exitosas: {len(filas)}/{total}")

if __name__ == "__main__":
    main()