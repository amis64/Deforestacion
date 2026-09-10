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
