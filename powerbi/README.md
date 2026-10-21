# Power BI — Etapa 4 (Conocimiento evidente)

Este archivo documenta el informe de Power BI de la Etapa 4:
`Deforestacion_Etapa4.pbix`, construido sobre `deforestacion_limpio.csv`
(dataset tratado con el nuevo método de limpieza indicado por el
docente; reemplaza al `dataset_tratado.csv` de la Etapa 2).

## Cómo abrir y actualizar el informe

1. Abrir `Deforestacion_Etapa4.pbix` con Power BI Desktop.
2. Si `deforestacion_limpio.csv` cambia, usar "Actualizar" (Inicio →
   Actualizar) para que el modelo tome los datos nuevos.
3. El origen de datos es el archivo `deforestacion_limpio.csv` de la raíz
   del repositorio; si se mueve de carpeta, hay que corregir la ruta en
   Power Query (Transformar datos → Origen).
4. Para publicarlo: Archivo → Publicar → Power BI, y pegar la URL
   resultante (o el código de inserción) en `contenido.py`
   (`CONOCIMIENTO_EVIDENTE["powerbi_url"]` o `["powerbi_embed_html"]`) y
   en el README principal del repositorio.

## Medidas DAX principales, por página

Cada integrante documenta aquí las medidas de la(s) página(s) que
construyó.

### Página 1 — Dimensión poblacional (Danna)

**Título**: Dimensión poblacional — composición del conjunto tratado

**Pregunta**: ¿Cómo está compuesto y cómo se distribuye el conjunto de
80.585 registros tratados según sus principales variables categóricas —
causa de la pérdida (`driver_dominante`), tipo de transformación del
suelo (`clase_transformacion_dominante`) y escala de medición
(`nivel_analisis`)?

**Variables utilizadas**: `driver_dominante`, `clase_transformacion_dominante`,
`nivel_analisis`, `fuente_origen`, `es_agregado_regional`.

**Filtros interactivos (segmentadores)**: `nivel_analisis` (Regional /
Nacional / Global) y `periodo` (2001-2012 / 2013-2024).

### 2.1 Medidas DAX

```DAX
Registros en la selección = COUNTROWS(dataset_tratado)

Registros con driver informado =
CALCULATE([Registros en la selección], NOT ISBLANK(dataset_tratado[driver_dominante]))

Categoría predominante (driver) =
VAR TablaRank =
    ADDCOLUMNS(
        VALUES(dataset_tratado[driver_dominante]),
        "Conteo", CALCULATE([Registros con driver informado])
    )
VAR Top1 = TOPN(1, TablaRank, [Conteo], DESC)
RETURN CONCATENATEX(Top1, dataset_tratado[driver_dominante])

% categoría predominante (driver) =
VAR TablaRank =
    ADDCOLUMNS(
        VALUES(dataset_tratado[driver_dominante]),
        "Conteo", CALCULATE([Registros con driver informado])
    )
VAR Top1Conteo = MAXX(TOPN(1, TablaRank, [Conteo], DESC), [Conteo])
RETURN DIVIDE(Top1Conteo, [Registros con driver informado])

% agregado regional =
DIVIDE(
    CALCULATE([Registros en la selección], dataset_tratado[es_agregado_regional] = TRUE),
    [Registros en la selección]
)
```
