CARGA CRP - SAN CRISTÓBAL
==========================

FUENTE
------
datos_abiertos_presupuesto_comprometido_xmeta_pp_01-10-2026.ods

La metadata oficial del propio archivo describe el conjunto como información
que relaciona los registros presupuestales con metas de presupuestos
participativos y las propuestas financiadas con dichos recursos.

PERFILAMIENTO SAN CRISTÓBAL
---------------------------
Filas fuente: 66
CRP distintos: 31
Metas distintas: 45
Pares CRP-meta distintos: 58
Líneas CRP-meta conservadas: 66
Relaciones CRP-propuesta únicas: 177
Propuestas financiadas distintas: 133
Valor total de las 66 líneas: $39,514,916,879 COP

INTEGRIDAD
----------
- Las 133 propuestas referenciadas ya existen en propuesta_ciudadana.
- No existen propuestas CRP apuntando a una meta distinta de su meta canónica.
- 35 propuestas están financiadas por más de un CRP.
- Una propuesta puede relacionarse hasta con 3 CRP en este corte.

CÓMO ENTENDER LAS TRES TABLAS
-----------------------------

1. crp
   Representa el certificado/compromiso presupuestal.
   Hay una fila por No_CRP + vigencia.
   Los atributos contractuales (fecha, compromiso, plazo, objeto, modalidad)
   son estables dentro de cada CRP.

2. crp_meta
   NO es una simple tabla puente.
   Representa líneas de asignación presupuestal de un CRP hacia una meta.
   Por eso contiene valor_asignado_pp y tiene su propia PK id_crp_meta.

   En la fuente existen 4 combinaciones CRP-meta repetidas con montos
   diferentes. No son descartadas ni consolidadas al cargar: se preservan
   las 66 líneas exactamente como están en la fuente.

   Para análisis se crea la vista vw_crp_meta_resumen, que consolida a
   58 pares CRP-meta y suma sus valores.

3. crp_propuesta
   Es una tabla puente N:M.
   El campo fuente Codigo_propuestas_financiadas_CRP trae varios códigos
   separados por punto y coma. La carga los separa y crea un registro por
   CRP-propuesta. Tras eliminar repeticiones de la lista fuente quedan
   177 relaciones únicas.

AJUSTE DE MODELO IDENTIFICADO
-----------------------------
Se identificó un dato de referencia que el modelo estaba perdiendo:
Entidad.

Las fuentes de propuestas y CRP muestran una entidad relacionada con cada
meta y la asociación es consistente en ambos conjuntos analizados.

Se agrega:
- entidad(id_entidad, nombre_entidad)
- meta_proyecto.id_entidad [nullable]

Se cargan 16 entidades y se asignan a 46 metas PP.
Las demás metas permanecen NULL porque no debemos inventar la entidad.

ORDEN DE EJECUCIÓN
------------------
1. sql/00_ajuste_entidad.sql
2. sql/01_carga_crp.sql
3. sql/02_validar_crp.sql

AJUSTE EN DBDIAGRAM.IO
----------------------
Ver AJUSTE_DBML_ENTIDAD.txt

IMPORTANTE SOBRE crp_meta
-------------------------
Mantener SIN:
    (id_crp, id_meta) [unique]

La duplicidad de ese par existe en la fuente y contiene montos diferentes.
La unicidad artificial eliminaría información válida.

IDEMPOTENCIA
------------
El script puede ejecutarse nuevamente:
- crp hace UPSERT por numero_crp + vigencia.
- crp_meta y crp_propuesta se reemplazan para los CRP del snapshot.
