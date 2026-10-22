# Power BI — Etapa 4 (Conocimiento evidente)

Este archivo documenta el informe de Power BI de la Etapa 4:
`Deforestacion_Etapa4.pbix`, construido sobre `deforestacion_limpio.csv`
(dataset tratado con el nuevo método de limpieza indicado por el
docente; reemplaza al `dataset_tratado.csv` de la Etapa 2). En el modelo,
la tabla de hechos se llama `deforestacion_limpio` y hay una tabla
auxiliar, `Pares de variables`, que alimenta el gráfico de correlaciones.

## Cómo abrir y actualizar el informe

1. Abrir `Deforestacion_Etapa4.pbix` con Power BI Desktop.
2. Si `deforestacion_limpio.csv` cambia, usar "Actualizar" (Inicio →
   Actualizar) para que el modelo tome los datos nuevos.
3. El origen de datos es el archivo `deforestacion_limpio.csv` de la raíz
   del repositorio; si se mueve de carpeta, hay que corregir la ruta en
   Power Query (Transformar datos → Origen).
4. El tema visual (paleta verde bosque / tierra / ámbar y fondo hueso,
   igual a la aplicación web) está en `tema_deforestacion.json`
   (Vista → Temas → Explorar temas → Importar tema).
5. Para publicarlo: Archivo → Publicar → Power BI, y pegar la URL
   resultante (o el código de inserción) en `contenido.py`
   (`CONOCIMIENTO_EVIDENTE["powerbi_url"]` o `["powerbi_embed_html"]`) y
   en el README principal del repositorio.

## Cómo está organizada cada página

Cada una de las 4 páginas tiene el mismo esquema, de arriba abajo:
título y pregunta; 2 segmentadores; tarjetas con los indicadores;
3 visualizaciones; un cuadro "Interpretación de las visualizaciones"
(lectura sin filtros de cada indicador y gráfico); y, debajo, la sección
**Conocimientos evidentes** con los 3 conocimientos (pregunta, variables,
procedimiento, evidencia, hallazgo, interpretación, utilidad y
limitación), la **Limitación del análisis** de la página y una **Posible
decisión sustentada en los datos**.

## Cómo leer las cifras (reglas de cálculo del proyecto)

- El conjunto mezcla tres escalas (Regional, Nacional y Global) y cada
  municipio-año de la escala Regional se repite hasta 3 veces (el área
  coincide; las emisiones varían levemente). Por eso `[Área perdida
  Colombia]`, que suma todas las filas de Colombia, **sirve para
  comparar entre filtros, no como hectáreas reales**: la pérdida única
  2001–2024 es de 5,60 millones de ha (una fila por municipio-año).
- Los porcentajes (departamento top, concentración top 5, variaciones)
  sí son comparables: cada escala repite el mismo total.
- Las correlaciones se calculan solo sobre los registros que tienen los
  dos valores (la medida filtra los vacíos y usa la fórmula centrada de
  Pearson, que es estable con valores tan grandes como las emisiones).

## Medidas DAX principales, por página

Cada integrante documenta aquí las medidas de la(s) página(s) que
construyó.

### Página 1 — Dimensión poblacional — composición del conjunto tratado (Danna)

**Pregunta**: ¿Cómo está compuesto y cómo se distribuye el conjunto de 80.585 registros tratados según sus principales variables categóricas — causa de la pérdida, tipo de transformación del suelo y escala de medición?

**Variables utilizadas**: `driver_dominante`, `clase_transformacion_dominante`, `nivel_analisis`, `fuente_origen`, `es_agregado_regional`.

**Segmentadores (2)**: Escala de medición (`nivel_analisis`); `periodo`.

**Indicadores (3 tarjetas)**:
- `[Registros en la selección]`
- `[Categoría predominante (driver)]` + `[% categoría predominante (driver)]`
- `[% agregado regional]`

