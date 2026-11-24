-- =====================================================================
-- 01_CARGA_ODS.SQL
-- Fuente: archivo_plano_ods_fdl_corte_30_junio_2026.xlsx
-- San Cristóbal:
--   13 ODS
--   30 metas ODS
--   83 relaciones meta_proyecto ↔ meta_ods
--
-- Los campos financieros del archivo ODS NO se cargan aquí.
-- Ya están modelados en POAI / seguimiento_meta (PMR).
-- =====================================================================

BEGIN;

-- 1. ODS
INSERT INTO "ods" ("codigo_ods","nombre_ods","esfera_ods")
VALUES
('1', 'Fin de la pobreza', 'Personas'),
('2', 'Hambre cero', 'Personas'),
('3', 'Salud y Bienestar', 'Personas'),
('4', 'Educación de Calidad', 'Personas'),
('5', 'Igualdad de género', 'Personas'),
('8', 'Trabajo decente y crecimiento económico', 'Prosperidad'),
('9', 'Industria, innovación e infraestructura', 'Prosperidad'),
('10', 'Reducción de las desigualdades', 'Prosperidad'),
('11', 'Ciudades y Comunidades Sostenibles', 'Prosperidad'),
('12', 'Producción y consumo responsables', 'Planeta'),
('13', 'Acción por el clima', 'Planeta'),
('15', 'Vida de ecosistemas terrestres', 'Planeta'),
('16', 'Paz, Justicia e Instituciones Sólidas', 'Paz')
ON CONFLICT ("codigo_ods")
DO UPDATE SET
  "nombre_ods" = EXCLUDED."nombre_ods",
  "esfera_ods" = EXCLUDED."esfera_ods";

