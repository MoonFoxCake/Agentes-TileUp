
# TileUp — Agentes de búsqueda y evolutivos (Tarea Corta 1, IC-6200)

Este README es el manual de ejecución del proyecto: requisitos, instalación, ejecución de agentes, pruebas automatizadas, formatos de entrada y salida, y la estructura del repositorio.

**Integrantes**

| Nombre | Carné |
|---|---|
| Ignacio Castillo Montero | 2021579556 |
| Natalia Sofía Rodríguez Slano | 2021033307 |
| Estefanía Delgado Castillo | 2018112159 |

---

## 1. Requisitos

| Qué | Versión | Para qué |
|---|---|---|
| Python | 3.10 o superior (probado en 3.13 y 3.14) | todo |
| `pytest` | ≥ 8 | pruebas |
| `matplotlib` | ≥ 3.8 | solo las gráficas de escalabilidad |

El motor, el validador y los dos agentes usan solo la biblioteca estándar de Python. Para ejecutar un agente no hace falta instalar nada: `pytest` y `matplotlib` solo se necesitan para las pruebas y las gráficas.

### 1.1 Dependencias que necesita cada parte

| Parte | Comando principal | Dependencias externas | ¿Hay que instalar algo? |
|---|---|---|---|
| Agentes, motor, CLI, validador, generador de instancias | `python -m tileup.cli ...` | Ninguna (solo biblioteca estándar: `argparse`, `random`, `time`, `dataclasses`) | No |
| Batería de escalabilidad (correr) | `python -m tileup.experimento_escalabilidad` | Ninguna (usa `csv`, `os`, `time`) | No |
| Pruebas | `python -m pytest` | `pytest` | Sí: `pip install -r requirements.txt` |
| Gráficas y tabla de escalabilidad | `python -m tileup.analizar_escalabilidad` | `matplotlib` (trae `numpy`, `pillow` y otras automáticamente) | Sí: `pip install -r requirements.txt` |

---

# 2. Instalación automatizada

El repositorio incluye un script `setup_and_menu.py` que crea un entorno virtual, instala las dependencias y ofrece un menú interactivo para ejecutar todos los comandos del proyecto.

### 2.1 Instalación rápida

Desde la raíz del proyecto:

```bash
python setup_and_menu.py --install
```

Esto crea la carpeta `.venv/`, instala `pytest` y `matplotlib` desde `requirements.txt`, y termina.


# 3. Menú interactivo (`setup_and_menu.py`)

Ejecuta el script sin argumentos para abrir el menú:

```bash
python setup_and_menu.py
```

El menú ofrece:

```
========================================================
  MENÚ TILEUP
========================================================
  --- Instalación ---
   1. Instalar todo (entorno + dependencias)

  --- Agentes ---
   2. Ejecutar agente (búsqueda / evolutivo)
   3. Validar una solución
   4. Generar instancia
   5. Ver y validar soluciones en resultados/

  --- Pruebas automatizadas ---
   6. Todas las pruebas (verbose, línea por test)
   7. Todas las pruebas (resumen)
   8. Pruebas unitarias (motor + validador)
   9. Pruebas de integración
  10. Pruebas de agentes
  11. Elegir archivo de prueba específico
  12. Buscar prueba por nombre (-k)

   0. Salir
--------------------------------------------------------
```

### Características del menú

*   **Listado automático de instancias**: al ejecutar un agente o validar, el script muestra los archivos `.txt` dentro de `instancias/` y permite elegir por número. También acepta rutas manuales.
*   **Salidas en `resultados/`**: por defecto, las soluciones se guardan en la carpeta `resultados/` con un nombre automático como `sol_busqueda_grande.txt`. Si el usuario escribe un nombre corto (ej. `sol.txt`), se redirige automáticamente a `resultados/`.
*   **Verificación posterior**: después de ejecutar un agente, el script comprueba que el archivo realmente se creó. Si quedó en la raíz por error, lo mueve a `resultados/`.
*   **Vista de soluciones**: la opción 5 lista las soluciones guardadas, muestra su tamaño y permite validarlas o ver su contenido.

