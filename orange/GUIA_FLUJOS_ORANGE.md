# Guía del flujo de Orange Data Mining (Etapa 6)

Versión de referencia: Orange 3.36 o superior con el complemento **Text** (*Options → Add-ons → Text*).
El trabajo en Orange está en **un solo flujo de 39 widgets con cuatro bloques**: `conocimiento_oculto/conocimiento_oculto.ows`.

| Bloque | Qué hace | Widgets |
|---|---|---|
| 1. Preparación | Del dataset tratado a una fila por municipio-año | File → Select Rows → Group By |
| 2. Supervisado | ¿La pérdida de bosque de un municipio será **alta** este año? | Python Script → Select Columns → Select Rows ×2 → 3 modelos → Test and Score → Confusion Matrix / ROC |
| 3. Clustering | Perfiles de municipios | Python Script → Select Columns → Preprocess → k-Means → Silhouette / Box Plot / Scatter Plot / Group By |
| 4. Comentarios de YouTube | Temas y grupos de comentarios | File → Corpus → Preprocess Text → Bag of Words / Topic Modelling / Distances → Hierarchical Clustering |

## 0. Antes de empezar
1. Abra Orange y el archivo `conocimiento_oculto/conocimiento_oculto.ows` (*File → Open*).
2. **Widgets File.** Los archivos guardan la ruta del computador donde se creó el flujo. En el widget *Dataset tratado* elija `deforestacion_limpio.csv` (raíz del repositorio) y en *Archivo comentarios limpios* elija `conocimiento_oculto/youtube/comentarios_limpios.csv`.
3. **Widget Corpus.** Debe tener idioma *Spanish* y usar como texto la columna `texto`.
4. **Widgets Python Script.** Cada uno trae su código; si aparece vacío, péguelo desde `conocimiento_oculto/orange_scripts/` (`script_supervisado.py` en *Rezagos y clase*, `script_clustering.py` en *Perfil por municipio*).
5. Los datos que producen el bloque 1 y los scripts también se generan fuera de Orange con `python conocimiento_oculto/preparar_datos_orange.py deforestacion_limpio.csv` (carpeta `conocimiento_oculto/datos/`); sirven para comprobar el resultado (la verificación en Python usa esos archivos).
6. Tras cada cambio, guarde el flujo (*File → Save*). Las capturas van en `orange/capturas/` con los nombres indicados abajo; el informe se regenera con ellas.

---
## Bloque 1 · Preparación

| Widget (título en el flujo) | Configuración | Para qué |
|---|---|---|
| **File** · Dataset tratado | `deforestacion_limpio.csv` | Cargar el dataset de las Etapas 1–3 |
| **Select Rows** · Solo municipios | `nivel_analisis` es *Regional* **y** `es_agregado_regional` es *False* | Quitar filas globales, nacionales y agregados regionales |
| **Group By** · Group By municipio-año | Agrupar por `departamento`, `municipio`, `anio`. Agregaciones: `area_perdida_bosque_ha` Mean, `area_transformada_ha` Mean, `latitud` Mean, `longitud` Mean, `num_focos_calor` Mean, `driver_dominante` First value | **Una fila por municipio-año**: el dataset trae hasta tres filas casi idénticas por municipio-año; si no se agrupan, quedarían «gemelas» en entrenamiento y prueba y las métricas saldrían infladas |

---
## Bloque 2 · Tres modelos supervisados

**Pregunta.** Con lo que se sabe de un municipio hasta el año anterior, ¿su pérdida de bosque de este año será **alta**? *Alta* = pérdida ≥ percentil 75 de 2004–2018 (129 ha). Es un problema de **clasificación binaria**.

