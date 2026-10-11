# Motor y validador de TileUp

Este documento describe el **motor de reglas** (`tileup/motor.py`), el **validador independiente** (`tileup/validador.py`) y las **pruebas** que los respaldan (`tests/test_motor.py`, `tests/test_validador.py`). Explica qué hace cada pieza, cómo funciona por dentro y por qué se diseñó así.

**Contenido**

1. El juego en una página
2. Regla de fusión (con las aclaraciones del profesor)
3. El motor: diseño, funcionamiento y justificación
4. Formatos de archivo
5. El validador independiente: diseño, funcionamiento y justificación
6. Restricciones del enunciado que se respetan
7. Pruebas: estrategia, qué cubre cada archivo y cómo ejecutarlas
8. Limitaciones y notas
9. Declaración de uso de IA

---

## 1. El juego en una página

- Tablero de **N × N** celdas, inicialmente vacío.
- Una secuencia de **M fichas** conocida de antemano; cada ficha es `(color, valor)`, con color en `1..K` y valor entero positivo.
- En cada turno se toma la siguiente ficha de la secuencia (orden fijo, no se puede cambiar) y se coloca en **una celda vacía** `p`. No hay gravedad ni restricción de columna.
- **Fusión** (ver §2): si al colocarla queda junto a fichas de su mismo color, todo ese grupo se funde en una sola ficha cuyo valor es la suma.
- **Victoria**: se colocaron las M fichas.
- **Derrota**: quedan fichas por colocar y no hay celdas vacías.
- **Objetivo**: terminar con el **menor número de celdas ocupadas** posible. La ficha mayor se reporta como métrica informativa.

---

## 2. Regla de fusión (con las aclaraciones del profesor)

Al colocar la ficha `(c, v)` en la celda `p`:

1. La ficha se coloca **primero** en `p`.
2. Se calcula `G`: la **componente conexa ortogonal** (arriba, abajo, izquierda, derecha; sin diagonales) de fichas del **mismo color `c`** que **contiene a `p`**.
3. Si `|G| ≥ 2`, se retiran todas las fichas de `G` y queda **una sola ficha `(c, suma de los valores de G)` en `p`**.
4. Si `|G| = 1` (ninguna vecina del mismo color), el tablero no cambia más.
5. **No hay fusión en cadena**: la ficha resultante no se vuelve a evaluar en ese turno.

Dos aclaraciones del profesor, que el motor y el validador cumplen de forma explícita:

| Aclaración | Qué significa en el código |
|---|---|
| **`p ∈ G`**: la ficha recién colocada forma parte del grupo que se combina. | El recorrido parte de `p` y `G` siempre incluye a `p`; el valor de la ficha nueva entra en la suma. |
| **La fusión ocurre en la celda donde se colocó la última ficha.** | La ficha resultante queda en `p`; todas las demás celdas de `G` quedan vacías. |

Consecuencias útiles:

- La **suma total** de valores en el tablero siempre es la suma de las fichas colocadas (invariante; está probado).
- Como las fichas de colores distintos nunca se fusionan, al final quedan **al menos tantas celdas ocupadas como colores distintos** haya en la secuencia. Esta cota inferior sirve de criterio de paro en los agentes.
- Una forma en L, o cualquier grupo conexo, se une completo, no solo los vecinos directos de `p`.

### Ejemplo (del enunciado)

N=4, K=3, secuencia `(1,2) (2,1) (1,3) (3,1) (1,1) (2,4)`, celdas `(0,0) (1,1) (0,1) (2,2) (0,2) (1,2)`.

1. `(1,2)` en (0,0).
2. `(2,1)` en (1,1).
3. `(1,3)` en (0,1): vecina del color 1 en (0,0) → fusión, queda `(1,5)` en **(0,1)**; (0,0) queda vacía.
4. `(3,1)` en (2,2).
5. `(1,1)` en (0,2): se une con (0,1) → `(1,6)` en (0,2).
6. `(2,4)` en (1,2): se une con (1,1) → `(2,5)` en (1,2).