**Visualizaciones (3)**:
- Columnas agrupadas: `driver_dominante` → `[Registros con driver informado]`
- Dona: `clase_transformacion_dominante` → `[Registros en la selección]`
- Columnas agrupadas: `fuente_origen` → `[Registros en la selección]` · filtro Top 6 del visual

#### Medidas de la página 1

```DAX
Registros en la selección = COUNTROWS(deforestacion_limpio)

Registros con driver informado = CALCULATE([Registros en la selección], KEEPFILTERS(deforestacion_limpio[driver_dominante] <> ""))

Categoría predominante (driver) =
VAR TablaRank =
    ADDCOLUMNS(
        VALUES(deforestacion_limpio[driver_dominante]),
        "Conteo", CALCULATE([Registros con driver informado])
    )
VAR Top1 = TOPN(1, TablaRank, [Conteo], DESC)
RETURN CONCATENATEX(Top1, deforestacion_limpio[driver_dominante])

% categoría predominante (driver) =
VAR TablaRank =
    ADDCOLUMNS(
        VALUES(deforestacion_limpio[driver_dominante]),
        "Conteo", CALCULATE([Registros con driver informado])
    )
VAR Top1Conteo = MAXX(TOPN(1, TablaRank, [Conteo], DESC), [Conteo])
RETURN DIVIDE(Top1Conteo, [Registros con driver informado])

% agregado regional =
DIVIDE(
    CALCULATE([Registros en la selección], deforestacion_limpio[es_agregado_regional] = TRUE),
    [Registros en la selección]
)
```

#### Conocimiento evidente 1 — La agricultura permanente explica 9 de cada 10 registros con causa

- **Pregunta**: ¿Qué causa de pérdida de bosque predomina en el conjunto?
- **Variables**: driver_dominante, nivel_analisis y area_perdida_bosque_ha.
- **Procedimiento**: Conteo de registros por driver_dominante sobre los 76.457 registros con causa informada (se excluyen 4.128 sin causa). Comprobación en área: suma de hectáreas con una fila por municipio-año (28.800 combinaciones de la escala Regional, 2001–2024).
- **Evidencia**: Tarjetas "Categoría predominante" y "% categoría predominante" (90,7 %) y gráfico "Registros con driver informado".
- **Hallazgo**: Agricultura permanente reúne 69.343 de 76.457 registros (90,7 %). En hectáreas únicas pesa aún más: 94,2 % de los 5,60 millones de ha perdidas a escala municipal. Le siguen agricultura migratoria (3,4 %) y silvicultura (3,3 %).
- **Interpretación**: La pérdida de bosque registrada se asocia casi siempre con la conversión a usos agropecuarios de largo plazo, no con eventos naturales ni con la infraestructura.
- **Utilidad**: Señala que las acciones de control con mayor alcance son las dirigidas a la expansión de la frontera agropecuaria.
- **Limitación**: Es la causa dominante de cada municipio-año: no mide causas secundarias.

#### Conocimiento evidente 2 — 80.585 registros no son 80.585 territorios

- **Pregunta**: ¿Qué representa cada registro y cuántas unidades distintas hay?
- **Variables**: nivel_analisis, pais, departamento, municipio, anio y es_agregado_regional.
- **Procedimiento**: Conteo de registros por nivel_analisis y de combinaciones distintas municipio-año (Regional), departamento -año (Nacional) y país-año (Global); cociente registros / combinaciones.
- **Evidencia**: Tarjeta "Registros en la selección" (80.585) con el filtro "Escala de medición".
- **Hallazgo**: Regional tiene 77.256 registros, pero solo 28.800 combinaciones municipio-año de 1.209 municipios (2,68 registros por combinación; 23.145 combinaciones aparecen 3 veces con la misma área). Nacional tiene 2.328 registros para 792 departamento-año y Global 1.001 registros de 296 países y 16 agregados.
- **Interpretación**: El conjunto mezcla tres escalas: un conteo o una suma directa sobrerrepresenta la escala municipal y multiplica las cantidades.
- **Utilidad**: Define la regla de cálculo del proyecto: filtrar una sola escala y usar una fila por unidad-año antes de sumar áreas o contar territorios.
- **Limitación**: El CSV no indica por qué hay tres filas por municipio- año (el área coincide y las emisiones varían levemente).

