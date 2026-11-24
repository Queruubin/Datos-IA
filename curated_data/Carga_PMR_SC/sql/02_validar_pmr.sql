-- =====================================================================
-- 02_VALIDAR_PMR.SQL
-- =====================================================================

-- 1. Total snapshot PMR.
SELECT COUNT(*) AS registros_seguimiento_meta
FROM "seguimiento_meta";
-- Esperado: 332

-- 2. Registros por fecha de corte.
SELECT "fecha_corte", COUNT(*) AS registros
FROM "seguimiento_meta"
GROUP BY "fecha_corte"
ORDER BY "fecha_corte";
-- Esperado:
-- 2026-03-31 | 166
-- 2026-06-30 | 166

-- 3. Registros por vigencia.
SELECT "vigencia", COUNT(*) AS registros
FROM "seguimiento_meta"
GROUP BY "vigencia"
ORDER BY "vigencia";
-- Esperado:
-- 2025 | 166
-- 2026 | 166

-- 4. Último corte: una fila por meta y vigencia.
SELECT COUNT(*) AS registros_ultimo_corte
FROM "vw_seguimiento_meta_ultimo_corte";
-- Esperado: 166

-- 5. Resumen financiero 2026 por corte.
SELECT
  "fecha_corte",
  SUM("presupuesto_programado") AS presupuesto,
  SUM("compromisos") AS compromisos,
  SUM("giros") AS giros
FROM "seguimiento_meta"
WHERE "vigencia" = 2026
GROUP BY "fecha_corte"
ORDER BY "fecha_corte";
-- Esperado:
-- 2026-03-31 | 127690480000 | 50044043250 | 18100878834
-- 2026-06-30 | 127690480000 | 55188169812 | 31737397354

-- 6. El presupuesto PMR 2026 coincide exactamente con POAI 2026.
SELECT COUNT(*) AS diferencias_presupuesto_2026
FROM "vw_calidad_poai_pmr"
WHERE "vigencia" = 2026
  AND "diferencia_presupuesto" IS DISTINCT FROM 0;
-- Esperado: 0

-- 7. Existen 6 diferencias de magnitud POAI vs PMR para 2026.
SELECT
  "codigo_meta_extendida",
  "codigo_indicador",
  "magnitud_poai",
  "magnitud_pmr",
  "diferencia_magnitud"
FROM "vw_calidad_poai_pmr"
WHERE "vigencia" = 2026
  AND "diferencia_magnitud" IS DISTINCT FROM 0
ORDER BY "codigo_meta_extendida";
-- Esperado: 6 filas.

-- 8. Para 2025, después de la corrección de integración,
-- la magnitud POAI coincide con PMR.
SELECT COUNT(*) AS diferencias_magnitud_2025
FROM "vw_calidad_poai_pmr"
WHERE "vigencia" = 2025
  AND "diferencia_magnitud" IS DISTINCT FROM 0;
-- Esperado: 0

-- 9. En 2025 el presupuesto PMR está redondeado a 2 decimales de millón.
-- Por eso puede diferir hasta $5.000 frente al POAI exacto.
SELECT MAX(ABS("diferencia_presupuesto")) AS maxima_diferencia_2025
FROM "vw_calidad_poai_pmr"
WHERE "vigencia" = 2025;
-- Esperado: <= 5000

-- 10. Evolución entre marzo y junio de 2026.
WITH mar AS (
  SELECT * FROM "seguimiento_meta"
  WHERE "vigencia" = 2026 AND "fecha_corte" = DATE '2026-03-31'
),
jun AS (
  SELECT * FROM "seguimiento_meta"
  WHERE "vigencia" = 2026 AND "fecha_corte" = DATE '2026-06-30'
)
SELECT
  COUNT(*) FILTER (WHERE mar."magnitud_contratada" IS DISTINCT FROM jun."magnitud_contratada")
    AS cambios_magnitud_contratada,
  COUNT(*) FILTER (WHERE mar."magnitud_entregada" IS DISTINCT FROM jun."magnitud_entregada")
    AS cambios_magnitud_entregada,
  COUNT(*) FILTER (WHERE mar."compromisos" IS DISTINCT FROM jun."compromisos")
    AS cambios_compromisos,
  COUNT(*) FILTER (WHERE mar."giros" IS DISTINCT FROM jun."giros")
    AS cambios_giros
FROM mar
JOIN jun USING ("id_meta");
-- Esperado: 17 | 14 | 9 | 57

-- 11. Los datos históricos 2025 son iguales en ambos cortes PMR.
WITH mar AS (
  SELECT * FROM "seguimiento_meta"
  WHERE "vigencia" = 2025 AND "fecha_corte" = DATE '2026-03-31'
),
jun AS (
  SELECT * FROM "seguimiento_meta"
  WHERE "vigencia" = 2025 AND "fecha_corte" = DATE '2026-06-30'
)
SELECT COUNT(*) AS metas_2025_con_cambios
FROM mar
JOIN jun USING ("id_meta")
WHERE mar."magnitud_programada" IS DISTINCT FROM jun."magnitud_programada"
   OR mar."magnitud_contratada" IS DISTINCT FROM jun."magnitud_contratada"
   OR mar."magnitud_entregada" IS DISTINCT FROM jun."magnitud_entregada"
   OR mar."presupuesto_programado" IS DISTINCT FROM jun."presupuesto_programado"
   OR mar."compromisos" IS DISTINCT FROM jun."compromisos";
-- Esperado: 0