---

## 4. Ejecución de agentes (CLI)

También puedes ejecutar los agentes directamente con `tileup.cli` sin usar el menú.

### Comando

```bash
python -m tileup.cli --instancia RUTA --agente {busqueda|evolutivo} --semilla S --tiempo SEGUNDOS [--salida ARCHIVO]
```

| Argumento | Obligatorio | Significado |
|---|---|---|
| `--instancia` | sí | Ruta del archivo de instancia. |
| `--agente` | sí | `busqueda` (beam search) o `evolutivo` (algoritmo genético). |
| `--semilla` | sí | Semilla del generador aleatorio. La búsqueda es determinista y la ignora. |
| `--tiempo` | sí | Límite de tiempo en segundos. |
| `--salida` | no | Archivo de solución (por defecto `solucion.txt`). |

**Parámetros opcionales de cada agente** (los valores por defecto son los del informe):

| Agente | Opciones |
|---|---|
| `evolutivo` | `--poblacion 100` `--generaciones 400` `--torneo 3` `--p-cruce 0.9` `--mut-factor 2.0` `--elitismo 3` `--estancamiento 100` `--margen-tiempo 0.9` |
| `busqueda` | `--w 50` (ancho del beam) `--beta 1.0` (peso del lookahead) |

`python -m tileup.cli --help` muestra la lista completa.

### Ejemplos

**Agente de búsqueda (beam search)** — es determinista: no usa la semilla.

```bash
# Ejemplo del enunciado
python -m tileup.cli --instancia instancias/ejemplo_enunciado.txt --agente busqueda --semilla 1 --tiempo 10 --salida resultados/sol_busqueda.txt

# Con un beam más ancho
python -m tileup.cli --instancia instancias/grande.txt --agente busqueda --semilla 1 --tiempo 10 --w 100 --salida resultados/sol_busqueda_w100.txt
```

**Agente evolutivo (algoritmo genético)** — depende de la semilla.

```bash
# Dos semillas distintas
python -m tileup.cli --instancia instancias/grande.txt --agente evolutivo --semilla 1 --tiempo 5 --salida resultados/sol_evolutivo_s1.txt
python -m tileup.cli --instancia instancias/grande.txt --agente evolutivo --semilla 2 --tiempo 5 --salida resultados/sol_evolutivo_s2.txt

# Con una población mayor
python -m tileup.cli --instancia instancias/grande.txt --agente evolutivo --semilla 1 --tiempo 10 --poblacion 200 --salida resultados/sol_evolutivo_p200.txt
```

### Métricas por salida estándar

**Búsqueda:**
```
agente=busqueda
instancia=instancias/ejemplo_enunciado.txt
semilla=1
colocadas=6
ocupadas=3
mayor=6
tiempo=0.043
nodos_expandidos=2956
w=50
beta=1.0
salida=resultados/sol_busqueda.txt
```

**Evolutivo:**
```
agente=evolutivo
instancia=instancias/ejemplo_enunciado.txt
semilla=1
colocadas=6
ocupadas=3
mayor=6
tiempo=0.004
evaluaciones_aptitud=100
generaciones=0
motivo_paro=optimo (cota inferior)
salida=resultados/sol_evolutivo.txt
```

| Campo | Significado |
|---|---|
| `colocadas` | Fichas colocadas de la secuencia. |
| `ocupadas` | Celdas ocupadas al terminar. |
| `mayor` | Valor de la ficha mayor al terminar. |
| `tiempo` | Segundos transcurridos. |
| `nodos_expandidos` | Medida de esfuerzo de la búsqueda: estados sucesores generados. |
| `evaluaciones_aptitud` | Medida de esfuerzo del evolutivo: cromosomas evaluados (sin contar los repetidos de la caché). |
| `generaciones`, `motivo_paro` | Generaciones recorridas y por qué paró: `optimo (cota inferior)`, `estancamiento`, `tiempo` o `generaciones`. |

