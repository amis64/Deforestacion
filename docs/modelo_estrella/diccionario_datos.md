# Diccionario de datos del modelo estrella

**Hecho:** hechos_perdida_forestal · **Granularidad:** Una fila por TERRITORIO y AÑO. La clave primaria compuesta (territorio_key, tiempo_key; la fuente es anual, así que hay un solo tiempo_key por año) impone esa granularidad. Un municipio-año que en el dataset tratado aparece en varias filas (copias con distinta combinación de fuentes) se consolida en una sola fila; el número de filas de origen se conserva en n_registros_origen.

## dim_territorio (Dimensión)

Clave primaria: `territorio_key`. Jerarquía: región natural → departamento → municipio.

| Campo | Tipo | Clave | Descripción | Origen | Transformación |
|---|---|---|---|---|---|
| territorio_key | INTEGER | PK | Clave sustituta del territorio. | — | Secuencia al cargar. |
| nivel_analisis | TEXT | UK | Nivel de la fuente: Regional, Nacional o Global. | nivel_analisis | Sin cambio. |
| escala | TEXT |  | Escala del miembro: Municipal, Departamental o País. | nivel_analisis | Regional→Municipal, Nacional→Departamental, Global→País. |
| pais | TEXT | UK | País. | pais | Espacios normalizados. |
| region_natural | TEXT |  | Región natural (Amazonía, Andina, Caribe, Orinoquía, Pacífica, Insular). | departamento | Asignada con la tabla departamento→región; «Sin región informada» / «No aplica» si no corresponde. |
| departamento | TEXT | UK | Departamento. | departamento | Nulo → «Sin departamento informado» (Global: «No aplica»). |
| municipio | TEXT | UK | Municipio. | municipio | Nulo → «Sin municipio informado»; nivel Nacional → «(total del departamento)». |
| es_agregado_regional | INTEGER |  | 1 si el miembro es un agregado de la fuente. | es_agregado_regional | True/False → 1/0. |
| latitud / longitud | REAL |  | Coordenadas del centroide. | latitud, longitud | Primer valor no nulo. |

## dim_tiempo (Dimensión)

Clave primaria: `id_dim_tiempo`. Jerarquía: calendario: año → semestre → trimestre → mes → día · análisis: periodo (12 años) → trienio → año.

| Campo | Tipo | Clave | Descripción | Origen | Transformación |
|---|---|---|---|---|---|
| id_dim_tiempo | INTEGER | PK | Clave sustituta con formato AAAAMMDD (ej. 20261104). Los hechos anuales usan AAAA0101. | anio | Calculada: año×10000 + mes×100 + día. |
| fecha | TEXT | UK | Fecha completa AAAA-MM-DD. | anio | Calendario generado (2001-01-01 a 2024-12-31, 8.766 días). |
| anio | INTEGER |  | Año calendario de 4 dígitos (2001–2024). | anio | Sin cambio. |
| anio_fiscal | TEXT |  | Año fiscal (FY2026). Coincide con el año calendario. | anio | 'FY' + año. |
| semestre | TEXT |  | Semestre 1 o 2. | (generada por el ETL) | Calculado desde el mes. |
| cuatrimestre | TEXT |  | Cuatrimestre 1 a 3. | (generada por el ETL) | Calculado desde el mes. |
| trimestre | TEXT |  | Trimestre 1 a 4. | (generada por el ETL) | Calculado desde el mes. |
| bimestre | TEXT |  | Bimestre 1 a 6. | (generada por el ETL) | Calculado desde el mes. |
| mes / mes_nombre / mes_nombre_corto | INTEGER / TEXT / TEXT |  | Número del mes (1–12), nombre (Noviembre) y abreviatura (Nov). | (generada por el ETL) | Calculado desde la fecha. |
| semana / semana_nombre | INTEGER / TEXT |  | Semana ISO 8601 del año (1–53) y su nombre (Semana 45). | (generada por el ETL) | Calculado con isocalendar(); la semana no se anida en el mes. |
| dia / dia_del_anio | INTEGER |  | Día del mes (1–31) y día secuencial del año (1–366). | (generada por el ETL) | Calculado desde la fecha. |
| dia_semana_numero / dia_semana_nombre / dia_semana_corto | INTEGER / TEXT / TEXT |  | Posición en la semana (1 = lunes a 7 = domingo), nombre (Miércoles) y abreviatura (Mié). | (generada por el ETL) | Calculado desde la fecha. |
| hora | INTEGER |  | Hora del día (0–23). El grano de la dimensión es el día, por lo que es NULL («No aplica»); no hay datos horarios. | (generada por el ETL) | NULL; no se multiplica la dimensión por 24. |
| es_periodo_pandemia | INTEGER |  | 1 si el día cae entre el 11-mar-2020 y el 5-may-2023 (declaración y fin de la emergencia internacional por COVID-19 de la OMS). | (generada por el ETL) | Bandera de contexto; 1.151 días. |
| es_anio_con_pandemia | INTEGER |  | 1 si el año tiene algún día de pandemia (2020–2023). Es la bandera aplicable a los hechos anuales. | anio | Derivada de es_periodo_pandemia. |
| trienio / trienio_orden | TEXT / INTEGER |  | Trienio al que pertenece el año (2001–2003, …) y su orden. | anio | Calculado: (año − 2001) ÷ 3. |
| periodo / periodo_orden | TEXT / INTEGER |  | Periodo de 12 años (2001–2012 o 2013–2024) y su orden. | anio | Calculado; ambos periodos tienen 12 años (equivalentes). |