#### Conocimiento evidente 3 — Los blancos de clase y causa son faltantes por cobertura

- **Pregunta**: ¿Los valores en blanco significan ausencia de transformación o de causa?
- **Variables**: clase_transformacion_dominante, driver_dominante, fuente_origen y nivel_analisis.
- **Procedimiento**: Cruce de los registros en blanco con fuente_origen y nivel_analisis; porcentajes sobre 80.585 registros y sobre los registros informados.
- **Evidencia**: Dona "Registros por clase_transformacion_dominante" (blanco 8,09 %) y barras "Registros por fuente_origen".
- **Hallazgo**: Los 6.523 registros sin clase (8,09 %) provienen todos de fuentes sin MapBiomas (GFW 4.171, GFW+FIRMS 1.256, FAO/OWID 938 y FIRMS 158). Entre los 74.062 registros con clase, Área agropecuaria es el 99,44 %. De los 4.128 sin causa, 929 son filas globales de otros países, donde la causa no aplica, y 3.199 son faltantes en Colombia.
- **Interpretación**: Los blancos dependen de qué fuente cubre cada registro; no son respuestas negativas y no indican que no haya transformación ni causa.
- **Utilidad**: Evita leer el 8,09 % como "sin transformación" y lleva a reportar los porcentajes sobre los registros informados.
- **Limitación**: La clase faltante no se puede imputar: las conclusiones sobre transformación solo valen para los registros con MapBiomas.

#### Limitación del análisis (página 1)

Las cifras de esta página cuentan registros, no hectáreas ni territorios únicos. La escala Regional aporta el 95,9 % de las filas y repite cada municipio-año hasta tres veces, por lo que un conteo o una suma directa la sobrerrepresenta.

#### Posible decisión sustentada en los datos (página 1)

Priorizar las acciones de control de la deforestación sobre la expansión agropecuaria permanente, que reúne el 90,7 % de los registros con causa y el 94,2 % de las hectáreas únicas perdidas a escala municipal. En el tablero, calcular las áreas con una fila por municipio-año.

---

### Página 3 — Dimensión temporal — evolución 2001-2024 (Nicolás)

**Pregunta**: ¿Cómo ha cambiado año a año la pérdida de bosque en Colombia entre 2001 y 2024, y cómo varía esa evolución según el departamento o la causa de pérdida?

**Segmentadores (2)**: `driver_dominante`; `departamento`.

**Indicadores (4 tarjetas)**:
- `[Variación 2001→2024 %]`
- `[Variación entre periodos %]`
- `[Año de mayor pérdida]`
- `[Área perdida Colombia]`

**Visualizaciones (3)**:
- Líneas: `anio` → `[Área perdida Colombia]`
- Columnas agrupadas: `periodo` → `[Promedio anual periodo]`
- Columnas agrupadas: `anio` → `[Variación interanual %]` · filtro Top 5 del visual

#### Medidas de la página 3 (usa también `[Área perdida Colombia]` de la página 2)

```DAX
Área perdida año anterior =
VAR AnioActual = MAX(deforestacion_limpio[anio])
RETURN CALCULATE([Área perdida Colombia], FILTER(ALL(deforestacion_limpio[anio]), deforestacion_limpio[anio] = AnioActual - 1))

Variación interanual % = DIVIDE([Área perdida Colombia] - [Área perdida año anterior], [Área perdida año anterior])

Variación interanual % (abs) = ABS([Variación interanual %])

Año de mayor pérdida =
VAR TablaRank = ADDCOLUMNS(VALUES(deforestacion_limpio[anio]), "Area", CALCULATE([Área perdida Colombia]))
VAR Top1 = TOPN(1, TablaRank, [Area], DESC)
RETURN CONCATENATEX(Top1, deforestacion_limpio[anio])

Variación 2001→2024 % =
VAR Primero = CALCULATE([Área perdida Colombia], deforestacion_limpio[anio] = 2001)
VAR Ultimo = CALCULATE([Área perdida Colombia], deforestacion_limpio[anio] = 2024)
RETURN DIVIDE(Ultimo - Primero, Primero)

Promedio anual periodo = AVERAGEX(VALUES(deforestacion_limpio[anio]), [Área perdida Colombia])

Promedio 2001-2012 = CALCULATE([Promedio anual periodo], deforestacion_limpio[periodo] = "2001-2012")

Promedio 2013-2024 = CALCULATE([Promedio anual periodo], deforestacion_limpio[periodo] = "2013-2024")

Variación entre periodos % = DIVIDE([Promedio 2013-2024] - [Promedio 2001-2012], [Promedio 2001-2012])
```

