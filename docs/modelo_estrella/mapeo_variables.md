# Correspondencia entre variables originales y campos del modelo

Origen: `deforestacion_limpio.csv` (dataset tratado en las etapas anteriores).

| Variable original | Campo del modelo | Transformación |
|---|---|---|
| — | dim_territorio.territorio_key | Secuencia al cargar. |
| nivel_analisis | dim_territorio.nivel_analisis | Sin cambio. |
| nivel_analisis | dim_territorio.escala | Regional→Municipal, Nacional→Departamental, Global→País. |
| pais | dim_territorio.pais | Espacios normalizados. |
| departamento | dim_territorio.region_natural | Asignada con la tabla departamento→región; «Sin región informada» / «No aplica» si no corresponde. |
| departamento | dim_territorio.departamento | Nulo → «Sin departamento informado» (Global: «No aplica»). |
| municipio | dim_territorio.municipio | Nulo → «Sin municipio informado»; nivel Nacional → «(total del departamento)». |
| es_agregado_regional | dim_territorio.es_agregado_regional | True/False → 1/0. |
| latitud, longitud | dim_territorio.latitud / longitud | Primer valor no nulo. |
| anio | dim_tiempo.id_dim_tiempo | Calculada: año×10000 + mes×100 + día. |
| anio | dim_tiempo.fecha | Calendario generado (2001-01-01 a 2024-12-31, 8.766 días). |
| anio | dim_tiempo.anio | Sin cambio. |
| anio | dim_tiempo.anio_fiscal | 'FY' + año. |
| (generada por el ETL) | dim_tiempo.semestre | Calculado desde el mes. |
| (generada por el ETL) | dim_tiempo.cuatrimestre | Calculado desde el mes. |
| (generada por el ETL) | dim_tiempo.trimestre | Calculado desde el mes. |
| (generada por el ETL) | dim_tiempo.bimestre | Calculado desde el mes. |
| (generada por el ETL) | dim_tiempo.mes / mes_nombre / mes_nombre_corto | Calculado desde la fecha. |
| (generada por el ETL) | dim_tiempo.semana / semana_nombre | Calculado con isocalendar(); la semana no se anida en el mes. |
| (generada por el ETL) | dim_tiempo.dia / dia_del_anio | Calculado desde la fecha. |
| (generada por el ETL) | dim_tiempo.dia_semana_numero / dia_semana_nombre / dia_semana_corto | Calculado desde la fecha. |
| (generada por el ETL) | dim_tiempo.hora | NULL; no se multiplica la dimensión por 24. |
| (generada por el ETL) | dim_tiempo.es_periodo_pandemia | Bandera de contexto; 1.151 días. |
| anio | dim_tiempo.es_anio_con_pandemia | Derivada de es_periodo_pandemia. |
| anio | dim_tiempo.trienio / trienio_orden | Calculado: (año − 2001) ÷ 3. |
| anio | dim_tiempo.periodo / periodo_orden | Calculado; ambos periodos tienen 12 años (equivalentes). |
| — | dim_causa.causa_key | Secuencia al cargar. |
| driver_dominante | dim_causa.driver_dominante | Vacío → «Sin causa informada» (Colombia) o «No aplica» (otros países). |
| driver_dominante | dim_causa.grupo_causa | Agrupación definida en el ETL. |
| — | dim_causa.tipo_valor | Distingue faltante de categoría no aplicable. |
| — | dim_transformacion.transformacion_key | Secuencia al cargar. |
| clase_transformacion_dominante | dim_transformacion.clase_transformacion | Vacío → «Sin clase informada» o «No aplica». |
| — | dim_transformacion.tipo_valor | Distingue faltante de categoría no aplicable. |
| — | dim_fuente.fuente_key | Secuencia al cargar. |
| fuente_origen | dim_fuente.fuente_origen | Se conserva la combinación textual. |
| fuente_origen | dim_fuente.n_fuentes | Conteo de componentes. |
| fuente_origen | dim_fuente.incluye_gfw / _mapbiomas / _firms / _fao / _owid | Derivados de la combinación. |
| — | hechos_perdida_forestal.territorio_key | Búsqueda por clave natural. |
| anio | hechos_perdida_forestal.tiempo_key | Calculada: año×10000 + 101. |
| driver_dominante | hechos_perdida_forestal.causa_key | Primer valor no nulo entre las copias. |
| clase_transformacion_dominante | hechos_perdida_forestal.transformacion_key | Primer valor no nulo entre las copias. |
| fuente_origen | hechos_perdida_forestal.fuente_key | Primer valor no nulo entre las copias. |
| — | hechos_perdida_forestal.n_registros_origen | Conteo de copias; permite reconstruir los 80.585 registros. |
| id_registro | hechos_perdida_forestal.id_registro_min | Mínimo. |
| area_perdida_bosque_ha | hechos_perdida_forestal.area_perdida_bosque_ha | Primer valor no nulo (las copias comparten el área). Nulo se conserva nulo. |
| emisiones_co2_mg | hechos_perdida_forestal.emisiones_co2_mg | Promedio de las copias (difieren levemente). |
| area_transformada_ha | hechos_perdida_forestal.area_transformada_ha | Primer valor no nulo. |
| num_focos_calor | hechos_perdida_forestal.num_focos_calor | Primer valor no nulo; nulo ≠ 0. |
| frp_promedio, confianza_promedio_focos | hechos_perdida_forestal.frp_promedio, confianza_promedio_focos | Primer valor no nulo. |
| porcentaje_area_forestal, area_forestal_ha | hechos_perdida_forestal.porcentaje_area_forestal, area_forestal_ha | Primer valor no nulo. |
| deforestacion_anual_ha_owid | hechos_perdida_forestal.deforestacion_anual_ha_owid | Primer valor no nulo. |
| *_atipico | hechos_perdida_forestal.area_perdida_atipica, emisiones_atipicas | Máximo entre las copias. Los atípicos NO se eliminan. |

## Procedimiento de carga

1. Leer deforestacion_limpio.csv (dataset tratado, 80.585 registros) y calcular su huella SHA-256.
2. Agrupar las filas por la clave natural del hecho: (nivel de análisis, país, departamento, municipio, año).
3. Generar la dimensión tiempo como calendario diario (2001-01-01 a 2024-12-31): atributos de año, año fiscal, semestre a bimestre, mes, semana ISO, día, hora (NULL) y banderas de pandemia; cada hecho anual se asocia al 1 de enero de su año.
4. Construir las demás dimensiones con claves sustitutas y asignar región natural, grupo de causa y periodos; los vacíos se mapean a «Sin … informada» o «No aplica» según corresponda.
5. Colapsar cada grupo en una fila de hechos: área = primer valor no nulo, emisiones = promedio de las copias, demás medidas = primer valor no nulo; se guarda n_registros_origen.
6. Crear las tablas con el DDL (sql/05_modelo_estrella_ddl.sql), cargar dimensiones y hechos con las claves foráneas activadas y registrar la trazabilidad en meta_carga.
7. Ejecutar multidimensional/validar_modelo.py: 30 verificaciones de integridad (incluye el calendario) y 10 comparaciones con el dataset tratado (reporte_validacion.json).