| Widget | Configuración | Para qué |
|---|---|---|
| **Python Script** · Rezagos y clase | `script_supervisado.py`: crea `perdida_t1`, `perdida_t2`, `perdida_media_3a`, `tendencia_perdida_t1`, `area_transformada_t1`, `var_transformada_t1`, `focos_t1` (todo con datos de años **anteriores**), el umbral de «Alta» (percentil 75 solo del entrenamiento), `clase_perdida` y `particion` (Entrenamiento ≤ 2018, Prueba ≥ 2019) | Construir variables sin mirar el futuro y evitar la fuga de información |
| **Select Columns** · Roles: objetivo y metas | *Target*: `clase_perdida`. *Features* (10): `perdida_t1`, `perdida_t2`, `perdida_media_3a`, `tendencia_perdida_t1`, `area_transformada_t1`, `var_transformada_t1`, `focos_t1`, `driver_dominante`, `latitud`, `longitud`. *Meta*: `departamento`, `municipio`, `anio`, `particion`, `area_perdida_bosque_ha` | Definir los roles; las metas identifican la fila pero no entran al modelo |
| **Select Rows** · Entrenamiento 2004-2018 / Prueba 2019-2024 | `particion` es *Entrenamiento* / `particion` es *Prueba* | Partición **temporal**: se entrena con el pasado y se evalúa con un futuro que el modelo no vio |
| **Distributions** · Balance de clases | Variable: **`clase_perdida`** (si el archivo abre con `departamento`, cámbiela) | Evidenciar el desbalance (≈ 25 % «Alta») |
| **Logistic Regression** | Regularización Ridge (L2), C = 1 | Modelo 1 (interpretable) |
| **Tree** | Árbol binario ✔; hojas con mínimo 50 instancias; no dividir subconjuntos de menos de 100; profundidad máxima 5 ✔; detener al alcanzar mayoría del 95 % ✔ | Modelo 2 |
| **Random Forest** | 200 árboles; no dividir subconjuntos de menos de 10 ✔; entrenamiento replicable ✔; sin límite de profundidad | Modelo 3 |
| **Test and Score** · prueba temporal | Datos de entrada: Entrenamiento. *Test Data*: Prueba. Muestreo: ***Test on test data***. *Target class*: **Alta** | Evalúa los tres modelos con los mismos datos de prueba |
| **Confusion Matrix** | Un modelo a la vez; cantidad: *Number of instances* | Falsos positivos y falsos negativos |
| **ROC Analysis** | Clase objetivo «Alta» | Curvas ROC y AUC |
| **Tree Viewer** | Desde *Tree* | Reglas del árbol |
| **Data Table** · Coeficientes logística | Desde la salida *Coefficients* de la regresión logística | Variables que más pesan |

**Anote de Test and Score** (clase «Alta», prueba 2019–2024): AUC, CA (exactitud), F1, Precisión, Recall y MCC de los tres modelos.

**Cifras de Orange** (Test and Score, *Test on test data*, clase Alta, prueba 2019–2024; son las del informe final) junto a la verificación en Python (`conocimiento_oculto/resultados/supervisado.json`):

| Modelo | | AUC | CA | F1 | Precisión | Recall | MCC |
|---|---|---|---|---|---|---|---|
| Regresión logística | Orange | 0,980 | 0,934 | 0,849 | 0,863 | 0,836 | 0,807 |
| | Python | 0,981 | 0,935 | 0,849 | 0,870 | 0,829 | 0,808 |
| Árbol | Orange | 0,958 | 0,927 | 0,846 | 0,788 | **0,914** | 0,802 |
| | Python | 0,978 | 0,930 | 0,845 | 0,824 | 0,867 | 0,800 |
| Random Forest | Orange | 0,981 | 0,932 | **0,850** | 0,833 | 0,867 | 0,806 |
| | Python | 0,982 | 0,933 | 0,852 | 0,832 | 0,873 | 0,809 |
| Predecir siempre «No alta» | Python | 0,500 | 0,779 | 0 | — | 0 | 0 |
| Regla de persistencia (sin modelo) | Python | — | 0,936 | 0,858 | 0,842 | 0,874 | 0,817 |

El orden por F1 coincide (Random Forest, regresión logística, árbol), se elige el **Random Forest**. El árbol de Orange (25 nodos, 13 hojas; primera división `perdida_media_3a ≤ 100,667`) cambia precisión por recall y su AUC es menor. Matriz de confusión del Random Forest en Orange: 1.284 Alta bien detectados, 197 falsos negativos, 257 falsos positivos y 4.976 «No alta» bien clasificados.

**Coeficientes de la regresión logística en Orange:** el widget los muestra para la clase «No alta» y en la escala original de cada variable, por lo que **no son comparables entre sí** (para jerarquizar variables use la importancia del bosque o coeficientes estandarizados, como en Python).

**Capturas:** `f1_flujo.png` (bloques 1 y 2 del lienzo), `f1_balance_clases.png`, `f1_test_score.png`, `f1_matriz_confusion.png`, `f1_roc.png`, `f1_tree_viewer.png`, `f1_coeficientes.png`.

**Qué debe quedar escrito en el informe:**
- Los tres modelos usan las mismas variables, la misma partición y la misma evaluación.
- **El desbalance:** «No alta» es ≈ 78 % de la prueba; por eso la exactitud sola engaña y se mira F1, precisión y recall de «Alta», AUC y MCC.
- **El modelo elegido y por qué.** Criterio sugerido: mayor F1 de «Alta» (en Python gana Random Forest, con diferencias de milésimas). Si en Orange el orden cambia, el informe debe seguir a Orange.
- **Compare con la regla de persistencia** (*Alta si la pérdida del año anterior ya fue de 129 ha o más*): rinde igual o mejor que los modelos. Es la conclusión honesta: lo que los modelos aprenden es la persistencia de la pérdida.
- Limitaciones: umbral arbitrario, saltos bruscos que el historial no anticipa, correlación y no causa.

