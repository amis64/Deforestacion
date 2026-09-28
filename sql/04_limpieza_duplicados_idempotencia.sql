-- =============================================================================
-- 04_limpieza_duplicados_idempotencia.sql
-- Proyecto: Deforestacion y Transformacion del Territorio - Etapa 3 (SSIS)
-- =============================================================================
-- CUANDO CORRERLO: solo si una corrida del paquete SSIS dejo copias
-- duplicadas en limpio.deforestacion (mismo hash_clave repetido). Es seguro
-- volver a correrlo las veces que haga falta: siempre deja exactamente 1 fila
-- por hash_clave (la de menor id_registro), sin importar cuantas copias se
-- hayan acumulado.
--
-- CONTEXTO / HALLAZGO (para el informe, seccion de manejo de errores):
-- Al probar la Iteracion 2 (repetir la ejecucion del mismo lote, punto 6 de
-- la actividad), el proceso NO fue idempotente: se insertaron filas nuevas
-- con contenido identico a filas ya cargadas (mismo hash_clave, distinto
-- id_registro). Causa raiz: el Lookup de idempotencia comparaba por
-- id_registro, pero el componente Sort (Eliminar_Duplicados) no garantiza
-- elegir siempre la misma fila fisica dentro de un grupo de duplicados
-- exactos entre una ejecucion y otra (no es un "stable sort" para los
-- empates de su propia clave de orden), incluso con la fuente ordenada con
-- ORDER BY id_registro. Es decir, el "ganador" de cada grupo de duplicados
-- podia cambiar de corrida a corrida.
--
-- FIX aplicado: se reconfiguro el Lookup Verificar_YaCargado para comparar
-- por las columnas de negocio (las mismas 19 que arman hash_clave) en vez de
-- por id_registro. Asi, sin importar cual copia fisica "gane" el Sort en cada
-- corrida, el Lookup reconoce el contenido como ya cargado.
--
-- Este script deja la tabla en el estado que el Lookup corregido espera
-- mantener de forma estable de aqui en adelante (1 copia por hash_clave, la
-- de menor id_registro).
-- =============================================================================

USE DeforestacionDW;
GO

-- Diagnostico ANTES de limpiar (evidencia para el informe: cuantas filas
-- estan duplicadas en este momento).
SELECT COUNT(*) AS total_filas_antes
FROM limpio.deforestacion;
GO

SELECT COUNT(*) AS grupos_hash_duplicados,
       SUM(repeticiones) AS filas_involucradas
FROM (
    SELECT hash_clave, COUNT(*) AS repeticiones
    FROM limpio.deforestacion
    GROUP BY hash_clave
    HAVING COUNT(*) > 1
) t;
GO

-- Limpieza: conserva 1 fila por hash_clave (la de menor id_registro).
;WITH duplicados AS (
    SELECT id_registro,
           ROW_NUMBER() OVER (PARTITION BY hash_clave ORDER BY id_registro) AS rn
    FROM limpio.deforestacion
)
DELETE FROM limpio.deforestacion
WHERE id_registro IN (SELECT id_registro FROM duplicados WHERE rn > 1);
GO

-- Verificacion DESPUES de limpiar: debe dar 0 filas.
SELECT hash_clave, COUNT(*) AS repeticiones
FROM limpio.deforestacion
GROUP BY hash_clave
HAVING COUNT(*) > 1;
GO

SELECT COUNT(*) AS total_filas_despues
FROM limpio.deforestacion;
GO