#### Conocimiento evidente 1 — 2016–2018: el salto más fuerte de la serie

- **Pregunta**: ¿En qué años se concentró la mayor pérdida de bosque?
- **Variables**: anio y area_perdida_bosque_ha (Colombia, escala Global).
- **Procedimiento**: Una fila por año (serie GFW 2001–2024); variación interanual y comparación del promedio 2016–2018 con el de 2013–2015.
- **Evidencia**: Tarjeta "Año de mayor pérdida" (2017), línea por año y "Variación interanual %" (2016: +106,5 %).
- **Hallazgo**: La pérdida pasó de 140.923 ha en 2015 a 290.868 ha en 2016 y a 424.642 ha en 2017, el máximo de la serie. El promedio 2016–2018 (355.910 ha/año) es 2,2 veces el de 2013–2015 (160.606 ha/año).
- **Interpretación**: Fue un cambio de nivel sostenido, no un año aislado. Como hipótesis que estos datos no pueden comprobar, coincide con la salida de las FARC de zonas de selva tras el Acuerdo de Paz de 2016.
- **Utilidad**: Identifica el periodo crítico para evaluar qué falló en el control y qué medidas posteriores ayudaron a reducir la pérdida.
- **Limitación**: El conjunto no tiene variables de conflicto, políticas ni precios: la coincidencia en el tiempo no permite probar causalidad.

#### Conocimiento evidente 2 — El periodo reciente pierde 22,6 % más bosque por año

- **Pregunta**: ¿La pérdida anual es mayor en 2013–2024 que en 2001–2012?
- **Variables**: periodo, anio y area_perdida_bosque_ha.
- **Procedimiento**: Promedio anual por periodo, con dos periodos de igual duración (12 años cada uno) para no comparar sumas de periodos distintos; variación porcentual.
- **Evidencia**: Gráfico "Promedio anual periodo" y tarjeta "Variación entre periodos %" (+22,6 %).
- **Hallazgo**: El promedio subió de 209.993 a 256.899 ha/año (+22,3 % con una fila por año; la tarjeta marca +22,6 % porque suma las tres escalas). En cambio, 2024 (213.030 ha) es 7,4 % menor que 2001 (229.961 ha).
- **Interpretación**: Comparar solo el primer y el último año sugiere una leve mejora, pero el nivel promedio del periodo reciente es más alto: los extremos de la serie no representan su tendencia.
- **Utilidad**: Recomienda fijar metas de reducción sobre promedios de varios años y no sobre un año puntual.
- **Limitación**: Dos bloques de 12 años ocultan cambios internos (el pico 2016–2018 pesa en el segundo).

#### Conocimiento evidente 3 — La evolución cambia según el departamento