Resultado: 3 celdas ocupadas, ficha mayor 6. Está cubierto por `test_ejemplo_del_enunciado` (motor) y `test_acepta_ejemplo_del_enunciado` (validador).

---

## 3. El motor (`tileup/motor.py`)

### 3.1 Idea general

El motor es un **sistema de transiciones puro**: dado un estado y una acción (una celda), calcula el estado siguiente. No guarda nada entre llamadas, no usa variables globales y no toma decisiones: solo aplica las reglas. Las decisiones las toman los agentes.

Esta separación responde a dos exigencias del enunciado:

- El motor debe ser **independiente de los agentes**, y ninguno de los dos puede alterar sus reglas.
- Dos ejecuciones con la misma instancia, agente y semilla deben producir la misma solución; por tanto el motor no puede introducir aleatoriedad ni depender del entorno.

### 3.2 Representación de los datos

- `Instancia(n, k, m, secuencia)`: datos fijos de la partida. `secuencia` es una tupla de `(color, valor)` en el orden en que se colocan.
- `Estado(tablero, indice_siguiente)`: lo que cambia durante la partida. `tablero` es una tupla de tuplas; cada celda es `None` (vacía) o una ficha `(color, valor)`. `indice_siguiente` es la posición en la secuencia de la próxima ficha por colocar.
- Ambas son `dataclass(frozen=True)`: **inmutables y hashables**. Ninguna función modifica un estado; `aplicar_accion` siempre devuelve **uno nuevo**.

### 3.3 Decisiones de diseño y su justificación

**Por qué datos inmutables.**
1. *Búsqueda sin deshacer cambios.* El agente de búsqueda expande muchos estados a partir de uno solo. Con estados mutables, cada rama tendría que copiar el estado o deshacer sus cambios, y un error ahí corrompe la búsqueda sin avisar. Con estados inmutables el original queda intacto.
2. *Estados hashables.* Una tupla de tuplas puede ser clave de un `dict` o miembro de un `set`. El beam search la usa para eliminar estados repetidos y el evolutivo para su caché de evaluaciones.
3. *Menos errores de aliasing.* Dos ramas nunca comparten por accidente un tablero que luego una de ellas modifica.
4. *Pruebas simples.* Se puede verificar que el estado original no cambió tras aplicar una acción.

El costo es copiar el tablero en cada jugada, O(N²), aceptable para los tamaños del curso.

**Por qué `None` o `(color, valor)` por celda.** No hace falta una estructura aparte para saber qué está vacío: "ocupada" es simplemente `celda is not None`. La ficha es una tupla, así que también es inmutable y hashable.

**Por qué la secuencia no vive en el estado.** El estado solo guarda el índice de la siguiente ficha; la secuencia es un dato fijo de la `Instancia`. Así el estado es pequeño, y dos estados con el mismo tablero y el mismo índice son realmente el mismo estado (clave para deduplicar en la búsqueda). Además la **victoria** queda definida de forma limpia: `indice_siguiente >= M`.

**Por qué una acción es solo una celda.** La ficha que se coloca no se elige: la dicta el orden de la secuencia. El factor de ramificación en un estado es el número de celdas vacías, tal como describe el enunciado.

**Por qué las celdas legales salen en orden fila-columna.** `acciones_legales` devuelve siempre el mismo orden. Ese orden fijo es lo que hace deterministas a los agentes: si recorrieran un conjunto sin orden, dos corridas con la misma semilla podrían diferir.

### 3.4 Funciones

