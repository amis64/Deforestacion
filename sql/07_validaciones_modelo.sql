-- =============================================================================
-- 07_validaciones_modelo.sql · Etapa 5: validaciones del modelo estrella
-- Cada consulta devuelve la columna «resultado» = 'OK' cuando la verificación se cumple.
-- Equivale a multidimensional/validar_modelo.py (que además compara con el CSV tratado).
-- =============================================================================
PRAGMA foreign_keys = ON;

-- V-01..V-05 · Unicidad de las claves de las dimensiones (filas = valores distintos).
SELECT 'V-01 dim_territorio' AS verificacion, COUNT(*) AS filas, COUNT(DISTINCT territorio_key) AS claves,
       CASE WHEN COUNT(*) = COUNT(DISTINCT territorio_key) THEN 'OK' ELSE 'FALLA' END AS resultado FROM dim_territorio
UNION ALL SELECT 'V-01b dim_territorio (clave natural)', COUNT(*),
       (SELECT COUNT(*) FROM (SELECT DISTINCT nivel_analisis, pais, departamento, municipio FROM dim_territorio)),
       CASE WHEN COUNT(*) = (SELECT COUNT(*) FROM (SELECT DISTINCT nivel_analisis, pais, departamento, municipio FROM dim_territorio)) THEN 'OK' ELSE 'FALLA' END FROM dim_territorio
UNION ALL SELECT 'V-02 dim_tiempo', COUNT(*), COUNT(DISTINCT id_dim_tiempo), CASE WHEN COUNT(*) = COUNT(DISTINCT id_dim_tiempo) THEN 'OK' ELSE 'FALLA' END FROM dim_tiempo
UNION ALL SELECT 'V-02b dim_tiempo (fecha)', COUNT(*), COUNT(DISTINCT fecha), CASE WHEN COUNT(*) = COUNT(DISTINCT fecha) THEN 'OK' ELSE 'FALLA' END FROM dim_tiempo
UNION ALL SELECT 'V-03 dim_causa', COUNT(*), COUNT(DISTINCT driver_dominante), CASE WHEN COUNT(*) = COUNT(DISTINCT driver_dominante) THEN 'OK' ELSE 'FALLA' END FROM dim_causa
UNION ALL SELECT 'V-04 dim_transformacion', COUNT(*), COUNT(DISTINCT clase_transformacion), CASE WHEN COUNT(*) = COUNT(DISTINCT clase_transformacion) THEN 'OK' ELSE 'FALLA' END FROM dim_transformacion
UNION ALL SELECT 'V-05 dim_fuente', COUNT(*), COUNT(DISTINCT fuente_origen), CASE WHEN COUNT(*) = COUNT(DISTINCT fuente_origen) THEN 'OK' ELSE 'FALLA' END FROM dim_fuente;

-- V-06 · Claves foráneas sin miembro (debe devolver 0 en cada dimensión).
SELECT 'V-06 hechos sin territorio' AS verificacion, COUNT(*) AS huerfanos,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END AS resultado
FROM hechos_perdida_forestal f LEFT JOIN dim_territorio d ON d.territorio_key = f.territorio_key WHERE d.territorio_key IS NULL
UNION ALL SELECT 'V-06 hechos sin tiempo', COUNT(*), CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END
FROM hechos_perdida_forestal f LEFT JOIN dim_tiempo d ON d.id_dim_tiempo = f.tiempo_key WHERE d.id_dim_tiempo IS NULL
UNION ALL SELECT 'V-06 hechos sin causa', COUNT(*), CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END
FROM hechos_perdida_forestal f LEFT JOIN dim_causa d ON d.causa_key = f.causa_key WHERE d.causa_key IS NULL
UNION ALL SELECT 'V-06 hechos sin transformación', COUNT(*), CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END
FROM hechos_perdida_forestal f LEFT JOIN dim_transformacion d ON d.transformacion_key = f.transformacion_key WHERE d.transformacion_key IS NULL
UNION ALL SELECT 'V-06 hechos sin fuente', COUNT(*), CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END
FROM hechos_perdida_forestal f LEFT JOIN dim_fuente d ON d.fuente_key = f.fuente_key WHERE d.fuente_key IS NULL;