**Dos comprobaciones opcionales** (no cambian el resultado, pero conviene dejarlas dichas):
1. `driver_dominante` es la causa del *mismo* año (solo existe si hubo pérdida). Pase la variable a *Meta* en *Select Columns* y vuelva a evaluar: en Python el F1 del bosque pasa de 0,852 a 0,849.
2. `latitud` y `longitud` del dataset son las del **departamento** en casi todos los registros; no identifican al municipio.

---
## Bloque 3 · Clustering de municipios

**Pregunta.** ¿Qué perfiles de municipios existen según cuánto pierden, con qué persistencia y evolución, y cuánto fuego y transformación del suelo los acompaña? **No** se usa la clase del bloque 2 ni la causa dominante.

| Widget | Configuración | Para qué |
|---|---|---|
| **Python Script** · Perfil por municipio | `script_clustering.py`: una fila por municipio (con al menos 10 años de dato) con 7 variables de perfil, `latitud`, `longitud` y `anios_con_datos` | Resumir 2004–2024 por municipio |
| **Select Columns** · Variables de agrupamiento | *Features* (7): `log_perdida_media_anual`, `proporcion_perdida_reciente`, `pendiente_perdida_rel`, `variabilidad_perdida_cv`, `log_focos_medios`, `log_area_transformada_media`, `crecimiento_transformada_pct`. *Meta*: `departamento`, `municipio`, `latitud`, `longitud`, `anios_con_datos` | Definir las variables del modelo |
| **Preprocess** · Imputar (media) | *Impute Missing Values → Average/Most frequent* | Rellenar los faltantes (163 valores, casi todos de área transformada) |
| **k-Means** | *Number of clusters*: **From 2 to 8**; Initialization: k-means++; Re-runs: 10; Maximum iterations: 300; **Normalize columns** ✔ | Muestra la **silueta** de cada k |
| **Preprocess** · Estandarizar (para Silhouette) | *Normalize Features → Standardize to μ=0, σ²=1* | Que la silueta se calcule con las variables en la misma escala |
| **Silhouette Plot** | *Group by*: Cluster | Calidad de cada grupo |
| **Box Plot** | *Group by*: Cluster; variables ordenadas por importancia | Qué distingue a cada grupo |
| **Scatter Plot** · Mapa | X: `longitud`; Y: `latitud`; Color: Cluster | Ubicación (ver advertencia) |
| **Group By** · Perfil promedio | Por Cluster: media de las 7 variables y conteo de municipios | Tabla de perfiles |
| **Data Table** (×2) | Municipios y cluster / Tabla de perfiles | Cantidad y perfil por grupo |

**Advertencia del mapa.** Como las coordenadas del dataset son las del departamento, el *Scatter Plot* muestra ≈ 33 puntos apilados (uno por departamento), no los municipios.

**Elección de k** (comprobación en Python):

| k | Silueta | Davies-Bouldin | Tamaños |
|---|---|---|---|
| 2 | 0,297 | 1,33 | 616 · 503 |
| 3 | 0,256 | 1,40 | 500 · 365 · 254 |
| **4** | 0,264 | 1,29 | 475 · 320 · 285 · 39 |
| 5 | 0,223 | 1,35 | 333 · 277 · 266 · 205 · 38 |

La silueta más alta es la de k = 2, pero solo separa «mucha» de «poca» pérdida. Entre k ≥ 3 el máximo es k = 4, que además aísla un grupo pequeño. El widget está configurado con *k* = 4 y *Optimize number of clusters* ✔; si Orange sugiere otro k, **explique la diferencia** en el informe.

**En Orange** la silueta por k es 0,297 (k = 2), 0,255, **0,264 (k = 4)**, 0,223, 0,230, 0,225 y 0,203 (k = 8); el Silhouette Plot de k = 4 da 0,156 (C4), 0,242 (C1), 0,215 (C3) y 0,319 (C2). **Orange numera los grupos distinto:** C4 = grupo 1, C1 = grupo 2, C3 = grupo 3 y C2 = grupo 4 (tamaños 39, 285, 320 y 475, iguales a los de Python).