- **Pregunta**: ¿Todos los departamentos y causas siguen la misma tendencia?
- **Variables**: departamento, driver_dominante, periodo y area_perdida_bosque_ha (escala Regional).
- **Procedimiento**: Una fila por municipio-año; suma por departamento y por causa en cada periodo de 12 años; variación entre periodos.
- **Evidencia**: Segmentadores "departamento" y "driver_dominante" aplicados a las tarjetas de variación y a la línea anual.
- **Hallazgo**: Entre periodos, Putumayo creció 101,5 %, Guaviare 74,1 % y Caquetá 43,1 %, mientras Antioquia bajó 1,1 % y Santander 43,5 %. Por causa, la agricultura permanente subió 20,3 % y la migratoria 23,3 % (la tarjeta marca +50,1 % porque suma también la escala nacional).
- **Interpretación**: El aumento nacional viene sobre todo del arco amazónico (Putumayo, Guaviare y Caquetá); en departamentos andinos la pérdida se estabilizó o bajó.
- **Utilidad**: Indica dónde reforzar el control (departamentos que crecen) y dónde mantener lo que funciona.
- **Limitación**: La causa es la dominante por municipio-año. Incendios y otras alteraciones casi no aparecen en 2001–2012, así que su crecimiento puede reflejar cambios de clasificación.

#### Limitación del análisis (página 3)

El gráfico interanual solo muestra el Top 5 de cambios y oculta las caídas, y los focos de calor solo existen de 2012 a 2022, por lo que no sirven para comparar periodos.

#### Posible decisión sustentada en los datos (página 3)

Usar el promedio 2013–2024 (unas 256.900 ha/año) como línea base de las metas de reducción, en lugar del año 2001, y reforzar el control en Putumayo, Guaviare y Caquetá, donde la pérdida creció entre 43 % y 102 % de un periodo a otro.

---

### Página 4 — Dimensión multivariada — relaciones y cruces entre causa, territorio, tiempo y medidas (Nicolás)

**Pregunta**: ¿Qué relaciones aparecen al cruzar tres o más variables a la vez —causa de pérdida, territorio, periodo y las medidas numéricas— en vez de analizar cada una por separado?

**Segmentadores (2)**: `departamento`; `periodo`.

**Indicadores (3 tarjetas)**:
- `[Correlación (Área perdida, Emisiones CO2)]`
- `[Driver con mayor crecimiento (base relevante)]`
- `[Driver principal en departamento top]`

**Visualizaciones (3)**:
- Columnas agrupadas: `Par` → `[Valor de correlación]`
- Matriz: `departamento` → `[Área perdida Colombia]` + `[Driver principal (dinámico, por fila)]` · filtro Top 6 del visual
- Columnas agrupadas: `driver_dominante` → `[Área perdida periodo 1 (por driver)]` + `[Área perdida periodo 2 (por driver)]`

#### Correlaciones de Pearson (tabla auxiliar `Pares de variables`)