-- 2. Metas ODS
WITH src ("codigo_meta_ods","codigo_ods","descripcion_meta_ods") AS (
  VALUES
  ('1.2', '1', 'De aquí a 2030, reducir al menos a la mitad la proporción de hombres, mujeres y niños de todas las edades que viven en la pobreza en todas sus dimensiones con arreglo a las definiciones nacionales'),
('10.2', '10', 'De aquí a 2030, potenciar y promover la inclusión social, económica y política de todas las personas, independientemente de su edad, sexo, discapacidad, raza, etnia, origen, religión o situación económica u otra condición'),
('11.2', '11', 'De aquí a 2030, proporcionar acceso a sistemas de transporte seguros, asequibles, accesibles y sostenibles para todos y mejorar la seguridad vial, en particular mediante la ampliación del transporte público, prestando especial atención a las necesidades de las personas en situación de vulnerabilidad, las mujeres, los niños, las personas con discapacidad y las personas de edad'),
('11.3', '11', 'De aquí a 2030, aumentar la urbanización inclusiva y sostenible y la capacidad para la planificación y la gestión participativas, integradas y sostenibles de los asentamientos'),
('11.4', '11', 'Redoblar los esfuerzos para proteger y salvaguardar el patrimonio cultural y natural del mundo'),
('11.7', '11', 'De aquí a 2030, proporcionar acceso universal a zonas verdes y espacios públicos seguros, inclusivos y accesibles, en particular para las mujeres y los niños, las personas de edad y las personas con discapacidad'),
('12.5', '12', 'De aquí a 2030, reducir considerablemente la generación de desechos mediante actividades de prevención, reducción, reciclado y reutilización'),
('13.1', '13', 'Fortalecer la resiliencia y la capacidad de adaptación a los riesgos relacionados con el clima y los desastres naturales en todos los países'),
('13.3', '13', 'Mejorar la educación, la sensibilización y la capacidad humana e institucional respecto de la mitigación del cambio climático, la adaptación a él, la reducción de sus efectos y la alerta temprana'),
('15.1', '15', 'De aquí a 2020, asegurar la conservación, el restablecimiento y el uso sostenible de los ecosistemas terrestres y los ecosistemas interiores de agua dulce y sus servicios, en particular los bosques, los humedales, las montañas y las zonas áridas, en consonancia con las obligaciones contraídas en virtud de acuerdos internacionales'),
('15.9', '15', 'De aquí a 2020, integrar los valores de los ecosistemas y la biodiversidad en la planificación, los procesos de desarrollo, las estrategias de reducción de la pobreza y la contabilidad nacionales y locales'),
('16.1', '16', 'Reducir significativamente todas las formas de violencia y las correspondientes tasas de mortalidad en todo el mundo'),
('16.10', '16', 'Garantizar el acceso público a la información y proteger las libertades fundamentales, de conformidad con las leyes nacionales y los acuerdos internacionales'),
('16.3', '16', 'Promover el estado de derecho en los planos nacional e internacional y garantizar la igualdad de acceso a la justicia para todos'),
('16.6', '16', 'Crear a todos los niveles instituciones eficaces y transparentes que rindan cuentas'),
('16.7', '16', 'Garantizar la adopción en todos los niveles de decisiones inclusivas, participativas y representativas que respondan a las necesidades'),
('16.a', '16', 'Fortalecer las instituciones nacionales pertinentes, incluso mediante la cooperación internacional, para crear a todos los niveles, particularmente en los países en desarrollo, la capacidad de prevenir la violencia y combatir el terrorismo y la delincuencia'),
('2.3', '2', 'De aquí a 2030, duplicar la productividad agrícola y los ingresos de los productores de alimentos en pequeña escala, en particular las mujeres, los pueblos indígenas, los agricultores familiares, los ganaderos y los pescadores, entre otras cosas mediante'),
('3.4', '3', 'De aquí a 2030, reducir en un tercio la mortalidad prematura por enfermedades no transmisibles mediante su prevención y tratamiento, y promover la salud mental y el bienestar'),
('3.5', '3', 'Fortalecer la prevención y el tratamiento del abuso de sustancias adictivas, incluido el uso indebido de estupefacientes y el consumo nocivo de alcohol'),
('3.7', '3', 'De aquí a 2030, garantizar el acceso universal a los servicios de salud sexual y reproductiva, incluidos los de planificación familiar, información y educación, y la integración de la salud reproductiva en las estrategias y los programas nacionales'),
('3.8', '3', 'Lograr la cobertura sanitaria universal, incluida la protección contra los riesgos financieros, el acceso a servicios de salud esenciales de calidad y el acceso a medicamentos y vacunas inocuos, eficaces, asequibles y de calidad para todos'),
('4.3', '4', 'De aquí a 2030, asegurar el acceso igualitario de todos los hombres y las mujeres a una formación técnica, profesional y superior de calidad, incluida la enseñanza universitaria.'),
('4.7', '4', 'De aquí a 2030, asegurar que todos los alumnos adquieran los conocimientos teóricos y prácticos necesarios para promover el desarrollo sostenible, entre otras cosas mediante la educación para el desarrollo sostenible y los estilos de vida sostenibles, los derechos humanos, la igualdad de género, la promoción de una cultura de paz y no violencia, la ciudadanía mundial y la valoración de la diversidad cultural y la contribución de la cultura al desarrollo sostenible'),
('5.2', '5', 'Eliminar todas las formas de violencia contra todas las mujeres y las niñas en los ámbitos público y privado, incluidas la trata y la explotación sexual y otros tipos de explotación'),
('5.4', '5', 'Reconocer y valorar los cuidados y el trabajo doméstico no remunerados mediante servicios públicos, infraestructuras y políticas de protección social, y promoviendo la responsabilidad compartida en el hogar y la familia, según proceda en cada país'),
('5.c', '5', 'Aprobar y fortalecer políticas acertadas y leyes aplicables para promover la igualdad de género y el empoderamiento de todas las mujeres y las niñas a todos los niveles'),
('8.3', '8', 'Promover políticas orientadas al desarrollo que apoyen las actividades productivas, la creación de puestos de trabajo decentes, el emprendimiento, la creatividad y la innovación, y fomentar la formalización y el crecimiento de las microempresas y las pequeñas y medianas empresas, incluso mediante el acceso a servicios financieros'),
('9.1', '9', 'Desarrollar infraestructuras fiables, sostenibles, resilientes y de calidad, incluidas infraestructuras regionales y transfronterizas, para apoyar el desarrollo económico y el bienestar humano, haciendo especial hincapié en el acceso asequible y equitativo para todos'),
('9.c', '9', 'Aumentar significativamente el acceso a la tecnología de la información y las comunicaciones y esforzarse por proporcionar acceso universal y asequible a Internet en los países menos adelantados de aquí a 2020')
)
INSERT INTO "meta_ods" ("id_ods","codigo_meta_ods","descripcion_meta_ods")
SELECT
  o."id_ods",
  s."codigo_meta_ods",
  s."descripcion_meta_ods"
FROM src s
JOIN "ods" o
  ON o."codigo_ods" = s."codigo_ods"
ON CONFLICT ("codigo_meta_ods")
DO UPDATE SET
  "id_ods" = EXCLUDED."id_ods",
  "descripcion_meta_ods" = EXCLUDED."descripcion_meta_ods";

-- 3. Stage de relaciones
CREATE TEMP TABLE stg_meta_ods_relacion (
  codigo_meta_extendida varchar(10) NOT NULL,
  codigo_meta_ods varchar(20) NOT NULL
) ON COMMIT DROP;

