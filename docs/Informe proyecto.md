
# Informe 

Este informe documenta la formulación completa del problema de TileUp y el diseño de los agentes desarrollados para resolverlo. 

---
## Motor y validador de TileUp

## Motor

###  Idea general

El motor es un sistema de transiciones; dado un estado y una acción (una celda), calcula el estado siguiente; no guarda nada entre llamadas, no usa variables globales y no toma decisiones, solo aplica las reglas y las decisiones las toman los agentes.

Esta separación responde a dos exigencias:

- Este es independiente de los agentes, y ninguno de los dos puede alterar sus reglas.
- Dos ejecuciones con la misma instancia, agente y semilla deben producir la misma solución; por tanto el motor no puede introducir aleatoriedad ni depender del entorno.

### Representación de los datos

El motor guarda la información en dos objetos, separados según si cambian o no durante la partida.

- Instancia: lo que NO cambia durante la partida (viene del archivo de entrada).
- n: el tamaño del tablero (N × N).
- k: la cantidad de colores distintos.
- m: la cantidad total de fichas que hay que colocar.
- Secuencia: corresponde a la lista de las M fichas, en el orden exacto en que van saliendo; y cada ficha se guarda como con su respectivo color y valor. Por ejemplo, (1, 3) es una ficha de color 1 con valor 3. El orden no se puede cambiar.

- Estado: corresponde a lo que puede ser la foto de la partida en un momento dado (esto sí cambia con cada jugada).
- Tablero: la cuadrícula; cada celda está vacía ("None") o tiene una ficha (color, valor).
- indice_siguiente: el número de la próxima ficha que falta por colocar; esta empieza en 0, y cuando llega a M ya se colocaron todas (es decir, una victoria).

Estos objetos son inmutables, es decir, una vez creados no se modifican; cuando se coloca una ficha, el motor no cambia el estado anterior, sino que crea uno nuevo. 

###  Decisiones de diseño del motor

#### Datos inmutables
Se decidió que los datos fueran inmutables de manera que, una vez creado un dato no se puede modificar, es decir, si se quiere hacer un cambio, no se edita el tablaro o partida original, si no que se crea uno nuevo con el cambio aplicado. Las razones porque se tomó la desición de hacerlo así son las siguinetes:

1. Búsqueda sin deshacer cambios: el agente de búsqueda expande muchos estados a partir de uno solo; con estados mutables, cada rama tendría que copiar el estado o deshacer sus cambios, y un error ahí corrompe la búsqueda sin avisar; y con los estados inmutables el original queda intacto.
2. Estados hashables: una tupla de tuplas puede ser clave de un "dict2 o miembro de un "set". El beam search la usa para eliminar estados repetidos y el evolutivo para su caché de evaluaciones.
3. Menos errores de aliasing: dos ramas nunca comparten por accidente un tablero que luego una de ellas modifica.
4. Pruebas simples: se puede verificar que el estado original no cambió tras aplicar una acción.

Cada celda del tablero guarda "None" si está vacía, o una ficha "(color, valor)" si está ocupada; con esta representación no hace falta ninguna estructura extra para saber qué celdas están libres: una celda está ocupada cuando su contenido no es "None". La ficha también es una tupla, así que es inmutable y se puede usar como clave de un diccionario o guardar en un conjunto, igual que el resto del estado; e
l costo de que los datos sean inmutables es que cada jugada crea una copia del tablero, lo que toma tiempo proporcional a N², algo aceptable para los tamaños que se usan en el curso.

La lista de fichas por colocar no se guarda dentro del estado. Como esa lista no cambia durante la partida, vive en la "Instancia", y el estado solo guarda el índice de la ficha que sigue. Esto tiene dos ventajas. Primero, el estado es pequeño, y dos estados con el mismo tablero y el mismo índice son realmente el mismo estado, lo que permite a la búsqueda descartar repetidos. Segundo, saber si se ganó es muy simple: la partida está ganada cuando "indice_siguiente >= M", es decir, cuando ya no quedan fichas.

Una acción se describe únicamente con la celda donde se coloca la ficha, porque la ficha en sí no se elige: siempre es la que corresponde según el orden de la secuencia, es por eso que, en un estado dado, las jugadas posibles son tantas como celdas vacías haya, que es el factor de ramificación. La función "acciones_legales" devuelve esas celdas siempre en el mismo orden (por filas, de izquierda a derecha). Esto es importante para el determinismo: si los agentes recorrieran las celdas en un orden que puede variar, dos ejecuciones con la misma semilla podrían dar soluciones distintas.

### Funciones

