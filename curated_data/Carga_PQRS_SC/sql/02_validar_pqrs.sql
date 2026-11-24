-- =====================================================================
-- 02_VALIDAR_PQRS.SQL
-- =====================================================================

-- 1. Registros
SELECT COUNT(*) AS total_pqrs FROM "pqrs";
-- Esperado: 4026

SELECT COUNT(DISTINCT "radicado") AS radicados_unicos FROM "pqrs";
-- Esperado: 4026

-- 2. Catálogos
SELECT COUNT(*) AS tipos_peticion FROM "tipo_peticion";
-- Esperado: 7

SELECT COUNT(*) AS medios_recepcion FROM "medio_recepcion";
-- Esperado: 7

SELECT COUNT(*) AS subtemas FROM "subtema_pqrs";
-- Esperado: 82

-- 3. Distribución por vigencia
SELECT "vigencia", COUNT(*) AS pqrs
FROM "pqrs"
GROUP BY "vigencia"
ORDER BY "vigencia";
-- Esperado:
-- 2022 | 1055
-- 2023 | 868
-- 2024 | 684
-- 2025 | 626
-- 2026 | 793

-- 4. Estado ORFEO
SELECT "estado_orfeo", COUNT(*) AS pqrs
FROM "pqrs"
GROUP BY "estado_orfeo"
ORDER BY pqrs DESC;
-- Esperado:
-- TRAMITE CERRADO      | 3838
-- RADICADO EN GESTION  | 188

-- 5. Nulos normalizados desde NA
SELECT
  COUNT(*) FILTER (WHERE "id_tipo_peticion" IS NULL) AS tipo_peticion_null,
  COUNT(*) FILTER (WHERE "tiempo_tramite" IS NULL) AS tiempo_tramite_null,
  COUNT(*) FILTER (WHERE "observacion_general" IS NULL) AS observacion_general_null,
  COUNT(*) FILTER (WHERE "observacion_sac" IS NULL) AS observacion_sac_null,
  COUNT(*) FILTER (WHERE "ultima_dependencia" IS NULL) AS ultima_dependencia_null,
  COUNT(*) FILTER (WHERE "radicado_respuesta" IS NULL) AS radicado_respuesta_null,
  COUNT(*) FILTER (WHERE "fecha_respuesta" IS NULL) AS fecha_respuesta_null,
  COUNT(*) FILTER (WHERE "fecha_seguimiento" IS NULL) AS fecha_seguimiento_null,
  COUNT(*) FILTER (WHERE "codigo_localidad_fuente" IS NULL) AS codigo_localidad_fuente_null
FROM "pqrs";
-- Esperado:
-- 448 | 448 | 15 | 3949 | 188 | 144 | 144 | 15 | 508

-- 6. El código de localidad fuente NO se usa como FK.
SELECT "codigo_localidad_fuente", COUNT(*) AS registros
FROM "pqrs"
GROUP BY "codigo_localidad_fuente"
ORDER BY registros DESC NULLS LAST;
-- Esperado:
-- 545  | 3474
-- NULL | 508
-- 460  | 41
-- 555  | 1
-- 695  | 1
-- 645  | 1

-- 7. Calidad: vigencia fuente distinta al año de fecha_registro.
SELECT
  "radicado",
  "vigencia",
  "fecha_registro",
  EXTRACT(YEAR FROM "fecha_registro")::smallint AS anio_fecha_registro
FROM "pqrs"
WHERE "vigencia" <> EXTRACT(YEAR FROM "fecha_registro")::smallint
ORDER BY "radicado";
-- Esperado: 4 filas.

-- 8. Tipos de petición
SELECT
  COALESCE(tp."nombre_tipo_peticion", '(NULL)') AS tipo_peticion,
  COUNT(*) AS pqrs
FROM "pqrs" q
LEFT JOIN "tipo_peticion" tp
  ON tp."id_tipo_peticion" = q."id_tipo_peticion"
GROUP BY tp."nombre_tipo_peticion"
ORDER BY pqrs DESC;

-- 9. Medios de recepción
SELECT
  mr."nombre_medio",
  COUNT(*) AS pqrs
FROM "pqrs" q
JOIN "medio_recepcion" mr
  ON mr."id_medio_recepcion" = q."id_medio_recepcion"
GROUP BY mr."nombre_medio"
ORDER BY pqrs DESC;

-- 10. Subtemas principales
SELECT
  st."nombre_subtema",
  COUNT(*) AS pqrs
FROM "pqrs" q
JOIN "subtema_pqrs" st
  ON st."id_subtema" = q."id_subtema"
GROUP BY st."nombre_subtema"
ORDER BY pqrs DESC
LIMIT 15;

-- 11. Rango temporal
SELECT
  MIN("fecha_registro") AS primera_fecha_registro,
  MAX("fecha_registro") AS ultima_fecha_registro
FROM "pqrs";
-- Esperado:
-- 2022-03-14 16:45:29
-- 2026-08-11 11:09:16

-- 12. Muestra normalizada
SELECT *
FROM "vw_pqrs_detalle"
ORDER BY "fecha_registro" DESC
LIMIT 25;
