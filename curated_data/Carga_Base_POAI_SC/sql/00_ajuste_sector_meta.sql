-- =====================================================================
-- 00_AJUSTE_SECTOR_META.SQL
-- Hallazgo de perfilamiento:
-- Los proyectos 2502 y 2802 contienen metas de más de un sector.
-- Por tanto, Sector depende de la META y no del PROYECTO.
-- Ejecutar una sola vez ANTES de la carga.
-- =====================================================================

BEGIN;

-- Eliminar la FK e índice del sector en proyecto.
ALTER TABLE "proyecto"
  DROP CONSTRAINT IF EXISTS "proyecto_id_sector_fkey";

DROP INDEX IF EXISTS "idx_proyecto_id_sector";

ALTER TABLE "proyecto"
  DROP COLUMN IF EXISTS "id_sector";

-- Incorporar sector a la entidad meta_proyecto.
ALTER TABLE "meta_proyecto"
  ADD COLUMN IF NOT EXISTS "id_sector" smallint;

ALTER TABLE "meta_proyecto"
  ALTER COLUMN "id_sector" SET NOT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'meta_proyecto_id_sector_fkey'
  ) THEN
    ALTER TABLE "meta_proyecto"
      ADD CONSTRAINT "meta_proyecto_id_sector_fkey"
      FOREIGN KEY ("id_sector") REFERENCES "sector" ("id_sector");
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS "idx_meta_proyecto_id_sector"
  ON "meta_proyecto" ("id_sector");

-- Reglas de negocio útiles para la carga y la trazabilidad.
CREATE UNIQUE INDEX IF NOT EXISTS "ux_objetivo_codigo"
  ON "objetivo_estrategico" ("codigo_objetivo");

CREATE UNIQUE INDEX IF NOT EXISTS "ux_programa_objetivo_codigo"
  ON "programa" ("id_objetivo", "codigo_programa");

COMMIT;
