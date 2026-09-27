-- =============================================================================
-- 01_crear_esquema.sql
-- Proyecto: Deforestacion y Transformacion del Territorio - Etapa 3 (SSIS)
-- =============================================================================
-- CUANDO CORRERLO: una sola vez, ANTES de abrir o ejecutar el paquete SSIS
-- (Deforestacion_ETL / Etapa3_Calidad.dtsx) por primera vez, y cada vez que
-- quieras reconstruir el entorno desde cero.
--
-- Que hace: crea la base de datos, los 3 esquemas (staging, limpio, revision)
-- y todas las tablas, incluyendo las tablas de referencia fijas (traduccion
-- de driver_dominante y lista de agregados regionales de "pais"). Es seguro
-- volver a correrlo las veces que quieras: si la base ya existia, la borra
-- primero y la crea de nuevo.
--
-- Que NO hace: no genera la homologacion de departamento/municipio (eso
-- depende de que staging ya tenga datos cargados), ver 02_generar_homologaciones.sql.
--
-- No contiene contrasenas ni credenciales.
-- =============================================================================

-- Permite volver a correr el script sin errores si la base ya existia.
IF DB_ID('DeforestacionDW') IS NOT NULL
BEGIN
    ALTER DATABASE DeforestacionDW SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE DeforestacionDW;
END
GO

CREATE DATABASE DeforestacionDW;
GO

USE DeforestacionDW;
GO

CREATE SCHEMA staging;
GO
CREATE SCHEMA limpio;
GO
CREATE SCHEMA revision;
GO

-- -----------------------------------------------------------------------------
-- staging.deforestacion_raw
-- Copia textual, sin convertir, de las 20 columnas del dataset consolidado.
-- Todo es NVARCHAR (incluso anio y los campos numericos) para que ninguna fila
-- se pierda por un error de formato antes de que SSIS pueda revisarla.
-- -----------------------------------------------------------------------------
CREATE TABLE staging.deforestacion_raw (
    id_registro                     INT,
    nivel_analisis                  NVARCHAR(20),
    fuente_origen                   NVARCHAR(50),
    pais                            NVARCHAR(150),
    departamento                    NVARCHAR(200),
    municipio                       NVARCHAR(200),
    anio                            NVARCHAR(10),
    latitud                         NVARCHAR(50),
    longitud                        NVARCHAR(50),
    area_perdida_bosque_ha          NVARCHAR(50),
    emisiones_co2_mg                NVARCHAR(50),
    driver_dominante                NVARCHAR(100),
    area_transformada_ha            NVARCHAR(50),
    clase_transformacion_dominante  NVARCHAR(100),
    num_focos_calor                 NVARCHAR(50),
    frp_promedio                    NVARCHAR(50),
    confianza_promedio_focos        NVARCHAR(50),
    porcentaje_area_forestal        NVARCHAR(50),
    area_forestal_ha                NVARCHAR(50),
    deforestacion_anual_ha_owid     NVARCHAR(50),
    fecha_carga                     DATETIME DEFAULT GETDATE(),
    lote_id                         INT
);
GO

-- -----------------------------------------------------------------------------
-- Tablas de referencia fijas (no dependen de los datos cargados)
-- -----------------------------------------------------------------------------

-- P2: Global Forest Watch entrega driver_dominante en ingles; el diccionario
-- de datos de la Etapa 1/2 lo documenta en espanol. Se homologa con esta tabla.
CREATE TABLE limpio.driver_homologado (
    valor_original   NVARCHAR(100) PRIMARY KEY,
    valor_homologado NVARCHAR(100)
);
GO
INSERT INTO limpio.driver_homologado (valor_original, valor_homologado) VALUES
('Permanent agriculture',        'Agricultura permanente'),
('Shifting cultivation',         'Agricultura migratoria'),
('Logging',                      'Silvicultura'),
('Other natural disturbances',   'Otras alteraciones naturales'),
('Settlements & Infrastructure', 'Urbanizacion e infraestructura'),
('Hard commodities',             'Mineria y otras materias primas'),
('Wildfire',                     'Incendios forestales');
GO