INSERT INTO stg_meta_ods_relacion ("codigo_meta_extendida","codigo_meta_ods")
VALUES
('22511', '8.3'),
('22521', '11.2'),
('22541', '11.7'),
('22571', '11.7'),
('22572', '11.7'),
('22731', '13.1'),
('22732', '13.1'),
('22851', '16.a'),
('22852', '16.a'),
('23161', '3.7'),
('23162', '3.4'),
('23163', '3.4'),
('23164', '3.8'),
('23165', '3.5'),
('23166', '3.8'),
('23491', '16.1'),
('23851', '5.2'),
('24051', '11.4'),
('24052', '11.4'),
('24053', '11.4'),
('24054', '11.4'),
('24091', '16.7'),
('24092', '16.7'),
('24093', '16.7'),
('24811', '15.9'),
('24812', '15.9'),
('24813', '15.9'),
('24951', '11.7'),
('24952', '11.7'),
('24953', '8.3'),
('24954', '11.7'),
('25021', '11.7'),
('25024', '12.5'),
('25025', '2.3'),
('25027', '11.3'),
('25061', '2.3'),
('26011', '16.7'),
('26061', '16.3'),
('26062', '16.3'),
('26063', '16.3'),
('26081', '8.3'),
('26151', '4.7'),
('26152', '4.3'),
('26153', '4.3'),
('26201', '16.1'),
('26202', '16.1'),
('26203', '16.1'),
('26271', '8.3'),
('26272', '8.3'),
('26331', '16.3'),
('26332', '16.3'),
('26333', '16.1'),
('26334', '16.3'),
('26335', '16.1'),
('26336', '16.1'),
('26337', '16.1'),
('26381', '11.4'),
('26481', '1.2'),
('26482', '1.2'),
('26483', '1.2'),
('26671', '16.6'),
('26672', '16.6'),
('26941', '9.c'),
('26942', '9.c'),
('27081', '10.2'),
('27082', '10.2'),
('27911', '9.1'),
('27912', '9.1'),
('27913', '9.1'),
('27914', '9.1'),
('27915', '9.1'),
('27916', '9.1'),
('27971', '16.10'),
('27972', '16.10'),
('28021', '5.2'),
('28022', '5.4'),
('28023', '5.4'),
('28024', '5.c'),
('28051', '15.1'),
('28052', '15.1'),
('28053', '11.3'),
('28054', '15.1'),
('250211', '13.3');

-- Control: las 83 metas de proyecto deben existir.
DO $$
DECLARE faltantes integer;
BEGIN
  SELECT COUNT(*)
  INTO faltantes
  FROM stg_meta_ods_relacion s
  LEFT JOIN "meta_proyecto" m
    ON m."codigo_meta_extendida" = s."codigo_meta_extendida"
  WHERE m."id_meta" IS NULL;

  IF faltantes > 0 THEN
    RAISE EXCEPTION 'Hay % relaciones ODS con meta_proyecto no encontrada.', faltantes;
  END IF;
END $$;

-- Control: las 30 metas ODS deben existir.
DO $$
DECLARE faltantes integer;
BEGIN
  SELECT COUNT(*)
  INTO faltantes
  FROM stg_meta_ods_relacion s
  LEFT JOIN "meta_ods" mo
    ON mo."codigo_meta_ods" = s."codigo_meta_ods"
  WHERE mo."id_meta_ods" IS NULL;

  IF faltantes > 0 THEN
    RAISE EXCEPTION 'Hay % relaciones con meta ODS no encontrada.', faltantes;
  END IF;
END $$;

-- Reemplazar las relaciones de las 83 metas incluidas en este snapshot.
DELETE FROM "meta_ods_relacion" r
USING "meta_proyecto" m
WHERE r."id_meta" = m."id_meta"
  AND m."codigo_meta_extendida" IN (
    SELECT "codigo_meta_extendida" FROM stg_meta_ods_relacion
  );

INSERT INTO "meta_ods_relacion" ("id_meta","id_meta_ods")
SELECT
  m."id_meta",
  mo."id_meta_ods"
FROM stg_meta_ods_relacion s
JOIN "meta_proyecto" m
  ON m."codigo_meta_extendida" = s."codigo_meta_extendida"
JOIN "meta_ods" mo
  ON mo."codigo_meta_ods" = s."codigo_meta_ods";

-- 4. Vista de consumo analítico
CREATE OR REPLACE VIEW "vw_meta_ods_detalle" AS
SELECT
  m."id_meta",
  m."codigo_meta_extendida",
  m."descripcion_meta",
  o."codigo_ods",
  o."nombre_ods",
  o."esfera_ods",
  mo."codigo_meta_ods",
  mo."descripcion_meta_ods"
FROM "meta_ods_relacion" r
JOIN "meta_proyecto" m
  ON m."id_meta" = r."id_meta"
JOIN "meta_ods" mo
  ON mo."id_meta_ods" = r."id_meta_ods"
JOIN "ods" o
  ON o."id_ods" = mo."id_ods";

COMMIT;
