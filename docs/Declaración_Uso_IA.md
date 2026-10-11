# Declaración de uso de IA

Se utilizó un asistente de IA (Claude) como apoyo para revisar la interpretación del enunciado, proponer la estructura del motor y del validador, y redactar pruebas y esta documentación. El equipo revisó, ejecutó y comprendió el código, verificó las reglas contra el ejemplo del enunciado y las aclaraciones del profesor, y es responsable del resultado final.


## Evolutivo 
Este agente se desarrolló con apoyo de varias herramientas de IA, cada una en una fase distinta. Todas las decisiones de diseño fueron revisadas y validadas por el grupo antes de integrarlas.

**Planeación y estructura del agente.** La fase inicial de planeación —discusión del problema, definición del orden de los pasos (representación, aptitud, población, selección, variación, reemplazo, paro, CLI) y armado del mapa mental del algoritmo— se hizo con DeepSeek. Las decisiones que salieron de esa fase se contrastaron después con la literatura y con el código de referencia del curso antes de pasar al código.

**Comparación con la literatura y definición de parámetros.** La revisión de la literatura sobre algoritmos genéticos (rangos típicos de tamaño de población, tamaños de torneo, tasas de cruce y mutación) y el análisis de los parámetros iniciales se hizo con apoyo de NotebookLM, contrastando varias fuentes (Russell & Norvig, Woodruff, material del curso). Los valores por defecto que quedaron en la tabla de hiperparámetros salen de esa comparación, no de una elección arbitraria, y están marcados como sujetos a validación empírica en la sección de evaluación pendiente.

**Definición del algoritmo evolutivo eficiente.** Con ayuda de Claude se
exploraron varias alternativas para la codificación del cromosoma, el diseño de la función de aptitud y los operadores de variación. La discusión concluyó en la codificación indirecta, la aptitud lexicográfica de tres componentes y el cruce de dos puntos con mutación por reset. Cada una de esas decisiones están justificadas en el documento ´Informe.md´.

## Pruebas y CLI.
 La generación del código de pruebas (unitarias y de integración) y el punto de entrada por línea de comandos se hicieron con DeepSeek, a partir de los requisitos de la especificación.