---

## 5. Formatos de entrada y salida

### Instancia

Archivo de texto plano. Las líneas en blanco y las que empiezan con `#` se ignoran. El resto se lee en este orden: una línea `N K`, una línea `M`, y `M` líneas `color valor`, en el orden en que deben colocarse.

```
# Ejemplo del enunciado: tablero 4x4, 3 colores, 6 fichas
4 3
6
1 2
2 1
1 3
3 1
1 1
2 4
```

| Símbolo | Significado | Restricción |
|---|---|---|
| `N` | Lado del tablero (N × N). | entero ≥ 1 |
| `K` | Cantidad de colores. | entero ≥ 1 |
| `M` | Cantidad de fichas. | entero ≥ 0 |
| `color` | Color de la ficha. | entero entre 1 y K |
| `valor` | Valor de la ficha. | entero positivo |

### Solución

Una línea por colocación, en el orden de la secuencia, con tres enteros: índice de la ficha (desde 0), fila y columna de la celda (ambas desde 0). La última línea empieza con `#` y resume el resultado.

```
0 0 0
1 1 1
2 0 1
3 2 2
4 0 2
5 1 2
# colocadas=6 ocupadas=3 mayor=6
```

---

## 6. Validar una solución

```bash
python -m tileup.validador INSTANCIA SOLUCION
```

El validador reproduce la partida paso a paso con su propia implementación de las reglas; no comparte código de decisión con el motor ni con los agentes: solo reutiliza el lector de instancias.

**Salida de una solución correcta:**
```
LEGAL
{'colocadas': 6, 'ocupadas': 3, 'mayor': 6, 'meta': True, 'derrota': False}
```

**Salida de una incorrecta:**
```
ILEGAL: ...
```

| Código de salida | Significado |
|---|---|
| 0 | La solución es legal. |
| 1 | La solución es ilegal. |
| 2 | Error de entrada (instancia mal formada, archivo inexistente, argumentos). |

Lo que verifica: tres enteros por línea, índices consecutivos desde 0, celda dentro del tablero, celda libre, no más colocaciones que fichas, y que la línea `# colocadas=... ocupadas=... mayor=...` coincida con lo que realmente resulta de reproducir la partida.

---

## 7. Generar instancias

Desde el menú (opción 4) o directamente:

```bash
python -c "from tileup.generador_instancias import escribir_instancia; escribir_instancia('instancias/mi_instancia.txt', n=6, k=4, m=60, semilla=7)"
```

Los argumentos son `n`, `k`, `m` y `semilla`. La misma combinación produce siempre el mismo archivo.

---

## 8. Pruebas automatizadas

### Comando general

```bash
python -m pytest -q
```

Para ver el detalle de cada prueba: `python -m pytest -v`. Deben pasar las 62 pruebas:

| Archivo | Pruebas | Qué cubre |
|---|---|---|
| `tests/test_motor.py` | 22 | Fusión de 2 fichas, fusión de 3 o más (componentes en L), colocación sin fusión, detección de victoria y derrota, inmutabilidad del estado, ejemplo del enunciado. |
| `tests/test_validador.py` | 24 | Aceptación y rechazo de cada tipo de ilegalidad, regla de fusión (p ∈ G, queda en p), independencia respecto del motor, 300 partidas aleatorias motor vs validador, códigos de salida. |
| `tests/test_agentes.py` | 14 | Ambos agentes por línea de comandos: solución legal y completa, cota inferior, métricas coherentes con el validador, misma semilla ⇒ misma solución, derrota, límite de tiempo, instancia mal formada. |
| `tests/test_integracion.py` | 2 | Resuelve una instancia pequeña de principio a fin y comprueba con el validador que es legal. |

### Desde el menú

