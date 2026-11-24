-- =====================================================================
-- 00_CORRECCION_INTEGRACION_POAI_2025.SQL
--
-- Hallazgo del cruce PMR ↔ POAI:
-- La homologación inicial de POAI 2025 utilizó texto de meta para recuperar
-- el código extendido. En dos pares, la descripción POAI 2026 está cruzada
-- respecto al indicador, lo que asignó 4 registros 2025 al código contrario.
--
-- Esta corrección NO modifica la fuente original. Corrige únicamente la
-- capa integrada cargada en PostgreSQL.
-- =====================================================================

BEGIN;

WITH correccion ("codigo_meta_extendida","magnitud_programada","valor_poai") AS (
  VALUES
  ('22851', 1, 2500000000),
('22852', 2, 1500000000),
('24953', 30, 770867000),
('24954', 3300, 1542844000)
)
UPDATE "poai" p
SET
  "magnitud_programada" = c."magnitud_programada",
  "valor_poai" = c."valor_poai"
FROM correccion c
JOIN "meta_proyecto" m
  ON m."codigo_meta_extendida" = c."codigo_meta_extendida"
WHERE p."id_meta" = m."id_meta"
  AND p."vigencia" = 2025;

-- Recalcular el porcentaje de participación 2025 después de la corrección.
WITH total AS (
  SELECT SUM("valor_poai") AS total_poai
  FROM "poai"
  WHERE "vigencia" = 2025
)
UPDATE "poai" p
SET "porcentaje_recursos_poai" =
  CASE
    WHEN total.total_poai = 0 THEN NULL
    ELSE p."valor_poai" / total.total_poai
  END
FROM total
WHERE p."vigencia" = 2025;

COMMIT;