## dim_causa (Dimensión)

Clave primaria: `causa_key`. Jerarquía: grupo de causa → causa (driver dominante).

| Campo | Tipo | Clave | Descripción | Origen | Transformación |
|---|---|---|---|---|---|
| causa_key | INTEGER | PK | Clave sustituta de la causa. | — | Secuencia al cargar. |
| driver_dominante | TEXT | UK | Causa dominante de la pérdida según la fuente. | driver_dominante | Vacío → «Sin causa informada» (Colombia) o «No aplica» (otros países). |
| grupo_causa | TEXT |  | Agropecuaria, Forestal (plantaciones), Natural, Infraestructura y minería. | driver_dominante | Agrupación definida en el ETL. |
| tipo_valor | TEXT |  | Informada / Sin informar / No aplica. | — | Distingue faltante de categoría no aplicable. |

## dim_transformacion (Dimensión)

Clave primaria: `transformacion_key`. Jerarquía: clase de transformación (un nivel).

| Campo | Tipo | Clave | Descripción | Origen | Transformación |
|---|---|---|---|---|---|
| transformacion_key | INTEGER | PK | Clave sustituta de la clase. | — | Secuencia al cargar. |
| clase_transformacion | TEXT | UK | Clase de transformación dominante del suelo (Área agropecuaria, Área sin vegetación). | clase_transformacion_dominante | Vacío → «Sin clase informada» o «No aplica». |
| tipo_valor | TEXT |  | Informada / Sin informar / No aplica. | — | Distingue faltante de categoría no aplicable. |

## dim_fuente (Dimensión)

Clave primaria: `fuente_key`. Jerarquía: número de fuentes → combinación de fuentes.

| Campo | Tipo | Clave | Descripción | Origen | Transformación |
|---|---|---|---|---|---|
| fuente_key | INTEGER | PK | Clave sustituta de la combinación de fuentes. | — | Secuencia al cargar. |
| fuente_origen | TEXT | UK | Combinación de fuentes (p. ej. GFW+MapBiomas+FIRMS). | fuente_origen | Se conserva la combinación textual. |
| n_fuentes | INTEGER |  | Cantidad de fuentes que aportaron al registro. | fuente_origen | Conteo de componentes. |
| incluye_gfw / _mapbiomas / _firms / _fao / _owid | INTEGER |  | Indicadores 0/1 de cada fuente. | fuente_origen | Derivados de la combinación. |

## hechos_perdida_forestal (Hechos)

Clave primaria: `(territorio_key, tiempo_key)`. Jerarquía: —.

