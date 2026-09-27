-- =============================================================================
-- 03_verificaciones.sql
-- Proyecto: Deforestacion y Transformacion del Territorio - Etapa 3 (SSIS)
-- =============================================================================
-- CUANDO CORRERLO: despues de CADA iteracion del paquete SSIS (1, 2 y 3).
-- No modifica nada, solo consulta. Estas son las mismas consultas que se
-- usan para capturar la evidencia de cada iteracion en el informe tecnico.
-- =============================================================================

USE DeforestacionDW;
GO

-- Resultado de la carga: filas aceptadas, con sus banderas de tratamiento.
SELECT * FROM limpio.deforestacion;
GO

-- Filas enviadas a revision, agrupadas por motivo (para justificar ajustes
-- de una iteracion a la siguiente).
SELECT motivo, COUNT(*) AS cantidad
FROM revision.deforestacion_revision
GROUP BY motivo
ORDER BY cantidad DESC;
GO

-- Conteos consolidados de todas las iteraciones corridas hasta el momento
-- (esta es la tabla comparativa que pide el informe).
SELECT * FROM staging.control_iteraciones
ORDER BY lote_id;
GO

-- Verificacion final de unicidad: debe devolver 0 filas, incluso despues
-- de volver a ejecutar el mismo lote (evidencia de que el Lookup de
-- idempotencia funciona).
SELECT hash_clave, COUNT(*) AS repeticiones
FROM limpio.deforestacion
GROUP BY hash_clave
HAVING COUNT(*) > 1;
GO