| Función | Qué hace |
|---|---|
| `estado_inicial(instancia)` | Tablero vacío, `indice_siguiente = 0`. |
| `celdas_vacias(estado)` | Lista de celdas `(fila, col)` vacías, en orden de lectura. |
| `acciones_legales(estado, instancia)` | Celdas donde se puede colocar la siguiente ficha; lista vacía si ya se ganó. |
| `es_meta(estado, instancia)` | `True` si `indice_siguiente >= M`. |
| `es_derrota(estado, instancia)` | `True` si quedan fichas y no hay celdas vacías. Excluyente con `es_meta`. |
| `celdas_ocupadas(estado)` | Número de celdas con ficha (la métrica a minimizar). |
| `ficha_mayor(estado)` | Mayor valor presente en el tablero (0 si está vacío). |
| `suma_total(estado)` | Suma de valores en el tablero (la usan las pruebas como invariante). |
| `_componente_conexa(tablero, origen)` | Recorrido ortogonal desde `origen`: devuelve `G` (incluye al origen) con las celdas conectadas del mismo color. |
| `_tablero_con_cambios(tablero, cambios)` | Construye un tablero nuevo aplicando `{celda: ficha o None}`; reutiliza las filas que no cambian. |
| `aplicar_accion(estado, instancia, celda)` | Coloca la siguiente ficha en `celda`, aplica la fusión (§2) y devuelve el nuevo estado. |
| `leer_instancia(ruta)` | Lee y valida el archivo de instancia. |
| `escribir_solucion(ruta, jugadas, estado_final)` | Escribe el archivo de solución con la línea de resumen. |

### 3.5 `aplicar_accion` paso a paso

1. **Validar.** Si la partida ya terminó, la celda está fuera del tablero o está ocupada, lanza `AccionInvalidaError`. El motor falla de forma explícita en vez de aceptar jugadas ilegales en silencio.
2. **Colocar primero.** La ficha va a `p` en un tablero temporal *antes* de mirar a los vecinos. Así se implementa `p ∈ G`: la ficha nueva ya es parte del grupo, y su valor entra en la suma.
3. **Calcular `G`.** `_componente_conexa` recorre desde `p` los vecinos ortogonales del mismo color, usando una pila (recorrido en profundidad iterativo) y un conjunto de visitados para no repetir celdas. El orden en que se visitan las celdas no importa: el conjunto `G` resultante es el mismo.
4. **Fusionar si `|G| ≥ 2`.** Se suma el valor de todas las celdas de `G`, se vacían todas y se escribe en **`p`** la ficha `(color, suma)`. Si `|G| = 1`, el tablero temporal ya es el definitivo.

El orden "vaciar todo `G` y luego escribir en `p`" es lo que garantiza que la ficha resultante quede en `p` y las demás celdas de `G` queden libres, como aclaró el profesor.

### 3.6 Por qué no hay fusión en cadena

`_componente_conexa` se invoca **una sola vez**, sobre la ficha recién colocada, y su resultado no se vuelve a evaluar. Si el nuevo grupo quedara junto a otras fichas, solo se fusionarían si fueran del mismo color, pero entonces ya habrían sido parte de `G`. El enunciado indica expresamente que no hay cadenas.

### 3.7 Por qué `es_meta` y `es_derrota` son excluyentes

- Victoria: ya se colocaron las M fichas.
- Derrota: queda al menos una ficha pendiente **y** no hay celdas vacías.

Si el tablero queda lleno justo con la última ficha, eso **es victoria**, no derrota. Por eso `es_derrota` comprueba primero `es_meta`. Así no se cuenta como perdida una partida que sí se completó.

### 3.8 Lectura de instancias y escritura de soluciones

- `leer_instancia` ignora líneas vacías y comentarios con `#`, y valida: que haya `N K` y `M`; que `N` y `K` sean enteros positivos; que la cantidad de líneas de ficha coincida con `M`; que cada color esté en `1..K` y cada valor sea positivo. Cualquier problema lanza `InstanciaInvalidaError` con un mensaje legible que incluye el número de línea. También captura `OSError` y `UnicodeDecodeError`.
- Esto responde a la exigencia del enunciado: un archivo mal formado produce un **mensaje de error legible y un código de salida distinto de cero, nunca una traza de excepción sin controlar**.
- `escribir_solucion` escribe las jugadas realizadas (aunque la partida termine en derrota) y una línea de resumen `# colocadas=… ocupadas=… mayor=…`, que luego el validador comprueba.

