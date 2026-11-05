-- =============================================================================
-- 05_modelo_estrella_ddl.sql  ·  Etapa 5: análisis multidimensional
-- Modelo estrella del proyecto "Deforestación y Transformación del Territorio".
-- Motor: SQLite 3 (se consulta desde Flask con el módulo estándar sqlite3).
-- Se ejecuta automáticamente desde multidimensional/cargar_modelo.py.
--
-- Tabla de hechos : hechos_perdida_forestal
-- Granularidad    : UNA FILA POR TERRITORIO Y AÑO (territorio_key + tiempo_key; un año por territorio).
-- Dimensiones     : territorio, tiempo, causa, transformacion, fuente.
-- =============================================================================

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS vw_cubo;
DROP TABLE IF EXISTS hechos_perdida_forestal;
DROP TABLE IF EXISTS dim_territorio;
DROP TABLE IF EXISTS dim_tiempo;
DROP TABLE IF EXISTS dim_causa;
DROP TABLE IF EXISTS dim_transformacion;
DROP TABLE IF EXISTS dim_fuente;
DROP TABLE IF EXISTS meta_carga;

-- ---------------------------------------------------------------------------
-- Dimensión territorio.  Jerarquía: región natural > departamento > municipio
-- (el atributo nivel_analisis/escala indica a qué escala pertenece el
-- miembro: Municipal, Departamental o País).
-- ---------------------------------------------------------------------------
CREATE TABLE dim_territorio (
    territorio_key       INTEGER PRIMARY KEY,
    nivel_analisis       TEXT NOT NULL CHECK (nivel_analisis IN ('Regional','Nacional','Global')),
    escala               TEXT NOT NULL CHECK (escala IN ('Municipal','Departamental','País')),
    pais                 TEXT NOT NULL,
    region_natural       TEXT NOT NULL,
    departamento         TEXT NOT NULL,
    municipio            TEXT NOT NULL,
    es_agregado_regional INTEGER NOT NULL CHECK (es_agregado_regional IN (0,1)),
    latitud              REAL,
    longitud             REAL,
    UNIQUE (nivel_analisis, pais, departamento, municipio)
);

-- ---------------------------------------------------------------------------
-- Dimensión tiempo: calendario DIARIO (2001-01-01 a 2024-12-31, 8.766 días).
-- Jerarquías: calendario  año > semestre > trimestre > mes > día
--             análisis    periodo (12 años) > trienio > año
-- La fuente de datos es ANUAL: cada hecho se asocia al primer día de su año
-- (id_dim_tiempo = AAAA0101). Por eso los datos solo pueden analizarse hasta el
-- nivel AÑO; los atributos sub-anuales (semestre, trimestre, mes, semana, día,
-- hora) describen el calendario y quedan disponibles para fuentes más finas,
-- pero NO se usan para agrupar los hechos actuales (todos caerían en enero).
-- La hora es NULL («No aplica»): el grano de esta dimensión es el día.
-- ---------------------------------------------------------------------------
CREATE TABLE dim_tiempo (
    id_dim_tiempo           INTEGER PRIMARY KEY,           -- AAAAMMDD, ej. 20261104
    fecha                   TEXT    NOT NULL UNIQUE,       -- AAAA-MM-DD
    anio                    INTEGER NOT NULL,
    anio_fiscal             TEXT    NOT NULL,              -- FY2026 (año fiscal = año calendario)
    semestre                TEXT    NOT NULL,              -- Semestre 1..2
    cuatrimestre            TEXT    NOT NULL,              -- Cuatrimestre 1..3
    trimestre               TEXT    NOT NULL,              -- Trimestre 1..4
    bimestre                TEXT    NOT NULL,              -- Bimestre 1..6
    mes                     INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    mes_nombre              TEXT    NOT NULL,
    mes_nombre_corto        TEXT    NOT NULL,
    semana                  INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 53),   -- semana ISO 8601
    semana_nombre           TEXT    NOT NULL,              -- Semana 45
    dia                     INTEGER NOT NULL CHECK (dia BETWEEN 1 AND 31),
    dia_del_anio            INTEGER NOT NULL CHECK (dia_del_anio BETWEEN 1 AND 366),
    dia_semana_numero       INTEGER NOT NULL CHECK (dia_semana_numero BETWEEN 1 AND 7),  -- 1 = lunes
    dia_semana_nombre       TEXT    NOT NULL,
    dia_semana_corto        TEXT    NOT NULL,
    hora                    INTEGER CHECK (hora IS NULL OR hora BETWEEN 0 AND 23),
    es_periodo_pandemia     INTEGER NOT NULL CHECK (es_periodo_pandemia IN (0,1)),  -- 2020-03-11 a 2023-05-05 (OMS)
    es_anio_con_pandemia    INTEGER NOT NULL CHECK (es_anio_con_pandemia IN (0,1)), -- el año tiene algún día de pandemia
    trienio                 TEXT    NOT NULL,
    trienio_orden           INTEGER NOT NULL,
    periodo                 TEXT    NOT NULL,
    periodo_orden           INTEGER NOT NULL
);
CREATE INDEX ix_tiempo_anio ON dim_tiempo (anio);

-- ---------------------------------------------------------------------------
-- Dimensión causa.  Jerarquía: grupo de causa > causa (driver dominante).
-- ---------------------------------------------------------------------------
CREATE TABLE dim_causa (
    causa_key        INTEGER PRIMARY KEY,
    driver_dominante TEXT NOT NULL UNIQUE,
    grupo_causa      TEXT NOT NULL,
    tipo_valor       TEXT NOT NULL CHECK (tipo_valor IN ('Informada','Sin informar','No aplica'))
);

