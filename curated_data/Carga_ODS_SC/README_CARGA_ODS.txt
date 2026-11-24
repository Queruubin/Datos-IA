CARGA ODS - SAN CRISTÓBAL
=========================

FUENTE
------
archivo_plano_ods_fdl_corte_30_junio_2026.xlsx

PERFILAMIENTO
-------------
Registros San Cristóbal: 83
Metas de proyecto distintas: 83
ODS distintos: 13
Metas ODS distintas: 30
Relaciones meta_proyecto ↔ meta_ods: 83

INTEGRIDAD
----------
- El código extendido se reconstruye concatenando:
    Código Proyecto + Código meta proyecto SEGPLAN
  Ejemplo:
    Proyecto 2349 + Meta 1 = 23491

- Los 83 códigos reconstruidos existen en meta_proyecto.
- No hay duplicados entre las 83 metas.
- Cada código de meta ODS tiene una sola descripción y pertenece a un solo ODS.
- Cada ODS tiene un único nombre y esfera.
- El sector relacionado en el archivo ODS coincide 83/83 con el sector ya
  asociado a meta_proyecto.

DECISIÓN DE MODELADO
--------------------
No se requiere ajuste del DBML.

Se utilizan las tres tablas ya previstas:
1. ods
   Catálogo de Objetivos de Desarrollo Sostenible.

2. meta_ods
   Metas ODS del CONPES 3918 de 2018.

3. meta_ods_relacion
   Tabla puente entre las metas de proyecto de San Cristóbal y las metas ODS.

En el corte actual cada meta de proyecto aparece relacionada con una sola meta
ODS. Sin embargo, se conserva la tabla puente N:M porque el modelo lógico permite
futuros casos donde una meta institucional pueda alinearse con más de una meta ODS.

POR QUÉ NO CARGAMOS LOS CAMPOS FINANCIEROS DEL ARCHIVO ODS
----------------------------------------------------------
El archivo ODS también repite:
- magnitud programada
- magnitud contratada
- magnitud entregada
- apropiación
- compromisos
- giros

Esos hechos ya están modelados y cargados en:
- poai
- seguimiento_meta (PMR)

Cargarlos nuevamente dentro del dominio ODS duplicaría hechos financieros,
aumentaría el riesgo de inconsistencias y dificultaría el linaje.

Por tanto, el bloque ODS se usa exclusivamente como CAPA DE ALINEACIÓN
ESTRATÉGICA.

ORDEN DE EJECUCIÓN EN DBEAVER
-----------------------------
1. sql/01_carga_ods.sql
2. sql/02_validar_ods.sql

RESULTADOS ESPERADOS
--------------------
ods: 13
meta_ods: 30
meta_ods_relacion: 83
metas con ODS: 83
metas sin ODS: 0

VISTA CREADA
------------
vw_meta_ods_detalle

Esta vista permite consultar directamente:
Meta de proyecto → Meta ODS → ODS → Esfera
sin que Power BI tenga que reconstruir los joins.