### 3.9 Qué NO hace el motor (a propósito)

- No decide jugadas ni usa heurísticas.
- No usa aleatoriedad.
- No imprime tableros ni dibuja nada (el enunciado no lo exige; si se quiere visualizar, va en un módulo aparte para no ensuciar el motor).
- No conoce a los agentes ni al CLI.

Esto lo mantiene pequeño, verificable y fácil de probar de forma aislada.

### 3.10 Errores y complejidad

- `InstanciaInvalidaError`: archivo ilegible, mal codificado o con formato o valores fuera de rango.
- `AccionInvalidaError`: celda fuera del tablero, celda ocupada o partida ya terminada.
- `celdas_vacias`, `acciones_legales`, `celdas_ocupadas`, `ficha_mayor`: O(N²). `aplicar_accion`: O(N²) (copia de filas afectadas y recorrido acotado por el número de celdas). Memoria por estado: O(N²).
- Se prefirió recalcular métricas en vez de guardar contadores dentro del estado: es un poco más lento, pero no hay datos redundantes que puedan quedar inconsistentes.

---

## 4. Formatos de archivo

**Instancia** (se ignoran líneas vacías y comentarios que empiezan con `#`):

```
N K
M
color valor      # M líneas, color en 1..K, valor entero ≥ 1
```

**Solución**: una línea por jugada, `indice fila columna` (índice desde 0 y en orden; fila y columna desde 0), y una línea final de resumen:

```
0 0 0
1 1 1
...
# colocadas=6 ocupadas=3 mayor=6
```

---

## 5. El validador independiente (`tileup/validador.py`)

### 5.1 Para qué sirve y por qué es independiente

El enunciado exige un validador **independiente de los agentes**: comprueba que una solución escrita en un archivo es legal, y que las métricas informadas coinciden con las reales. Si el validador usara la misma lógica del motor, un error del motor pasaría desapercibido (se "validaría a sí mismo"). Por eso:

- **Reimplementa** la colocación y la fusión con su propio recorrido, sin llamar a `aplicar_accion`, `_componente_conexa`, `es_meta`, etc.
- Solo reutiliza `leer_instancia`, que es lectura de datos y no lógica del juego.
- Una prueba (`test_validador_no_reutiliza_la_logica_de_juego_del_motor`) vigila por código que esto se mantenga.
- Otra prueba compara validador y motor sobre 300 partidas aleatorias: si discreparan en la interpretación de las reglas, fallaría.

### 5.2 Cómo funciona

`validar(instancia, ruta_solucion)` reconstruye la partida jugada por jugada sobre un tablero propio (lista de listas, mutable porque aquí no hay búsqueda que proteger):

1. Lee el archivo (UTF-8). Si no se puede abrir, devuelve ilegal.
2. Ignora líneas vacías; las que empiezan con `#` se guardan como línea de resumen.
3. Para cada línea de jugada comprueba, en este orden:
   - que tenga exactamente **3 enteros**;
   - que no haya **más colocaciones que fichas** (M);
   - que el **índice** sea el esperado (0, 1, 2, … sin saltos ni repeticiones: la secuencia no se puede alterar);
   - que la celda esté **dentro del tablero**;
   - que la celda esté **vacía** en ese momento (considerando las fusiones previas).
4. Aplica la regla de fusión del §2 con su propio recorrido por componentes conexas (con índice sobre una lista, es decir, en anchura).
5. Al final calcula las métricas: `colocadas`, `ocupadas`, `mayor`, `meta` (se colocaron las M fichas) y `derrota` (quedaron fichas pendientes con el tablero lleno).
6. Si había línea de resumen, exige que **coincida** con lo reproducido. Un resumen que no coincide hace la solución ilegal, y se devuelven igualmente las métricas reales.