*   **Opción 6**: todas las pruebas en modo verbose (`pytest -v`).
*   **Opción 7**: todas las pruebas en modo resumen (`pytest -q`).
*   **Opción 8**: pruebas unitarias de motor y validador.
*   **Opción 9**: pruebas de integración.
*   **Opción 10**: pruebas de agentes.
*   **Opción 11**: elegir un archivo de prueba específico.
*   **Opción 12**: buscar pruebas por nombre (`pytest -k patron`).

### Ejecutar solo una parte (línea de comandos)

```bash
python -m pytest tests/test_motor.py -v
python -m pytest tests/test_agentes.py -v
```

Resultado esperado:
```
62 passed in ~8s
```

---

## 9. Estudio de escalabilidad

Compara los dos agentes al crecer el tablero (N) y la cantidad de colores (K).

**Prueba rápida (≈ 20 s):**
```bash
python -m tileup.experimento_escalabilidad --rapido
python -m tileup.analizar_escalabilidad
```

**Batería completa (≈ 20–35 min):**
```bash
python -m tileup.experimento_escalabilidad
python -m tileup.analizar_escalabilidad
```

| | Rápida | Completa |
|---|---|---|
| N | 5, 7 | 5, 7, 10 |
| K | 3, 5 | 3, 5, 8 |
| M | 2·N² | 2·N² |
| Instancias por configuración | 1 | 3 |
| Semillas del agente | 1 | 3 |
| Límite por corrida | 3 s | 15 s |

**Opciones**: `--agentes busqueda evolutivo` (por defecto corren los dos) y `--salida RUTA` (CSV de salida).

**Qué se genera:**

| Archivo | Contenido |
|---|---|
| `instancias/escalabilidad/` | Las instancias generadas. |
| `soluciones/escalabilidad/` | Una solución por corrida (se pueden verificar con el validador). |
| `resultados/escalabilidad.csv` | Una fila por corrida: agente, N, K, M, semillas, colocadas, ocupadas, mayor, tiempo, esfuerzo. |
| `resultados/tabla_resumen.csv` | Media y desviación estándar entre semillas, por agente, N y K. |
| `resultados/escalabilidad_por_N.png` | Celdas ocupadas contra N. |
| `resultados/escalabilidad_por_K.png` | Celdas ocupadas contra K. |

Verificar una solución de la batería:
```bash
python -m tileup.validador instancias/escalabilidad/<instancia>.txt soluciones/escalabilidad/<solucion>.txt
```

---

## 10. Comparación experimental del núcleo

El script `comparacion_experimental.py` ejecuta una batería de configuraciones para comparar ambos agentes bajo distintas condiciones. El enunciado exige al menos 6 configuraciones y 3 semillas por configuración.

```bash
python -m tileup.comparacion_experimental
```

Este comando genera un CSV con los resultados y deja las soluciones en `resultados/comparacion_experimental/`. Las configuraciones incluyen variaciones de N, K y M, y se ejecutan con las semillas 1, 2 y 3 para cada agente. Los resultados se pueden analizar con las mismas herramientas de escalabilidad.

---

## 11. Estructura del repositorio

```
Agentes-TileUp/
├── pytest.ini
├── requirements.txt
├── setup_and_menu.py          # instalador y menú interactivo
├── README.md
├── tileup/                    # paquete principal
│   ├── __init__.py
│   ├── cli.py
│   ├── motor.py
│   ├── validador.py
│   ├── generador_instancias.py
│   ├── experimento_escalabilidad.py
│   ├── analizar_escalabilidad.py
│   └── comparacion_experimental.py
├── tests/
│   ├── test_motor.py
│   ├── test_validador.py
│   ├── test_agentes.py
│   └── test_integracion.py
├── instancias/                # instancias de entrada
│   ├── ejemplo_enunciado.txt
│   └── ...
├── resultados/                # soluciones, CSV y gráficas
└── .venv/                     # entorno virtual (generado por setup_and_menu.py)
```