-- V-07 · Sin duplicados en la granularidad (territorio, año): debe devolver 0 filas de grupos repetidos.
SELECT 'V-07 grupos (territorio, año) repetidos' AS verificacion, COUNT(*) AS repetidos,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END AS resultado
FROM (SELECT territorio_key, tiempo_key FROM hechos_perdida_forestal GROUP BY 1, 2 HAVING COUNT(*) > 1);

-- V-08 · La vista vw_cubo no multiplica filas: mismas filas que la tabla de hechos.
SELECT 'V-08 filas vw_cubo = filas de hechos' AS verificacion,
       (SELECT COUNT(*) FROM vw_cubo) AS vista, (SELECT COUNT(*) FROM hechos_perdida_forestal) AS hechos,
       CASE WHEN (SELECT COUNT(*) FROM vw_cubo) = (SELECT COUNT(*) FROM hechos_perdida_forestal) THEN 'OK' ELSE 'FALLA' END AS resultado;

-- V-09 · Los registros de origen se reconstruyen (80.585) y coinciden con meta_carga.
SELECT 'V-09 SUM(n_registros_origen) = registros del CSV' AS verificacion,
       (SELECT SUM(n_registros_origen) FROM hechos_perdida_forestal) AS modelo,
       (SELECT registros_origen FROM meta_carga) AS csv,
       CASE WHEN (SELECT SUM(n_registros_origen) FROM hechos_perdida_forestal) = (SELECT registros_origen FROM meta_carga) THEN 'OK' ELSE 'FALLA' END AS resultado;

-- V-10 · Faltantes: el área ausente se conserva como NULL (no 0) y el 0 real se distingue.
SELECT 'V-10 area NULL / area = 0 / area > 0' AS verificacion,
       SUM(area_perdida_bosque_ha IS NULL) AS nulos, SUM(area_perdida_bosque_ha = 0) AS ceros,
       SUM(area_perdida_bosque_ha > 0) AS positivos
FROM hechos_perdida_forestal;

-- V-11 · Categorías desconocidas vs «No aplica» (no se mezclan).
SELECT c.tipo_valor AS tipo_valor_causa, COUNT(*) AS hechos FROM hechos_perdida_forestal f
JOIN dim_causa c ON c.causa_key = f.causa_key GROUP BY c.tipo_valor;
SELECT t.tipo_valor AS tipo_valor_transformacion, COUNT(*) AS hechos FROM hechos_perdida_forestal f
JOIN dim_transformacion t ON t.transformacion_key = f.transformacion_key GROUP BY t.tipo_valor;

-- V-12 · Coherencia de agregación: municipal vs departamental vs país (misma pérdida; diferencias mínimas por redondeo).
SELECT nivel_analisis, SUM(area_perdida_bosque_ha) AS area_ha FROM vw_cubo WHERE pais = 'Colombia' GROUP BY nivel_analisis;

-- V-13 · Calendario diario: 8.766 días (2001-01-01 a 2024-12-31), sin huecos y con 365/366 días por año.
SELECT 'V-13 días del calendario' AS verificacion, COUNT(*) AS dias, 8766 AS esperado,
       CASE WHEN COUNT(*) = 8766 THEN 'OK' ELSE 'FALLA' END AS resultado FROM dim_tiempo
UNION ALL SELECT 'V-13b años con días ≠ 365/366', COUNT(*), 0, CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END
FROM (SELECT anio, COUNT(*) n FROM dim_tiempo GROUP BY anio
      HAVING n != CASE WHEN (anio % 4 = 0 AND anio % 100 != 0) OR anio % 400 = 0 THEN 366 ELSE 365 END);

-- V-14 · Cada hecho anual referencia el 1 de enero de su año (tiempo_key = AAAA0101).
SELECT 'V-14 hechos fuera del 1 de enero' AS verificacion, COUNT(*) AS filas,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FALLA' END AS resultado
FROM hechos_perdida_forestal WHERE tiempo_key % 10000 != 101;

-- V-15 · Bandera de pandemia (OMS, 2020-03-11 a 2023-05-05): 1.151 días.
SELECT 'V-15 días de pandemia' AS verificacion, SUM(es_periodo_pandemia) AS dias, 1151 AS esperado,
       CASE WHEN SUM(es_periodo_pandemia) = 1151 THEN 'OK' ELSE 'FALLA' END AS resultado FROM dim_tiempo;