| Función                                        | Qué hace                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| estado_inicial(instancia)                      | Tablero vacío, indice_siguiente = 0.                                                                                                                                                                                                                                                                                                                               |
| celdas_vacias(estado)                          | Lista de celdas (fila, col) vacías, en orden de lectura.                                                                                                                                                                                                                                                                                                           |
| acciones_legales(estado, instancia)            | Celdas donde se puede colocar la siguiente ficha; lista vacía si ya se ganó.                                                                                                                                                                                                                                                                                       |
| es_meta(estado, instancia)                     | Devuelve "True" cuando la partida está ganada: ya se colocaron todas las fichas de la secuencia ("indice_siguiente >= M"), sin importar cuántas celdas queden ocupadas.                                                                                                                                                                                            |
| es_derrota(estado, instancia)                  | Devuelve "True" cuando la partida está perdida: todavía quedan fichas por colocar, pero el tablero está lleno y no hay ninguna celda libre donde ponerlas. Si ya se colocaron todas las fichas devuelve "False", aunque el tablero esté lleno, porque en ese caso la partida se ganó ("es_meta2). Por eso una partida nunca puede ser victoria y derrota a la vez. |
| celdas_ocupadas(estado)                        | Número de celdas con ficha (la métrica a minimizar).                                                                                                                                                                                                                                                                                                               |
| ficha_mayor(estado)                            | Mayor valor presente en el tablero (0 si está vacío).                                                                                                                                                                                                                                                                                                              |
| suma_total(estado)                             | Suma de valores en el tablero (la usan las pruebas como invariante).                                                                                                                                                                                                                                                                                               |
| _componente_conexa(tablero, origen)            | Recorrido ortogonal desde origen: devuelve "G" (incluye al origen) con las celdas conectadas del mismo color.                                                                                                                                                                                                                                                      |
| _tablero_con_cambios(tablero, cambios)         | Construye un tablero nuevo aplicando "{celda: ficha o None}"; reutiliza las filas que no cambian.                                                                                                                                                                                                                                                                  |
| aplicar_accion(estado, instancia, celda)       | Coloca la siguiente ficha en "celda", aplica la fusión y devuelve el nuevo estado.                                                                                                                                                                                                                                                                                 |
| leer_instancia(ruta)                           | Lee y valida el archivo de instancia.                                                                                                                                                                                                                                                                                                                              |
| escribir_solucion(ruta, jugadas, estado_final) | Escribe el archivo de solución con la línea de resumen.                                                                                                                                                                                                                                                                                                            |

### "aplicar_accion" paso a paso

1. Validar: si la partida ya terminó, la celda está fuera del tablero o está ocupada, lanza "AccionInvalidaError". El motor falla de forma explícita en vez de aceptar jugadas ilegales en silencio.
2. Colocar primero: La ficha va a "p" en un tablero temporal antes de mirar a los vecinos. Así se implementa p ∈ G: la ficha nueva ya es parte del grupo, y su valor entra en la suma.
3. Calcular "G": "\_componente_conexa" recorre desde "p" los vecinos ortogonales del mismo color, usando una pila (recorrido en profundidad iterativo) y un conjunto de visitados para no repetir celdas. El orden en que se visitan las celdas no importa: el conjunto "G" resultante es el mismo.
4. Fusionar si |G| ≥ 2: se suma el valor de todas las celdas de "G", se vacían todas y se escribe en "p" la ficha (color, suma). Si |G| = 1, el tablero temporal ya es el definitivo.

El orden "vaciar todo "G" y luego escribir en "p"" es lo que garantiza que la ficha resultante quede en "p" y las demás celdas de "G" queden libres, como aclaró el profesor.

### Por qué no hay fusión en cadena

componente_conexa se invoca una sola vez, sobre la ficha recién colocada, y su resultado no se vuelve a evaluar. Si el nuevo grupo quedara junto a otras fichas, solo se fusionarían si fueran del mismo color, pero entonces ya habrían sido parte de "G". El enunciado indica expresamente que no hay cadenas.



### Lectura de instancias y escritura de soluciones

- "leer_instancia" ignora líneas vacías y comentarios con #, y valida: que haya N, K y M; que N y K sean enteros positivos; que la cantidad de líneas de ficha coincida con M; que cada color esté en 1..K y cada valor sea positivo. Cualquier problema lanza "InstanciaInvalidaError" con un mensaje legible que incluye el número de línea; también captura "OSError" y "UnicodeDecodeError".
- Esto responde a la exigencia del enunciado: un archivo mal formado produce un mensaje de error legible y un código de salida distinto de cero, nunca una traza de excepción sin controlar.
- "escribir_solucion" escribe las jugadas realizadas (aunque la partida termine en derrota) y una línea de resumen # colocadas=… ocupadas=… mayor=…, que luego el validador comprueba.

### Aspectos importantes del motor

- No decide jugadas ni usa heurísticas.
- No usa aleatoriedad.
- No imprime tableros ni dibuja nada (el enunciado no lo exige; si se quiere visualizar, va en un módulo aparte para no ensuciar el motor).
- No conoce a los agentes ni al CLI.

Esto lo mantiene pequeño, verificable y fácil de probar de forma aislada.

### Errores y complejidad

- "InstanciaInvalidaError": archivo ilegible, mal codificado o con formato o valores fuera de rango.
- "AccionInvalidaError`: celda fuera del tablero, celda ocupada o partida ya terminada.
- "celdas_vacias", "acciones_legales", "celdas_ocupadas", "ficha_mayor": O(N²). "aplicar_accion": O(N²) (copia de filas afectadas y recorrido acotado por el número de celdas). Memoria por estado: O(N²).
- Se prefirió recalcular métricas en vez de guardar contadores dentro del estado: es un poco más lento, pero no hay datos redundantes que puedan quedar inconsistentes.


## Formatos de archivo

**Instancia** (se ignoran líneas vacías y comentarios que empiezan con #):

```
N K
M
color valor      # M líneas, color en 1..K, valor entero ≥ 1
```

**Solución**: una línea por jugada, indice fila columna (donde índice desde 0 y en orden; fila y columna desde 0), y una línea final de resumen:

```
0 0 0
1 1 1
...
# colocadas=6 ocupadas=3 mayor=6
```


## El validador independiente

Un validador independiente de los agentes comprueba que una solución escrita en un archivo es legal, y que las métricas informadas coinciden con las reales. Si el validador usara la misma lógica del motor, un error del motor pasaría desapercibido (se "validaría a sí mismo"). Por eso:

- Reimplementa la colocación y la fusión con su propio recorrido, sin llamar a "aplicar_accion", "_componente_conexa", "es_meta", etc.
- Solo reutiliza "leer_instancia", que es lectura de datos y no lógica del juego.
- Una prueba vigila por código que esto se mantenga.
- Otra prueba compara validador y motor sobre 300 partidas aleatorias: si discreparan en la interpretación de las reglas, fallaría.

### Cómo funciona

La función "validar(instancia, ruta_solucion)" reconstruye la partida jugada por jugada sobre un tablero propio (lista de listas, mutable porque aquí no hay búsqueda que proteger):

1. Lee el archivo (UTF-8). Si no se puede abrir, devuelve ilegal.
2. Ignora líneas vacías; las que empiezan con # se guardan como línea de resumen.
3. Para cada línea de jugada comprueba, en este orden:
   - que tenga exactamente 3 enteros;
   - que no haya más colocaciones que fichas (M);
   - que el índice sea el esperado (0, 1, 2, … sin saltos ni repeticiones: la secuencia no se puede alterar);
   - que la celda esté dentro del tablero;
   - que la celda esté **vacía** en ese momento (considerando las fusiones previas).
4. Aplica la regla de fusión con su propio recorrido por componentes conexas (con índice sobre una lista, es decir, en anchura).
5. Al final calcula las métricas: colocadas, ocupada, mayor, meta (se colocaron las M fichas) y derrota (quedaron fichas pendientes con el tablero lleno).
6. Si había línea de resumen, exige que coincida con lo reproducido; un resumen que no coincide hace la solución ilegal, y se devuelven igualmente las métricas reales.

Una solución puede ser parcial (terminar en derrota): es legal si todas sus jugadas lo son; las métricas reportan "meta=False, derrota=True".

### Valor de retorno

"validar" devuelve "es_legal", mensaje, metricas, con "metricas = {colocadas, ocupadas, mayor, meta, derrota}". Si la solución falla antes de poder reproducirse (por ejemplo, línea mal formada), `metricas` es `None`.

### Uso por línea de comandos y códigos de salida

```bash
python -m tileup.validador instancias/mediana.txt sol.txt
```

| Código | Significado                                                     |
| ------ | --------------------------------------------------------------- |
| 0      | Solución legal (imprime `LEGAL` y las métricas).                |
| 1      | Solución ilegal (imprime `ILEGAL: motivo`).                     |
| 2      | Error de entrada (instancia inválida o argumentos incorrectos). |

Separar los códigos permite que un script distinga "la solución es incorrecta" de "me pasaron mal los archivos". Una instancia mal formada se informa con un mensaje, sin traza de excepción.

### Qué detecta el validador

| Falla | Ejemplo |
|---|---|
| Celda ocupada | Colocar dos veces en la misma celda. |
| Índice fuera de orden | Saltarse una ficha, repetirla o no empezar en 0. |
| Fuera del tablero | Fila o columna negativa o ≥ N. |
| Más colocaciones que fichas | Líneas de jugada de sobra. |
| Línea mal formada | No son 3 enteros, o no son números. |
| Resumen alterado | colocadas, ocupadas o mayor que no coinciden con la reproducción. |
| Archivo ilegible | No existe o no es texto UTF-8. |



## Pruebas

### Estrategia

Las pruebas unitarias se organizaron de la siguiente manera:

- test_motor.py: pruebas unitarias del motor, sin agentes ni validador.
- test_validador.py: pruebas del validador (aceptación, cada tipo de rechazo, la regla del profesor, concordancia con el motor y línea de comandos).
- test_integracion.py: resuelve una instancia con los agentes y valida el resultado (se documenta aparte).
Todo esto esta en la carpeta de tests

Criterios que se siguieron:

- **Una prueba, una regla:** Cada prueba comprueba un comportamiento concreto, de modo que el nombre de la prueba que falla dice qué regla se rompió.
- **Casos construidos a mano:** con tableros pequeños y resultados que se pueden verificar a ojo.
- **Regresión con el ejemplo del enunciado:** que fija el comportamiento correcto.
- **Pruebas de propiedades:** invariante de suma, concordancia con 300 partidas aleatorias con semilla fija, de modo que son reproducibles.
- **Casos negativos:** cada error documentado tiene al menos una prueba que lo provoca.

### tests/test_motor.py

| Tema | Qué comprueba |
|---|---|
| Colocación sin fusión | La ficha queda en la celda; las demás no cambian. |
| Fusión de dos fichas, en p | Dos fichas del mismo color se funden **en la celda de la última ficha**; la otra celda queda libre. |
| p ∈ G y forma en L | Un grupo no lineal se funde completo; la suma es correcta. |
| Componente de tres o más | Se funden todas las fichas conectadas del color. |
| Colores distintos | No se fusionan. |
| Sin fusión en cadena | La ficha resultante no dispara otra fusión en el mismo turno. |
| Victoria y derrota | "es_meta" y "es_derrota" correctos y excluyentes (la derrota se construye con un patrón de ajedrez para evitar fusiones). |
| Acciones inválidas | Celda ocupada, fuera de rango o partida terminada, entonces "AccionInvalidaError". |
| Inmutabilidad | "aplicar_accion" no modifica el estado original. |
| Lectura de instancias | Un caso válido y 5 casos inválidos parametrizados. |
| Escritura de solución | Formato y línea de resumen. |
| Invariante de suma | La suma total se conserva tras las fusiones. |
| Ejemplo del enunciado | Reproduce 3 celdas ocupadas y ficha mayor 6. |



## Algoritmo de busqueda

Este algoritmo es el opuesto al evolutivo, este usara distinto al evolutivo

##  Descripción del juego y formulación del problema

### Qué es TileUp?

TileUp es un juego de rompecabezas en el que se colocan fichas sobre un tablero. Cada ficha tiene dos valores: un color y un número. Cuando se coloca una ficha, se revisan las fichas adyacentes; si hay dos o más fichas adyacentes del mismo color, se fusionan en una sola. El valor de la ficha fusionada es la suma de los valores de las fichas que la componen. La secuencia de fichas por colocar es fija y se conoce por completo desde el inicio de la partida.

A partir de la observación del juego se pueden extraer las siguientes conclusiones:

1. **Es determinista.** Si se coloca una ficha en una posición dada, el resultado es siempre el mismo.
2. **Es completamente observable.** El tablero es visible en todo momento y se conoce el orden de las fichas por venir.
3. **Puede ser finito o infinito.** Existen modos de juego con un número finito de fichas (el motor del juego tiene un fin) y modos infinitos (como el *Endless Mode*). Este informe se centra en el modo finito. (https://www.reddit.com/r/TileUp/comments/1x0b35m/tile_up_endless_mode_october_7/) 
4. **Tiene un factor de ramificación muy alto.** Bajo una estrategia óptima, en cada paso se pueden colocar piezas juntas para fusionarlas, en lados aleatorios, o en el mismo lado pero con valores distintos. El espacio de búsqueda crece exponencialmente.

###  Representación del estado

El estado del tablero se representa como una tupla de filas y columnas. Cada ficha se representa como una tupla de dos valores: color y número. En consecuencia, el estado completo es una tupla de tuplas.

El estado es manejado por el motor del juego y se le pasa al agente. El agente no necesita construir el estado desde cero; lo recibe ya estructurado y opera sobre él.

Un estado es un par de 2 valores; T e i

T es el tablero que es la tupla de la cantidad de tuplas con la cantidad de celdas

i es el indice de la siguiente ficha pendiente que va desde 0 hata M
 
### Operador de sucesión

El operador de sucesión también es manejado por el motor y se le pasa al algoritmo de búsqueda. Su funcionamiento es el siguiente:

1. Se revisan las acciones legales (celdas vacías donde se pueda colocar la ficha actual).
2. Se coloca la ficha en la celda elegida.
3. Se revisan las fichas adyacentes. Si hay dos o más fichas adyacentes del mismo color se fusionan y suman valores de las fichas.

### Costo de las acciones

El costo de cada acción es **0**. Esto se debe a que la cantidad de fichas o pasos se define al inicio de la partida, sin importar las decisiones que se tomen, siempre se tendrá que colocar la misma cantidad de fichas. Por lo tanto, no hay un costo diferencial entre acciones.  Esto hace que no exista ningun camino mas corto que otro o algo que optimizar, lo que se optimiza es el final de la partida por asi decirlo

###  Prueba de meta

La condición de meta verifica si ya se colocaron todas las fichas. Si es así, la partida termina con éxito.

La condición de derrota es un poco más compleja: primero verifica si ya se terminó; si no se ha terminado y ya no hay espacio disponible en el tablero, se alcanza la derrota.

En esta parte hay una exclusion mutua, es decir que si se da una condicion(que primero se evalua la meta) inmediatamente se descarta una derrota

##  Exploración de algoritmos de búsqueda

###  Restricciones del problema

La solución debe ser rápida y económica: no debe consumir muchos recursos y debe resolver en un tiempo razonable, ya que el juego toma tiempo. Con esto en mente, se evaluaron las siguientes opciones.


###  Algoritmos descartados de entrada

- **DFS (Depth-First Search):** dado el alto factor de ramificación, DFS explora caminos extremadamente largos y puede quedar atrapado en ramas improductivas. Es extremadamente ineficiente.
- **BFS (Breadth-First Search):** el número de estados posibles crece exponencialmente con la profundidad. BFS requiere almacenar todos los estados de un nivel, lo cual es inviable en memoria y tiempo.

Ambos fueron descartados por ineficiencia estructural frente al tamaño del espacio de estados.

### Algoritmos considerados

#### Greedy

Algoritmo informado a corto plazo: solo ve los nodos que tiene frente a él y sigue el más barato. Se asemeja a DFS en que profundiza una única ruta. Es difícil definir una buena heurística para él y no garantiza eficiencia ni completitud, aunque al ser partidas cortas no debería tener problemas graves.

#### Beam Search

Explora varias ramas en paralelo, lo que consume más memoria que Greedy pero puede encontrar mejores soluciones. También es difícil definir una heurística adecuada y no garantiza completitud ni optimalidad. Sin embargo, su naturaleza de exploración acotada lo hace atractivo para problemas con ramificación alta.

#### A*

El más complejo y con más requerimientos. Requiere una heurística admisible para garantizar completitud y optimalidad. Al almacenar los caminos no útiles, es más pesado en memoria. Si la heurística no es admisible, se pierden las garantías.

###  Propuesta de heurística para Beam

La heurística diseñada combina el costo presente con un estimado del potencial de fusión futuro. Se definen las siguientes cantidades:

T(s): número de celdas ocupadas en el estado s.
vivos(s): conjunto de colores que tienen al menos una ficha en el tablero.
c:un color cualquiera del juego (c ∈ {1, ..., K}).
σ_c(s): número de celdas vacías adyacentes a componentes del color c (slots de fusión).
freq(c, i): número de fichas del color c que aparecen en la secuencia desde el paso i hasta el final.
β: peso ajustable del término de lookahead.

Al unir todos estos elementos queda una heuristica algo asi:

```
T(s) − β · Σ{c ∈ vivos(s) min(σ_c(s), freq(c, i))}
```


Aca el T(s) es el presente, mientras mas celdas ocupadas es peor, ya que la heuristica mientras menor mejor,  β reoresenta el futuro ya que es el lookahead, la sumatoria ko que hace es que revisa el tablero para colores, el minimo es para poder ver el menor cantidad de espacios

## Admisibilidad

La heuristica no es admisible, esto es porque en una admisible se puede garantizar que la heuristica sea optima.  Esto es debido a que varias fichas pueden estar en el mismo lugar o debido al posicionamiento de alguna de un color distinto.

Lo que se pierde a la hora de que no sea admisible, se pierde a la garantia de que sea optima. Esto no es algo importante ya que con beam search no se garantiza que sea optimo del todo. 

Lo que se gana en cambio es que es mejor escalable, la heuristica es mas facil de manejar y se puede ajustar mejor los parametros.


---

## Parametros del agente de busqueda

El agente tiene 2 parametros que son los que lo influencian

W y Beta

W se encarga del branching del algoritmo, si se tiene un W alto va a explorar mejor distintos caminitos

Beta lo que hace es de ver que tanto al futuro pone atencion, mientras tenga un Beta chico se queda en el presente, si tiene un Beta grande mas al futuro se enfoca


##  Agente evolutivo

Algoritmo genético generacional con elitismo y decodificación indirecta, escrito desde cero (sin librerías de computación evolutiva). El agente planifica la partida completa antes de colocar la primera ficha. 


---

##  Formulación del agente

### Idea general

En TileUp la secuencia de fichas es fija y se conoce por completo desde el
inicio. Eso significa que la partida queda determinada únicamente por
**dónde** se coloca cada una de las M fichas. El evolutivo busca esa lista
de decisiones.

### Representación del individuo

Cada individuo tiene un **cromosoma**: una lista de M enteros.

```
cromosoma = [g_0, g_1, ..., g_{M-1}]
```

Cada gen `g_i` no es una celda absoluta, sino un **índice sobre las celdas
vacías** en el momento de colocar la ficha `i`:

```
celda_i = celdas_vacias(estado_i)[g_i mod len(celdas_vacias(estado_i))]
```

Esto se llama **codificación indirecta**, y se eligió por tres razones:

**1. Todo cromosoma produce una partida legal.** El módulo acota el índice
al número actual de celdas vacías, así que nunca se puede colocar sobre
una celda ocupada. No hace falta reparar individuos ni penalizar jugadas
ilegales. Eso simplifica muchísimo el resto del algoritmo.

**2. El cromosoma mide M, no N².** El tamaño depende de las decisiones que
hay que tomar, no del tamaño del tablero. Como la fusión libera celdas,
una partida puede colocar más de N² fichas, así que el cromosoma debe
tener una casilla por decisión y no por celda.

**3. Aceptamos la epistasis como costo.** Cambiar un gen temprano cambia
el estado y por tanto el significado de los genes posteriores. Es una
consecuencia inevitable de esta codificación. Para mitigarla, los
operadores de variación están pensados para preservar bloques contiguos
de genes (cruce de dos puntos, mutación de baja probabilidad por gen).

---

##  Función de aptitud

Simulamos la partida con el motor y comparamos cada cromosoma con una
tupla lexicográfica:

```
fitness = (colocadas, -ocupadas_finales, -ocupacion_media)
```

Mayor es mejor. Python compara tuplas elemento por elemento, así que el
primer componente manda, y solo si empatan pasa al segundo.

### Por qué estos tres componentes

- **Colocadas**: es el primer criterio del concurso. Más fichas colocadas
  es mejor, siempre.
- **−Ocupadas finales**: es el segundo criterio del concurso. El signo
  negativo es un truco para que "menos ocupadas" sea "mayor" en la tupla.
  Un tablero con 2 celdas ocupadas da −2, que es mayor que −5.
- **−Ocupación media**: un tercer componente de gradiente. Es el promedio
  de celdas ocupadas a lo largo de la partida. Sirve para desempatar cuando
  muchos individuos tienen las mismas dos primeras componentes, y evita
  mesetas planas en la población. Premia partidas que mantuvieron el
  tablero despejado en el camino, no solo al final.

---

##  Población inicial

- **Tamaño P = 100**.
- **Todos aleatorios**.

Se consideró sembrar parte de la población con un jugador voraz (que en
cada paso elige la celda que deja menos celdas ocupadas tras la fusión),
pero se descartó por dos razones.

**Costo.** Generar un cromosoma voraz cuesta O(M·N²) simulaciones en el
motor. El aleatorio cuesta O(M). Con P=100 y tableros grandes la diferencia
se nota.

**Diversidad.** La siembra voraz concentra la población inicial en un
mismo valle de atracción. El arranque aleatorio maximiza la diversidad y
permite explorar trayectorias que no son obvias a corto plazo.

**Sobre el tamaño.** Woodruff (2025) recomienda 20–100 para problemas
simples y 100–1000 para problemas combinatorios complejos. TileUp es un
problema combinatorio de tamaño moderado, así que P=100 se ubica en el
límite inferior del rango para problemas complejos, ofreciendo un balance
entre diversidad y costo por generación.

La comparación empírica entre arranque aleatorio y arranque mixto queda
como evaluación pendiente.

---

##  Operadores evolutivos

### Selección por torneo (k = 3)

Se eligen 3 individuos al azar con reposición, y el de mejor aptitud es
el padre. Se repite cada vez que se necesita un padre.

**Por qué k=3?** El tamaño del torneo controla la presión selectiva. Con
k=2 la presión es débil y la convergencia lenta. Con k≥5 los mejores
dominan la población demasiado rápido y se pierde diversidad. Woodruff
(2025) usa k=5 en sus ejemplos, pero la práctica común en problemas
combinatorios sitúa el rango útil entre 2 y 5. Se adoptó k=3 como punto
medio. Como todos los parámetros, queda sujeto a validación empírica.

**Por qué torneo y no ruleta?** La ruleta requiere convertir las aptitudes
en probabilidades positivas, y nuestra aptitud es una tupla con valores
negativos. Habría que normalizar de forma arbitraria. El torneo solo
compara con `>`, que funciona directo sobre tuplas.

### Cruce de dos puntos (p_cruce = 0.9)

Con probabilidad 0.9, se eligen dos puntos de corte `i < j` al azar y se
intercambia el bloque central entre los padres:

```
hijo1 = padre[:i] + madre[i:j] + padre[j:]
hijo2 = madre[:i] + padre[i:j] + madre[j:]
```

Se eligió cruce de dos puntos en vez de uniforme porque preserva **bloques
contiguos** de genes. Dada la epistasis, los genes que están juntos suelen
funcionar juntos; romperlos al azar destruye sub-rutinas coherentes.

Woodruff (2025) recomienda tasas de cruce entre 0.6 y 0.9. El valor 0.9 se
ubica en el extremo superior del rango, favoreciendo la recombinación como
motor principal de exploración. El 10% restante de probabilidad de
no-cruce permite que cromosomas de alta aptitud se transmitan intactos.

### Mutación por reset (mut_factor = 2.0)

Cada gen se reemplaza por un entero aleatorio en `[0, N²)` con probabilidad:

```
p_mut = mut_factor / M
```

Con `mut_factor = 2.0`, en promedio mutan 2 genes por hijo,
independientemente del tamaño de M.

**Por qué relativo a M?** La tasa de mutación debe fijarse en relación al tamaño del cromosoma, no en términos absolutos. Si fijáramos `p_mut` como escalar (por ejemplo, 0.05), en cromosomas largos mutarían demasiados genes y en cortos casi ninguno. La formulación relativa mantiene constante el nivel de perturbación.

**Por qué reset y no incremento ±1?** Los genes indexan celdas vacías, y
las celdas vacías cambian en cada paso. Sumar o restar 1 al gen no equivale
a moverse a una celda adyacente, así que no hay búsqueda local real con
ese operador.

Woodruff (2025) da rangos generales de 0.001–0.1 para la tasa de mutación
y recomienda 1/M para cromosomas binarios. Nuestra fórmula es coherente
con esa recomendación.

---

## Reemplazo, caché y criterios de parada

### Generacional con elitismo (E = 3)

Los 3 mejores individuos pasan intactos a la siguiente generación. El
resto se llena con hijos generados por cruce y mutación.

**Por qué E=3?** Russell & Norvig (2021) demuestran que conservar intactos
los mejores individuos garantiza que la aptitud global del sistema no
decrezca entre generaciones. Woodruff (2025) recomienda preservar entre el
1% y el 5% de la población como élites. Con P=100, E=3 es exactamente el
3%, dentro del rango recomendado. E≥5 empieza a congelar la exploración.

### Caché de aptitudes

Mantenemos un diccionario `{tuple(cromosoma): fitness}` para no recalcular
aptitudes de cromosomas ya evaluados.

Los duplicados aparecen por dos vías:

- Los elites pasan intactos de una generación a otra.
- Los hijos que no cruzaron ni mutaron son copias exactas de un padre.

Usamos `OrderedDict` con política LRU: cuando la caché llega a 50 000
entradas, se elimina solo la entrada menos reciente, no toda la caché.
Así preservamos las evaluaciones de la generación en curso.

El contador de evaluaciones que reportamos cuenta solo **simulaciones
reales**, no intentos de evaluar.

### Criterios de paro

El bucle se detiene al cumplirse lo primero de:

1. **Óptimo demostrable.** La fusión nunca elimina la última ficha de un
   color, así que al terminar quedan al menos tantas celdas ocupadas como
   colores distintos aparezcan en la secuencia. Si el mejor individuo
   coloca las M fichas y alcanza esa cota, es óptimo global.
2. **Estancamiento.** 100 generaciones seguidas sin mejorar el récord.
   Russell & Norvig (2021) discuten cómo los algoritmos de búsqueda local
   se quedan atrapados en mesetas, y Woodruff (2025) recomienda 100
   generaciones sin mejora como umbral estándar. Nuestro valor coincide
   con esa recomendación.
3. **Generaciones máximas.** G = 400. Woodruff (2025) usa 1000 en sus
   ejemplos; nuestro valor es más conservador porque el estancamiento y
   el tiempo suelen dispararse antes.
4. **Tiempo.** Se usa a lo sumo el 90% del `--tiempo` recibido, dejando el
   10% para reconstruir la solución y escribir el archivo. La fecha límite
   se revisa antes de cada simulación, no solo al final de la generación.
   Este margen responde al contrato de la especificación, no a una fuente
   externa.

---

##  Hiperparámetros

| Parámetro | Valor | Qué controla |
|---|---|---|
| `poblacion` | 100 | Individuos por generación |
| `generaciones` | 400 | Tope de generaciones |
| `torneo` | 3 | Tamaño del torneo de selección |
| `p_cruce` | 0.9 | Probabilidad de cruce |
| `mut_factor` | 2.0 | Genes mutados esperados por hijo |
| `elitismo` | 3 | Individuos preservados intactos |
| `estancamiento` | 100 | Generaciones sin mejora antes de parar |
| `margen_tiempo` | 0.9 | Fracción del tiempo límite que se usa |

Todos son configurables por línea de comandos. Los valores por defecto
siguen la práctica común en algoritmos genéticos y se plantea validarlos
con barridos experimentales.

---

##  Determinismo

Los criterios de parada por óptimo, estancamiento y generaciones son
deterministas. Toda la aleatoriedad viene de un único `random.Random(semilla)`
creado al inicio de `resolver()`.

El criterio por tiempo es la única fuente de no-determinismo: depende de
la velocidad de la máquina. Para reproducibilidad estricta se recomienda
usar límites de tiempo holgados, o confiar en los otros criterios.

---

## Comparacion experimental


Se tiene un programa hecho para comparar ambos, lo que se hace es que se les dan un set de parametros, y se imprime el resultado:


=== N=4, K=2, M=6 ===
  [1/36] busqueda semilla=1: coloc=6, ocup=2, t=0.044segundos, esfuerzo=3056
  [2/36] busqueda semilla=42: coloc=6, ocup=2, t=0.044segundos, esfuerzo=3056
  [3/36] busqueda semilla=123: coloc=6, ocup=2, t=0.042segundos, esfuerzo=3056
  [4/36] evolutivo semilla=1: coloc=6, ocup=2, t=0.004segundos, esfuerzo=100
  [5/36] evolutivo semilla=42: coloc=6, ocup=2, t=0.011segundos, esfuerzo=290
  [6/36] evolutivo semilla=123: coloc=6, ocup=2, t=0.008segundos, esfuerzo=195

=== N=4, K=3, M=10 ===
  [7/36] busqueda semilla=1: coloc=10, ocup=3, t=0.085segundos, esfuerzo=5638
  [8/36] busqueda semilla=42: coloc=10, ocup=3, t=0.104segundos, esfuerzo=5638
  [9/36] busqueda semilla=123: coloc=10, ocup=3, t=0.083segundos, esfuerzo=5638
  [10/36] evolutivo semilla=1: coloc=10, ocup=3, t=0.074segundos, esfuerzo=1138
  [11/36] evolutivo semilla=42: coloc=10, ocup=3, t=0.025segundos, esfuerzo=386
  [12/36] evolutivo semilla=123: coloc=10, ocup=3, t=0.053segundos, esfuerzo=859

=== N=5, K=3, M=12 ===
  [13/36] busqueda semilla=1: coloc=12, ocup=3, t=0.210segundos, esfuerzo=11850
  [14/36] busqueda semilla=42: coloc=12, ocup=3, t=0.208segundos, esfuerzo=11850
  [15/36] busqueda semilla=123: coloc=12, ocup=3, t=0.207segundos, esfuerzo=11850
  [16/36] evolutivo semilla=1: coloc=12, ocup=3, t=0.266segundos, esfuerzo=3217
  [17/36] evolutivo semilla=42: coloc=12, ocup=3, t=0.822segundos, esfuerzo=9599
  [18/36] evolutivo semilla=123: coloc=12, ocup=3, t=0.344segundos, esfuerzo=4158

=== N=6, K=3, M=15 ===
  [19/36] busqueda semilla=1: coloc=15, ocup=3, t=0.481segundos, esfuerzo=22804
  [20/36] busqueda semilla=42: coloc=15, ocup=3, t=0.483segundos, esfuerzo=22804
  [21/36] busqueda semilla=123: coloc=15, ocup=3, t=0.479segundos, esfuerzo=22804
  [22/36] evolutivo semilla=1: coloc=15, ocup=3, t=1.183segundos, esfuerzo=9969
  [23/36] evolutivo semilla=42: coloc=15, ocup=3, t=1.781segundos, esfuerzo=14684
  [24/36] evolutivo semilla=123: coloc=15, ocup=3, t=0.943segundos, esfuerzo=8135

=== N=6, K=4, M=20 ===
  [25/36] busqueda semilla=1: coloc=20, ocup=4, t=0.719segundos, esfuerzo=29912
  [26/36] busqueda semilla=42: coloc=20, ocup=4, t=0.727segundos, esfuerzo=29912
  [27/36] busqueda semilla=123: coloc=20, ocup=4, t=0.705segundos, esfuerzo=29912
  [28/36] evolutivo semilla=1: coloc=20, ocup=4, t=1.926segundos, esfuerzo=12066
  [29/36] evolutivo semilla=42: coloc=20, ocup=5, t=2.632segundos, esfuerzo=16523
  [30/36] evolutivo semilla=123: coloc=20, ocup=4, t=2.167segundos, esfuerzo=13555

=== N=8, K=4, M=25 ===
  [31/36] busqueda semilla=1: coloc=25, ocup=4, t=2.347segundos, esfuerzo=72564
  [32/36] busqueda semilla=42: coloc=25, ocup=4, t=2.252segundos, esfuerzo=72564
  [33/36] busqueda semilla=123: coloc=25, ocup=4, t=2.282segundos, esfuerzo=72564
  [34/36] evolutivo semilla=1: coloc=25, ocup=7, t=6.603segundos, esfuerzo=28721
  [35/36] evolutivo semilla=42: coloc=25, ocup=6, t=8.980segundos, esfuerzo=37393
  [36/36] evolutivo semilla=123: coloc=25, ocup=6, t=7.504segundos, esfuerzo=32030

Para hacer las comparaciones, se evalua lo siguiente;


El tamaño del tablero, los colores disponibles, la cantidad de fichas

La cantidad de espacios ocupados

La cantidad de fichas que se pusieron

El tiempo que se tardo

La semilla

Y el esfuerzo; el cual en español se refiere a cuantos nodos hizo

##  Referencias

- Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern
  Approach* (4th ed.). Pearson.
- Woodruff, C. (2025). *Day 31: Best Practices for Tuning Genetic
  Algorithm Parameters*. woodruff.dev
- Material del curso
- Especificación oficial de la Tarea Corta 1 (TC1-tileup).
- Udacity. (2016, 6 junio). _Beam search_ [Vídeo]. YouTube. https://www.youtube.com/watch?v=UXW6Cs82UKo
- Efficient NLP. (2023, 6 junio). _How is Beam Search Really Implemented?_ [Vídeo]. YouTube. https://www.youtube.com/watch?v=tOhWpF5-_z4
- Llama Elitista. (2024, 5 septiembre). _¿Por qué este Algoritmo está en tantos Videojuegos? - A* Explicado_ [Vídeo]. YouTube. https://www.youtube.com/watch?v=hQa9JTtq4OkProgramar es increíble. (2019, 26 diciembre). _Cómo funciona el algoritmo A* en los videojuegos_ [Vídeo]. YouTube. https://www.youtube.com/watch?v=1gszEk8rUS4
- Chio Code. (2022, 26 mayo). _Algoritmos voraces | Programación Greedy_ [Vídeo]. YouTube. https://www.youtube.com/watch?v=ALtJncFD8N8