-- P3: agregados regionales y de grupo de ingreso que FAO/OWID mezclan dentro
-- de la columna "pais" (Africa, World, Low-income countries, etc.). No se
-- eliminan filas: sirven para marcar la bandera es_agregado_regional.
CREATE TABLE limpio.paises_agregados (
    nombre_pais NVARCHAR(150) PRIMARY KEY
);
GO
INSERT INTO limpio.paises_agregados (nombre_pais) VALUES
('Africa'), ('Americas'), ('Asia'), ('Europe'),
('High-income countries'),
('Land Locked Developing Countries (LLDCs)'),
('Least Developed Countries (LDCs)'),
('Low-income countries'),
('Lower-middle-income countries'),
('North America'), ('Oceania'),
('Small Island Developing States (SIDS)'),
('South America'), ('Sub-Saharan Africa'),
('Upper-middle-income countries'), ('World');
GO

-- -----------------------------------------------------------------------------
-- Tablas de homologacion de lugar (P5, P6). La ESTRUCTURA se crea aqui;
-- el CONTENIDO se genera en 02_generar_homologaciones.sql, una vez staging
-- ya tenga datos cargados.
-- -----------------------------------------------------------------------------
CREATE TABLE limpio.departamentos_homologados (
    valor_original   NVARCHAR(200) PRIMARY KEY,
    valor_homologado NVARCHAR(200)
);
GO

CREATE TABLE limpio.municipios_homologados (
    valor_original   NVARCHAR(200) PRIMARY KEY,
    valor_homologado NVARCHAR(200)
);
GO

-- -----------------------------------------------------------------------------
-- Funcion fn_titulo_caso: replica el tratamiento.py de la Etapa 2
-- (normalizar_departamento / normalizar_municipio), que para cualquier valor
-- en MAYUSCULA SOSTENIDA aplica el equivalente de Python .title() (mayuscula
-- solo en la primera letra de cada palabra, resto en minuscula) y luego
-- vuelve a minuscula los conectores " de ", " del " y " y ". No busca ninguna
-- "pareja" en los datos: es una transformacion de texto pura, igual que en
-- Python. Se usa en 02_generar_homologaciones.sql para generar el valor
-- homologado directamente a partir del valor original.
-- -----------------------------------------------------------------------------
CREATE FUNCTION limpio.fn_titulo_caso (@texto NVARCHAR(200))
RETURNS NVARCHAR(200)
AS
BEGIN
    DECLARE @resultado NVARCHAR(200) = '';
    DECLARE @i INT = 1;
    DECLARE @len INT = LEN(@texto);
    DECLARE @c NCHAR(1);
    DECLARE @anterior_es_letra BIT = 0;

    WHILE @i <= @len
    BEGIN
        SET @c = SUBSTRING(@texto, @i, 1);

        IF @anterior_es_letra = 0
            SET @resultado = @resultado + (UPPER(@c COLLATE Latin1_General_CI_AS) COLLATE Latin1_General_CS_AS);
        ELSE
            SET @resultado = @resultado + (LOWER(@c COLLATE Latin1_General_CI_AS) COLLATE Latin1_General_CS_AS);

        -- "Es letra" = un caracter que cambia entre mayuscula y minuscula
        -- (espacios, guiones, numeros y puntuacion no lo son, y por lo tanto
        -- "cortan" la palabra, igual que en Python .title()).
        IF UPPER(@c COLLATE Latin1_General_CI_AS) <> LOWER(@c COLLATE Latin1_General_CI_AS)
            SET @anterior_es_letra = 1;
        ELSE
            SET @anterior_es_letra = 0;

        SET @i = @i + 1;
    END

    SET @resultado = REPLACE(@resultado, ' De ', ' de ');
    SET @resultado = REPLACE(@resultado, ' Del ', ' del ');
    SET @resultado = REPLACE(@resultado, ' Y ', ' y ');

    RETURN @resultado;
