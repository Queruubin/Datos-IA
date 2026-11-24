-- =====================================================================
-- 02_VALIDAR_CRP.SQL
-- =====================================================================

-- 1. CRP únicos.
SELECT COUNT(*) AS total_crp FROM "crp";
-- Esperado: 31

-- 2. Líneas de asignación CRP-meta.
SELECT COUNT(*) AS lineas_crp_meta FROM "crp_meta";
-- Esperado: 66

-- 3. Pares CRP-meta consolidados.
SELECT COUNT(*) AS pares_crp_meta
FROM "vw_crp_meta_resumen";
-- Esperado: 58

-- 4. Total de presupuesto PP asociado a CRP.
SELECT SUM("valor_asignado_pp") AS valor_total_pp
FROM "crp_meta";
-- Esperado: 39514916879

-- 5. Relaciones CRP-propuesta.
SELECT COUNT(*) AS relaciones_crp_propuesta
FROM "crp_propuesta";
-- Esperado: 177

-- 6. Propuestas financiadas distintas.
SELECT COUNT(DISTINCT "id_propuesta") AS propuestas_financiadas
FROM "crp_propuesta";
-- Esperado: 133

-- 7. Entidades de referencia.
SELECT COUNT(*) AS entidades FROM "entidad";
-- Esperado: 16

SELECT COUNT(*) AS metas_con_entidad
FROM "meta_proyecto"
WHERE "id_entidad" IS NOT NULL;
-- Esperado: 46

-- 8. Integridad semántica:
-- la meta de cada propuesta financiada debe estar presente entre las metas del mismo CRP.
SELECT COUNT(*) AS relaciones_incoherentes
FROM "crp_propuesta" cp
JOIN "propuesta_ciudadana" p
  ON p."id_propuesta" = cp."id_propuesta"
WHERE NOT EXISTS (
  SELECT 1
  FROM "crp_meta" cm
  WHERE cm."id_crp" = cp."id_crp"
    AND cm."id_meta" = p."id_meta"
);
-- Esperado: 0

-- 9. Combinaciones CRP-meta con más de una línea de asignación.
SELECT
  "numero_crp",
  "codigo_meta_extendida",
  "numero_lineas_asignacion",
  "valor_total_crp_meta"
FROM "vw_crp_meta_resumen"
WHERE "numero_lineas_asignacion" > 1
ORDER BY "numero_lineas_asignacion" DESC, "numero_crp";
-- Esperado: 4 combinaciones.

-- 10. Propuestas financiadas por más de un CRP.
SELECT
  p."codigo_propuesta",
  COUNT(*) AS numero_crp
FROM "crp_propuesta" cp
JOIN "propuesta_ciudadana" p
  ON p."id_propuesta" = cp."id_propuesta"
GROUP BY p."codigo_propuesta"
HAVING COUNT(*) > 1
ORDER BY numero_crp DESC, p."codigo_propuesta";
-- Esperado: 35 propuestas; máximo 3 CRP para una propuesta.

-- 11. Ejemplo completo de trazabilidad.
SELECT
  c."numero_crp",
  c."fecha_registro",
  c."numero_compromiso",
  m."codigo_meta_extendida",
  p."codigo_propuesta",
  p."nombre_propuesta"
FROM "crp_propuesta" cp
JOIN "crp" c ON c."id_crp" = cp."id_crp"
JOIN "propuesta_ciudadana" p ON p."id_propuesta" = cp."id_propuesta"
JOIN "meta_proyecto" m ON m."id_meta" = p."id_meta"
ORDER BY c."numero_crp", m."codigo_meta_extendida", p."codigo_propuesta"
LIMIT 30;
