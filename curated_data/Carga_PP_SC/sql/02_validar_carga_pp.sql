-- =====================================================================
-- VALIDACIÓN CARGA PP - SAN CRISTÓBAL
-- =====================================================================

-- 1. Deben existir 232 propuestas.
SELECT COUNT(*) AS total_propuestas
FROM propuesta_ciudadana;
-- Esperado: 232

-- 2. Seguimientos por corte.
SELECT fecha_corte, COUNT(*) AS registros
FROM seguimiento_propuesta
GROUP BY fecha_corte
ORDER BY fecha_corte;
-- Esperado:
-- 2026-03-31 | 232
-- 2026-10-01 | 232

-- 3. Total de seguimientos.
SELECT COUNT(*) AS total_seguimientos
FROM seguimiento_propuesta;
-- Esperado: 464

-- 4. Todas las propuestas deben apuntar a una meta existente.
SELECT COUNT(*) AS propuestas_sin_meta
FROM propuesta_ciudadana p
LEFT JOIN meta_proyecto m ON m.id_meta = p.id_meta
WHERE m.id_meta IS NULL;
-- Esperado: 0

-- 5. Cobertura: 46 metas con propuestas.
SELECT COUNT(DISTINCT id_meta) AS metas_con_propuestas
FROM propuesta_ciudadana;
-- Esperado: 46

-- 6. Estados del corte más reciente.
SELECT estado_propuesta, COUNT(*) AS propuestas
FROM seguimiento_propuesta
WHERE fecha_corte = DATE '2026-10-01'
GROUP BY estado_propuesta
ORDER BY propuestas DESC, estado_propuesta;
-- Esperado:
-- En formulación 92
-- En ejecución 78
-- Materializada 36
-- Contratada 19
-- No ejecutada 7

-- 7. Vigencia de ejecución del corte más reciente.
SELECT vigencia_ejecucion, COUNT(*) AS propuestas
FROM seguimiento_propuesta
WHERE fecha_corte = DATE '2026-10-01'
GROUP BY vigencia_ejecucion
ORDER BY vigencia_ejecucion;
-- Esperado: 2025 = 142 | 2026 = 90

-- 8. Propuestas que cambiaron de estado entre cortes.
WITH mar AS (
  SELECT id_propuesta, estado_propuesta
  FROM seguimiento_propuesta
  WHERE fecha_corte = DATE '2026-03-31'
),
oct AS (
  SELECT id_propuesta, estado_propuesta
  FROM seguimiento_propuesta
  WHERE fecha_corte = DATE '2026-10-01'
)
SELECT COUNT(*) AS propuestas_con_cambio_estado
FROM mar
JOIN oct USING (id_propuesta)
WHERE mar.estado_propuesta IS DISTINCT FROM oct.estado_propuesta;
-- Esperado: 22

-- 9. Metodologías ya normalizadas.
SELECT metodologia, COUNT(*) AS propuestas
FROM propuesta_ciudadana
GROUP BY metodologia
ORDER BY propuestas DESC, metodologia;

-- 10. Muestra integrada meta + propuesta + último seguimiento.
SELECT
    m.codigo_meta_extendida,
    p.codigo_propuesta,
    p.nombre_propuesta,
    p.metodologia,
    s.vigencia_ejecucion,
    s.estado_propuesta,
    s.poblacion_beneficiada
FROM propuesta_ciudadana p
JOIN meta_proyecto m ON m.id_meta = p.id_meta
JOIN seguimiento_propuesta s ON s.id_propuesta = p.id_propuesta
WHERE s.fecha_corte = DATE '2026-10-01'
ORDER BY m.codigo_meta_extendida, p.codigo_propuesta
LIMIT 25;
