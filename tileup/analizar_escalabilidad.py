"""
Análisis del CSV de escalabilidad: tabla resumen + gráfica de tendencia.

Produce:
    - resultados/tabla_resumen.csv: promedio y desviación por (agente, N, K)
    - resultados/escalabilidad_por_N.png: ocupadas vs N, por agente
    - resultados/escalabilidad_por_K.png: ocupadas vs K, por agente
"""
import csv
import os
import statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def leer_csv(ruta="resultados/escalabilidad.csv"):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def agrupar(filas, campo):
    """Devuelve {clave: [valores]} donde clave = (agente, n, k)."""
    grupos = defaultdict(list)
    for fila in filas:
        v = fila.get(campo, "")
        if v in ("", None):
            continue
        clave = (fila["agente"], int(fila["n"]), int(fila["k"]))
        grupos[clave].append(float(v))
    return grupos


def tabla_resumen(filas, ruta="resultados/tabla_resumen.csv"):
    columnas = ["colocadas", "ocupadas", "tiempo", "esfuerzo"]
    filas_out = []
    for campo in columnas:
        for (agente, n, k), valores in agrupar(filas, campo).items():
            filas_out.append({
                "agente": agente, "n": n, "k": k, "metrica": campo,
                "media": round(st.mean(valores), 4),
                "desv": round(st.pstdev(valores), 4) if len(valores) > 1 else 0.0,
                "n_semillas": len(valores),
            })
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=filas_out[0].keys())
        w.writeheader()
        w.writerows(filas_out)
    print(f"Tabla resumen → {ruta}")


def graficar_por_N(filas, ruta="resultados/escalabilidad_por_N.png"):
    """Ocupadas promedio vs N, con una línea por agente (promedio sobre K)."""
    plt.figure()
    for agente in sorted({f["agente"] for f in filas}):
        puntos = defaultdict(list)
        for fila in filas:
            if fila["agente"] != agente:
                continue
            if fila["ocupadas"] == "":
                continue
            puntos[int(fila["n"])].append(float(fila["ocupadas"]))
        ns = sorted(puntos)
        ys = [st.mean(puntos[n]) for n in ns]
        plt.plot(ns, ys, marker="o", label=agente)
    plt.xlabel("N (tamaño del tablero)")
    plt.ylabel("Celdas ocupadas (promedio sobre K y semillas)")
    plt.title("Escalabilidad: efecto de N")
    plt.legend()
    plt.grid(True)
    plt.savefig(ruta, dpi=120)
    plt.close()
    print(f"Gráfica → {ruta}")


def graficar_por_K(filas, ruta="resultados/escalabilidad_por_K.png"):
    """Ocupadas promedio vs K, con una línea por agente (promedio sobre N)."""
    plt.figure()
    for agente in sorted({f["agente"] for f in filas}):
        puntos = defaultdict(list)
        for fila in filas:
            if fila["agente"] != agente:
                continue
            if fila["ocupadas"] == "":
                continue
            puntos[int(fila["k"])].append(float(fila["ocupadas"]))
        ks = sorted(puntos)
        ys = [st.mean(puntos[k]) for k in ks]
        plt.plot(ks, ys, marker="s", label=agente)
    plt.xlabel("K (número de colores)")
    plt.ylabel("Celdas ocupadas (promedio sobre N y semillas)")
    plt.title("Escalabilidad: efecto de K")
    plt.legend()
    plt.grid(True)
    plt.savefig(ruta, dpi=120)
    plt.close()
    print(f"Gráfica → {ruta}")


if __name__ == "__main__":
    filas = leer_csv("resultados/escalabilidad.csv")
    tabla_resumen(filas)
    graficar_por_N(filas)
    graficar_por_K(filas)