Una solución puede ser **parcial** (terminar en derrota): es legal si todas sus jugadas lo son; las métricas reportan `meta=False, derrota=True`.

### 5.3 Valor de retorno

`validar` devuelve `(es_legal, mensaje, metricas)`, con `metricas = {colocadas, ocupadas, mayor, meta, derrota}`. Si la solución falla antes de poder reproducirse (por ejemplo, línea mal formada), `metricas` es `None`.

### 5.4 Uso por línea de comandos y códigos de salida

```bash
python -m tileup.validador instancias/mediana.txt sol.txt
```

| Código | Significado |
|---|---|
| 0 | Solución legal (imprime `LEGAL` y las métricas). |
| 1 | Solución ilegal (imprime `ILEGAL: motivo`). |
| 2 | Error de entrada (instancia inválida o argumentos incorrectos). |

Separar los códigos permite que un script distinga "la solución es incorrecta" de "me pasaron mal los archivos". Una instancia mal formada se informa con un mensaje, sin traza de excepción.

### 5.5 Qué detecta el validador

| Falla | Ejemplo |
|---|---|
| Celda ocupada | Colocar dos veces en la misma celda. |
| Índice fuera de orden | Saltarse una ficha, repetirla o no empezar en 0. |
| Fuera del tablero | Fila o columna negativa o ≥ N. |
| Más colocaciones que fichas | Líneas de jugada de sobra. |
| Línea mal formada | No son 3 enteros, o no son números. |
| Resumen alterado | `colocadas`, `ocupadas` o `mayor` que no coinciden con la reproducción. |
| Archivo ilegible | No existe o no es texto UTF-8. |

---

## 6. Restricciones del enunciado que se respetan

- Solo biblioteca estándar en motor, validador y agentes (`heapq`, `random`, `dataclasses`, …); `matplotlib` solo para las gráficas del informe y `pytest` para las pruebas. Sin librerías de búsqueda en grafos, frameworks evolutivos, solvers CSP/SAT ni LLM en ejecución, y sin un motor de juego de terceros.
- Motor **determinista**: sin aleatoriedad; el único azar de los agentes viene de la semilla.
- Motor **puro e inmutable**: sin estado global ni efectos secundarios (salvo leer y escribir archivos en las funciones de E/S).
- Motor **independiente de los agentes**: ningún agente puede alterar sus reglas.
- Validador **independiente** del motor y de los agentes (§5.1).
- Archivos mal formados: mensaje de error legible y código de salida distinto de cero, nunca traza sin controlar.
- Un único punto de entrada por línea de comandos (`python -m tileup.cli ...`) con límite de tiempo `--tiempo`.

---

## 7. Pruebas

### 7.1 Estrategia

El enunciado pide que las pruebas unitarias verifiquen el motor **de forma aislada**, con al menos estos casos: fusión de dos fichas, fusión de una componente de tres o más, colocación sin fusión y detección de derrota. Además pide pruebas de integración que resuelvan una instancia pequeña de principio a fin y comprueben con el validador que la solución es legal.

Se organizaron así:

- **`tests/test_motor.py`**: pruebas unitarias del motor, sin agentes ni validador.
- **`tests/test_validador.py`**: pruebas del validador (aceptación, cada tipo de rechazo, la regla del profesor, concordancia con el motor y línea de comandos).
- **`tests/test_integracion.py`**: resuelve una instancia con los agentes y valida el resultado (se documenta aparte).

Criterios que se siguieron:

