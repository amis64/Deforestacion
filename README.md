# Deforestación y Transformación del Territorio

Proyecto de Minería de Datos que documenta, a través de una aplicación web
construida en Flask, el proceso de análisis del fenómeno de deforestación y
transformación del uso del suelo en Colombia, comparado contra el panorama
global.

El proyecto se desarrolla por etapas. Cada etapa agrega una nueva sección a
la aplicación sin reemplazar el contenido de las etapas anteriores, de modo
que la aplicación funciona como una bitácora técnica completa del proceso.

## Etapas del proyecto

### Etapa 1: del problema a los datos

Plantea el problema, la pregunta principal y las preguntas secundarias,
identifica las necesidades de información, documenta las fuentes de datos
utilizadas (Global Forest Watch, MapBiomas Colombia, NASA FIRMS, FAO y Our
World in Data), describe el dataset consolidado que integra esas fuentes,
presenta su diccionario de datos y hace un primer diagnóstico de calidad y
de limitaciones.

### Etapa 2: calidad de datos

Evalúa en profundidad la calidad del dataset consolidado por la Etapa 1:

* Perfila el conjunto de datos (cantidad de registros y variables, tipos de
  dato, valores únicos, nulos, duplicados, estadísticos y valores atípicos).
* Mide seis dimensiones de calidad (completitud, unicidad, consistencia,
  validez, exactitud y actualidad) con una métrica verificable para cada
  una.
* Documenta un inventario de los problemas encontrados, con la variable
  afectada, la cantidad de registros, la dimensión relacionada, el nivel de
  impacto y la evidencia obtenida.
* Analiza las causas probables de esos problemas y describe la integración
  y homologación aplicada entre fuentes.
* Aplica un plan de tratamiento sobre el dataset (deduplicación,
  homologación de categorías y de nombres de lugar, corrección de formato,
  marcado de agregados regionales y de valores atípicos) y presenta la
  comparación antes y después del tratamiento.

Los scripts que sustentan estas cifras están en `calidad_datos/` y son
reproducibles: se ejecutan sobre `dataset_consolidado.csv` y generan tanto
el dataset tratado (`dataset_tratado.csv`) como los reportes en formato
JSON que alimentan las cifras mostradas en la aplicación.

### Etapa 5: análisis multidimensional

Organiza el dataset tratado (`deforestacion_limpio.csv`, 80.585 registros) en un
**modelo estrella** y lo explora desde varias perspectivas. La aplicación tiene un
nuevo elemento de menú, **Análisis multidimensional**, con:

* Resumen: propósito, relación con la Etapa 4, datos y cobertura, acceso a las vistas.
* Modelo estrella: diagrama, granularidad, dimensiones, medidas, jerarquías, carga y validaciones.
* Operaciones: drill-down, roll-up, slice, dice y pivot, cada una con una consulta ejecutada.
* Cuatro vistas interactivas (cada una con 3 indicadores, 2 visualizaciones, 1 matriz, 2 filtros,
  controles de operaciones, 2 conocimientos, 1 limitación y 1 decisión).
* Conocimientos (8), limitaciones y conclusiones.

**Modelo.** Tabla de hechos `hechos_perdida_forestal` (una fila por territorio y año) y cinco
dimensiones: `dim_territorio`, `dim_tiempo`, `dim_causa`, `dim_transformacion`, `dim_fuente`.
Se almacena en SQLite (`multidimensional/modelo_estrella.db`) y Flask lo consulta con `sqlite3`.

**Reproducir la solución** (solo biblioteca estándar de Python; Flask ya está en `requirements.txt`):

```bash
pip install -r requirements.txt
python multidimensional/cargar_modelo.py      # ETL: CSV tratado -> modelo estrella (idempotente)
python multidimensional/validar_modelo.py     # 30 verificaciones de integridad + 12 comparaciones
python multidimensional/generar_docs.py       # regenera docs/modelo_estrella/*.md
python app.py                                 # http://localhost:5000/analisis-multidimensional/
# opcional (requiere pandas): recalcula las cifras de los conocimientos de forma independiente
python multidimensional/verificar_cifras.py
```

Si `modelo_estrella.db` no existe, la aplicación lo reconstruye sola al arrancar a partir del CSV.

**Archivos de la Etapa 5**

```
├── deforestacion_limpio.csv               # dataset tratado (entrada del ETL)
├── sql/
│   ├── 05_modelo_estrella_ddl.sql         # creación de tablas, claves, relaciones y vista vw_cubo
│   ├── 06_consultas_olap.sql              # consultas de los análisis (drill-down, roll-up, slice, dice, pivot)
│   └── 07_validaciones_modelo.sql         # validaciones del modelo en SQL
├── multidimensional/
│   ├── __init__.py                        # Blueprint de Flask (rutas /analisis-multidimensional/...)
│   ├── cargar_modelo.py                   # ETL reproducible
│   ├── validar_modelo.py                  # validaciones + reporte_validacion.json
│   ├── olap.py                            # motor de consultas multidimensionales (SQL parametrizado)
│   ├── graficos.py                        # gráficas SVG generadas en el servidor
│   ├── vistas/                            # las cuatro vistas (v1..v4) y utilidades comunes
│   ├── conocimientos.py, cifras.py        # los 8 conocimientos; las cifras se consultan al modelo
│   ├── operaciones.py                     # ejemplo ejecutado de cada operación
│   ├── documentacion.py, generar_docs.py, diagrama.py
│   ├── verificar_cifras.py                # comprobación independiente (pandas)
│   └── modelo_estrella.db                 # base SQLite del modelo (generada por el ETL)
├── docs/modelo_estrella/                  # diagrama (.svg/.png), diccionario, mapeo de variables, jerarquías
├── templates/multidimensional/            # plantillas de la sección
└── static/css/multidimensional.css, static/img/etapa5/
```