| Campo | Tipo | Clave | Descripción | Origen | Transformación |
|---|---|---|---|---|---|
| territorio_key | INTEGER | PK, FK | → dim_territorio. | — | Búsqueda por clave natural. |
| tiempo_key | INTEGER | PK, FK | → dim_tiempo.id_dim_tiempo; el 1 de enero del año del hecho (AAAA0101). | anio | Calculada: año×10000 + 101. |
| causa_key | INTEGER | FK | → dim_causa. | driver_dominante | Primer valor no nulo entre las copias. |
| transformacion_key | INTEGER | FK | → dim_transformacion. | clase_transformacion_dominante | Primer valor no nulo entre las copias. |
| fuente_key | INTEGER | FK | → dim_fuente. | fuente_origen | Primer valor no nulo entre las copias. |
| n_registros_origen | INTEGER |  | Filas del dataset tratado consolidadas en este hecho. | — | Conteo de copias; permite reconstruir los 80.585 registros. |
| id_registro_min | INTEGER |  | Menor id_registro del grupo (trazabilidad). | id_registro | Mínimo. |
| area_perdida_bosque_ha | REAL | Medida | Hectáreas de bosque perdidas. | area_perdida_bosque_ha | Primer valor no nulo (las copias comparten el área). Nulo se conserva nulo. |
| emisiones_co2_mg | REAL | Medida | Emisiones estimadas de CO₂e (Mg). | emisiones_co2_mg | Promedio de las copias (difieren levemente). |
| area_transformada_ha | REAL | Medida | Área con transformación del suelo (ha). | area_transformada_ha | Primer valor no nulo. |
| num_focos_calor | REAL | Medida | Focos de calor FIRMS asociados (2012–2022). | num_focos_calor | Primer valor no nulo; nulo ≠ 0. |
| frp_promedio, confianza_promedio_focos | REAL | Medida | Potencia radiativa y confianza promedio de los focos. | frp_promedio, confianza_promedio_focos | Primer valor no nulo. |
| porcentaje_area_forestal, area_forestal_ha | REAL | Medida | Contexto forestal del país (FAO). | porcentaje_area_forestal, area_forestal_ha | Primer valor no nulo. |
| deforestacion_anual_ha_owid | REAL | Medida | Deforestación anual del país (OWID). | deforestacion_anual_ha_owid | Primer valor no nulo. |
| area_perdida_atipica, emisiones_atipicas | INTEGER | Marca | 1 si el valor fue marcado atípico en el tratamiento. | *_atipico | Máximo entre las copias. Los atípicos NO se eliminan. |

## Relaciones

| Clave foránea | Referencia | Cardinalidad |
|---|---|---|
| hechos_perdida_forestal.territorio_key | dim_territorio.territorio_key | muchos a uno |
| hechos_perdida_forestal.tiempo_key | dim_tiempo.id_dim_tiempo | muchos a uno |
| hechos_perdida_forestal.causa_key | dim_causa.causa_key | muchos a uno |
| hechos_perdida_forestal.transformacion_key | dim_transformacion.transformacion_key | muchos a uno |
| hechos_perdida_forestal.fuente_key | dim_fuente.fuente_key | muchos a uno |

## Medidas de análisis

| Medida | Unidad | Fórmula | Agregación | Cuándo se suma |
|---|---|---|---|---|
| Área perdida de bosque | ha | `SUM(area_perdida_bosque_ha)` | SUM | Aditiva: se suma entre territorios y entre años (dentro de una misma escala). |
| Emisiones de CO₂e | Mg CO₂e | `SUM(emisiones_co2_mg)` | SUM | Aditiva. Si un municipio-año tenía copias, se usó el promedio de ellas. |
| Intensidad de emisiones | Mg CO₂e/ha | `SUM(emisiones_co2_mg / área > 0) / SUM(area_perdida_bosque_ha / área > 0)` | RAZÓN | NO aditiva: es una razón; se recalcula como cociente de sumas en cada nivel. Solo usa filas con área > 0 porque el área está redondeada a hectárea entera (las filas con 0 ha tienen emisiones pequeñas por pérdidas menores a 1 ha y distorsionarían el cociente). |
| Pérdida promedio anual | ha/año | `SUM(area_perdida_bosque_ha) / COUNT(DISTINCT anio)` | PROMEDIO | NO se suma entre periodos: se divide entre los años presentes en cada grupo, para comparar periodos de igual duración (12 años). |
| Focos de calor | focos | `SUM(num_focos_calor)` | SUM | Aditiva, pero solo existe donde la fuente FIRMS aporta datos (2012–2022). |
| Focos por 100 ha perdidas | focos/100 ha | `100 · SUM(num_focos_calor) / SUM(area_perdida_bosque_ha / con focos registrados)` | RAZÓN | NO aditiva: razón; el denominador solo incluye la pérdida de los territorio-año que tienen focos registrados. |
| Territorios con pérdida | territorios | `COUNT(DISTINCT territorio_key / área > 0)` | CONTEO DISTINTO | NO aditiva: cuenta entidades únicas; un mismo municipio aparece en varios años y no debe contarse varias veces. |
| Registros de origen | registros | `SUM(n_registros_origen)` | SUM | Aditiva: reconstruye el conteo de filas del dataset tratado (no es conteo de territorios). |
| Territorio-año | filas | `COUNT(*)` | CONTEO | Conteo de filas de la tabla de hechos (una por territorio y año). |
| Pérdida en territorio-año con focos registrados | ha | `SUM(area_perdida_bosque_ha / num_focos_calor no nulo)` | SUM | Aditiva. |
| Pérdida sin clase de transformación informada | ha | `SUM(area_perdida_bosque_ha / clase = 'Sin clase informada')` | SUM | Aditiva. |