```DAX
Correlación (Área perdida, Emisiones CO2) =
VAR Pares = FILTER(deforestacion_limpio, NOT ISBLANK(deforestacion_limpio[area_perdida_bosque_ha]) && NOT ISBLANK(deforestacion_limpio[emisiones_co2_mg]))
VAR MediaX = AVERAGEX(Pares, deforestacion_limpio[area_perdida_bosque_ha])
VAR MediaY = AVERAGEX(Pares, deforestacion_limpio[emisiones_co2_mg])
VAR Covarianza = SUMX(Pares, (deforestacion_limpio[area_perdida_bosque_ha] - MediaX) * (deforestacion_limpio[emisiones_co2_mg] - MediaY))
VAR SumaCuadX = SUMX(Pares, (deforestacion_limpio[area_perdida_bosque_ha] - MediaX) ^ 2)
VAR SumaCuadY = SUMX(Pares, (deforestacion_limpio[emisiones_co2_mg] - MediaY) ^ 2)
RETURN DIVIDE(Covarianza, SQRT(SumaCuadX * SumaCuadY))

Correlación (Área perdida, Focos de calor) =
VAR Pares = FILTER(deforestacion_limpio, NOT ISBLANK(deforestacion_limpio[area_perdida_bosque_ha]) && NOT ISBLANK(deforestacion_limpio[num_focos_calor]))
VAR MediaX = AVERAGEX(Pares, deforestacion_limpio[area_perdida_bosque_ha])
VAR MediaY = AVERAGEX(Pares, deforestacion_limpio[num_focos_calor])
VAR Covarianza = SUMX(Pares, (deforestacion_limpio[area_perdida_bosque_ha] - MediaX) * (deforestacion_limpio[num_focos_calor] - MediaY))
VAR SumaCuadX = SUMX(Pares, (deforestacion_limpio[area_perdida_bosque_ha] - MediaX) ^ 2)
VAR SumaCuadY = SUMX(Pares, (deforestacion_limpio[num_focos_calor] - MediaY) ^ 2)
RETURN DIVIDE(Covarianza, SQRT(SumaCuadX * SumaCuadY))

Correlación (Área perdida, Área transformada) =
VAR Pares = FILTER(deforestacion_limpio, NOT ISBLANK(deforestacion_limpio[area_perdida_bosque_ha]) && NOT ISBLANK(deforestacion_limpio[area_transformada_ha]))
VAR MediaX = AVERAGEX(Pares, deforestacion_limpio[area_perdida_bosque_ha])
VAR MediaY = AVERAGEX(Pares, deforestacion_limpio[area_transformada_ha])
VAR Covarianza = SUMX(Pares, (deforestacion_limpio[area_perdida_bosque_ha] - MediaX) * (deforestacion_limpio[area_transformada_ha] - MediaY))
VAR SumaCuadX = SUMX(Pares, (deforestacion_limpio[area_perdida_bosque_ha] - MediaX) ^ 2)
VAR SumaCuadY = SUMX(Pares, (deforestacion_limpio[area_transformada_ha] - MediaY) ^ 2)
RETURN DIVIDE(Covarianza, SQRT(SumaCuadX * SumaCuadY))

Correlación (Focos de calor, Área transformada) =
VAR Pares = FILTER(deforestacion_limpio, NOT ISBLANK(deforestacion_limpio[num_focos_calor]) && NOT ISBLANK(deforestacion_limpio[area_transformada_ha]))
VAR MediaX = AVERAGEX(Pares, deforestacion_limpio[num_focos_calor])
VAR MediaY = AVERAGEX(Pares, deforestacion_limpio[area_transformada_ha])
VAR Covarianza = SUMX(Pares, (deforestacion_limpio[num_focos_calor] - MediaX) * (deforestacion_limpio[area_transformada_ha] - MediaY))
VAR SumaCuadX = SUMX(Pares, (deforestacion_limpio[num_focos_calor] - MediaX) ^ 2)
VAR SumaCuadY = SUMX(Pares, (deforestacion_limpio[area_transformada_ha] - MediaY) ^ 2)
RETURN DIVIDE(Covarianza, SQRT(SumaCuadX * SumaCuadY))

Correlación (Emisiones CO2, Área transformada) =
VAR Pares = FILTER(deforestacion_limpio, NOT ISBLANK(deforestacion_limpio[emisiones_co2_mg]) && NOT ISBLANK(deforestacion_limpio[area_transformada_ha]))
VAR MediaX = AVERAGEX(Pares, deforestacion_limpio[emisiones_co2_mg])
VAR MediaY = AVERAGEX(Pares, deforestacion_limpio[area_transformada_ha])
VAR Covarianza = SUMX(Pares, (deforestacion_limpio[emisiones_co2_mg] - MediaX) * (deforestacion_limpio[area_transformada_ha] - MediaY))
VAR SumaCuadX = SUMX(Pares, (deforestacion_limpio[emisiones_co2_mg] - MediaX) ^ 2)
VAR SumaCuadY = SUMX(Pares, (deforestacion_limpio[area_transformada_ha] - MediaY) ^ 2)
RETURN DIVIDE(Covarianza, SQRT(SumaCuadX * SumaCuadY))

Correlación (Emisiones CO2, Focos de calor) =
VAR Pares = FILTER(deforestacion_limpio, NOT ISBLANK(deforestacion_limpio[emisiones_co2_mg]) && NOT ISBLANK(deforestacion_limpio[num_focos_calor]))
VAR MediaX = AVERAGEX(Pares, deforestacion_limpio[emisiones_co2_mg])
VAR MediaY = AVERAGEX(Pares, deforestacion_limpio[num_focos_calor])
VAR Covarianza = SUMX(Pares, (deforestacion_limpio[emisiones_co2_mg] - MediaX) * (deforestacion_limpio[num_focos_calor] - MediaY))
VAR SumaCuadX = SUMX(Pares, (deforestacion_limpio[emisiones_co2_mg] - MediaX) ^ 2)
VAR SumaCuadY = SUMX(Pares, (deforestacion_limpio[num_focos_calor] - MediaY) ^ 2)
RETURN DIVIDE(Covarianza, SQRT(SumaCuadX * SumaCuadY))

Valor de correlación =
SWITCH(
    SELECTEDVALUE('Pares de variables'[Par]),
    "área perdida / emisiones CO2", [Correlación (Área perdida, Emisiones CO2)],
    "área perdida / focos de calor", [Correlación (Área perdida, Focos de calor)],
    "área perdida / área transformada", [Correlación (Área perdida, Área transformada)],
    "focos de calor / área transformada", [Correlación (Focos de calor, Área transformada)],
    "emisiones CO2 / área transformada", [Correlación (Emisiones CO2, Área transformada)],
    "emisiones CO2 / focos de calor", [Correlación (Emisiones CO2, Focos de calor)]
)
```

