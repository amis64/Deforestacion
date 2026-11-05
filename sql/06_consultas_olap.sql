-- =============================================================================
-- 06_consultas_olap.sql · Etapa 5: consultas del análisis multidimensional
-- Se ejecutan sobre la vista vw_cubo (hechos + 5 dimensiones, sin multiplicar filas).
-- Todas filtran nivel_analisis = 'Regional' (escala municipal): las escalas
-- departamental y país contienen la misma pérdida y NO se mezclan.
-- Cada consulta indica la operación, la vista de Flask y el conocimiento que respalda.
-- =============================================================================

-- C-01 · Indicadores base (vista 1 / página principal)
-- Suma de hectáreas, conteo de entidades únicas y registros de origen (tres cosas distintas).
SELECT SUM(area_perdida_bosque_ha)                                              AS area_ha,
       COUNT(DISTINCT CASE WHEN area_perdida_bosque_ha > 0 THEN territorio_key END) AS municipios_con_perdida,
       COUNT(*)                                                                 AS filas_de_hechos,
       SUM(n_registros_origen)                                                  AS registros_de_origen
FROM vw_cubo WHERE nivel_analisis = 'Regional';

-- C-02 · Región × grupo de causa (vista 1). Denominador del %: total de la región.
SELECT region_natural, grupo_causa, SUM(area_perdida_bosque_ha) AS area_ha,
       ROUND(100.0 * SUM(area_perdida_bosque_ha) /
             SUM(SUM(area_perdida_bosque_ha)) OVER (PARTITION BY region_natural), 1) AS pct_de_la_region
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY region_natural, grupo_causa ORDER BY region_natural, area_ha DESC;

-- C-03 · DRILL-DOWN + SLICE (K1.1): departamento × causa dentro de la región Pacífica.
SELECT departamento, driver_dominante, SUM(area_perdida_bosque_ha) AS area_ha,
       ROUND(100.0 * SUM(area_perdida_bosque_ha) /
             SUM(SUM(area_perdida_bosque_ha)) OVER (PARTITION BY departamento), 1) AS pct_del_departamento
FROM vw_cubo WHERE nivel_analisis = 'Regional' AND region_natural = 'Pacífica'
GROUP BY departamento, driver_dominante ORDER BY departamento, area_ha DESC;

-- C-04 · DICE (K1.2): región Pacífica (Territorio) y causa Incendios forestales (Causa), departamento × año.
SELECT departamento, anio, SUM(area_perdida_bosque_ha) AS area_ha
FROM vw_cubo
WHERE nivel_analisis = 'Regional' AND region_natural = 'Pacífica' AND driver_dominante = 'Incendios forestales'
GROUP BY departamento, anio HAVING SUM(area_perdida_bosque_ha) > 0 ORDER BY area_ha DESC;

-- C-05 · ROLL-UP (K2.1): pérdida promedio anual por región y periodo (periodos de 12 años).
-- Medida NO aditiva: SUM(ha) / COUNT(DISTINCT año), recalculada en cada nivel.
SELECT region_natural, periodo, SUM(area_perdida_bosque_ha) * 1.0 / COUNT(DISTINCT anio) AS ha_por_anio
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY region_natural, periodo ORDER BY region_natural, periodo;

-- C-06 · DRILL-DOWN (K2.1): lo mismo por departamento.
SELECT region_natural, departamento, periodo, SUM(area_perdida_bosque_ha) * 1.0 / COUNT(DISTINCT anio) AS ha_por_anio
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY region_natural, departamento, periodo ORDER BY region_natural, departamento, periodo;

-- C-07 · PIVOT (K2.2): trienio × región (filas = trienio, columnas = región; en SQL, una columna por región).
SELECT trienio,
       ROUND(SUM(CASE WHEN region_natural='Amazonía'  THEN area_perdida_bosque_ha END) / 3.0) AS amazonia,
       ROUND(SUM(CASE WHEN region_natural='Andina'    THEN area_perdida_bosque_ha END) / 3.0) AS andina,
       ROUND(SUM(CASE WHEN region_natural='Caribe'    THEN area_perdida_bosque_ha END) / 3.0) AS caribe,
       ROUND(SUM(CASE WHEN region_natural='Orinoquía' THEN area_perdida_bosque_ha END) / 3.0) AS orinoquia,
       ROUND(SUM(CASE WHEN region_natural='Pacífica'  THEN area_perdida_bosque_ha END) / 3.0) AS pacifica,
       ROUND(SUM(area_perdida_bosque_ha) / 3.0) AS nacional
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY trienio ORDER BY trienio;

-- C-08 · Intensidad de emisiones región × causa (K3.1). Razón de sumas con área > 0.
SELECT region_natural, driver_dominante,
       SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN emisiones_co2_mg END) * 1.0 /
       NULLIF(SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN area_perdida_bosque_ha END), 0) AS mg_co2e_por_ha,
       SUM(area_perdida_bosque_ha) AS base_ha
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY region_natural, driver_dominante ORDER BY region_natural, driver_dominante;

