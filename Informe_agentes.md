
# Informe 

Este informe documenta la formulación completa del problema de TileUp y el diseño de los agentes desarrollados para resolverlo. 

---

## 1. Descripción del juego y formulación del problema

### 1.1 Qué es TileUp?

TileUp es un juego de rompecabezas en el que se colocan fichas sobre un tablero. Cada ficha tiene dos valores: un color y un número. Cuando se coloca una ficha, se revisan las fichas adyacentes; si hay dos o más fichas adyacentes del mismo color, se fusionan en una sola. El valor de la ficha fusionada es la suma de los valores de las fichas que la componen. La secuencia de fichas por colocar es fija y se conoce por completo desde el inicio de la partida.

A partir de la observación del juego se pueden extraer las siguientes conclusiones:

1. **Es determinista.** Si se coloca una ficha en una posición dada, el resultado es siempre el mismo.
2. **Es completamente observable.** El tablero es visible en todo momento y se conoce el orden de las fichas por venir.
3. **Puede ser finito o infinito.** Existen modos de juego con un número finito de fichas (el motor del juego tiene un fin) y modos infinitos (como el *Endless Mode*). Este informe se centra en el modo finito. (https://www.reddit.com/r/TileUp/comments/1x0b35m/tile_up_endless_mode_october_7/) 
4. **Tiene un factor de ramificación muy alto.** Bajo una estrategia óptima, en cada paso se pueden colocar piezas juntas para fusionarlas, en lados aleatorios, o en el mismo lado pero con valores distintos. El espacio de búsqueda crece exponencialmente.

### 1.2 Representación del estado

El estado del tablero se representa como una tupla de filas y columnas. Cada ficha se representa como una tupla de dos valores: color y número. En consecuencia, el estado completo es una tupla de tuplas.

El estado es manejado por el motor del juego y se le pasa al agente. El agente no necesita construir el estado desde cero; lo recibe ya estructurado y opera sobre él.

Un estado es un par de 2 valores; T e i

T es el tablero que es la tupla de la cantidad de tuplas con la cantidad de celdas

i es el indice de la siguiente ficha pendiente que va desde 0 hata M
 
### 1.3 Operador de sucesión

El operador de sucesión también es manejado por el motor y se le pasa al algoritmo de búsqueda. Su funcionamiento es el siguiente:

1. Se revisan las acciones legales (celdas vacías donde se pueda colocar la ficha actual).
2. Se coloca la ficha en la celda elegida.
3. Se revisan las fichas adyacentes. Si hay dos o más fichas adyacentes del mismo color se fusionan y suman valores de las fichas.

### 1.4 Costo de las acciones

El costo de cada acción es **0**. Esto se debe a que la cantidad de fichas o pasos se define al inicio de la partida, sin importar las decisiones que se tomen, siempre se tendrá que colocar la misma cantidad de fichas. Por lo tanto, no hay un costo diferencial entre acciones.  Esto hace que no exista ningun camino mas corto que otro o algo que optimizar, lo que se optimiza es el final de la partida por asi decirlo

### 1.5 Prueba de meta

La condición de meta verifica si ya se colocaron todas las fichas. Si es así, la partida termina con éxito.

La condición de derrota es un poco más compleja: primero verifica si ya se terminó; si no se ha terminado y ya no hay espacio disponible en el tablero, se alcanza la derrota.

En esta parte hay una exclusion mutua, es decir que si se da una condicion(que primero se evalua la meta) inmediatamente se descarta una derrota

## 2. Exploración de algoritmos de búsqueda

### 2.1 Restricciones del problema

La solución debe ser rápida y económica: no debe consumir muchos recursos y debe resolver en un tiempo razonable, ya que el juego toma tiempo. Con esto en mente, se evaluaron las siguientes opciones.

### 2.2 Algoritmos descartados de entrada

- **DFS (Depth-First Search):** dado el alto factor de ramificación, DFS explora caminos extremadamente largos y puede quedar atrapado en ramas improductivas. Es extremadamente ineficiente.
- **BFS (Breadth-First Search):** el número de estados posibles crece exponencialmente con la profundidad. BFS requiere almacenar todos los estados de un nivel, lo cual es inviable en memoria y tiempo.

Ambos fueron descartados por ineficiencia estructural frente al tamaño del espacio de estados.

### 2.3 Algoritmos considerados

#### Greedy

Algoritmo informado a corto plazo: solo ve los nodos que tiene frente a él y sigue el más barato. Se asemeja a DFS en que profundiza una única ruta. Es difícil definir una buena heurística para él y no garantiza eficiencia ni completitud, aunque al ser partidas cortas no debería tener problemas graves.

#### Beam Search

Explora varias ramas en paralelo, lo que consume más memoria que Greedy pero puede encontrar mejores soluciones. También es difícil definir una heurística adecuada y no garantiza completitud ni optimalidad. Sin embargo, su naturaleza de exploración acotada lo hace atractivo para problemas con ramificación alta.

#### A*

El más complejo y con más requerimientos. Requiere una heurística admisible para garantizar completitud y optimalidad. Al almacenar los caminos no útiles, es más pesado en memoria. Si la heurística no es admisible, se pierden las garantías.

### 2.4 Propuesta de heurística para Beam

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

## 2.5 Admisibilidad

La heuristica no es admisible, esto es porque en una admisible se puede garantizar que la heuristica sea optima.  Esto es debido a que varias fichas pueden estar en el mismo lugar o debido al posicionamiento de alguna de un color distinto.

Lo que se pierde a la hora de que no sea admisible, se pierde a la garantia de que sea optima. Esto no es algo importante ya que con beam search no se garantiza que sea optimo del todo. 

Lo que se gana en cambio es que es mejor escalable, la heuristica es mas facil de manejar y se puede ajustar mejor los parametros.


---

## 3. Agente evolutivo


Algoritmo genético generacional con elitismo y decodificación indirecta, escrito desde cero (sin librerías de computación evolutiva). El agente planifica la partida completa antes de colocar la primera ficha. 



---

## 3. 1. Formulación del agente

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

## 3. 2. Función de aptitud

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

## 3. 3. Población inicial

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

## 3. 4. Operadores evolutivos

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

## 3. 5. Reemplazo, caché y criterios de parada

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

## 3. 6. Hiperparámetros

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

## 3. 7. Determinismo

Los criterios de parada por óptimo, estancamiento y generaciones son
deterministas. Toda la aleatoriedad viene de un único `random.Random(semilla)`
creado al inicio de `resolver()`.

El criterio por tiempo es la única fuente de no-determinismo: depende de
la velocidad de la máquina. Para reproducibilidad estricta se recomienda
usar límites de tiempo holgados, o confiar en los otros criterios.

---
##  Referencias

- Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern
  Approach* (4th ed.). Pearson.
- Woodruff, C. (2025). *Day 31: Best Practices for Tuning Genetic
  Algorithm Parameters*. woodruff.dev
- Material del curso IC-6200, Tecnológico de Costa Rica.
- Especificación oficial de la Tarea Corta 1 (TC1-tileup).

