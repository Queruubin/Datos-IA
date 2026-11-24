-- =====================================================================
-- 01_CARGA_BASE_POAI.SQL
-- Carga estructural inicial: localidad, sector, objetivo, programa,
-- proyecto, meta_proyecto y POAI 2025-2026.
-- Requiere haber ejecutado 00_ajuste_sector_meta.sql.
-- =====================================================================

BEGIN;



INSERT INTO "localidad" ("id_localidad","nombre_localidad")
VALUES (4, 'San Cristóbal')
ON CONFLICT ("id_localidad")
DO UPDATE SET "nombre_localidad" = EXCLUDED."nombre_localidad";


INSERT INTO "sector" ("nombre_sector")
VALUES ('AMBIENTE'),
('CULTURA, RECREACIÓN Y DEPORTE'),
('DESARROLLO ECONÓMICO, INDUSTRIA Y TURISMO'),
('EDUCACIÓN'),
('GESTIÓN PÚBLICA'),
('GOBIERNO'),
('HÁBITAT'),
('INTEGRACIÓN SOCIAL'),
('MOVILIDAD'),
('MUJERES'),
('SALUD'),
('SEGURIDAD, CONVIVENCIA Y JUSTICIA')
ON CONFLICT ("nombre_sector") DO NOTHING;


INSERT INTO "objetivo_estrategico" ("codigo_objetivo","nombre_objetivo")
VALUES (1, 'Bogotá avanza en su seguridad'),
(2, 'Bogotá confía en su bien-estar'),
(3, 'Bogotá confía en su potencial'),
(4, 'Bogotá ordena su territorio y avanza en su acción climática'),
(5, 'Bogotá confía en su gobierno')
ON CONFLICT ("codigo_objetivo")
DO UPDATE SET "nombre_objetivo" = EXCLUDED."nombre_objetivo";


WITH src ("codigo_objetivo","codigo_programa","nombre_programa") AS (
  VALUES
  (1, 1, 'Diálogo social y cultura ciudadana para la convivencia pacifica y la recuperación de la confianza'),
(1, 2, 'Cero tolerancia a las violencias contra las mujeres y basadas en género'),
(1, 3, 'Desmantelamiento de estructuras criminales y delincuenciales con mejores capacidades y activos tecnológicos'),
(1, 4, 'Servicios centrados en la justicia'),
(1, 5, 'Espacio público seguro e inclusivo'),
(2, 7, 'Bogotá, una ciudad con menos Pobreza'),
(2, 8, 'Erradicación del hambre en Bogotá'),
(2, 10, 'Salud Pública Integrada e Integral'),
(2, 12, 'Bogotá cuida a su gente'),
(2, 13, 'Bogotá, un territorio de paz y reconciliación en donde todos puedan volver a empezar'),
(2, 14, 'Bogotá deportiva, recreativa, artística, patrimonial e intercultural'),
(2, 15, 'Bogotá protege todas las formas de vida'),
(3, 16, 'Atención Integral a la Primera Infancia y Educación como Eje del Potencial Humano'),
(3, 19, 'Desarrollo empresarial, productividad y empleo'),
(3, 20, 'Promoción del emprendimiento formal, equitativo e incluyente'),
(4, 24, 'Revitalización y renovación urbana y rural con inclusión'),
(4, 25, 'Aumento de la resiliencia al cambio climático y reducción de la vulnerabilidad'),
(4, 26, 'Movilidad Sostenible'),
(4, 27, 'Gestión del riesgo de desastres para un territorio seguro'),
(4, 30, 'Atención del déficit social para un hábitat digno'),
(5, 33, 'Fortalecimiento institucional para un gobierno confiable'),
(5, 35, 'Bogotá ciudad Inteligente'),
(5, 39, 'Camino hacia una democracia deliberativa con un gobierno cercano a la gente y con participación ciudadana')
)
INSERT INTO "programa" ("id_objetivo","codigo_programa","nombre_programa")
SELECT o."id_objetivo", s."codigo_programa", s."nombre_programa"
FROM src s
JOIN "objetivo_estrategico" o
  ON o."codigo_objetivo" = s."codigo_objetivo"
ON CONFLICT ("id_objetivo","codigo_programa")
DO UPDATE SET "nombre_programa" = EXCLUDED."nombre_programa";


WITH src ("codigo_proyecto","id_localidad","codigo_objetivo","codigo_programa","nombre_proyecto") AS (
  VALUES
  ('2251', 4, 3, 20, 'Sostenibilidad del Ecosistema Cultural y Creativo'),
('2252', 4, 4, 26, 'Transformando Espacios, Conectando Comunidades/San Cristóbal Vial: Caminos de Oportunidad y Progreso.'),
('2254', 4, 1, 5, 'Caminos Sostenibles/Solidez en San Cristóbal: Ampliando y Conservando los Espacios Peatonales'),
('2257', 4, 4, 24, 'Red de Oportunidades: Parques y Cultura para el Bienestar Común'),
('2273', 4, 4, 27, 'San Cristóbal Resiliente: Fortaleciendo Capacidades Locales'),
('2285', 4, 1, 3, 'Seguridad y Oportunidades con Fuerzas Policiales Equipadas'),
('2316', 4, 2, 10, 'San Cristóbal sin barreras, salud, bienestar y oportunidades para todos'),
('2349', 4, 1, 5, 'San Cristóbal: Espacio Público Seguro y Pacífico'),
('2385', 4, 1, 2, 'San Cristóbal: Mujeres en Acción contra la Violencia'),
('2405', 4, 2, 14, 'Cultura y memoria en movimiento, San Cristóbal vive su patrimonio'),
('2409', 4, 5, 39, 'San Cristóbal Incidente'),
('2481', 4, 2, 15, 'San Cristóbal Cuida: Bienestar Animal Y Educación Para Todos'),
('2495', 4, 2, 14, 'Actívate San Cristóbal: Deporte, Recreación y Bienestar'),
('2502', 4, 4, 25, 'San Cristóbal, oportunidades para el futuro sostenible'),
('2506', 4, 2, 8, 'Oportunidades con Bien-estar: San Cristóbal Avanza'),
('2601', 4, 1, 5, 'Pacto por Espacios Sostenibles en San Cristóbal'),
('2606', 4, 2, 13, 'Tejiendo Memoria y Reconciliación para el Futuro'),
('2608', 4, 3, 20, 'San Cristóbal Emprende: Fortaleciendo el Tejido Empresarial Local'),
('2615', 4, 3, 16, 'Educación que genera oportunidades'),
('2620', 4, 1, 1, 'San Cristóbal: Camina Seguro, Vive Seguro'),
('2627', 4, 3, 19, 'El Delirio del Turismo/San Cristóbal: Un Delirio Turístico de Oportunidades'),
('2633', 4, 1, 4, 'San Cristóbal: Un Territorio de Oportunidades para la Gestión de Conflictos y la Convivencia'),
('2638', 4, 4, 24, 'San Cristóbal activa el sector cultural'),
('2648', 4, 2, 7, 'Oportunidades con Bien-Estar: San Cristóbal Avanza Más'),
('2667', 4, 5, 33, 'Gobierno de lo Cotidiano'),
('2694', 4, 5, 35, 'Redes de Oportunidad: Formación Digital y Participación Ciudadana'),
('2708', 4, 5, 39, 'Changó y territorios indígenas en resistencia'),
('2791', 4, 4, 30, 'Creciendo Juntos: Atención Integral y Oportunidades para la Comunidad'),
('2797', 4, 5, 39, 'San Cristóbal: Nuestra pasión'),
('2802', 4, 2, 12, 'Fortaleciendo Vidas: Mujeres en San Cristóbal por la Prevención y Autonomía'),
('2805', 4, 4, 25, 'San Cristóbal: Oportunidades para un Futuro Reverdecido')
)
INSERT INTO "proyecto" ("codigo_proyecto","id_localidad","id_programa","nombre_proyecto")
SELECT
  s."codigo_proyecto",
  s."id_localidad",
  p."id_programa",
  s."nombre_proyecto"
FROM src s
JOIN "objetivo_estrategico" o
  ON o."codigo_objetivo" = s."codigo_objetivo"
JOIN "programa" p
  ON p."id_objetivo" = o."id_objetivo"
 AND p."codigo_programa" = s."codigo_programa"
ON CONFLICT ("id_localidad","codigo_proyecto")
DO UPDATE SET
  "id_programa" = EXCLUDED."id_programa",
  "nombre_proyecto" = EXCLUDED."nombre_proyecto";


