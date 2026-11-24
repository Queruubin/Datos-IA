CARGA PRESUPUESTOS PARTICIPATIVOS - SAN CRISTÓBAL
=================================================

FUENTES UTILIZADAS
------------------
1. datos_abiertos_presupuestos_participativos_corte_31-marzo_2026.xlsx
2. datos_abiertos_avance_propuestas_priorizadas_pp_01-10-2026.ods

RESULTADO DEL PERFILAMIENTO
---------------------------
- Propuestas San Cristóbal: 232
- Códigos de propuesta únicos: 232
- Metas distintas asociadas: 46
- Todas las 46 metas existen en meta_proyecto.
- Las mismas 232 propuestas aparecen en ambos cortes.
- Cambios de estado entre marzo y octubre: 22
- Cambios en texto de avance entre marzo y octubre: 68

DECISIÓN DE MODELADO
--------------------
No se requiere ajuste estructural adicional.

La separación ya definida funciona correctamente:
- propuesta_ciudadana = identidad y atributos relativamente estables.
- seguimiento_propuesta = información temporal por fecha de corte.

Por ello se cargan DOS snapshots:
- 2026-03-31: 232 seguimientos
- 2026-10-01: 232 seguimientos
Total: 464 seguimientos

TRANSFORMACIONES DE CALIDAD
---------------------------
1. Se normalizaron espacios repetidos en textos.
2. Metodología se estandarizó:
   - D. General -> Diálogo General
   - D. Diferencial -> Diálogo Diferencial
   - Transforma Lo Local -> Transforma lo Local
   Resultado: 4 categorías canónicas.
3. El valor "-" en Clasif_Poblacional se convirtió a NULL porque en ambos
   cortes aparece en las 232 propuestas y no aporta una clasificación real.
4. fecha_corte no existe como columna en las fuentes; se deriva del nombre y
   fecha declarada de cada archivo:
   - 31/03/2026
   - 01/10/2026
5. Tipo_acuerdo se conserva como texto fuente. No se convierte en catálogo:
   presenta alta variedad y contenido libre, por lo que no hay soporte para
   tratarlo como dato de referencia controlado.

ORDEN DE EJECUCIÓN EN DBEAVER
-----------------------------
1. sql/01_carga_presupuestos_participativos.sql
2. sql/02_validar_carga_pp.sql

RESULTADOS ESPERADOS
--------------------
propuesta_ciudadana: 232
seguimiento_propuesta: 464
metas con propuestas: 46
cambios de estado entre cortes: 22

IMPORTANTE
----------
El script de carga es idempotente:
- propuesta_ciudadana actualiza por codigo_propuesta.
- seguimiento_propuesta actualiza por id_propuesta + fecha_corte.
Por tanto, puede ejecutarse nuevamente sin duplicar registros.