- **Una prueba, una regla.** Cada prueba comprueba un comportamiento concreto, de modo que el nombre de la prueba que falla dice qué regla se rompió.
- **Casos construidos a mano**, con tableros pequeños y resultados que se pueden verificar a ojo.
- **Regresión con el ejemplo del enunciado**, que fija el comportamiento correcto.
- **Pruebas de propiedades** (invariante de suma, concordancia con 300 partidas aleatorias con semilla fija, de modo que son reproducibles).
- **Casos negativos**: cada error documentado tiene al menos una prueba que lo provoca.

### 7.2 `tests/test_motor.py` (22 casos)

| Tema | Qué comprueba |
|---|---|
| Colocación sin fusión | La ficha queda en la celda; las demás no cambian. |
| Fusión de dos fichas, en `p` | Dos fichas del mismo color se funden **en la celda de la última ficha**; la otra celda queda libre. |
| `p ∈ G` y forma en L | Un grupo no lineal se funde completo; la suma es correcta. |
| Componente de tres o más | Se funden todas las fichas conectadas del color. |
| Colores distintos | No se fusionan. |
| Sin fusión en cadena | La ficha resultante no dispara otra fusión en el mismo turno. |
| Victoria y derrota | `es_meta` y `es_derrota` correctos y excluyentes (la derrota se construye con un patrón de ajedrez para evitar fusiones). |
| Acciones inválidas | Celda ocupada, fuera de rango o partida terminada → `AccionInvalidaError`. |
| Inmutabilidad | `aplicar_accion` no modifica el estado original. |
| Lectura de instancias | Un caso válido y 5 casos inválidos parametrizados. |
| Escritura de solución | Formato y línea de resumen. |
| Invariante de suma | La suma total se conserva tras las fusiones. |
| Ejemplo del enunciado | Reproduce 3 celdas ocupadas y ficha mayor 6. |

### 7.3 `tests/test_validador.py` (24 casos)

| Tema | Qué comprueba |
|---|---|
| Aceptación | Ejemplo del PDF; solución sin línea de resumen; solución parcial que termina en derrota. |
| Regla del profesor | La fusión queda en `p` (repetir `p` es ilegal y la celda del vecino queda libre); forma en L; sin cadena. |
| Rechazos | Celda ocupada; índice fuera de orden o que no empieza en 0; fuera del tablero (incluye negativos); más colocaciones que fichas; línea con ≠ 3 enteros; valores no enteros; resumen alterado (3 variantes); archivo inexistente; archivo binario. |
| Independencia | El código del validador no menciona funciones de juego del motor. |
| Concordancia | 300 partidas aleatorias (semilla fija): validador y motor coinciden en colocadas, ocupadas, mayor y meta, y el muestreo incluye derrotas. |
| Línea de comandos | Códigos 0, 1 y 2 (instancia mal formada sin traza; argumentos incorrectos). |

### 7.4 Cómo ejecutarlas

```bash
python -m pytest tests/ -v
```

Resultado esperado: **46 pruebas pasan** entre `test_motor.py` y `test_validador.py` (las de integración y agentes se cuentan aparte).

---

## 8. Limitaciones y notas

- El validador reproduce la partida completa: O(M · N²). Es suficiente para las instancias del curso.
- El motor recalcula métricas recorriendo el tablero; se priorizó la simplicidad sobre la velocidad.
- Si un agente corta por tiempo, el resultado puede depender de la velocidad de la máquina; con la misma semilla y sin corte por tiempo, el resultado es idéntico.
- La visualización del tablero no forma parte del motor ni de lo que exige el enunciado.

---

## 9. Declaración de uso de IA

Se utilizó un asistente de IA (Claude) como apoyo para revisar la interpretación del enunciado, proponer la estructura del motor y del validador, y redactar pruebas y esta documentación. El equipo revisó, ejecutó y comprendió el código, verificó las reglas contra el ejemplo del enunciado y las aclaraciones del profesor, y es responsable del resultado final.

*(Completar con los nombres de los integrantes y con el detalle definitivo del uso de IA en la declaración global del README.)*
