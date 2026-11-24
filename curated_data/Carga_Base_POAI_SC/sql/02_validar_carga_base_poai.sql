-- =====================================================================
-- 02_VALIDAR_CARGA_BASE_POAI.SQL
-- Resultados esperados indicados en comentarios.
-- =====================================================================

-- Estructura maestra
SELECT COUNT(*) AS localidades FROM "localidad";              -- 1
SELECT COUNT(*) AS sectores FROM "sector";                    -- 12
SELECT COUNT(*) AS objetivos FROM "objetivo_estrategico";     -- 5
SELECT COUNT(*) AS programas FROM "programa";                  -- 23
SELECT COUNT(*) AS proyectos FROM "proyecto";                  -- 31
SELECT COUNT(*) AS metas FROM "meta_proyecto";                 -- 83

-- POAI: 83 por cada vigencia
SELECT "vigencia", COUNT(*) AS registros, SUM("valor_poai") AS valor_total
FROM "poai"
GROUP BY "vigencia"
ORDER BY "vigencia";
-- Esperado:
-- 2025 | 83 | 130871828000
-- 2026 | 83 | 127690480000

-- Integridad: ninguna meta sin proyecto o sector.
SELECT COUNT(*) AS metas_sin_proyecto_o_sector
FROM "meta_proyecto" m
LEFT JOIN "proyecto" p ON p."id_proyecto" = m."id_proyecto"
LEFT JOIN "sector" s ON s."id_sector" = m."id_sector"
WHERE p."id_proyecto" IS NULL OR s."id_sector" IS NULL;
-- Esperado: 0

-- Evidencia del ajuste multisector.
SELECT
    p."codigo_proyecto",
    p."nombre_proyecto",
    COUNT(DISTINCT s."id_sector") AS sectores_distintos,
    STRING_AGG(DISTINCT s."nombre_sector", ' | ' ORDER BY s."nombre_sector") AS sectores
FROM "proyecto" p
JOIN "meta_proyecto" m ON m."id_proyecto" = p."id_proyecto"
JOIN "sector" s ON s."id_sector" = m."id_sector"
WHERE p."codigo_proyecto" IN ('2502','2802')
GROUP BY p."codigo_proyecto", p."nombre_proyecto"
ORDER BY p."codigo_proyecto";
-- Esperado: 2 sectores para 2502 y 2 sectores para 2802.

-- Unicidad de metas.
SELECT "codigo_meta_extendida", COUNT(*)
FROM "meta_proyecto"
GROUP BY "codigo_meta_extendida"
HAVING COUNT(*) > 1;
-- Esperado: 0 filas

-- Unicidad POAI por meta/vigencia.
SELECT "id_meta","vigencia",COUNT(*)
FROM "poai"
GROUP BY "id_meta","vigencia"
HAVING COUNT(*) > 1;
-- Esperado: 0 filas

-- Muestra integrada
SELECT
  m."codigo_meta_extendida",
  p."codigo_proyecto",
  s."nombre_sector",
  po."vigencia",
  po."magnitud_programada",
  po."valor_poai"
FROM "meta_proyecto" m
JOIN "proyecto" p ON p."id_proyecto" = m."id_proyecto"
JOIN "sector" s ON s."id_sector" = m."id_sector"
JOIN "poai" po ON po."id_meta" = m."id_meta"
ORDER BY m."codigo_meta_extendida", po."vigencia"
LIMIT 20;