#### Driver × periodo y departamento × driver (usa `[Departamento top]` y `[Área perdida Colombia]` de la página 2)

```DAX
Área perdida periodo 1 (por driver) = CALCULATE([Área perdida Colombia], deforestacion_limpio[periodo] = "2001-2012")

Área perdida periodo 2 (por driver) = CALCULATE([Área perdida Colombia], deforestacion_limpio[periodo] = "2013-2024")

Crecimiento % (por driver) = DIVIDE([Área perdida periodo 2 (por driver)] - [Área perdida periodo 1 (por driver)], [Área perdida periodo 1 (por driver)])

Driver con mayor crecimiento (base relevante) =
VAR TablaRank =
    FILTER(
        ADDCOLUMNS(
            VALUES(deforestacion_limpio[driver_dominante]),
            "P1", CALCULATE([Área perdida periodo 1 (por driver)]),
            "Crecimiento", CALCULATE([Crecimiento % (por driver)])
        ),
        [P1] > 1000
    )
VAR Top1 = TOPN(1, TablaRank, [Crecimiento], DESC)
RETURN CONCATENATEX(Top1, deforestacion_limpio[driver_dominante])

Driver principal en departamento top =
VAR DepTop = [Departamento top]
VAR TablaRank =
    ADDCOLUMNS(
        VALUES(deforestacion_limpio[driver_dominante]),
        "Area", CALCULATE([Área perdida Colombia], deforestacion_limpio[departamento] = DepTop)
    )
VAR Top1 = TOPN(1, TablaRank, [Area], DESC)
RETURN CONCATENATEX(Top1, deforestacion_limpio[driver_dominante])

Driver principal (dinámico, por fila) =
VAR TablaRank = ADDCOLUMNS(VALUES(deforestacion_limpio[driver_dominante]), "Area", CALCULATE([Área perdida Colombia]))
VAR Top1 = TOPN(1, TablaRank, [Area], DESC)
RETURN CONCATENATEX(Top1, deforestacion_limpio[driver_dominante])
```

#### Conocimiento evidente 1 — Emisiones y área perdida miden casi lo mismo

