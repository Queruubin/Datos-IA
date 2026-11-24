-- =====================================================================
-- 01_CARGA_CRP.SQL
-- Corte fuente: 01/10/2026
-- Vigencia de ejecución observada en San Cristóbal: 2025
--
-- Carga:
--   16 entidades de referencia
--   31 CRP
--   66 líneas CRP-meta
--   177 relaciones CRP-propuesta
-- =====================================================================

BEGIN;

-- 1. Catálogo Entidad
INSERT INTO "entidad" ("nombre_entidad")
VALUES
('Departamento Administrativo de la Defensoría del Espacio Público - DADEP'),
('Instituto Distrital de Protección y Bienestar Animal - IDPYBA'),
('Instituto Distrital de Recreación y Deporte - IDRD'),
('Instituto Distrital de la Participación y Acción Comunal - IDPAC'),
('Instituto de Desarrollo Urbano - IDU'),
('Jardín Botánico José Celestino Mutis - JBB'),
('Oficina de Alta Consejería Distrital de Tecnologías de Información y las Comunicaciones -ACDTIC'),
('Oficina de Alta Consejería de Paz, víctimas y reconciliación'),
('Secretaría Distrital de Ambiente'),
('Secretaría Distrital de Cultura, Recreación y Deporte'),
('Secretaría Distrital de Desarrollo Económico'),
('Secretaría Distrital de Integración Social'),
('Secretaría Distrital de Salud'),
('Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('Secretaría Distrital de la Mujer'),
('UAE de Servicios Públicos - UAESP')
ON CONFLICT ("nombre_entidad") DO NOTHING;

-- 2. Relacionar las 46 metas PP con su entidad de referencia.
WITH src ("codigo_meta_extendida","nombre_entidad") AS (
  VALUES
  ('22511', 'Secretaría Distrital de Cultura, Recreación y Deporte'),
('22521', 'Instituto de Desarrollo Urbano - IDU'),
('22541', 'Instituto de Desarrollo Urbano - IDU'),
('22571', 'Instituto Distrital de Recreación y Deporte - IDRD'),
('22572', 'Instituto Distrital de Recreación y Deporte - IDRD'),
('23162', 'Secretaría Distrital de Salud'),
('23851', 'Secretaría Distrital de la Mujer'),
('24052', 'Secretaría Distrital de Cultura, Recreación y Deporte'),
('24053', 'Secretaría Distrital de Cultura, Recreación y Deporte'),
('24054', 'Secretaría Distrital de Cultura, Recreación y Deporte'),
('24091', 'Instituto Distrital de la Participación y Acción Comunal - IDPAC'),
('24093', 'Instituto Distrital de la Participación y Acción Comunal - IDPAC'),
('24811', 'Instituto Distrital de Protección y Bienestar Animal - IDPYBA'),
('24812', 'Instituto Distrital de Protección y Bienestar Animal - IDPYBA'),
('24813', 'Instituto Distrital de Protección y Bienestar Animal - IDPYBA'),
('24951', 'Instituto Distrital de Recreación y Deporte - IDRD'),
('24952', 'Instituto Distrital de Recreación y Deporte - IDRD'),
('24953', 'Instituto Distrital de Recreación y Deporte - IDRD'),
('24954', 'Instituto Distrital de Recreación y Deporte - IDRD'),
('25024', 'UAE de Servicios Públicos - UAESP'),
('25025', 'Jardín Botánico José Celestino Mutis - JBB'),
('25027', 'Jardín Botánico José Celestino Mutis - JBB'),
('26011', 'Departamento Administrativo de la Defensoría del Espacio Público - DADEP'),
('26061', 'Oficina de Alta Consejería de Paz, víctimas y reconciliación'),
('26062', 'Oficina de Alta Consejería de Paz, víctimas y reconciliación'),
('26063', 'Oficina de Alta Consejería de Paz, víctimas y reconciliación'),
('26081', 'Secretaría Distrital de Desarrollo Económico'),
('26201', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26202', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26203', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26271', 'Secretaría Distrital de Desarrollo Económico'),
('26272', 'Secretaría Distrital de Desarrollo Económico'),
('26331', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26332', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26333', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26334', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26335', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26336', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26337', 'Secretaría Distrital de Seguridad, Convivencia y Justicia'),
('26381', 'Secretaría Distrital de Cultura, Recreación y Deporte'),
('26941', 'Oficina de Alta Consejería Distrital de Tecnologías de Información y las Comunicaciones -ACDTIC'),
('26942', 'Oficina de Alta Consejería Distrital de Tecnologías de Información y las Comunicaciones -ACDTIC'),
('28021', 'Secretaría Distrital de Integración Social'),
('28022', 'Secretaría Distrital de la Mujer'),
('28024', 'Secretaría Distrital de la Mujer'),
('250211', 'Secretaría Distrital de Ambiente')
)
UPDATE "meta_proyecto" m
SET "id_entidad" = e."id_entidad"
FROM src s
JOIN "entidad" e
  ON e."nombre_entidad" = s."nombre_entidad"
WHERE m."codigo_meta_extendida" = s."codigo_meta_extendida";

-- 3. CRP: una fila por número de CRP + vigencia.
WITH src (
  "numero_crp","vigencia","fecha_registro","numero_compromiso","tipo_compromiso",
  "plazo","objeto","codigo_modalidad","modalidad_seleccion","tipo_documento_beneficiario"
) AS (
  VALUES
  ('1118', 2025, DATE '2025-02-12', '042 2025', 'CONTRATO DE PRESTACION DE SERVICIOS PROFESIONALES', 323, 'PRESTACIÓN DE SERVICIOS PROFESIONALES ESPECIALIZADOS PARA APOYAR LA IMPLEMENTACIÓN, EJECUCIÓN Y SEGUIMIENTO DE LOS PROYECTOS Y PROGRAMAS QUE CONTRIBUYAN AL CUMPLIMIENTO DE LAS METAS DEL PDL', '10', 'CONTRATACIÓN DIRECTA', 'CC'),
('1245', 2025, DATE '2025-03-11', '099 2025', 'CONTRATO DE PRESTACION DE SERVICIOS PROFESIONALES', 296, 'PRESTAR SUS SERVICIOS PROFESIONALES ESPECIALIZADOS PARA LA FORMULACIÓN, EVALUACIÓN Y SEGUIMIENTO DE LOS PROYECTOS DE GESTIÓN AMBIENTAL, ASI COMO ORIENTAR TECNICAMENTE LA GESTION DE LAS ACTIVIDADES EJECUTADAS TERRITORIALMENTE EN CUMPLIMIENTO A LAS METAS ES', '10', 'CONTRATACIÓN DIRECTA', 'CC'),
('1325', 2025, DATE '2025-03-21', '240 2025', 'CONTRATO DE PRESTACION DE SERVICIOS PROFESIONALES', 287, 'PRESTAR SUS SERVICIOS PROFESIONALES EN LO CONCERNIENTE A LAS ACTIVIDADESA DMINISTRATIVAS Y DE CAMPO EN LOS PROCESOS DE, AGRICULTURA URBANA Y PERIURBANA, ASI COMO EN LAS ACCIONES DE JARDINERIA CONVENCIONAL Y NO CONVENCIONAL Y LOS PROCESOS DE FORMULACION D', '10', 'CONTRATACIÓN DIRECTA', 'CC'),
('1331', 2025, DATE '2025-03-21', '237 2025', 'CONTRATO DE PRESTACION DE SERVICIOS PROFESIONALES', 287, 'PRESTAR SUS SERVICIOS PROFESIONALES APOYANDO LA FORMULACIÓN, EJECUCIÓN Y SEGUIMIENTO DE LOS PROYECTOS Y PROGRAMAS DEL PDL PROCURANDO SU MEJORA CONTINUA', '10', 'CONTRATACIÓN DIRECTA', 'CC'),
('1369', 2025, DATE '2025-03-27', '284 2025', 'CONTRATO DE PRESTACION DE SERVICIOS PROFESIONALES', 280, 'PRESTAR SERVICIOS PROFESIONALES ESPECIALIZADOS PARA REALIZAR LAS ACTIVIDADES DE ARTICULAR<(>,<)> ORIENTAR, IDENTIFICAR Y GESTIONAR ESTRATEGIAS Y ACCIONES RELACIONADAS CON LA BÚSQUEDA DE COOPERACIÓN INTERNACIONAL PARA LA TRANSFERENCIA DE CONOCIMIENTO TÉCNI', '10', 'CONTRATACIÓN DIRECTA', 'CC'),
('1831', 2025, DATE '2025-07-15', '679 2025', 'CONVENIO INTERADMINISTRATIVO', 169, 'Aunar esfuerzos técnicos, administrativos y financieros entre la SCRD, IDARTES y EL FONDO DE DESARROLLO LOCAL DE USAQUÉN; FONDO DE DESARROLLO LOCAL DE CHAPINERO; FONDO DE DESARROLLO LOCAL DE SAN CRISTÓBAL; FONDO DEDESARROLLO LOCAL DE USME; FONDO DE DESARR', '10', 'CONTRATACIÓN DIRECTA', 'NITC'),
('1832', 2025, DATE '2025-07-15', '679 2025', 'CONVENIO INTERADMINISTRATIVO', 169, 'Aunar esfuerzos técnicos, administrativos y financieros entre la SCRD, IDARTES y EL FONDO DE DESARROLLO LOCAL DE USAQUÉN; FONDO DE DESARROLLO LOCAL DE CHAPINERO; FONDO DE DESARROLLO LOCAL DE SAN CRISTÓBAL; FONDO DEDESARROLLO LOCAL DE USME; FONDO DE DESARR', '10', 'CONTRATACIÓN DIRECTA', 'NIT'),
('1873', 2025, DATE '2025-08-28', '716 2025', 'CONVENIO INTERADMINISTRATIVO', 125, 'AUNAR ESFUERZOS TÉCNICOS, ADMINISTRATIVOS, ACADÉMICOS Y FINANCIEROS ENTRE LA ALCALDÍA LOCAL DE SAN CRISTÓBAL Y LA UNIVERSIDAD DISTRITAL FRANCISCO JOSÉ DE CALDAS, PARA LA PLANEACIÓN, DESARROLLO Y EJECUCIÓN DE ACTIVIDADES RECREO DEPORTIVAS, PROCESOS DE CAPA', '10', 'CONTRATACIÓN DIRECTA', 'NIT'),
('2198', 2025, DATE '2025-09-30', '760 2025', 'CONTRATO DE OBRA PUBLICA', 92, 'CONTRATAR POR MEDIO DE PRECIOS UNITARIOS Y A MONTO AGOTABLE, LAS OBRAS DE CONSERVACIÓN DE LA MALLA VIAL, ESPACIO PÚBLICO ASOCIADO Y OBRAS COMPLEMENTARIAS EN LA LOCALIDAD DE SAN CRISTÓBAL, BOGOTÁ, D.C RECURSOS VIGENCIA 2025', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2227', 2025, DATE '2025-10-06', '776 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 86, 'PRESTAR LOS SERVICIOS DE APOYO TÉCNICO Y OPERATIVO PARA LA EJECUCIÓN DE LAS INCUBADORAS DE IDEAS DE NEGOCIO E INICIATIVAS PRODUCTIVAS EN LA LOCALIDAD DE SAN CRISTÓBAL 2.0 - 2025', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2384', 2025, DATE '2025-10-21', '785 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 75, 'CONTRATAR LOS SERVICIOS DE ESTERILIZACIÓN Y LA ATENCIÓN DE URGENCIAS, DE CANINOS Y FELINOS PERTENECIENTES A LOS ESTRATOS SOCIOECONÓMICOS 1, 2 Y 3, ASÍ COMO DE CANINOS Y FELINOS EN CONDICIÓN DE CALLE, CON EL FIN DE CONTRIBUIR AL BIENESTAR ANIMAL Y AL CONTR', '10', 'CONTRATACIÓN DIRECTA', 'NIT'),
('2450', 2025, DATE '2025-10-31', '805 2025', 'CONVENIO INTERADMINISTRATIVO', 61, 'El Convenio que se pretende celebrar tendrá por objeto Aunar esfuerzos para la implementación de las iniciativas priorizadas en los presupuestos participativos, orientadas a la prevención del feminicidio, la violenciaintrafamiliar, sexual y otras vulnerac', '10', 'CONTRATACIÓN DIRECTA', 'NIT'),
('2452', 2025, DATE '2025-11-04', '809 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 57, 'CONTRATAR BAJO LA MODALIDAD DE MONTO AGOTABLE LA GESTIÓN LOGÍSTICA, SUMINISTRO DE INSUMOS, PRODUCCIÓN TÉCNICA, OPERACIÓN, GESTIÓN DE PERMISOS Y PROMOCIÓN PARA LA REALIZACIÓN DE EVENTOS, ACTIVIDADES Y ESTRATEGIAS LIDERADAS POR LA ALCALDÍA LOCAL DE SAN CRIS', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2474', 2025, DATE '2025-11-13', '760 2025', 'CONTRATO DE OBRA PUBLICA', 48, 'CONTRATAR POR MEDIO DE PRECIOS UNITARIOS Y A MONTO AGOTABLE, LAS OBRAS DE CONSERVACIÓN DE LA MALLA VIAL, ESPACIO PÚBLICO ASOCIADO Y OBRAS COMPLEMENTARIAS EN LA LOCALIDAD DE SAN CRISTÓBAL, BOGOTÁ, D.C RECURSOS VIGENCIA 2025', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2475', 2025, DATE '2025-11-13', '776 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 48, 'PRESTAR LOS SERVICIOS DE APOYO TÉCNICO Y OPERATIVO PARA LA EJECUCIÓN DE LAS INCUBADORAS DE IDEAS DE NEGOCIO E INICIATIVAS PRODUCTIVAS EN LA LOCALIDAD DE SAN CRISTÓBAL 2.0 - 2025', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2477', 2025, DATE '2025-11-13', '809 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 48, 'CONTRATAR BAJO LA MODALIDAD DE MONTO AGOTABLE LA GESTIÓN LOGÍSTICA, SUMINISTRO DE INSUMOS, PRODUCCIÓN TÉCNICA, OPERACIÓN, GESTIÓN DE PERMISOS Y PROMOCIÓN PARA LA REALIZACIÓN DE EVENTOS, ACTIVIDADES Y ESTRATEGIAS LIDERADAS POR LA ALCALDÍA LOCAL DE SAN CRIS', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2483', 2025, DATE '2025-11-14', '819 2025', 'CONVENIO INTERADMINISTRATIVO', 47, 'AUNAR ESFUERZOS TÉCNICOS, ADMINISTRATIVOS Y LOGÍSTICOS PARA LA IMPLEMENTACIÓN DE SOLUCIONES TECNOLÓGICAS INTEGRALES, QUE INCLUYEN LA ADQUISICIÓN, INSTALACIÓN, CONFIGURACIÓN Y PUESTA EN FUNCIONAMIENTO DE KITS DE VIDEOVIGILANCIA, ASÍ COMO LA ADECUACIÓN DE E', '10', 'CONTRATACIÓN DIRECTA', 'NIT'),
('2488', 2025, DATE '2025-11-19', '846 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 42, 'CONTRATAR SERVICIOS TÉCNICOS Y OPERATIVOS PARA EL MANTENIMIENTO DE ARBOLADO (RURAL Y URBANO) Y JARDINERÍA CONVENCIONAL Y NO CONVENCIONAL EN LA LOCALIDAD DE SAN CRISTÓBAL', '02', 'SELEC. ABREV. MENOR CUANTÍA', 'NIT'),
('2490', 2025, DATE '2025-11-19', '816 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 42, 'CONTRATAR LOS BIENES Y SERVICIOS QUE PERMITAN EL FUNCIONAMIENTO DE SISTEMAS INTEGRADOS DE CONVIVENCIA BASADOS EN METODOLOGÍAS APLICADAS EN OCHO ZONAS DE PREVENCIÓN COMUNAL IDENTIFICADAS DE LA LOCALIDAD DE SAN CRISTÓBAL EN CUMPLIMIENTO DE PROYECTOS PARTICI', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2510', 2025, DATE '2025-12-04', '850 2025', 'CONTRATO DE SUMINISTRO', 28, 'SUMINISTRAR LOS ELEMENTOS, MATERIALES E INSUMOS NECESARIOS PARA LA REALIZACIÓN DE TALLERES DIRIGIDOS A VENDEDORES INFORMALES Y PARA LA EJECUCIÓN DE ACTIVIDADES DE EMBELLECIMIENTO Y ADECUACIÓN DEL ESPACIO PÚBLICO, INCLUYENDO LOS IMPLEMENTOS PARA LA ORGANIZ', '10', 'CONTRATACIÓN DIRECTA', 'NIT'),
('2522', 2025, DATE '2025-12-11', '866 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 20, 'PRESTACIÓN DE SERVICIOS TÉCNICOS, LOGÍSTICOS Y METODOLÓGICOS DIRIGIDOS AL FORTALECIMIENTO DE LAS ORGANIZACIONES COMUNALES, SOCIALES COMUNITARIAS E INSTANCIAS DE PARTICIPACIÓN DE LA LOCALIDAD DE SAN CRISTÓBAL, MEDIANTE LA IMPLEMENTACIÓN DE PROCESOS INCIDEN', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2532', 2025, DATE '2025-12-17', '873 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 14, 'CONTRATAR LA PRESTACIÓN DE SERVICIOS DE ASISTENCIA Y ACOMPAÑAMIENTO TÉCNICO PARA LA IMPLEMENTACIÓN DE PROCESOS CIUDADANOS DE EDUCACIÓN AMBIENTAL (PROCEDA), FORTALECIMIENTO DE PROYECTOS DE AGRICULTURA URBANA Y PERIURBANA, Y DESARROLLO DE ACCIONES PEDAGÓGI', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2534', 2025, DATE '2025-12-17', '885 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 14, 'CONTRATAR BIENES Y SERVICIOS PARA EL DESARROLLO DE ACTIVIDADES PEDAGÓGICAS, CULTURALES Y COMUNITARIAS ORIENTADAS A LA PROMOCIÓN DE LA CONVIVENCIA CIUDADANA Y LA JUSTICIA RESTAURATIVA, INCLUYENDO PRODUCCIÓN AUDIOVISUAL, SUMINISTRO DE MATERIALES Y KITS ACAD', '02', 'SELEC. ABREV. MENOR CUANTÍA', 'NIT'),
('2537', 2025, DATE '2025-12-23', '892 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 8, 'IMPLEMENTAR UNA ESTRATEGIA PEDAGÓGICA DIRIGIDA A LA POBLACIÓN VÍCTIMA DEL CONFLICTO ARMADO MEDIANTE EL DESARROLLO DE LA ESCUELA DE PAZ, QUE PROMUEVA LA MEMORIA, LA REPARACIÓN, LA RECONCILIACIÓN Y EL FORTALECIMIENTO DE CAPACIDADES PARA LA CONSTRUCCIÓN DE P', '02', 'SELEC. ABREV. MENOR CUANTÍA', 'NIT'),
('2540', 2025, DATE '2025-12-26', '857 2025', 'CONTRATO DE PRESTACION DE SERVICIOS DE APOYO A LA GESTION', 5, 'PRESTAR SUS SERVICIOS TECNICOS PARA LA EJECUCIÓN DE ACTIVIDADES COMO OFICIAL DE OBRA CIVIL, QUE CONLLEVEN AL MEJORAMIENTO Y ADECUACIÓN DEL ESPACIO PÚBLICO Y MALLA VIAL DE LA LOCALIDAD DE SAN CRISTOBAL', '10', 'CONTRATACIÓN DIRECTA', 'CC'),
('2543', 2025, DATE '2025-12-26', '890 2025', 'CONTRATO DE CONSULTORIA', 5, 'CONTRATAR UNA CONSULTORÍA ESPECIALIZADA PARA LA ELABORACIÓN DE LOS ESTUDIOS Y DISEÑOS TÉCNICOS REQUERIDOS PARA LA FORMULACIÓN DE PROYECTOS DE CONSTRUCCIÓN DE PARQUES DE PROXIMIDAD DE LA LOCALIDAD DE SAN CRISTÓBAL EN LA CIUDAD DE BOGOTÁ D.C., EL ALCANCE IN', '08', 'CONCURSO DE MÉRITOS ABIERTO', 'NIT'),
('2544', 2025, DATE '2025-12-26', '895 2025', 'CONTRATO DE OBRA PUBLICA', 5, 'CONTRATAR MEDIANTE EL SISTEMA DE PRECIOS UNITARIOS A MONTO AGOTABLE, LAS OBRAS DE REHABILITACIÓN Y/O CONSERVACIÓN Y/O MEJORAMIENTO Y/O MANTENIMIENTO DE PARQUES DE PROXIMIDAD DE LA LOCALIDAD DE SAN CRISTÓBAL PDL 2025 2028 VIGENCIA 2025', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2545', 2025, DATE '2025-12-26', '896 2025', 'CONTRATO DE PRESTACION DE SERVICIOS', 5, 'Prestar servicios para la implementación de estrategias integrales en salud, en el marco del Proyecto 2316 del Plan de Desarrollo Local ¿Territorio de Oportunidades, Camina Segura¿ de la localidad de San Cristóbal, orientadas a la reducción de riesgos por', '01', 'LICITACIÓN PÚBLICA', 'NIT'),
('2554', 2025, DATE '2025-12-29', '898 2025', 'CONTRATO DE INTERVENTORIA', 2, '¿REALIZAR LA INTERVENTORÍA TÉCNICA, ADMINISTRATIVA, FINANCIERA, SOCIAL, AMBIENTAL, CONTABLE Y JURÍDICA AL CONTRATO CUYO OBJETO ES: ¿CONTRATAR MEDIANTE EL SISTEMA DE PRECIOS UNITARIOS A MONTO AGOTABLE, LAS OBRAS DE REHABILITACIÓN Y/O CONSERVACIÓN Y/O MEJOR', '08', 'CONCURSO DE MÉRITOS ABIERTO', 'NIT'),
('2556', 2025, DATE '2025-12-29', '900 2025', 'CONTRATO DE SUMINISTRO', 2, 'ADQUISICIÓN DE ELEMENTOS TÉCNICOS, ESCÉNICOS Y MODULARES PARA DOTAR INTEGRALMENTE EL CAMPUS CULTURAL, EL CENTRO DE DOCUMENTACIÓN DE LA ALCALDÍA LOCAL DE SAN CRISTÓBAL Y EL TEATRO LA VICTORIA, FORTALECIENDO PROCESOS ARTÍSTICOS, PEDAGÓGICOS, COMUNITARIOS Y', '03', 'SELEC. ABREV. SUBASTA INVERSA', 'NIT'),
('2559', 2025, DATE '2025-12-30', '679 2025', 'CONVENIO INTERADMINISTRATIVO', 1, 'Adiconar el contrato FDLSC-CVNI-700-2025 que tiene por objeto Aunar esfuerzos técnicos, administrativos y financieros entre la SCRD, IDARTESy EL FONDO DE DESARROLLO LOCAL DE USAQUÉN; FONDO DE DESARROLLO LOCAL DE CHAPINERO; FONDO DE DESARROLLO LOCAL DE SAN', '10', 'CONTRATACIÓN DIRECTA', 'NITC')
)
INSERT INTO "crp" (
  "numero_crp","vigencia","fecha_registro","numero_compromiso","tipo_compromiso",
  "plazo","objeto","codigo_modalidad","modalidad_seleccion","tipo_documento_beneficiario"
)
SELECT * FROM src
ON CONFLICT ("numero_crp","vigencia")
DO UPDATE SET
  "fecha_registro" = EXCLUDED."fecha_registro",
  "numero_compromiso" = EXCLUDED."numero_compromiso",
  "tipo_compromiso" = EXCLUDED."tipo_compromiso",
  "plazo" = EXCLUDED."plazo",
  "objeto" = EXCLUDED."objeto",
  "codigo_modalidad" = EXCLUDED."codigo_modalidad",
  "modalidad_seleccion" = EXCLUDED."modalidad_seleccion",
  "tipo_documento_beneficiario" = EXCLUDED."tipo_documento_beneficiario";

-- 4. Stage de las 66 líneas CRP-meta exactamente como aparecen en la fuente.
CREATE TEMP TABLE stg_crp_meta (
  numero_crp varchar(20) NOT NULL,
  vigencia smallint NOT NULL,
  codigo_meta_extendida varchar(10) NOT NULL,
  valor_asignado_pp decimal(18,2)
) ON COMMIT DROP;

INSERT INTO stg_crp_meta
(numero_crp, vigencia, codigo_meta_extendida, valor_asignado_pp)
VALUES
('1831', 2025, '22511', 122150000),
('1832', 2025, '22511', 553850000),
('2474', 2025, '22521', 109989000),
('2474', 2025, '22521', 2945000000),
('2474', 2025, '22521', 6996917188),
('2474', 2025, '22521', 4143339000),
('2198', 2025, '22521', 0),
('2540', 2025, '22521', 4800000),
('2474', 2025, '22541', 1889397000),
('2543', 2025, '22571', 850000000),
('2544', 2025, '22572', 1242363600),
('2554', 2025, '22572', 138039595),
('2477', 2025, '23162', 130000000),
('2452', 2025, '23162', 0),
('2545', 2025, '23162', 933198969),
('2450', 2025, '23851', 1196332527),
('2477', 2025, '23851', 170000000),
('2559', 2025, '24052', 44030668),
('1831', 2025, '24053', 1449250000),
('2559', 2025, '24054', 58560000),
('2522', 2025, '24091', 100000000),
('2522', 2025, '24091', 475219166),
('2522', 2025, '24091', 575219167),
('2477', 2025, '24093', 450000000),
('2452', 2025, '24093', 0),
('2477', 2025, '24811', 250000000),
('2384', 2025, '24812', 122702250),
('2384', 2025, '24813', 792132000),
('1873', 2025, '24951', 599378275),
('1873', 2025, '24952', 809689442),
('1873', 2025, '24953', 770867000),
('1873', 2025, '24954', 1146161888),
('2532', 2025, '25024', 213000000),
('2532', 2025, '25024', 331000000),
('2532', 2025, '25024', 436732514),
('1325', 2025, '25025', 48000000),
('1245', 2025, '25025', 64000000),
('2488', 2025, '25027', 167085596),
('2510', 2025, '26011', 123042335),
('2537', 2025, '26061', 241116781),
('2537', 2025, '26062', 191290000),
('2537', 2025, '26063', 7498164),
('1331', 2025, '26081', 54400000),
('2227', 2025, '26081', 0),
('2475', 2025, '26081', 1160000000),
('2490', 2025, '26201', 200000000),
('2490', 2025, '26202', 100000000),
('2534', 2025, '26202', 223788297),
('2483', 2025, '26203', 398925812),
('2483', 2025, '26203', 900000000),
('1118', 2025, '26271', 32000000),
('1118', 2025, '26272', 32000000),
('2490', 2025, '26331', 100000000),
('2490', 2025, '26332', 100000000),
('2490', 2025, '26333', 100000000),
('2483', 2025, '26334', 132180000),
('2510', 2025, '26335', 114426578),
('2534', 2025, '26336', 155551000),
('2490', 2025, '26337', 190918567),
('2534', 2025, '26337', 178481636),
('2556', 2025, '26381', 1028203439),
('2483', 2025, '26941', 1022585478),
('1369', 2025, '26942', 64000000),
('2450', 2025, '28021', 468422180),
('2450', 2025, '28022', 1427681767),
('2477', 2025, '28024', 440000000);

-- Control: todas las metas deben existir.
DO $$
DECLARE faltantes integer;
BEGIN
  SELECT COUNT(*) INTO faltantes
  FROM stg_crp_meta s
  LEFT JOIN "meta_proyecto" m
    ON m."codigo_meta_extendida" = s."codigo_meta_extendida"
  WHERE m."id_meta" IS NULL;

  IF faltantes > 0 THEN
    RAISE EXCEPTION 'Hay % líneas CRP-meta con meta no encontrada.', faltantes;
  END IF;
END $$;

-- Recarga por snapshot para que el script sea idempotente.
DELETE FROM "crp_meta" cm
USING "crp" c
WHERE cm."id_crp" = c."id_crp"
  AND (c."numero_crp", c."vigencia") IN (
    SELECT DISTINCT "numero_crp", "vigencia" FROM stg_crp_meta
  );

INSERT INTO "crp_meta" ("id_crp","id_meta","valor_asignado_pp")
SELECT
  c."id_crp",
  m."id_meta",
  s."valor_asignado_pp"
FROM stg_crp_meta s
JOIN "crp" c
  ON c."numero_crp" = s."numero_crp"
 AND c."vigencia" = s."vigencia"
JOIN "meta_proyecto" m
  ON m."codigo_meta_extendida" = s."codigo_meta_extendida";

-- 5. CRP-Propuesta: explotar la lista de códigos y guardar pares únicos.
CREATE TEMP TABLE stg_crp_propuesta (
  numero_crp varchar(20) NOT NULL,
  vigencia smallint NOT NULL,
  codigo_propuesta varchar(20) NOT NULL
) ON COMMIT DROP;

INSERT INTO stg_crp_propuesta
(numero_crp, vigencia, codigo_propuesta)
VALUES
('1118', 2025, '39580'),
('1118', 2025, '40143'),
('1118', 2025, '40255'),
('1118', 2025, '40263'),
('1118', 2025, '40782'),
('1118', 2025, '41263'),
('1245', 2025, '39760'),
('1245', 2025, '40305'),
('1245', 2025, '40916'),
('1245', 2025, '41640'),
('1245', 2025, '42108'),
('1325', 2025, '40916'),
('1325', 2025, '41640'),
('1325', 2025, '42108'),
('1331', 2025, '37875'),
('1331', 2025, '38863'),
('1369', 2025, '40900'),
('1831', 2025, '37646'),
('1831', 2025, '38062'),
('1831', 2025, '38950'),
('1831', 2025, '39044'),
('1831', 2025, '39051'),
('1831', 2025, '40437'),
('1831', 2025, '42139'),
('1831', 2025, '43219'),
('1831', 2025, '43221'),
('1831', 2025, '43257'),
('1832', 2025, '38062'),
('1832', 2025, '39044'),
('1832', 2025, '39051'),
('1832', 2025, '40437'),
('1832', 2025, '42139'),
('1873', 2025, '38910'),
('1873', 2025, '39676'),
('1873', 2025, '40668'),
('1873', 2025, '40681'),
('1873', 2025, '40746'),
('1873', 2025, '40951'),
('1873', 2025, '41159'),
('1873', 2025, '41463'),
('1873', 2025, '42345'),
('1873', 2025, '42615'),
('1873', 2025, '43210'),
('1873', 2025, '43214'),
('1873', 2025, '43218'),
('1873', 2025, '43220'),
('1873', 2025, '43222'),
('1873', 2025, '43223'),
('1873', 2025, '43249'),
('2198', 2025, '43849'),
('2227', 2025, '37875'),
('2227', 2025, '38863'),
('2227', 2025, '40013'),
('2227', 2025, '41117'),
('2227', 2025, '41611'),
('2384', 2025, '40463'),
('2384', 2025, '40469'),
('2384', 2025, '40493'),
('2384', 2025, '40504'),
('2384', 2025, '42384'),
('2450', 2025, '40855'),
('2450', 2025, '43197'),
('2450', 2025, '43217'),
('2450', 2025, '43224'),
('2450', 2025, '43228'),
('2450', 2025, '43229'),
('2450', 2025, '43231'),
('2450', 2025, '43232'),
('2450', 2025, '43236'),
('2450', 2025, '43237'),
('2450', 2025, '43239'),
('2450', 2025, '43240'),
('2450', 2025, '43241'),
('2450', 2025, '43242'),
('2450', 2025, '43243'),
('2450', 2025, '43248'),
('2452', 2025, '39718'),
('2452', 2025, '43225'),
('2452', 2025, '43230'),
('2452', 2025, '43247'),
('2452', 2025, '43250'),
('2452', 2025, '43261'),
('2452', 2025, '43559'),
('2474', 2025, '43849'),
('2474', 2025, '43880'),
('2475', 2025, '37875'),
('2475', 2025, '38863'),
('2475', 2025, '40013'),
('2475', 2025, '41117'),
('2475', 2025, '41611'),
('2477', 2025, '39718'),
('2477', 2025, '40112'),
('2477', 2025, '40855'),
('2477', 2025, '41494'),
('2477', 2025, '42199'),
('2477', 2025, '43225'),
('2477', 2025, '43228'),
('2477', 2025, '43229'),
('2477', 2025, '43230'),
('2477', 2025, '43232'),
('2477', 2025, '43234'),
('2477', 2025, '43235'),
('2477', 2025, '43236'),
('2477', 2025, '43237'),
('2477', 2025, '43243'),
('2477', 2025, '43244'),
('2477', 2025, '43245'),
('2477', 2025, '43246'),
('2477', 2025, '43247'),
('2477', 2025, '43250'),
('2477', 2025, '43261'),
('2477', 2025, '43264'),
('2477', 2025, '43350'),
('2477', 2025, '43559'),
('2483', 2025, '40385'),
('2483', 2025, '41411'),
('2483', 2025, '43212'),
('2488', 2025, '43886'),
('2490', 2025, '38888'),
('2490', 2025, '39038'),
('2490', 2025, '39856'),
('2490', 2025, '40557'),
('2490', 2025, '41012'),
('2490', 2025, '41236'),
('2490', 2025, '41529'),
('2490', 2025, '41737'),
('2490', 2025, '43213'),
('2490', 2025, '43215'),
('2510', 2025, '40226'),
('2510', 2025, '40239'),
('2522', 2025, '40490'),
('2522', 2025, '41554'),
('2522', 2025, '41575'),
('2522', 2025, '42535'),
('2522', 2025, '42677'),
('2532', 2025, '40511'),
('2532', 2025, '41564'),
('2534', 2025, '39336'),
('2534', 2025, '40535'),
('2534', 2025, '43216'),
('2534', 2025, '43226'),
('2534', 2025, '43227'),
('2537', 2025, '43238'),
('2537', 2025, '43566'),
('2537', 2025, '43570'),
('2540', 2025, '43849'),
('2543', 2025, '43841'),
('2543', 2025, '43844'),
('2544', 2025, '43853'),
('2544', 2025, '43855'),
('2544', 2025, '43858'),
('2544', 2025, '43862'),
('2544', 2025, '43865'),
('2544', 2025, '43868'),
('2544', 2025, '43869'),
('2545', 2025, '43225'),
('2545', 2025, '43230'),
('2545', 2025, '43247'),
('2545', 2025, '43250'),
('2545', 2025, '43261'),
('2545', 2025, '43559'),
('2554', 2025, '43853'),
('2554', 2025, '43855'),
('2554', 2025, '43858'),
('2554', 2025, '43862'),
('2554', 2025, '43865'),
('2554', 2025, '43868'),
('2554', 2025, '43869'),
('2556', 2025, '43872'),
('2556', 2025, '43874'),
('2556', 2025, '43876'),
('2559', 2025, '37701'),
('2559', 2025, '37709'),
('2559', 2025, '40084'),
('2559', 2025, '40507'),
('2559', 2025, '40591'),
('2559', 2025, '41802');

-- Control: todas las propuestas referenciadas deben existir.
DO $$
DECLARE faltantes integer;
BEGIN
  SELECT COUNT(*) INTO faltantes
  FROM stg_crp_propuesta s
  LEFT JOIN "propuesta_ciudadana" p
    ON p."codigo_propuesta" = s."codigo_propuesta"
  WHERE p."id_propuesta" IS NULL;

  IF faltantes > 0 THEN
    RAISE EXCEPTION 'Hay % relaciones CRP-propuesta con propuesta no encontrada.', faltantes;
  END IF;
END $$;

DELETE FROM "crp_propuesta" cp
USING "crp" c
WHERE cp."id_crp" = c."id_crp"
  AND (c."numero_crp", c."vigencia") IN (
    SELECT DISTINCT "numero_crp", "vigencia" FROM stg_crp_propuesta
  );

INSERT INTO "crp_propuesta" ("id_crp","id_propuesta")
SELECT
  c."id_crp",
  p."id_propuesta"
FROM stg_crp_propuesta s
JOIN "crp" c
  ON c."numero_crp" = s."numero_crp"
 AND c."vigencia" = s."vigencia"
JOIN "propuesta_ciudadana" p
  ON p."codigo_propuesta" = s."codigo_propuesta";

-- 6. Vista agregada para análisis:
-- una fila por CRP + meta, sumando las líneas de asignación.
CREATE OR REPLACE VIEW "vw_crp_meta_resumen" AS
SELECT
  c."id_crp",
  c."numero_crp",
  c."vigencia",
  m."id_meta",
  m."codigo_meta_extendida",
  COUNT(*) AS "numero_lineas_asignacion",
  SUM(cm."valor_asignado_pp") AS "valor_total_crp_meta"
FROM "crp_meta" cm
JOIN "crp" c ON c."id_crp" = cm."id_crp"
JOIN "meta_proyecto" m ON m."id_meta" = cm."id_meta"
GROUP BY
  c."id_crp", c."numero_crp", c."vigencia",
  m."id_meta", m."codigo_meta_extendida";

COMMIT;