**Grupos de k = 4** (por pérdida media de mayor a menor):
1. **Frentes de mayor pérdida** (39): San Vicente del Caguán, La Macarena, Cartagena del Chairá, San José del Guaviare… 3 % de los municipios y 38 % de la pérdida media anual.
2. **Pérdida alta sostenida** (285).
3. **Pérdida moderada** (320).
4. **Pérdida baja y en descenso** (475, zona andina).

**Capturas:** `f2_flujo.png`, `f2_kmeans_silueta.png`, `f2_silhouette_plot.png`, `f2_boxplot.png`, `f2_mapa.png`, `f2_perfiles.png`.

---
## Bloque 4 · Comentarios de YouTube

**Datos:** `conocimiento_oculto/youtube/comentarios_limpios.csv` (117 comentarios de 3 videos; ver `LEEME_YOUTUBE.md`).

| Widget | Configuración | Para qué |
|---|---|---|
| **File** · Archivo comentarios limpios | `comentarios_limpios.csv` | Cargar |
| **Corpus** | Idioma *Spanish*; texto: `texto` | Declarar el texto |
| **Preprocess Text** · español | Transformación: minúsculas, quitar acentos, quitar URL. Tokenización: expresión regular `\w+`. Normalización: lematizador en español. Filtrado, **en este orden**: palabras vacías en español, quitar números y frecuencia de documento **absoluta de 3 a 100**. Resultado en Orange: 516 tokens y 78 términos distintos en 117 comentarios | Limpiar y normalizar el texto |
| **Bag of Words** · TF-IDF | Term frequency: Count; Document frequency: IDF; Regularization: L2 | Matriz de términos |
| **Topic Modelling** · LDA | Método LDA, **5 temas** (pruebe 3 a 6 y compare) | Temas |
| **Word Cloud** · por tema | Entrada: tema seleccionado | Apoyo visual (no basta por sí sola) |
| **LDAvis** | Todos los temas | Distancia entre temas y términos relevantes |
| **Corpus Viewer** · evidencias | Busque: gobierno, ganader, coca, miner, tala, quema, indígena | Ejemplos citables |
| **Distances** · coseno | Entre filas (documentos) | Distancia entre comentarios |
| **Hierarchical Clustering** | Linkage: **Ward**; corte en 4 grupos (*Top N*) | Agrupar comentarios |
| **Select Rows** · Grupo de comentarios elegido | Elige el grupo (cluster) que se quiere caracterizar | Pasar un solo grupo a Word Enrichment |
| **Word Enrichment** | Grupo seleccionado frente al resto del corpus (entrada de referencia: Bag of Words) | Términos que caracterizan a cada grupo |

**Capturas:** `f3_flujo.png`, `f3_preprocess.png`, `f3_temas_lda.png`, `f3_ldavis.png`, `f3_nube_tema.png`, `f3_corpus_viewer.png`, `f3_clustering_jerarquico.png`, `f3_word_enrichment.png`.

**Qué debe responder el informe:** qué temas aparecen y cuántos comentarios agrupa cada uno; qué causas y responsables mencionan (gobierno, ganadería, coca, minería…) frente a los resultados de los bloques 2 y 3; qué piden o proponen; y que **solo representan a quienes comentaron esos tres videos**: una parte es uso escolar del video y otra viene de otros países.

**Lo que muestra Orange:** LDA de 5 temas con coherencia 0,394; los términos salen dominados por verbos y palabras frecuentes (ser, tener, hacer, si) y por lemas erróneos (colombiar, arbolar, cocar), así que los temas se interpretan con la verificación NMF. Hierarchical Clustering (Ward, 4 grupos): 6, 9, 80 y 22 comentarios; Word Enrichment del grupo de 22: humano, medio, tierra y ambiente (FDR ≤ 0,2).

**Lo que muestra la verificación en Python** (`conocimiento_oculto/resultados/comentarios.json`, temas con NMF; el LDA de Orange cambiará el orden y los términos): 5 temas (uso escolar y agradecimientos, 38 %; Colombia y gobiernos; reclamo al gobierno; cuidar el ambiente; el ser humano y el bosque), 21 comentarios que reclaman al gobierno, 6 que nombran la ganadería, 8 la coca o los grupos armados y 5 la minería o los megaproyectos; la silueta de la agrupación es muy baja (≈ 0,09).

---
## Qué entregar de cada bloque
1. El `.ows` actualizado (con las rutas que usted corrigió) y las capturas en `orange/capturas/`.
2. Las cifras de Test and Score, la silueta por k, el tamaño y el perfil de cada grupo, y los temas LDA con sus términos, para pasarlos al informe (el informe se regenera con ellas).
3. Un comentario por widget en el informe: *qué recibe, qué parámetro cambia y qué produce*.
