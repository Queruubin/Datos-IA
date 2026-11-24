-- =====================================================================
-- 02_VALIDAR_ODS.SQL
-- =====================================================================

-- 1. Catálogo ODS
SELECT COUNT(*) AS total_ods
FROM "ods";
-- Esperado: 13

-- 2. Metas ODS
SELECT COUNT(*) AS total_metas_ods
FROM "meta_ods";
-- Esperado: 30

-- 3. Relaciones meta proyecto ↔ meta ODS
SELECT COUNT(*) AS total_relaciones
FROM "meta_ods_relacion";
-- Esperado: 83

-- 4. Las 83 metas del modelo deben quedar relacionadas.
SELECT COUNT(DISTINCT "id_meta") AS metas_con_ods
FROM "meta_ods_relacion";
-- Esperado: 83

-- 5. Ninguna meta sin relación ODS.
SELECT COUNT(*) AS metas_sin_ods
FROM "meta_proyecto" m
LEFT JOIN "meta_ods_relacion" r
  ON r."id_meta" = m."id_meta"
WHERE r."id_meta" IS NULL;
-- Esperado: 0

-- 6. Distribución por ODS.
SELECT
  o."codigo_ods",
  o."nombre_ods",
  COUNT(*) AS metas_proyecto
FROM "vw_meta_ods_detalle" v
JOIN "ods" o
  ON o."codigo_ods" = v."codigo_ods"
GROUP BY o."codigo_ods", o."nombre_ods"
ORDER BY o."codigo_ods"::integer;

-- 7. Distribución por esfera.
SELECT
  "esfera_ods",
  COUNT(*) AS metas_proyecto
FROM "vw_meta_ods_detalle"
GROUP BY "esfera_ods"
ORDER BY metas_proyecto DESC, "esfera_ods";

-- 8. Verificación de unicidad actual:
-- en este corte cada meta de proyecto tiene exactamente una meta ODS.
SELECT
  "codigo_meta_extendida",
  COUNT(*) AS relaciones
FROM "vw_meta_ods_detalle"
GROUP BY "codigo_meta_extendida"
HAVING COUNT(*) <> 1;
-- Esperado: 0 filas

-- 9. Muestra de trazabilidad.
SELECT
  "codigo_meta_extendida",
  "codigo_ods",
  "nombre_ods",
  "codigo_meta_ods",
  "descripcion_meta_ods"
FROM "vw_meta_ods_detalle"
ORDER BY "codigo_meta_extendida"
LIMIT 25;