**Cambios en la aplicación existente** (solo dos líneas en `app.py` y una opción de menú, junto a «Etapa 4», en `templates/base.html`):
ver `docs/modelo_estrella/INTEGRACION_FLASK.md`.

**Repositorio:** https://github.com/amis64/Deforestacion · **Aplicación publicada:** (URL del despliegue en Render, ver informe técnico de la Etapa 5).

### Etapa 6: Conocimiento Oculto (aprendizaje supervisado, clustering y comentarios de YouTube)

Sección **Conocimiento Oculto** de la aplicación (`/conocimiento-oculto`): síntesis de hallazgos, informe técnico
en PDF, video de sustentación y las páginas de cada análisis. El trabajo se hizo en **Orange Data Mining** (un solo
flujo de 38 widgets); el repositorio guarda el flujo, los scripts, los datos de entrada, la extracción de comentarios
y una verificación en Python que alimenta las páginas.

```
orange/
├── GUIA_FLUJOS_ORANGE.md        # guía del flujo: widgets, conexiones, parámetros y capturas
└── capturas/                    # capturas de Orange que cita el informe
conocimiento_oculto/
├── conocimiento_oculto.ows      # flujo de Orange (4 bloques: preparación, supervisado, clustering, comentarios)
├── orange_scripts/              # código de los widgets Python Script (script_supervisado.py, script_clustering.py)
├── preparar_datos_orange.py     # arma los CSV de entrada desde deforestacion_limpio.csv
├── datos/                       # datos_supervisado.csv, datos_clustering.csv, reporte_preparacion.json
├── supervisado.py, clustering.py, analizar_comentarios.py, referencia.py   # verificación en Python
├── resultados/                  # JSON que leen las páginas de Flask
├── graficos_oculto.py, config.py, __init__.py                              # Blueprint de Flask
├── extraer_comentarios_youtube.py   # YouTube Data API v3 (clave por variable de entorno)
└── youtube/
    ├── LEEME_YOUTUBE.md         # criterios, restricciones y cómo repetir la extracción
    └── videos.csv, comentarios_limpios.csv, reporte_extraccion.json
```

```bash
# 1. datos de entrada de Orange
python conocimiento_oculto/preparar_datos_orange.py deforestacion_limpio.csv
# 2. abrir conocimiento_oculto/conocimiento_oculto.ows en Orange (corregir las rutas de los widgets File; ver orange/GUIA_FLUJOS_ORANGE.md)
# 3. verificación en Python (supervisado, clustering y comentarios) -> conocimiento_oculto/resultados/*.json
python conocimiento_oculto/referencia.py
# 4. (opcional) repetir la extracción de comentarios; requiere YOUTUBE_API_KEY (ver youtube/LEEME_YOUTUBE.md)
python conocimiento_oculto/extraer_comentarios_youtube.py
```

**Seguridad y privacidad.** La clave de la API de YouTube nunca se versiona (se lee de `YOUTUBE_API_KEY`). No se guardan
nombres ni identificadores de los autores de los comentarios, solo un código anónimo; los comentarios crudos no se
publican (`.gitignore`).

## Estructura del repositorio

```
.
├── app.py                        # Rutas de la aplicación Flask
├── contenido.py                   # Contenido y datos de las Etapas 1 y 2
├── dataset_consolidado.csv        # Dataset consolidado (salida de la Etapa 1)
├── dataset_tratado.csv            # Dataset tratado (salida de la Etapa 2)
├── requirements.txt
├── Procfile
├── render.yaml
├── runtime.txt
├── calidad_datos/
│   ├── perfilamiento.py           # Perfilamiento del dataset consolidado
│   ├── metricas_calidad.py        # Métricas de las seis dimensiones de calidad
│   ├── tratamiento.py             # Plan de tratamiento y comparación antes/después
│   ├── reporte_perfilamiento.json
│   ├── reporte_metricas.json
│   └── reporte_tratamiento.json
├── anexo_construccion_dataset/
│   ├── build_dataset.py           # Script que integra las fuentes originales
│   └── README.md
├── static/css/style.css
└── templates/
    ├── base.html, _sidebar.html, index.html
    ├── problema.html, preguntas.html, necesidades.html, fuentes.html,
    │   dataset.html, diccionario.html, calidad.html, limitaciones.html   (Etapa 1)
    └── etapa2/
        ├── descripcion.html, requisitos.html, perfilamiento.html,
        └── dimensiones.html, problemas.html, tratamiento.html            (Etapa 2)
```

## Dataset

El dataset consolidado y el dataset tratado están incluidos directamente en
este repositorio (`dataset_consolidado.csv` y `dataset_tratado.csv`). El
detalle de cada fuente original, su método de adquisición y sus
restricciones de uso está documentado en la sección "Fuentes de datos" de
la Etapa 1 de la aplicación.

## Integrantes

Danna, Amy y Nicolás.
