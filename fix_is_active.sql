-- Script SQL para corregir el error de is_active = NULL
-- Ejecutar en MySQL:
-- mysql -u api -p Esquelahorra < fix_is_active.sql

-- 1. Ver cantidad de registros con is_active = NULL
SELECT COUNT(*) as registros_null FROM locals WHERE is_active IS NULL;

-- 2. Actualizar todos los registros con is_active = NULL a is_active = 1 (TRUE)
UPDATE locals SET is_active = 1 WHERE is_active IS NULL;

-- 3. Asegurar que la columna no permite NULL en el futuro
ALTER TABLE locals MODIFY COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- 4. Verificar que todo está correcto
SELECT COUNT(*) as registros_total FROM locals;
SELECT COUNT(*) as registros_activos FROM locals WHERE is_active = 1;
SELECT COUNT(*) as registros_inactivos FROM locals WHERE is_active = 0;
SELECT COUNT(*) as registros_null FROM locals WHERE is_active IS NULL;

-- Debería mostrar:
-- registros_null = 0 (no debe haber ningún NULL)