WITH src (
  "codigo_meta_extendida","codigo_proyecto","nombre_sector","codigo_indicador",
  "indicador_producto","descripcion_meta","componente_proyecto","linea_inversion",
  "concepto_gasto","componente_presupuestal","meta_total_2025_2028","tipo_anualizacion"
) AS (
  VALUES
  ('22511', '2251', 'CULTURA, RECREACIÓN Y DEPORTE', '56', 'Número de proyectos financiados y acompañados del sector cultural y creativo.', 'Financiar 120 proyectos del sector cultural y creativo.', 'SOSTENIBILIDAD', 'Bogotá cultural y deportiva', 'Sostenibilidad del ecosistema cultural y creativo', 'Presupuestos Participativos', 120, 'Suma'),
('22521', '2252', 'MOVILIDAD', '77', 'Kilómetros-carril construidos y/o conservados de malla vial urbana (local y/o intermedia)', 'Intervenir 17 Kilómetros-carril de malla vial urbana (local y/o intermedia) con acciones de construcción y/o conservación', 'INTERVENCIÓN MALLA VIAL LOCAL', 'Infraestructura segura e incluyente', 'Diseño, construcción y conservación (mantenimiento y rehabilitación) de la malla vial local e intermedia urbana o rural.', 'Presupuestos Participativos', 17, 'Suma'),
('22541', '2254', 'MOVILIDAD', '15', 'Metros cuadrados construidos y/o conservados de elementos del sistema de espacio público peatonal.', 'Intervenir 4.290 metros cuadrados de elementos del sistema de espacio público peatonal con acciones de construcción y/o conservación.', 'INTERVENCIÓN', 'Infraestructura segura e incluyente', 'Construcción y/o conservación de elementos del sistema de espacio público', 'Presupuestos Participativos', 4290, 'Suma'),
('22571', '2257', 'CULTURA, RECREACIÓN Y DEPORTE', '60', 'm2 de Parques de la red de proximidad construidos y dotados', 'Construir 880 m2 de Parques de la red de proximidad (la construcción incluye su dotación).', 'CONSTRUCCIÓN', 'Desarrollo urbano y rural integral', 'Construcción, mantenimiento y dotación de parques de la red de proximidad', 'Presupuestos Participativos', 880, 'Suma'),
('22572', '2257', 'CULTURA, RECREACIÓN Y DEPORTE', '61', 'Número de Parques de la red de proximidad intervenidos en mejoramiento, mantenimiento y/o dotación', 'Intervenir 32 Parques de la red de proximidad con acciones de mejoramiento, mantenimiento y/o dotación.', 'INTERVENCIÓN', 'Desarrollo urbano y rural integral', 'Construcción, mantenimiento y dotación de parques de la red de proximidad', 'Presupuestos Participativos', 32, 'Suma'),
('22731', '2273', 'AMBIENTE', '113', 'Número de obras de mitigación y/u obras de mitigación existentes con mantenimiento', 'Realizar 4 obras de mitigación y/u obras de mitigación existentes con mantenimiento', 'OBRAS DE MITIGACIÓN', 'Protección del ambiente y resiliencia al cambio climático', 'Manejo de emergencias y mitigación del riesgo de desastres', 'Gestión Pública Local', 4, 'Suma'),
('22732', '2273', 'AMBIENTE', '79', 'Número de acciones efectivas para el fortalecimiento de las capacidades locales en torno a la gestión del riesgo', 'Realizar 4 acciones efectivas para el fortalecimiento de las capacidades locales en torno a la gestión del riesgo', 'GESTIÓN DEL RIESGO', 'Protección del ambiente y resiliencia al cambio climático', 'Manejo de emergencias y mitigación del riesgo de desastres', 'Gestión Pública Local', 4, 'Suma'),
('22851', '2285', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '5', 'Dotaciones suministradas a organismos de seguridad', 'Intervenir 11 equipamientos de seguridad y acceso a la justicia con acciones de fortalecimiento, operación, adecuación y/o dotación', 'DOTACIÓN', 'Mejores capacidades al servicio de la seguridad', 'Dotación, mantenimiento de equipamientos que permitan el fortalecimiento de la seguridad y justicia.', 'Gestión Pública Local', 4, 'Suma'),
('22852', '2285', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '6', 'Equipamientos de seguridad y acceso a la justicia intervenidos con acciones de fortalecimiento, operación, adecuación y/o dotación', 'Suministrar 4 dotaciones a organismos de seguridad', 'INTERVENCIÓN', 'Mejores capacidades al servicio de la seguridad', 'Dotación, mantenimiento de equipamientos que permitan el fortalecimiento de la seguridad y justicia.', 'Gestión Pública Local', 11, 'Suma'),
('23161', '2316', 'SALUD', '20', 'Número de personas vinculadas a las acciones y estrategias para promover la salud sexual y reproductiva consciente en los diferentes ciclos de vida', 'Vincular 2.000 personas a las acciones y estrategias para promover la salud sexual y reproductiva consciente en los diferentes ciclos de vida', 'SALUD SEXUAL Y REPRODUCTIVA', 'Ciudad saludable y con bien-estar', 'Salud sexual y reproductiva consciente en adolescentes y jóvenes', 'Gestión Pública Local', 2000, 'Suma'),
('23162', '2316', 'SALUD', '23', 'Número de personas beneficiadas con acciones para la promoción y atención de la salud mental', 'Beneficiar 6.000 personas con acciones para la promoción y atención de la salud mental', 'SALUD MENTAL', 'Ciudad saludable y con bien-estar', 'Acciones para la promoción y atención de la salud mental', 'Presupuestos Participativos', 6000, 'Suma'),
('23163', '2316', 'SALUD', '22', 'Número de personas vinculadas en las acciones complementarias en salud física, nutricional y oral, a través del Circuito del Cuidado', 'Vincular 3.200 personas en acciones complementarias en salud física, nutricional y oral, a través del Circuito del Cuidado', 'SALUD FÍSICA Y NUTRICIONAL', 'Ciudad saludable y con bien-estar', 'Acciones complementarias en salud física y nutricional', 'Gestión Pública Local', 3200, 'Suma'),
('23164', '2316', 'SALUD', '19', 'Número de personas con discapacidad beneficiadas con Dispostivos de Asistencia Personal - Ayudas Técnicas (no incluidas en los Planes de Beneficios)', 'Beneficiar 2.000 personas con discapacidad a través de Dispositivos de Asistencia Personal - Ayudas Técnicas (no incluidas en los Planes de Beneficios)', 'DISPOSITIVOS DE ASISTENCIA PERSONAL', 'Ciudad saludable y con bien-estar', 'Otorgamiento de Dispositivos de asistencia Personal - DAP - a personas con discapacidad', 'Gestión Pública Local', 2000, 'Suma'),
('23165', '2316', 'SALUD', '18', 'Números de personas vinculadas a las acciones desarrolladas desde los dispositivos de base comunitaria en respuesta al consumo de SPA', 'Vincular 1.600 personas a las acciones desarrolladas desde los dispositivos de base comunitaria en respuesta al consumo de SPA', 'DISMINUCIÓN FACTORES DE RIESGO SPA', 'Ciudad saludable y con bien-estar', 'Acciones para la disminución de los factores de riesgo frente al consumo de sustancias psicoactivas.', 'Gestión Pública Local', 1600, 'Suma'),
('23166', '2316', 'SALUD', '17', 'Número de personas con discapacidad, cuidadadores y cuidadoras, vinculados en actividades complementarias en salud', 'Vincular 1.200 personas con discapacidad, cuidadores y cuidadoras, en actividades complementarias en salud', 'ACCIONES COMPLEMENTARIAS', 'Ciudad saludable y con bien-estar', 'Acciones complementarias para personas con discapacidad y sus cuidadores', 'Gestión Pública Local', 1200, 'Suma'),
('23491', '2349', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '16', 'Estrategias de seguridad y convivencia implementadas a través de gestores locales, que permitan el uso y disfrute del espacio público', 'Implementar 4 estrategias de seguridad y convivencia a través de gestores locales, que permitan el uso y disfrute del espacio público', 'ESTRATEGIAS DE SEGURIDAD Y CONVIVENCIA', 'Cultura ciudadana para la convivencia pacífica', 'Cultura ciudadana en torno a la seguridad', 'Gestión Pública Local', 4, 'Suma'),
('23851', '2385', 'MUJERES', '4', 'Número de Personas vinculadas en acciones para la prevención del feminicidio y la violencia contra la mujer', 'Vincular 6.000 personas en acciones para la prevención del feminicidio y la violencia contra la mujer.', 'PREVENCIÓN', 'Cero tolerancia a las violencias', 'Prevención del feminicidio y las violencias contra las mujeres', 'Presupuestos Participativos', 6000, 'Suma'),
('24051', '2405', 'CULTURA, RECREACIÓN Y DEPORTE', '33', 'Estímulos otorgados de apoyo al sector artístico y cultural', 'Otorgar 100 estímulos de apoyo al sector artístico y cultural.', 'ESTÍMULOS', 'Bogotá cultural y deportiva', 'Iniciativas de interés cultural, artístico, patrimonial y de cultura ciudadana.', 'Gestión Pública Local', 100, 'Suma'),
('24052', '2405', 'CULTURA, RECREACIÓN Y DEPORTE', '40', 'No. Organizaciones artísticas, culturales y patrimoniales beneficiadas con elementos entregados.', 'Beneficiar 60 organizaciones artísticas, culturales y patrimoniales con elementos entregados.', 'ENTREGA DE ELEMENTOS', 'Bogotá cultural y deportiva', 'Arte, cultura y patrimonio', 'Presupuestos Participativos', 60, 'Suma'),
('24053', '2405', 'CULTURA, RECREACIÓN Y DEPORTE', '38', 'Eventos de promoción, circulción y apropiación de actividades artísticas, culturales y patrimoniales realizadas', 'Realizar 80 eventos de promoción, circulción y apropiación de actividades artísticas, culturales y patrimoniales.', 'EVENTOS', 'Bogotá cultural y deportiva', 'Arte, cultura y patrimonio', 'Presupuestos Participativos', 80, 'Suma'),
('24054', '2405', 'CULTURA, RECREACIÓN Y DEPORTE', '39', 'Personas beneficiadas y capacitadas con procesos de formación y exploración en los campos artísticos, culturales y patrimoniales', 'Capacitar 1.480 personas en los campos artísticos, interculturales, culturales y/o patrimoniales.', 'CAPACITACIÓN', 'Bogotá cultural y deportiva', 'Arte, cultura y patrimonio', 'Presupuestos Participativos', 1480, 'Suma'),
('24091', '2409', 'GOBIERNO', '98', 'Personas capacitadas a través de procesos de formación para la participación de manera virtual y presencial.', 'Capacitar 2.600 personas a través de procesos de formación para la participación de manera virtual y presencial.', 'CAPACITACIÓN', 'Democracia deliberativa y participación', 'Procesos de formación en capacidades democráticas para la participación ciudadana incidente', 'Presupuestos Participativos', 2600, 'Suma'),
('24092', '2409', 'GOBIERNO', '99', 'Organizaciones comunales fortalecidas.', 'Fortalecer 100 organizaciones comunales.', 'FORTALECIMIENTO COMUNAL', 'Democracia deliberativa y participación', 'Fortalecimiento a organizaciones comunales', 'Gestión Pública Local', 100, 'Suma'),
('24093', '2409', 'GOBIERNO', '97', 'Organizaciones sociales e Instancias de participación ciudadana fortalecidas.', 'Fortalecer 200 Organizaciones sociales e Instancias de participación ciudadana.', 'FORTALECIMIENTO DE ORGANIZACIONES', 'Democracia deliberativa y participación', 'Fortalecimiento a organizaciones sociales y comunitarias y a instancias de participación.', 'Presupuestos Participativos', 200, 'Suma'),
('24811', '2481', 'AMBIENTE', '43', 'Número de personas vinculadas en acciones de educación en temas de protección y bienestar animal', 'Vincular 2.400 personas en acciones educativas en temas de protección y bienestar animal', 'ACCIONES PEDAGÓGICAS', 'Cuidado de la vida', 'Protección y bienestar animal', 'Presupuestos Participativos', 2400, 'Suma'),
('24812', '2481', 'AMBIENTE', '44', 'Número de animales atendidos por los programas de brigadas médicas, urgencias veterinarias y adopciones', 'Atender 10.000 animales en los programas de brigadas médicas, urgencias veterinarias y adopciones', 'BIENESTAR ANIMAL', 'Cuidado de la vida', 'Protección y bienestar animal', 'Presupuestos Participativos', 10000, 'Suma'),
('24813', '2481', 'AMBIENTE', '45', 'Número de animales esterilizados', 'Esterilizar 15.000 perros y gatos incluyendo los que está en condición de vulnerabilidad', 'ESTERILIZACIÓN', 'Cuidado de la vida', 'Protección y bienestar animal', 'Presupuestos Participativos', 15000, 'Suma'),
('24951', '2495', 'CULTURA, RECREACIÓN Y DEPORTE', '36', 'Personas capacitadas en los campos deportivos o recreativos', 'Capacitar 6.400 personas en los campos deportivos o recreativos', 'CAPACITACIÓN', 'Bogotá cultural y deportiva', 'Recreación y deporte', 'Presupuestos Participativos', 6400, 'Suma'),
('24952', '2495', 'CULTURA, RECREACIÓN Y DEPORTE', '37', 'Personas beneficiadas con la entrega de dotaciones deportivas.', 'Beneficiar 4.000 Personas con la entrega de dotaciones deportivas.', 'DOTACIÓN', 'Bogotá cultural y deportiva', 'Recreación y deporte', 'Presupuestos Participativos', 4000, 'Suma'),
('24953', '2495', 'CULTURA, RECREACIÓN Y DEPORTE', '34', 'Colectivos u organizaciones recreo deportivas inscritas en el Banco que implementan iniciativas de carácter barrial beneficiadas con apoyos economicos', 'Beneficiar 13.200 personas en actividades recreo-deportivas comunitarias.', 'BANCO DE INICIATIVAS', 'Bogotá cultural y deportiva', 'Recreación y deporte', 'Presupuestos Participativos', 120, 'Suma'),
('24954', '2495', 'CULTURA, RECREACIÓN Y DEPORTE', '35', 'Personas beneficiadas con actividades recreo-deportivas comunitarias', 'Beneficiar 120 colectivos u organizaciones recreo deportivas inscritas en el Banco que implementan iniciativas de carácter barrial con apoyos economicos', 'ACTIVIDADES RECREODEPORTIVAS', 'Bogotá cultural y deportiva', 'Recreación y deporte', 'Presupuestos Participativos', 13200, 'Suma'),
('25021', '2502', 'AMBIENTE', '71', 'Número de árboles mantenidos en zona urbana', 'Mantener 1.000 árboles en zona urbana', 'ARBOLADO', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 1000, 'Suma'),
('25024', '2502', 'HÁBITAT', '76', 'Personas capacitadas en separación en la fuente y reciclaje', 'Capacitar 6.000 personas en separación en la fuente y reciclaje.', 'SEPARACIÓN EN LA FUENTE', 'Protección del ambiente y resiliencia al cambio climático', 'Cambios de hábitos de consumo, separación en la fuente y reciclaje.', 'Presupuestos Participativos', 6000, 'Suma'),
('25025', '2502', 'AMBIENTE', '68', 'Número de huertas urbanas implementadas', 'Implementar 160 huertas urbanas', 'HUERTAS URBANAS', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 160, 'Constante'),
('25027', '2502', 'AMBIENTE', '70', 'Número de m2 de jardinería convencional y biodiversa mantenidos', 'Mantener 2.000 m2 de jardinería', 'JARDINERÍA', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 2000, 'Constante'),
('25061', '2506', 'INTEGRACIÓN SOCIAL', '49', 'Número de cupos habilitados para la atención de población en inseguridad alimentaria y nutricional del Distrito Capital, a través de comedores comunitarios.', 'Habilitar 300 cupos para la atención de población en inseguridad alimentaria y nutricional del Distrito Capital, a través de comedores comunitarios.', 'SEGURIDAD ALIMENTARIA', 'Menos pobreza', 'Comedores Comunitarios', 'Gestión Pública Local', 300, 'Suma'),
('26011', '2601', 'GOBIERNO', '14', 'Acuerdos realizados para la organización, la recuperación, el cuidado, el embellecimiento, la sostenibilidad, el mejoramiento y el aprovechamiento económico del espacio público.', 'Realizar 16 acuerdos para la organización, la recuperación, el cuidado, el embellecimiento, la sostenibilidad, el mejoramiento y el aprovechamiento económico del espacio público.', 'ACUERDOS', 'Cultura ciudadana para la convivencia pacífica', 'Acuerdos para el uso y aprovechamiento del espacio público', 'Presupuestos Participativos', 16, 'Suma'),
('26061', '2606', 'GESTIÓN PÚBLICA', '30', 'Procesos pedagógicos, artísticos, culturales, formativos o académicos realizados para el fortalecimiento de iniciativas ciudadanas para la apropiación social de la memoria, verdad, reparación integral a víctimas, paz y reconciliación.', 'Realizar 4 procesos pedagógicos, artísticos, culturales, formativos o para el fortalecimiento de iniciativas ciudadanas para la apropiación social de la memoria, verdad, reparación integral a víctimas, paz y reconciliación.', 'INICIATIVAS', 'Cuidado de la vida', 'Construcción de memoria, verdad, reparación, víctimas, paz y reconciliación', 'Presupuestos Participativos', 4, 'Suma'),
('26062', '2606', 'GESTIÓN PÚBLICA', '32', 'Procesos realizados para el fortalecimiento de habilidades y capacidades de la población víctima del conflicto armado o excombatientes que promuevan su participación en diferentes escenarios.', 'Realizar 4 procesos de fortalecimiento de habilidades y capacidades de la población víctima del conflicto armado o excombatientes para promover su partitipación en los diferentes escenarios.', 'FORTALECIMIENTO DE CAPACIDADES', 'Cuidado de la vida', 'Construcción de memoria, verdad, reparación, víctimas, paz y reconciliación', 'Presupuestos Participativos', 4, 'Suma'),
('26063', '2606', 'GESTIÓN PÚBLICA', '31', 'Acciones de construcción de paz realizadas que contribuyan al tejido social, la integración local, la sostenibilidad económica y/o desarrollo territorial para la reconciliación.', 'Realizar 4 acciones de construcción de paz que contribuyan al tejido social, la integración local, la sostenibilidad económica y/o desarrollo territorial para la reconciliación.', 'ACCIONES DE CONSTRUCCIÓN DE PAZ', 'Cuidado de la vida', 'Construcción de memoria, verdad, reparación, víctimas, paz y reconciliación', 'Presupuestos Participativos', 4, 'Suma'),
('26081', '2608', 'DESARROLLO ECONÓMICO, INDUSTRIA Y TURISMO', '58', 'Número de Mipymes, emprendimientos y/o actores de la economia informal apoyados para el fortalecimiento del tejido empresarial local.', 'Apoyar 800 Mipymes, emprendimientos y/o actores de la economia informal para el fortalecimiento del tejido empresarial local.', 'TEJIDO EMPRESARIAL LOCAL', 'Emprendimiento equitativo e incluyente', 'Fortalecimiento del tejido empresarial local', 'Presupuestos Participativos', 800, 'Suma'),
('26151', '2615', 'EDUCACIÓN', '50', 'Sedes educativas urbanas y rurales dotadas con recursos pedagógicos y/o tecnológicos', 'Dotar 61 sedes educativas urbanas y rurales con recursos pedagógicos y/o tecnológicos', 'DOTACIÓN', 'Educación como eje del potencial humano', 'Dotación de equipamientos para instituciones educativas públicas del distrito.', 'Gestión Pública Local', 61, 'Suma'),
('26152', '2615', 'EDUCACIÓN', '51', 'Número de estudiantes beneficiados con apoyo de sostenimiento para la permanencia en la educación posmedia (niveles de formación técnico profesional, tecnólogo, profesional universitario y educación para el trabajo y desarrollo humano).', 'Beneficiar 840 estudiantes con apoyo de sostenimiento para la permanencia en la educación posmedia (niveles de formación técnico profesional, tecnólogo, profesional universitario y educación para el trabajo y desarrollo humano).', 'SOSTENIMIENTO', 'Educación como eje del potencial humano', 'Apoyo para educación superior', 'Gestión Pública Local', 840, 'Suma'),
('26153', '2615', 'EDUCACIÓN', '52', 'Número de estudiantes beneficiados en programas de educación posmedia (niveles de formación técnico profesional, tecnólogo, profesional universitario y educación para el trabajo y desarrollo humano).', 'Beneficiar 840 estudiantes en programas de educación posmedia (niveles de formación técnico profesional, tecnólogo, profesional universitario y educación para el trabajo y desarrollo humano).', 'APOYO EDUCACIÓN POSMEDIA', 'Educación como eje del potencial humano', 'Apoyo para educación superior', 'Gestión Pública Local', 840, 'Suma'),
('26201', '2620', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '2', 'Acciones formativas diferenciales para la promoción de la convivencia ciudadana implementadas', 'Implementar 120 acciones formativas diferenciales para la promoción de la convivencia ciudadana', 'FORMACIÓN', 'Cultura ciudadana para la convivencia pacífica', 'Promoción de la convivencia ciudadana', 'Presupuestos Participativos', 120, 'Suma'),
('26202', '2620', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '3', 'Iniciativas de convivencia con participación ciudadana implementadas', 'Implementar 120 iniciativas de convivencia con participación de la ciudadanía', 'INICIATIVAS', 'Cultura ciudadana para la convivencia pacífica', 'Promoción de la convivencia ciudadana', 'Presupuestos Participativos', 120, 'Suma'),
('26203', '2620', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '1', 'Organizaciones comunitarias fortalecidas a través de capacidades para promover acciones de corresponsabilidad en la gestión de la seguridad y la convivencia', 'Fortalecer 100 organizaciones comunitarias a través de capacidades para promover acciones de corresponsabilidad en la gestión de la seguridad y la convivencia', 'FORTALECIMIENTO DE CAPACIDADES', 'Cultura ciudadana para la convivencia pacífica', 'Promoción de la convivencia ciudadana', 'Presupuestos Participativos', 100, 'Suma'),
('26271', '2627', 'DESARROLLO ECONÓMICO, INDUSTRIA Y TURISMO', '55', 'Número de Mipymes y/o emprendimientos orientados al fortalecimiento de las capacidades locales para la gestión y el desarrollo turístico apoyados.', 'Apoyar 120 Mipymes y/o emprendimientos orientados al fortalecimiento de las capacidades locales para la gestión y el desarrollo turístico', 'DESARROLLO TURÍSTICO', 'Emprendimiento equitativo e incluyente', 'Desarrollo turístico local', 'Presupuestos Participativos', 120, 'Suma'),
('26272', '2627', 'DESARROLLO ECONÓMICO, INDUSTRIA Y TURISMO', '54', 'Número de acciones realizadas para fortalecer las capacidades y/o habilidades, técnicas y blandas de las personas de la localidad, con el fin de mejorar el acceso a oportunidades de empleo.', 'Realizar 8 acciones para fortalecer las capacidades y/o habilidades, técnicas y blandas de las personas de la localidad, con el fin de mejorar el acceso a oportunidades de empleo.', 'FORTALECIMIENTO DE CAPACIDADES', 'Desarrollo empresarial, productividad y empleo', 'Fortalecimiento de habilidades para la empleabilidad - impulso al empleo local.', 'Presupuestos Participativos', 8, 'Suma'),
('26331', '2633', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '8', 'Actores comunitarios fortalecidos con herramientas y capacidades para la implementación de un enfoque restaurativo para la justicia y la convivencia', 'Fortalecer 1.600 actores comunitarios con herramientas y capacidades para la implementación de un enfoque restaurativo para la justicia y la convivencia', 'FORTALECIMIENTO DE CAPACIDADES', 'Cultura ciudadana para la convivencia pacífica', 'Acceso a la Justicia', 'Presupuestos Participativos', 1600, 'Suma'),
('26332', '2633', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '11', 'Proyectos comunitarios implementados en la localidad, para la apropiación del Código Nacional de Seguridad y Convivencia Ciudadana', 'Implementar 24 proyectos comunitarios en la localidad, para la apropiación del Código Nacional de Seguridad y Convivencia Ciudadana', 'CÓDIGO NACIONAL DE SEGURIDAD Y CONVIVENCIA', 'Cultura ciudadana para la convivencia pacífica', 'Acceso a la Justicia', 'Presupuestos Participativos', 24, 'Suma'),
('26333', '2633', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '10', 'Ciudadanos beneficiados con habilidades y capacidades para gestionar la convivencia constructivamente', 'Beneficiar 680 ciudadanos con habilidades y capacidades para gestionar la convivencia constructivamente', 'GESTIÓN DE LA CONVIVENCIA', 'Cultura ciudadana para la convivencia pacífica', 'Acceso a la Justicia', 'Presupuestos Participativos', 680, 'Suma'),
('26334', '2633', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '9', 'Proyectos de justicia local para la resolución efectiva de conflictividades de manera integral en el sistema de justicia implementados', 'Implementar 24 proyectos de justicia local para la resolución efectiva de conflictividades de manera integral en el sistema de justicia', 'RESOLUCIÓN DE CONFLICTIVIDADES', 'Cultura ciudadana para la convivencia pacífica', 'Acceso a la Justicia', 'Presupuestos Participativos', 24, 'Suma'),
('26335', '2633', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '13', 'Programas comunitarios con enfoque restaurativo para el cuidado del espacio público y del medio ambiente ejecutados', 'Ejecutar 4 programas comunitarios con enfoque restaurativo para el cuidado del espacio público y del medio ambiente', 'ACCIONES DE CUIDADO', 'Cultura ciudadana para la convivencia pacífica', 'Acceso a la Justicia', 'Presupuestos Participativos', 4, 'Suma'),
('26336', '2633', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '7', 'Programas de abordaje de conflictividad escolar para la convivencia con enfoque restaurativo fortalecidos', 'Fortalecer 4 programas de abordaje de conflictividad escolar para la convivencia con enfoque restaurativo', 'CONFLICTIVIDAD ESCOLAR', 'Cultura ciudadana para la convivencia pacífica', 'Acceso a la Justicia', 'Presupuestos Participativos', 4, 'Suma'),
('26337', '2633', 'SEGURIDAD, CONVIVENCIA Y JUSTICIA', '12', 'Acciones pedagógicas para la gestión de conflictividades y prevención de violencias implementadas', 'Implementar 80 acciones pedagógicas para la gestión de conflictividades y prevención de violencias', 'ACCIONES PEDAGÓGICAS', 'Cultura ciudadana para la convivencia pacífica', 'Acceso a la Justicia', 'Presupuestos Participativos', 80, 'Suma'),
('26381', '2638', 'CULTURA, RECREACIÓN Y DEPORTE', '62', 'No. de equipamientos culturales intervenidos con acciones de construcción, adecuación y/o dotación', 'Intervenir 4 equipamientos culturales con acciones de construcción, adecuación y/o dotación', 'INTERVENCIÓN', 'Desarrollo urbano y rural integral', 'Dotación de equipamientos culturales de escala local', 'Presupuestos Participativos', 4, 'Suma'),
('26481', '2648', 'INTEGRACIÓN SOCIAL', '46', 'Jóvenes beneficiados con transferencias condicionadas y acompañamiento psicosocial para la promoción al acceso y permanencia a oportunidades de formación y empleabilidad', 'Beneficiar 1.160 jóvenes con transferencias condicionadas y acompañamiento psicosocial para la promoción al acceso y permanencia a oportunidades de formación y empleabilidad', 'TRANSFERENCIAS MONETARIAS', 'Menos pobreza', 'Transferencias monetarias condicionadas para jóvenes', 'Gestión Pública Local', 1160, 'Suma'),
('26482', '2648', 'INTEGRACIÓN SOCIAL', '47', 'Personas atendidas con apoyos que contribuyan al ingreso mínimo garantizado', 'Atender 8.000 personas con apoyos que contribuyan al ingreso mínimo garantizado.', 'INGRESO MÍNIMO', 'Menos pobreza', 'Otras Transferencias Monetarias', 'Gestión Pública Local', 8000, 'Constante'),
('26483', '2648', 'INTEGRACIÓN SOCIAL', '48', 'Número de personas mayores con transferencias Monetarias', 'Beneficiar 6.250 personas mayores con transferencias monetarias', 'APOYO ECONÓMICO PERSONA MAYOR', 'Menos pobreza', 'Apoyo económico para persona mayor - tipo C', 'Gestión Pública Local', 6250, 'Constante'),
('26671', '2667', 'GOBIERNO', '93', 'Estrategias de fortalecimiento institucional realizadas', 'Realizar 4 estrategias de fortalecimiento institucional (una por vigencia).', 'FORTALECIMIENTO INSTITUCIONAL', 'Gobierno confiable', 'Fortalecimiento institucional', 'Gestión Pública Local', 4, 'Suma'),
('26672', '2667', 'GOBIERNO', '94', 'Estrategias de inspección, vigilancia y control realizada', 'Realizar 1 acciones de inspección, vigilancia y control.', 'IVC', 'Gobierno confiable', 'Inspección, vigilancia y control.', 'Gestión Pública Local', 1, 'Constante'),
('26941', '2694', 'GESTIÓN PÚBLICA', '95', 'Servicios TIC´s generados en zonas rurales y/o apartadas y urbanas', 'Operativizar 20 Centros de Acceso Comunitario en zonas rurales y/o apartadas y/o urbanas, con énfasis en Servicios TIC´s generados.', 'CONECTIVIDAD', 'Ciudad inteligente​', 'Conectividad y redes de comunicación.', 'Presupuestos Participativos', 20, 'Suma'),
('26942', '2694', 'GESTIÓN PÚBLICA', '96', 'Procesos de formacion y desarrollo de competencias digitales realizados en zonas rurales y/o apartadas y urbanas', 'Operativizar 20 Centros de Acceso Comunitario en zonas rurales y/o apartadas y/o urbanas, con énfasis en procesos de formación y desarrollo de competencias digitales.', 'FORTALECIMIENTO DE CAPACIDADES', 'Ciudad inteligente​', 'Conectividad y redes de comunicación.', 'Presupuestos Participativos', 20, 'Suma'),
('27081', '2708', 'GOBIERNO', '103', 'Iniciativa de inversión local concertada e implementada con los pueblos indígenas', 'Concertar e implementar cuatro (4) iniciativa de inversión local con los pueblos indígenas (aplica en todas las localidades con autoridades indígenas)', 'INICIATIVAS PUEBLO INDÍGENA', 'Línea diferencial étnica', 'Iniciativas diferenciales étnicas para comunidades Negras, Afrocolombianas, Raizales, Palenqueras, y los Pueblos Indígenas, Rrom o Gitano', 'Gestión Pública Local', 4, 'Suma'),
('27082', '2708', 'GOBIERNO', '104', 'Iniciativa de inversión local concertada e implementada con las comunidades negras, afrocolombianas y palenqueras', 'Concertar e implementar cuatro (4) iniciativa de inversión local con las comunidades negras, afrocolombianas y palenqueras (aplica en todas las localidades con autoridades NAP)', 'INICIATIVAS COMUNIDADES NEGRAS, AFROCOLOMBIANAS, PALENQUERAS', 'Línea diferencial étnica', 'Iniciativas diferenciales étnicas para comunidades Negras, Afrocolombianas, Raizales, Palenqueras, y los Pueblos Indígenas, Rrom o Gitano', 'Gestión Pública Local', 4, 'Suma'),
('27911', '2791', 'INTEGRACIÓN SOCIAL', '82', 'Unidades operativas orientadas a la atención de la primera infancia (Jardines Infantiles, Casas de Pensamiento Intercultural, Modalidad Espacios Rurales, Crecemos en la Ruralidad, Creciendo Juntos, Centros Amar) dotadas y/o acondicionadas', 'Dotar y/o acondicionar 16 unidades operativas orientadas a la atención de la primera infancia (Jardines Infantiles, Casas de Pensamiento Intercultural, Modalidad Espacios Rurales, Crecemos en la Ruralidad, Creciendo Juntos, Centros Amar, Centros Forjar)', 'DOTACIÓN', 'Desarrollo urbano y rural integral', 'Dotación, adecuación y mejoramiento a unidades operativas de servicios sociales de la SDIS', 'Presupuestos Participativos', 16, 'Suma'),
('27912', '2791', 'INTEGRACIÓN SOCIAL', '83', 'Unidades operativas de atención especializada (Centros Integrarte, Centros Crecer, Cadis) dotados y/o acondicionados', 'Dotar y/o acondicionar 2 unidades operativas de atención especializada (Centros Integrarte, Centros Crecer y Cadis)', 'DOTACIÓN', 'Desarrollo urbano y rural integral', 'Dotación, adecuación y mejoramiento a unidades operativas de servicios sociales de la SDIS', 'Presupuestos Participativos', 2, 'Suma'),
('27913', '2791', 'INTEGRACIÓN SOCIAL', '84', 'Unidades operativas orientadas a la atención de jóvenes (casas de la juventud, centros forjar) dotadas y/o acondicionadas', 'Dotar y/o acondicionar 1 unidades operativas orientadas a la atención de jóvenes (casas de la juventud, centros forjar)', 'DOTACIÓN', 'Desarrollo urbano y rural integral', 'Dotación, adecuación y mejoramiento a unidades operativas de servicios sociales de la SDIS', 'Presupuestos Participativos', 1, 'Suma'),
('27914', '2791', 'INTEGRACIÓN SOCIAL', '85', 'Sedes de Centros de Desarrollo Comunitarios dotados y/o acondicionados para la prestación de servicios sociales dirigidas al desarrollo de capacidades y generación de oportunidades.', 'Dotar y/o acondicionar 2 Centros de Desarrollo Comunitarios para la prestación de servicios sociales dirigidas al desarrollo de capacidades y generación de oportunidades', 'DOTACIÓN', 'Desarrollo urbano y rural integral', 'Dotación, adecuación y mejoramiento a unidades operativas de servicios sociales de la SDIS', 'Presupuestos Participativos', 2, 'Suma'),
('27915', '2791', 'INTEGRACIÓN SOCIAL', '87', 'Unidades operativas para la prestación de servicios sociales y la generación de estrategias dirigidas a personas habitantes de calle y/o en riesgo de estarlo (Hogares de paso, Autocuidado, SEDID, Atención Socio-sanitaria y Comunidad de Vida El Camino) dotadas y/o acondicionadas.', 'Dotar y/o acondicionar 1 unidades operativas para la prestación de servicios y la generación de estrategias dirigidas a personas habitantes de calle y/o en riesgo de estarlo (Hogares de paso, Autocuidado, SEDID, Atención Socio-saniatria y Comunidad de Vida El Camino)', 'DOTACIÓN', 'Desarrollo urbano y rural integral', 'Dotación, adecuación y mejoramiento a unidades operativas de servicios sociales de la SDIS', 'Presupuestos Participativos', 1, 'Suma'),
('27916', '2791', 'INTEGRACIÓN SOCIAL', '88', 'Unidades operativas orientadas a la prestación de servicios sociales a la persona mayor dotadas y/o acondicionadas', 'Dotar y/o acondicionar 2 unidades operativas orientadas a la prestación de servicios a la persona mayor', 'DOTACIÓN', 'Desarrollo urbano y rural integral', 'Dotación, adecuación y mejoramiento a unidades operativas de servicios sociales de la SDIS', 'Presupuestos Participativos', 2, 'Suma'),
('27971', '2797', 'GOBIERNO', '101', 'Unidades de innovación publica y social fortalecidas', 'Fortalecer 1 unidades de innovación publica y social a nivel local', 'INNOVACIÓN PÚBLICA', 'Gobierno confiable', 'Bogotaneidad', 'Gestión Pública Local', 1, 'Constante'),
('27972', '2797', 'GOBIERNO', '100', 'Acciones desarrolladas, orientadas a la ciudadanía en el marco de la estrategía Bogotaneidad', 'Desarrollar 4 acciones orientadas a la ciudadanía, en el marco de la estrategia "Bogotaneidad', 'ESTRATEGIA BOGOTANEIDAD', 'Gobierno confiable', 'Bogotaneidad', 'Gestión Pública Local', 4, 'Suma'),
('28021', '2802', 'INTEGRACIÓN SOCIAL', '25', 'Número de Personas que participan en procesos para la prevención de violencias en el contexto familiar y/o violencia sexual.', 'Vincular 4.000 personas en procesos para la prevención de violencias en el contexto familiar y/o violencia sexual', 'PREVENCIÓN', 'Cuidado de la vida', 'Prevención y atención de violencia intrafamiliar y sexual para poblaciones en situaciones de riesgo y vulnerabilidad de derechos', 'Presupuestos Participativos', 4000, 'Suma'),
('28022', '2802', 'MUJERES', '26', 'Mujeres cuidadoras vinculadas a estrategias de cuidado', 'Vincular 6.000 mujeres cuidadoras a estrategias de cuidado.', 'ESTRATEGIAS DE CUIDADO', 'Cuidado de la vida', 'Estrategias de cuidado a personas cuidadoras', 'Presupuestos Participativos', 6000, 'Suma'),
('28023', '2802', 'MUJERES', '28', 'Numero de espacios con adecuación y dotación en las manzanas del cuidado', 'Adecuar y dotar 2 espacios en las manzanas del cuidado', 'DOTACIÓN', 'Cuidado de la vida', 'Adecuación y dotación de manzanas del cuidado', 'Gestión Pública Local', 2, 'Suma'),
('28024', '2802', 'MUJERES', '27', 'Mujeres vinculadas para el ejercicio de derechos y el fortalecimiento de su autonomía económica', 'Vincular 1.600 mujeres para el ejercicio de derechos y el fortalecimiento de su autonomía económica', 'FORTALECIMIENTO DE CAPACIDADES', 'Cuidado de la vida', 'Fortalecimiento de capacidades para el ejercicio de derechos y para la autonomía económica de las mujeres.', 'Presupuestos Participativos', 1600, 'Suma'),
('28051', '2805', 'AMBIENTE', '66', 'Número de hectáreas de conectores ecosistémicos de la Estructura Ecológica Principal intervenidos', 'Intervenir 4 hectáreas de conectores ecosistémicos', 'CONECTORES ECOSISTÉMICOS', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 4, 'Suma'),
('28052', '2805', 'AMBIENTE', '65', 'Número de hectáreas de Estructura Ecológica Principal con acciones de conservación', 'Realizar acciones de conservación en 5 hectáreas de la Estructura Ecológica Principal', 'CONSERVACIÓN', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 5, 'Suma'),
('28053', '2805', 'AMBIENTE', '63', 'Número de m2 de áreas renaturalizadas', 'Generar 4.000 m2 de áreas renaturalizadas', 'RENATURALIZACIÓN', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 4000, 'Suma'),
('28054', '2805', 'AMBIENTE', '64', 'Número de hectáreas en proceso de restauración ecológica', 'Lograr 10 hectáreas en proceso de restauración ecológica', 'RESTAURACIÓN ECOLÓGICA', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 10, 'Suma'),
('250211', '2502', 'AMBIENTE', '67', 'Número de procesos comunitarios de educación ambiental implementados', 'Implementar 4 procesos comunitarios de educación ambiental que promueven la conservación de la biodiversidad y el agua', 'EDUCACIÓN AMBIENTAL', 'Protección del ambiente y resiliencia al cambio climático', 'Reverdecimeinto Urbano', 'Presupuestos Participativos', 4, 'Suma')
)
INSERT INTO "meta_proyecto" (
  "codigo_meta_extendida","id_proyecto","id_sector","codigo_indicador",
  "indicador_producto","descripcion_meta","componente_proyecto","linea_inversion",
  "concepto_gasto","componente_presupuestal","meta_total_2025_2028","tipo_anualizacion"
)
SELECT
  s."codigo_meta_extendida",
  p."id_proyecto",
  sec."id_sector",
  s."codigo_indicador",
  s."indicador_producto",
  s."descripcion_meta",
  s."componente_proyecto",
  s."linea_inversion",
  s."concepto_gasto",
  s."componente_presupuestal",
  s."meta_total_2025_2028",
  s."tipo_anualizacion"