-- C-09 · SLICE (K3.2): pérdida sin clase de transformación por región (categoría DESCONOCIDA, no cero).
SELECT region_natural, clase_transformacion, SUM(area_perdida_bosque_ha) AS area_ha,
       ROUND(100.0 * SUM(area_perdida_bosque_ha) /
             SUM(SUM(area_perdida_bosque_ha)) OVER (PARTITION BY region_natural), 1) AS pct_de_la_region
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY region_natural, clase_transformacion ORDER BY region_natural, clase_transformacion;

-- C-09b · Comprobación: toda la pérdida sin clase proviene de registros sin MapBiomas.
SELECT fu.incluye_mapbiomas, SUM(v.area_perdida_bosque_ha) AS area_sin_clase_ha
FROM vw_cubo v JOIN dim_fuente fu ON fu.fuente_key = v.fuente_key
WHERE v.nivel_analisis = 'Regional' AND v.clase_transformacion = 'Sin clase informada'
GROUP BY fu.incluye_mapbiomas;

-- C-10 · ROLL-UP de una razón: intensidad por departamento de la Amazonía y recalculada a región.
SELECT departamento,
       SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN emisiones_co2_mg END) * 1.0 /
       NULLIF(SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN area_perdida_bosque_ha END), 0) AS mg_co2e_por_ha
FROM vw_cubo WHERE nivel_analisis = 'Regional' AND region_natural = 'Amazonía' GROUP BY departamento
UNION ALL
SELECT 'AMAZONÍA (roll-up recalculado)',
       SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN emisiones_co2_mg END) * 1.0 /
       NULLIF(SUM(CASE WHEN area_perdida_bosque_ha > 0 THEN area_perdida_bosque_ha END), 0)
FROM vw_cubo WHERE nivel_analisis = 'Regional' AND region_natural = 'Amazonía';

-- C-11 · Focos por 100 ha perdidas, región × trienio (K4.1). El denominador solo incluye
-- los territorio-año con focos registrados (un faltante no es cero focos).
SELECT region_natural, trienio,
       SUM(num_focos_calor) * 100.0 /
       NULLIF(SUM(CASE WHEN num_focos_calor IS NOT NULL THEN area_perdida_bosque_ha END), 0) AS focos_por_100ha
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY region_natural, trienio ORDER BY region_natural, trienio;

-- C-11b · SLICE (Región = Orinoquía) y drill-down a departamento.
SELECT departamento, SUM(num_focos_calor) AS focos,
       SUM(CASE WHEN num_focos_calor IS NOT NULL THEN area_perdida_bosque_ha END) AS area_con_focos_ha,
       SUM(num_focos_calor) * 100.0 /
       NULLIF(SUM(CASE WHEN num_focos_calor IS NOT NULL THEN area_perdida_bosque_ha END), 0) AS focos_por_100ha
FROM vw_cubo WHERE nivel_analisis = 'Regional' AND region_natural = 'Orinoquía'
GROUP BY departamento ORDER BY focos_por_100ha DESC;

-- C-12 · Cobertura de la fuente de focos (FIRMS) 2012–2022: pérdida con focos registrados / pérdida total.
SELECT region_natural,
       SUM(CASE WHEN num_focos_calor IS NOT NULL THEN area_perdida_bosque_ha END) AS area_con_focos_ha,
       SUM(area_perdida_bosque_ha) AS area_total_ha,
       ROUND(100.0 * SUM(CASE WHEN num_focos_calor IS NOT NULL THEN area_perdida_bosque_ha END) /
             SUM(area_perdida_bosque_ha), 1) AS cobertura_pct
FROM vw_cubo WHERE nivel_analisis = 'Regional' AND anio BETWEEN 2012 AND 2022
GROUP BY region_natural ORDER BY region_natural;

-- C-13 · ROLL-UP de Fuente (combinación → número de fuentes) × periodo (K4.2). Denominador: pérdida del periodo.
SELECT n_fuentes, periodo, SUM(area_perdida_bosque_ha) AS area_ha,
       ROUND(100.0 * SUM(area_perdida_bosque_ha) /
             SUM(SUM(area_perdida_bosque_ha)) OVER (PARTITION BY periodo), 1) AS pct_del_periodo
FROM vw_cubo WHERE nivel_analisis = 'Regional'
GROUP BY n_fuentes, periodo ORDER BY periodo, n_fuentes DESC;

-- C-14 · Verificación entre escalas (misma pérdida): el cambio entre periodos coincide en las tres escalas.
SELECT nivel_analisis,
       ROUND((SUM(CASE WHEN periodo='2013–2024' THEN area_perdida_bosque_ha END) /
              SUM(CASE WHEN periodo='2001–2012' THEN area_perdida_bosque_ha END) - 1) * 100, 2) AS cambio_pct
FROM vw_cubo WHERE pais = 'Colombia' GROUP BY nivel_analisis;