- **Pregunta**: ¿Las emisiones de CO2 aportan información distinta del área perdida?
- **Variables**: area_perdida_bosque_ha y emisiones_co2_mg.
- **Procedimiento**: Coeficiente de Pearson sobre los 77.698 registros con ambos valores; se repitió con totales por año y por departamento; razón emisiones / área por registro municipal (mediana).
- **Evidencia**: Tarjeta "Correlación (Área perdida, Emisiones CO2)" y gráfico "Valor de correlación por Par".
- **Hallazgo**: r = 0,998 entre área perdida y emisiones; se mantiene con totales anuales (0,989) y por departamento (0,994). La mediana es de unas 472 Mg de CO2 por hectárea perdida.
- **Interpretación**: GFW calcula las emisiones a partir del área perdida y de la biomasa, así que la relación es casi una identidad, no un hallazgo causal.
- **Utilidad**: Basta un indicador (área perdida) para priorizar territorios; las emisiones se pueden estimar con el factor medio cuando se necesite el dato climático.
- **Limitación**: El factor por hectárea varía con la biomasa de cada zona.

#### Conocimiento evidente 2 — La transformación del suelo acompaña a la pérdida; los focos, menos

- **Pregunta**: ¿Qué variables se mueven junto con la pérdida de bosque?
- **Variables**: area_perdida_bosque_ha, area_transformada_ha, num_focos_calor y emisiones_co2_mg.
- **Procedimiento**: Pearson por par sobre los registros con ambos valores (n distinto por par: 72.262 con área transformada y 26.170 con focos, que solo existen de 2012 a 2022); comparación con totales anuales.
- **Evidencia**: Gráfico "Valor de correlación por Par".
- **Hallazgo**: Área perdida–área transformada 0,74; área transformada–focos 0,71; área perdida–focos 0,48. Con totales anuales, la relación área perdida–focos baja a 0,15 (11 años).
- **Interpretación**: Donde se pierde más bosque también hay más transformación agropecuaria, y los focos se asocian más con la transformación que con la pérdida. Es una asociación, no una causa: el tamaño del municipio puede explicar parte de la relación.
- **Utilidad**: Sugiere usar el área transformada como indicador complementario de seguimiento y no depender de los focos de calor para estimar la pérdida.
- **Limitación**: Cada par usa un n y un periodo distintos; los focos cubren solo el 34,5 % de los registros municipales y no se controla por el área del municipio.

#### Conocimiento evidente 3 — Una causa domina; otras emergen desde bases pequeñas

- **Pregunta**: ¿La causa principal cambia según el departamento y el periodo?
- **Variables**: driver_dominante, departamento, periodo y area_perdida_bosque_ha.
- **Procedimiento**: Escala Regional con una fila por municipio-año; área por causa en cada departamento y periodo; causa con mayor área por departamento y variación entre periodos de 12 años.
- **Evidencia**: Tabla "departamento – Área – Driver principal", tarjetas "Driver principal en departamento top" y "Driver con mayor crecimiento", y columnas por periodo y causa.
- **Hallazgo**: La agricultura permanente es la causa principal en 29 de 33 departamentos y pasa del 95,1 % al 93,5 % del área entre periodos. En Amazonas, Guainía y Vaupés domina la agricultura migratoria. Los incendios forestales pasan de 46 a 29.908 ha y la minería de 1.071 a 8.501 ha.
- **Interpretación**: La estructura de causas es estable, pero en el periodo reciente aparecen causas nuevas; su crecimiento porcentual es enorme porque parten casi de cero.
- **Utilidad**: La política general debe centrarse en la agricultura permanente, con estrategias diferenciadas para Amazonas, Guainía y Vaupés y vigilancia temprana de incendios y minería.
- **Limitación**: "Mayor crecimiento" no significa mayor impacto: los incendios siguen por debajo del 1 % del área, y su casi ausencia antes de 2013 puede reflejar cambios de clasificación.

#### Limitación del análisis (página 4)

Las comparaciones por causa usan la causa dominante de cada municipio-año, no la causa de cada hectárea.

#### Posible decisión sustentada en los datos (página 4)

Usar el área perdida como indicador principal (las emisiones son casi proporcionales, r = 0,998) y diseñar dos líneas de acción: control de la expansión agropecuaria permanente en los 29 departamentos donde domina y estrategias para la agricultura migratoria en Amazonas, Guainía y Vaupés, con alertas tempranas de incendios y minería.