FROM src s
JOIN "proyecto" p
  ON p."id_localidad" = 4
 AND p."codigo_proyecto" = s."codigo_proyecto"
JOIN "sector" sec
  ON sec."nombre_sector" = s."nombre_sector"
ON CONFLICT ("codigo_meta_extendida")
DO UPDATE SET
  "id_proyecto" = EXCLUDED."id_proyecto",
  "id_sector" = EXCLUDED."id_sector",
  "codigo_indicador" = EXCLUDED."codigo_indicador",
  "indicador_producto" = EXCLUDED."indicador_producto",
  "descripcion_meta" = EXCLUDED."descripcion_meta",
  "componente_proyecto" = EXCLUDED."componente_proyecto",
  "linea_inversion" = EXCLUDED."linea_inversion",
  "concepto_gasto" = EXCLUDED."concepto_gasto",
  "componente_presupuestal" = EXCLUDED."componente_presupuestal",
  "meta_total_2025_2028" = EXCLUDED."meta_total_2025_2028",
  "tipo_anualizacion" = EXCLUDED."tipo_anualizacion";


WITH src (
  "codigo_meta_extendida","vigencia","recurso_indicativo",
  "porcentaje_plan_plurianual","magnitud_programada","valor_poai",
  "porcentaje_recursos_poai","tiene_propuesta_pp","fecha_corte"
) AS (
  VALUES
  ('22511', 2025, NULL, NULL, 30, 1311806000, 0.010023593465814508, NULL, NULL),
('22521', 2025, NULL, NULL, 4.25, 18945103000, 0.1447607425488089, NULL, NULL),
('22541', 2025, NULL, NULL, 1230, 2099334000, 0.016041145234098816, NULL, NULL),
('22571', 2025, NULL, NULL, 220, 1511743000, 0.011551324858089396, NULL, NULL),
('22572', 2025, NULL, NULL, 8, 718661000, 0.005491334620923916, NULL, NULL),
('22731', 2025, NULL, NULL, 1, 4500000000, 0.034384787534258325, NULL, NULL),
('22732', 2025, NULL, NULL, 1, 500000000, 0.0038205319482509255, NULL, NULL),
('22851', 2025, NULL, NULL, 2, 1500000000, 0.011461595844752776, NULL, NULL),
('22852', 2025, NULL, NULL, 1, 2500000000, 0.019102659741254628, NULL, NULL),
('23161', 2025, NULL, NULL, 500, 600000000, 0.00458463833790111, NULL, NULL),
('23162', 2025, NULL, NULL, 1500, 1968265000, 0.015039638630248216, NULL, NULL),
('23163', 2025, NULL, NULL, 800, 600000000, 0.00458463833790111, NULL, NULL),
('23164', 2025, NULL, NULL, 500, 2091488000, 0.015981193446766864, NULL, NULL),
('23165', 2025, NULL, NULL, 400, 534667000, 0.004085424710350955, NULL, NULL),
('23166', 2025, NULL, NULL, 300, 700000000, 0.005348744727551295, NULL, NULL),
('23491', 2025, NULL, NULL, 1, 2356445000, 0.018005746813592304, NULL, NULL),
('23851', 2025, NULL, NULL, 1500, 2033800000, 0.015540395752705464, NULL, NULL),
('24051', 2025, NULL, NULL, 25, 625000000, 0.004775664935313657, NULL, NULL),
('24052', 2025, NULL, NULL, 15, 357664000, 0.0027329334774784378, NULL, NULL),
('24053', 2025, NULL, NULL, 20, 2379245000, 0.018179963070432546, NULL, NULL),
('24054', 2025, NULL, NULL, 370, 777531000, 0.0059411640525109805, NULL, NULL),
('24091', 2025, NULL, NULL, 650, 1639480000, 0.012527371437036854, NULL, NULL),
('24092', 2025, NULL, NULL, 25, 1547099000, 0.011821482313214117, NULL, NULL),
('24093', 2025, NULL, NULL, 50, 1639480000, 0.012527371437036854, NULL, NULL),
('24811', 2025, NULL, NULL, 600, 226595000, 0.0017314268736278368, NULL, NULL),
('24812', 2025, NULL, NULL, 2500, 757537000, 0.005788388620964323, NULL, NULL),
('24813', 2025, NULL, NULL, 3750, 984132000, 0.007519815494592159, NULL, NULL),
('24951', 2025, NULL, NULL, 1600, 1157411000, 0.008843851405514103, NULL, NULL),
('24952', 2025, NULL, NULL, 1000, 1003015000, 0.007664101704149804, NULL, NULL),
('24953', 2025, NULL, NULL, 3300, 1542844000, 0.011788969586334502, NULL, NULL),
('24954', 2025, NULL, NULL, 30, 770867000, 0.005890244002704692, NULL, NULL),
('25021', 2025, NULL, NULL, 250, 133291000, 0.0010184850478286282, NULL, NULL),
('25024', 2025, NULL, NULL, 1500, 1508411000, 0.011525864833186253, NULL, NULL),
('25025', 2025, NULL, NULL, 160, 443193000, 0.003386466031482345, NULL, NULL),
('25027', 2025, NULL, NULL, 2000, 206601000, 0.0015786514420811789, NULL, NULL),
('25061', 2025, NULL, NULL, 75, 717176000, 0.005479987641037611, NULL, NULL),
('26011', 2025, NULL, NULL, 4, 1901619000, 0.014530392285801953, NULL, NULL),
('26061', 2025, NULL, NULL, 1, 277690000, 0.0021218470334195987, NULL, NULL),
('26062', 2025, NULL, NULL, 1, 277690000, 0.0021218470334195987, NULL, NULL),
('26063', 2025, NULL, NULL, 1, 402095000, 0.0030724335874639116, NULL, NULL),
('26081', 2025, NULL, NULL, 200, 1311806000, 0.010023593465814508, NULL, NULL),
('26151', 2025, NULL, NULL, 15, 2778465000, 0.021230428599194013, NULL, NULL),
('26152', 2025, NULL, NULL, 210, 2500000000, 0.019102659741254628, NULL, NULL),
('26153', 2025, NULL, NULL, 210, 6500000000, 0.04966691532726203, NULL, NULL),
('26201', 2025, NULL, NULL, 30, 592034000, 0.004523769622901577, NULL, NULL),
('26202', 2025, NULL, NULL, 30, 592034000, 0.004523769622901577, NULL, NULL),
('26203', 2025, NULL, NULL, 25, 522057000, 0.003989070894616067, NULL, NULL),
('26271', 2025, NULL, NULL, 30, 1573945000, 0.012026614314579605, NULL, NULL),
('26272', 2025, NULL, NULL, 2, 1968265000, 0.015039638630248216, NULL, NULL),
('26331', 2025, NULL, NULL, 400, 396541000, 0.00302999511858274, NULL, NULL),
('26332', 2025, NULL, NULL, 6, 132180000, 0.0010099958258396147, NULL, NULL),
('26333', 2025, NULL, NULL, 170, 264361000, 0.002019999292743126, NULL, NULL),
('26334', 2025, NULL, NULL, 6, 132180000, 0.0010099958258396147, NULL, NULL),
('26335', 2025, NULL, NULL, 1, 197715000, 0.0015107529482968633, NULL, NULL),
('26336', 2025, NULL, NULL, 1, 197715000, 0.0015107529482968633, NULL, NULL),
('26337', 2025, NULL, NULL, 20, 448747000, 0.003428904500363516, NULL, NULL),
('26381', 2025, NULL, NULL, 1, 1311806000, 0.010023593465814508, NULL, NULL),
('26481', 2025, NULL, NULL, 290, 1954496000, 0.01493442882145728, NULL, NULL),
('26482', 2025, NULL, NULL, 8000, 2032948000, 0.015533885566265644, NULL, NULL),
('26483', 2025, NULL, NULL, 6250, 11000000000, 0.08405170286152036, NULL, NULL),
('26671', 2025, NULL, NULL, 1, 14298130000, 0.10925292493049, NULL, NULL),
('26672', 2025, NULL, NULL, 1, 3000000000, 0.022923191689505552, NULL, NULL),
('26941', 2025, NULL, NULL, 5, 1110759000, 0.008487380492614499, NULL, NULL),
('26942', 2025, NULL, NULL, 5, 528721000, 0.004039990944422355, NULL, NULL),
('27081', 2025, NULL, NULL, 1, 900000000, 0.006876957506851665, NULL, NULL),
('27082', 2025, NULL, NULL, 1, 900000000, 0.006876957506851665, NULL, NULL),
('27911', 2025, NULL, NULL, 3, 649794000, 0.004965117473563523, NULL, NULL),
('27912', 2025, NULL, NULL, 0, 0, 0, NULL, NULL),
('27913', 2025, NULL, NULL, 0, 0, 0, NULL, NULL),
('27914', 2025, NULL, NULL, 0, 0, 0, NULL, NULL),
('27915', 2025, NULL, NULL, 1, 648683000, 0.00495662825157451, NULL, NULL),
('27916', 2025, NULL, NULL, 0, 0, 0, NULL, NULL),
('27971', 2025, NULL, NULL, 1, 200000000, 0.00152821277930037, NULL, NULL),
('27972', 2025, NULL, NULL, 1, 600000000, 0.00458463833790111, NULL, NULL),
('28021', 2025, NULL, NULL, 1000, 1311806000, 0.010023593465814508, NULL, NULL),
('28022', 2025, NULL, NULL, 1500, 1770550000, 0.013528885681951352, NULL, NULL),
('28023', 2025, NULL, NULL, 0, 0, 0, NULL, NULL),
('28024', 2025, NULL, NULL, 400, 2020470000, 0.015438540370965094, NULL, NULL),
('28051', 2025, NULL, NULL, 1, 58870000, 0.00044982943158706394, NULL, NULL),
('28052', 2025, NULL, NULL, 1.25, 58870000, 0.00044982943158706394, NULL, NULL),
('28053', 2025, NULL, NULL, 1000, 158839000, 0.0012136989482564575, NULL, NULL),
('28054', 2025, NULL, NULL, 2.5, 295462000, 0.00225764402098823, NULL, NULL),
('250211', 2025, NULL, NULL, 1, 206601000, 0.0015786514420811789, NULL, NULL),
('22511', 2026, 1215000000, 0.009975369458128078, 30, 1185000000, 0.009280253312541389, TRUE, NULL),
('22521', 2026, 17554000000, 0.1441215106732348, 4.25, 17500000000, 0.13705015440461968, TRUE, NULL),
('22541', 2026, 1945000000, 0.0159688013136289, 1230, 2500000000, 0.019578593486374238, FALSE, NULL),
('22571', 2026, 1401000000, 0.011502463054187192, 220, 1100000000, 0.008614581134004665, TRUE, NULL),
('22572', 2026, 665000000, 0.005459770114942529, 8, 1085240000, 0.008498989118061111, TRUE, NULL),
('22731', 2026, 1858000000, 0.015254515599343186, 1, 1900000000, 0.01487973104964442, TRUE, NULL),
('22732', 2026, 515000000, 0.004228243021346469, 1, 600000000, 0.004698862436729817, FALSE, NULL),
('22851', 2026, 1858000000, 0.015254515599343186, 3, 1200000000, 0.009397724873459634, FALSE, NULL),
('22852', 2026, 1029000000, 0.008448275862068965, 1, 2000000000, 0.01566287478909939, FALSE, NULL),
('23161', 2026, 566000000, 0.00464696223316913, 500, 500000000, 0.0039157186972748476, TRUE, NULL),
('23162', 2026, 1824000000, 0.01497536945812808, 1500, 1800000000, 0.014096587310189451, FALSE, NULL),
('23163', 2026, 818000000, 0.006715927750410509, 800, 600000000, 0.004698862436729817, TRUE, NULL),
('23164', 2026, 2153000000, 0.017676518883415437, 500, 2200000000, 0.01722916226800933, TRUE, NULL),
('23165', 2026, 550000000, 0.00451559934318555, 400, 500000000, 0.0039157186972748476, TRUE, NULL),
('23166', 2026, 669000000, 0.0054926108374384235, 300, 700000000, 0.005482006176184787, TRUE, NULL),
('23491', 2026, 2425000000, 0.01990968801313629, 1, 2400000000, 0.01879544974691927, TRUE, NULL),
('23851', 2026, 1884000000, 0.015467980295566503, 1500, 1900000000, 0.01487973104964442, FALSE, NULL),
('24051', 2026, 643000000, 0.005279146141215107, 25, 600000000, 0.004698862436729817, TRUE, NULL),
('24052', 2026, 331000000, 0.002717569786535304, 15, 635000000, 0.004972962745539057, TRUE, NULL),
('24053', 2026, 2205000000, 0.01810344827586207, 20, 3100000000, 0.024277455923104055, TRUE, NULL),
('24054', 2026, 722000000, 0.005927750410509031, 370, 750000000, 0.005873578045912271, TRUE, NULL),
('24091', 2026, 1519000000, 0.012471264367816093, 650, 1600000000, 0.012530299831279512, TRUE, NULL),
('24092', 2026, 823000000, 0.006756978653530378, 25, 1000000000, 0.007831437394549695, TRUE, NULL),
('24093', 2026, 1519000000, 0.012471264367816093, 50, 1600000000, 0.012530299831279512, FALSE, NULL),
('24811', 2026, 210000000, 0.0017241379310344827, 600, 210000000, 0.001644601852855436, TRUE, NULL),
('24812', 2026, 702000000, 0.005763546798029557, 2500, 750000000, 0.005873578045912271, TRUE, NULL),
('24813', 2026, 912000000, 0.00748768472906404, 3750, 950000000, 0.00743986552482221, TRUE, NULL),
('24951', 2026, 1072000000, 0.008801313628899837, 1600, 1000000000, 0.007831437394549695, FALSE, NULL),
('24952', 2026, 929000000, 0.007627257799671593, 1000, 1300000000, 0.010180868612914604, FALSE, NULL),
('24953', 2026, 715000000, 0.005870279146141215, 3300, 1700000000, 0.013313443570734482, TRUE, NULL),
('24954', 2026, 1429000000, 0.011732348111658457, 30, 700000000, 0.005482006176184787, FALSE, NULL),
('25021', 2026, 123000000, 0.0010098522167487686, 250, 130000000, 0.0010180868612914603, TRUE, NULL),
('25024', 2026, 1398000000, 0.01147783251231527, 1500, 1800000000, 0.014096587310189451, TRUE, NULL),
('25025', 2026, 410000000, 0.0033661740558292284, 160, 350000000, 0.0027410030880923933, TRUE, NULL),
('25027', 2026, 191000000, 0.0015681444991789818, 2000, 200000000, 0.001566287478909939, FALSE, NULL),
('25061', 2026, 532000000, 0.004367816091954023, 75, 200000000, 0.001566287478909939, FALSE, NULL),
('26011', 2026, 1762000000, 0.014466338259441708, 4, 2000000000, 0.01566287478909939, FALSE, NULL),
('26061', 2026, 257000000, 0.002110016420361248, 1, 250000000, 0.0019578593486374238, TRUE, NULL),
('26062', 2026, 257000000, 0.002110016420361248, 1, 250000000, 0.0019578593486374238, TRUE, NULL),
('26063', 2026, 373000000, 0.0030623973727422005, 1, 350000000, 0.0027410030880923933, TRUE, NULL),
('26081', 2026, 1215000000, 0.009975369458128078, 200, 1500000000, 0.011747156091824543, TRUE, NULL),
('26151', 2026, 2316000000, 0.019014778325123154, 15, 2300000000, 0.0180123060074643, FALSE, NULL),
('26152', 2026, 2573000000, 0.021124794745484402, 210, 2600000000, 0.020361737225829207, TRUE, NULL),
('26153', 2026, 6690000000, 0.05492610837438423, 210, 6600000000, 0.05168748680402799, TRUE, NULL),
('26201', 2026, 548000000, 0.004499178981937603, 30, 300000000, 0.0023494312183649085, TRUE, NULL),
('26202', 2026, 548000000, 0.004499178981937603, 30, 600000000, 0.004698862436729817, FALSE, NULL),
('26203', 2026, 484000000, 0.003973727422003284, 25, 600000000, 0.004698862436729817, FALSE, NULL),
('26271', 2026, 1459000000, 0.011978653530377668, 30, 900000000, 0.007048293655094726, TRUE, NULL),
('26272', 2026, 1824000000, 0.01497536945812808, 2, 2000000000, 0.01566287478909939, TRUE, NULL),
('26331', 2026, 367000000, 0.003013136288998358, 400, 400000000, 0.003132574957819878, FALSE, NULL),
('26332', 2026, 122000000, 0.0010016420361247948, 6, 100000000, 0.0007831437394549695, FALSE, NULL),
('26333', 2026, 245000000, 0.002011494252873563, 170, 250000000, 0.0019578593486374238, FALSE, NULL),
('26334', 2026, 122000000, 0.0010016420361247948, 6, 100000000, 0.0007831437394549695, FALSE, NULL),
('26335', 2026, 184000000, 0.0015106732348111659, 1, 250000000, 0.0019578593486374238, FALSE, NULL),
('26336', 2026, 184000000, 0.0015106732348111659, 1, 150000000, 0.0011747156091824543, FALSE, NULL),
('26337', 2026, 416000000, 0.0034154351395730706, 20, 350000000, 0.0027410030880923933, FALSE, NULL),
('26381', 2026, 1215000000, 0.009975369458128078, 1, 1000000000, 0.007831437394549695, TRUE, NULL),
('26481', 2026, 1712000000, 0.01405582922824302, 290, 498800000, 0.003906320972401388, TRUE, NULL),
('26482', 2026, 1344000000, 0.011034482758620689, 8000, 4379922000, 0.03430108493601089, TRUE, NULL),
('26483', 2026, 11321000000, 0.09294745484400657, 6250, 13500000000, 0.10572440482642088, FALSE, NULL),
('26671', 2026, 14434000000, 0.11850574712643679, 1, 13963518000, 0.10935441702466778, FALSE, NULL),
('26672', 2026, 3088000000, 0.02535303776683087, 1, 3088000000, 0.02418347867436946, FALSE, NULL),
('26941', 2026, 1029000000, 0.008448275862068965, 5, 1000000000, 0.007831437394549695, FALSE, NULL),
('26942', 2026, 1029000000, 0.008448275862068965, 5, 500000000, 0.0039157186972748476, TRUE, NULL),
('27081', 2026, 823000000, 0.006756978653530378, 1, 842000000, 0.006594070286210844, FALSE, NULL),
('27082', 2026, 823000000, 0.006756978653530378, 1, 823000000, 0.006445272975714399, FALSE, NULL),
('27911', 2026, 403000000, 0.003308702791461412, 2, 500000000, 0.0039157186972748476, FALSE, NULL),
('27912', 2026, 200000000, 0.0016420361247947454, 1, 200000000, 0.001566287478909939, FALSE, NULL),
('27913', 2026, 0, 0, 0, 0, 0, FALSE, NULL),
('27914', 2026, 400000000, 0.003284072249589491, 1, 400000000, 0.003132574957819878, FALSE, NULL),
('27915', 2026, 0, 0, 0, 0, 0, FALSE, NULL),
('27916', 2026, 200000000, 0.0016420361247947454, 1, 300000000, 0.0023494312183649085, FALSE, NULL),
('27971', 2026, 206000000, 0.001691297208538588, 1, 200000000, 0.001566287478909939, FALSE, NULL),
('27972', 2026, 412000000, 0.003382594417077176, 1, 400000000, 0.003132574957819878, FALSE, NULL),
('28021', 2026, 1215000000, 0.009975369458128078, 1000, 1000000000, 0.007831437394549695, TRUE, NULL),
('28022', 2026, 1641000000, 0.013472906403940887, 1500, 1800000000, 0.014096587310189451, FALSE, NULL),
('28023', 2026, 450000000, 0.003694581280788177, 1, 250000000, 0.0019578593486374238, TRUE, NULL),
('28024', 2026, 1872000000, 0.015369458128078817, 400, 2000000000, 0.01566287478909939, TRUE, NULL),
('28051', 2026, 55000000, 0.000451559934318555, 1, 100000000, 0.0007831437394549695, FALSE, NULL),
('28052', 2026, 55000000, 0.000451559934318555, 1.25, 100000000, 0.0007831437394549695, FALSE, NULL),
('28053', 2026, 148000000, 0.0012151067323481117, 1000, 200000000, 0.001566287478909939, FALSE, NULL),
('28054', 2026, 274000000, 0.0022495894909688014, 2.5, 300000000, 0.0023494312183649085, FALSE, NULL),
('250211', 2026, 191000000, 0.0015681444991789818, 1, 250000000, 0.0019578593486374238, FALSE, NULL)
)
INSERT INTO "poai" (
  "id_meta","vigencia","recurso_indicativo","porcentaje_plan_plurianual",
  "magnitud_programada","valor_poai","porcentaje_recursos_poai",
  "tiene_propuesta_pp","fecha_corte"
)
SELECT
  m."id_meta",
  s."vigencia",
  s."recurso_indicativo",
  s."porcentaje_plan_plurianual",
  s."magnitud_programada",
  s."valor_poai",
  s."porcentaje_recursos_poai",
  s."tiene_propuesta_pp",
  s."fecha_corte"::date
FROM src s
JOIN "meta_proyecto" m
  ON m."codigo_meta_extendida" = s."codigo_meta_extendida"
ON CONFLICT ("id_meta","vigencia")
DO UPDATE SET
  "recurso_indicativo" = EXCLUDED."recurso_indicativo",
  "porcentaje_plan_plurianual" = EXCLUDED."porcentaje_plan_plurianual",
  "magnitud_programada" = EXCLUDED."magnitud_programada",
  "valor_poai" = EXCLUDED."valor_poai",
  "porcentaje_recursos_poai" = EXCLUDED."porcentaje_recursos_poai",
  "tiene_propuesta_pp" = EXCLUDED."tiene_propuesta_pp",
  "fecha_corte" = EXCLUDED."fecha_corte";


COMMIT;
