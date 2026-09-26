CREATE DATABASE DeforestacionDW;
GO
USE DeforestacionDW;
GO

CREATE SCHEMA staging;
CREATE SCHEMA limpio;
CREATE SCHEMA revision;
GO

CREATE TABLE staging.deforestacion_raw (
    id_registro INT,
    departamento NVARCHAR(200),
    fecha_reporte NVARCHAR(50),
    area_deforestada NVARCHAR(50),
    tipo_bosque NVARCHAR(100),
    fuente NVARCHAR(200),
    fecha_carga DATETIME DEFAULT GETDATE(),
    lote_id INT
);

CREATE TABLE limpio.deforestacion (
    id_registro INT PRIMARY KEY,
    departamento NVARCHAR(200),
    fecha_reporte DATE,
    area_deforestada DECIMAL(18,2),
    tipo_bosque NVARCHAR(100),
    fuente NVARCHAR(200),
    hash_clave AS HASHBYTES('SHA2_256', CONCAT(departamento,'|',fecha_reporte)) PERSISTED
);

CREATE TABLE revision.deforestacion_revision (
    id_registro INT,
    valor_original NVARCHAR(MAX),
    campo_afectado NVARCHAR(100),
    motivo NVARCHAR(300),
    lote_id INT,
    fecha_revision DATETIME DEFAULT GETDATE()
);

CREATE TABLE staging.control_iteraciones (
    lote_id INT IDENTITY PRIMARY KEY,
    iteracion INT,
    fecha_ejecucion DATETIME DEFAULT GETDATE(),
    registros_recibidos INT,
    registros_aceptados INT,
    registros_duplicados INT,
    registros_revision INT
);

CREATE TABLE staging.log_errores (
    id_log INT IDENTITY PRIMARY KEY,
    mensaje NVARCHAR(MAX),
    fecha DATETIME DEFAULT GETDATE()
);