END
GO

-- -----------------------------------------------------------------------------
-- limpio.deforestacion
-- Tabla final: tipos reales ya corregidos, mas las banderas de tratamiento
-- definidas en el plan de la Etapa 2 (PLAN_TRATAMIENTO2). Conserva el
-- id_registro original (no se regenera), lo que facilita la trazabilidad y
-- permite usarlo como clave de idempotencia en el Lookup de SSIS.
-- -----------------------------------------------------------------------------
CREATE TABLE limpio.deforestacion (
    id_registro                     INT PRIMARY KEY,
    nivel_analisis                  NVARCHAR(20),
    fuente_origen                   NVARCHAR(50),
    pais                            NVARCHAR(150),
    es_agregado_regional            BIT NOT NULL DEFAULT 0,
    departamento                    NVARCHAR(200),
    municipio                       NVARCHAR(200),
    anio                            SMALLINT,
    latitud                         FLOAT NULL,
    longitud                        FLOAT NULL,
    area_perdida_bosque_ha          DECIMAL(18,2) NULL,
    area_perdida_bosque_ha_atipico  BIT NOT NULL DEFAULT 0,
    emisiones_co2_mg                DECIMAL(18,2) NULL,
    emisiones_co2_mg_atipico        BIT NOT NULL DEFAULT 0,
    driver_dominante                NVARCHAR(100) NULL,
    area_transformada_ha            DECIMAL(18,2) NULL,
    area_transformada_ha_atipico    BIT NOT NULL DEFAULT 0,
    clase_transformacion_dominante  NVARCHAR(100) NULL,
    num_focos_calor                 DECIMAL(10,0) NULL,
    num_focos_calor_atipico         BIT NOT NULL DEFAULT 0,
    frp_promedio                    DECIMAL(10,2) NULL,
    confianza_promedio_focos        DECIMAL(5,2) NULL,
    porcentaje_area_forestal        DECIMAL(5,2) NULL,
    area_forestal_ha                DECIMAL(18,2) NULL,
    deforestacion_anual_ha_owid     DECIMAL(18,2) NULL,
    hash_clave AS HASHBYTES('SHA2_256', CONCAT(
        nivel_analisis,'|',fuente_origen,'|',pais,'|',departamento,'|',municipio,'|',anio,'|',
        latitud,'|',longitud,'|',area_perdida_bosque_ha,'|',emisiones_co2_mg,'|',driver_dominante,'|',
        area_transformada_ha,'|',clase_transformacion_dominante,'|',num_focos_calor,'|',frp_promedio,'|',
        confianza_promedio_focos,'|',porcentaje_area_forestal,'|',area_forestal_ha,'|',deforestacion_anual_ha_owid
    )) PERSISTED
);
GO

-- -----------------------------------------------------------------------------
-- Zona de revision, control de iteraciones y log de errores
-- -----------------------------------------------------------------------------
CREATE TABLE revision.deforestacion_revision (
    id_registro     INT,
    valor_original  NVARCHAR(MAX),
    campo_afectado  NVARCHAR(100),
    motivo          NVARCHAR(300),
    lote_id         INT,
    fecha_revision  DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE staging.control_iteraciones (
    lote_id                  INT IDENTITY PRIMARY KEY,
    iteracion                INT,
    fecha_ejecucion          DATETIME DEFAULT GETDATE(),
    registros_recibidos      INT,
    registros_aceptados      INT,
    registros_duplicados     INT,
    registros_revision       INT,
    registros_ya_existentes  INT
);
GO

CREATE TABLE staging.log_errores (
    id_log   INT IDENTITY PRIMARY KEY,
    mensaje  NVARCHAR(MAX),
    fecha    DATETIME DEFAULT GETDATE()
);
GO

-- Verificacion rapida de que todo quedo creado (debe devolver 0 filas, sin error):
SELECT * FROM staging.deforestacion_raw;
GO