-- ---------------------------------------------------------------------------
-- Dimensión transformación del suelo (clase de transformación dominante).
-- ---------------------------------------------------------------------------
CREATE TABLE dim_transformacion (
    transformacion_key   INTEGER PRIMARY KEY,
    clase_transformacion TEXT NOT NULL UNIQUE,
    tipo_valor           TEXT NOT NULL CHECK (tipo_valor IN ('Informada','Sin informar','No aplica'))
);

-- ---------------------------------------------------------------------------
-- Dimensión fuente (cobertura de datos).  Jerarquía: número de fuentes >
-- combinación de fuentes.
-- ---------------------------------------------------------------------------
CREATE TABLE dim_fuente (
    fuente_key        INTEGER PRIMARY KEY,
    fuente_origen     TEXT NOT NULL UNIQUE,
    n_fuentes         INTEGER NOT NULL,
    incluye_gfw       INTEGER NOT NULL CHECK (incluye_gfw IN (0,1)),
    incluye_mapbiomas INTEGER NOT NULL CHECK (incluye_mapbiomas IN (0,1)),
    incluye_firms     INTEGER NOT NULL CHECK (incluye_firms IN (0,1)),
    incluye_fao       INTEGER NOT NULL CHECK (incluye_fao IN (0,1)),
    incluye_owid      INTEGER NOT NULL CHECK (incluye_owid IN (0,1))
);

-- ---------------------------------------------------------------------------
-- Tabla de hechos.  PK compuesta = granularidad (territorio, año).
-- Las medidas ausentes quedan en NULL (no se rellenan con 0).
-- ---------------------------------------------------------------------------
CREATE TABLE hechos_perdida_forestal (
    territorio_key           INTEGER NOT NULL REFERENCES dim_territorio (territorio_key),
    tiempo_key               INTEGER NOT NULL REFERENCES dim_tiempo (id_dim_tiempo),  -- AAAA0101
    causa_key                INTEGER NOT NULL REFERENCES dim_causa (causa_key),
    transformacion_key       INTEGER NOT NULL REFERENCES dim_transformacion (transformacion_key),
    fuente_key               INTEGER NOT NULL REFERENCES dim_fuente (fuente_key),
    n_registros_origen       INTEGER NOT NULL CHECK (n_registros_origen >= 1),
    id_registro_min          INTEGER NOT NULL,
    area_perdida_bosque_ha   REAL CHECK (area_perdida_bosque_ha   IS NULL OR area_perdida_bosque_ha   >= 0),
    emisiones_co2_mg         REAL CHECK (emisiones_co2_mg         IS NULL OR emisiones_co2_mg         >= 0),
    area_transformada_ha     REAL CHECK (area_transformada_ha     IS NULL OR area_transformada_ha     >= 0),
    num_focos_calor          REAL CHECK (num_focos_calor          IS NULL OR num_focos_calor          >= 0),
    frp_promedio             REAL,
    confianza_promedio_focos REAL,
    porcentaje_area_forestal REAL,
    area_forestal_ha         REAL,
    deforestacion_anual_ha_owid REAL,
    area_perdida_atipica     INTEGER NOT NULL DEFAULT 0 CHECK (area_perdida_atipica IN (0,1)),
    emisiones_atipicas       INTEGER NOT NULL DEFAULT 0 CHECK (emisiones_atipicas IN (0,1)),
    PRIMARY KEY (territorio_key, tiempo_key)
);

CREATE INDEX ix_hechos_tiempo        ON hechos_perdida_forestal (tiempo_key);
CREATE INDEX ix_hechos_causa         ON hechos_perdida_forestal (causa_key);
CREATE INDEX ix_hechos_transformacion ON hechos_perdida_forestal (transformacion_key);
CREATE INDEX ix_hechos_fuente        ON hechos_perdida_forestal (fuente_key);
CREATE INDEX ix_territorio_region    ON dim_territorio (nivel_analisis, region_natural, departamento);

-- Trazabilidad de la carga.
CREATE TABLE meta_carga (
    csv_origen       TEXT NOT NULL,
    sha256_csv       TEXT NOT NULL,
    registros_origen INTEGER NOT NULL,
    filas_hechos     INTEGER NOT NULL
);

-- ---------------------------------------------------------------------------
-- Vista desnormalizada que usan las consultas de análisis: une los hechos con
-- sus cinco dimensiones sin multiplicar filas (todas las relaciones son
-- muchos-a-uno desde la tabla de hechos).
-- ---------------------------------------------------------------------------
CREATE VIEW vw_cubo AS
SELECT f.territorio_key, f.tiempo_key, ti.anio, ti.anio_fiscal, ti.es_anio_con_pandemia, f.causa_key, f.transformacion_key, f.fuente_key,
       t.nivel_analisis, t.escala, t.pais, t.region_natural, t.departamento, t.municipio,
       ti.trienio, ti.trienio_orden, ti.periodo, ti.periodo_orden,
       c.driver_dominante, c.grupo_causa,
       tr.clase_transformacion,
       fu.fuente_origen, fu.n_fuentes, fu.incluye_firms,
       f.n_registros_origen, f.area_perdida_bosque_ha, f.emisiones_co2_mg,
       f.area_transformada_ha, f.num_focos_calor, f.frp_promedio,
       f.porcentaje_area_forestal, f.area_forestal_ha, f.deforestacion_anual_ha_owid
FROM hechos_perdida_forestal f
JOIN dim_territorio     t  ON t.territorio_key     = f.territorio_key
JOIN dim_tiempo         ti ON ti.id_dim_tiempo     = f.tiempo_key
JOIN dim_causa          c  ON c.causa_key          = f.causa_key
JOIN dim_transformacion tr ON tr.transformacion_key = f.transformacion_key
JOIN dim_fuente         fu ON fu.fuente_key        = f.fuente_key;
