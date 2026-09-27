-- =============================================================================
-- 02_generar_homologaciones.sql
-- Proyecto: Deforestacion y Transformacion del Territorio - Etapa 3 (SSIS)
-- =============================================================================
-- CUANDO CORRERLO: una sola vez, DESPUES de que el paquete SSIS haya
-- ejecutado al menos una vez el Data Flow "Cargar_Staging_Desde_Archivo"
-- (es decir, cuando staging.deforestacion_raw YA TIENE FILAS). Si lo corres
-- con staging vacio no falla, pero las tablas de homologacion quedaran
-- vacias y no serviran de nada: en ese caso, vuelve a correrlo despues de
-- cargar staging.
--
-- Requiere haber corrido antes 01_crear_esquema.sql (crea la estructura de
-- limpio.departamentos_homologados / limpio.municipios_homologados y la
-- funcion limpio.fn_titulo_caso).
--
-- Que hace: genera la homologacion de "departamento" y "municipio"
-- (problemas P5 y P6 del inventario de la Etapa 2), REPLICANDO exactamente
-- la logica que ya se aplico y publico en la Etapa 2
-- (calidad_datos/tratamiento.py, funciones normalizar_departamento y
-- normalizar_municipio): para cualquier valor que este en MAYUSCULA
-- SOSTENIDA, el valor homologado es su version en Title Case (con los
-- conectores "de"/"del"/"y" en minuscula). No se busca ninguna "pareja"
-- bien escrita dentro del propio dataset (eso fue un enfoque anterior,
-- descartado: solo funcionaba quando por casualidad existia otra fila con
-- el mismo lugar bien escrito, y por eso dejaba fuera casi todos los
-- municipios). Es una transformacion de texto directa, igual que en Python.
--
-- NOTA SOBRE ERRORES ENCONTRADOS EN EL CAMINO (se documenta aqui para el
-- informe de manejo de errores):
--   1) Encoding: el Flat File Connection Manager no tenia el Code Page en
--      65001 (UTF-8), con lo que las tildes y "n" se corrompian al leer el
--      CSV (que Python/pandas escribe en UTF-8). Se corrigio en las
--      propiedades de CN_Origen_Deforestacion.
--   2) Text Qualifier: el mismo Connection Manager no tenia configurado el
--      calificador de texto ("). Los dos valores de departamento que
--      contienen una coma dentro del propio valor ("Bogota, D.C." y
--      "ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA") se
--      partian a la mitad en la coma, corriendo una columna hacia la
--      derecha TODO el resto de esa fila (el resto del departamento caia en
--      municipio, el municipio real caia en anio, etc). Se corrigio
--      poniendo Text qualifier = " en CN_Origen_Deforestacion y recargando
--      staging desde cero.
--   3) Collation: la instancia usa SQL_Latin1_General_CP1_CI_AS (insensible
--      a mayusculas), por lo que para detectar "esta en mayuscula
--      sostenida" hay que forzar COLLATE Latin1_General_CS_AS en las
--      comparaciones; y para que UPPER()/LOWER() manejen bien los acentos
--      se fuerza el argumento a COLLATE Latin1_General_CI_AS (una collation
--      Windows moderna) antes de comparar.
--
-- Es seguro volver a correrlo las veces que quieras (vacia las tablas antes
-- de regenerarlas).
-- =============================================================================

USE DeforestacionDW;
GO

-- -----------------------------------------------------------------------------
-- Departamento (P5)
-- -----------------------------------------------------------------------------
TRUNCATE TABLE limpio.departamentos_homologados;
GO

-- Casos especiales que la Etapa 2 documento con una equivalencia fija (no es
-- solo un problema de mayusculas, ver normalizar_departamento en tratamiento.py):
INSERT INTO limpio.departamentos_homologados (valor_original, valor_homologado) VALUES
('Bogotá, D.C.', 'Bogotá D.C.'),
('ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA', 'San Andrés y Providencia');
GO

-- Todo el resto de valores en mayuscula sostenida: Title Case directo.
INSERT INTO limpio.departamentos_homologados (valor_original, valor_homologado)
SELECT DISTINCT
    departamento,
    limpio.fn_titulo_caso(departamento)
FROM staging.deforestacion_raw
WHERE departamento IS NOT NULL
  AND departamento COLLATE Latin1_General_CS_AS
      = UPPER(departamento COLLATE Latin1_General_CI_AS) COLLATE Latin1_General_CS_AS   -- esta en mayuscula sostenida...
  AND departamento COLLATE Latin1_General_CS_AS
      <> LOWER(departamento COLLATE Latin1_General_CI_AS) COLLATE Latin1_General_CS_AS  -- ...y tiene al menos una letra
  AND departamento NOT IN (
        'Bogotá, D.C.',
        'ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA'
      );
GO

-- -----------------------------------------------------------------------------
-- Municipio (P6) - mismo criterio, sin casos especiales (no hay ninguno
-- documentado en normalizar_municipio).
-- -----------------------------------------------------------------------------
TRUNCATE TABLE limpio.municipios_homologados;
GO
INSERT INTO limpio.municipios_homologados (valor_original, valor_homologado)
SELECT DISTINCT
    municipio,
    limpio.fn_titulo_caso(municipio)
FROM staging.deforestacion_raw
WHERE municipio IS NOT NULL
  AND municipio COLLATE Latin1_General_CS_AS
      = UPPER(municipio COLLATE Latin1_General_CI_AS) COLLATE Latin1_General_CS_AS
  AND municipio COLLATE Latin1_General_CS_AS
      <> LOWER(municipio COLLATE Latin1_General_CI_AS) COLLATE Latin1_General_CS_AS;
GO

-- Verificacion: en la Etapa 2 se documentaron ~11 variantes de departamento
-- (9 por mayuscula sostenida + 2 casos especiales) y ~17 variantes de
-- municipio en mayuscula sostenida. Estos conteos deben acercarse a esas
-- cifras (pueden no ser exactamente iguales si al recargar staging con el
-- Text Qualifier corregido aparecen o desaparecen valores).
SELECT COUNT(*) AS departamentos_homologados FROM limpio.departamentos_homologados;
SELECT COUNT(*) AS municipios_homologados    FROM limpio.municipios_homologados;
GO

-- Inspeccion rapida de como quedo cada transformacion (para pegar en el informe):
SELECT * FROM limpio.departamentos_homologados ORDER BY valor_original;
SELECT * FROM limpio.municipios_homologados ORDER BY valor_original;
GO
