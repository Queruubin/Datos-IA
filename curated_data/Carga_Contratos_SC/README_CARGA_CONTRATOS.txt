CARGA CONTRATOS SECOP II - SAN CRISTÓBAL
========================================

FUENTE
------
csv/Consulta_agente_San_Cristobal_2025_2026.csv
Contratos de la Alcaldía Local de San Cristóbal publicados en SECOP II (vigencias 2025 y
2026), vinculados por el equipo a proyectos, metas y CRP. El archivo se conserva sin cambios.

GRANO
-----
Una fila por vínculo contrato ↔ (proyecto, meta, CRP). Un contrato puede tener varias filas:
el VALOR COMPLETO del contrato se repite en cada una.

PERFILAMIENTO
-------------
Filas (vínculos): 3.853
Contratos distintos (ID Contrato): 1.936
Contratos con más de un vínculo: 1.318
Vínculos con proyecto verificado: 2.091 (los 1.762 pendientes no traen código de proyecto)
Vínculos con meta verificada: 1.034 (los 2.819 pendientes no traen código de meta)
Contratos con valor 0: 45
Valor total (un valor por contrato): $204.352.632.384
Sumar las filas daría $480.841.384.658: por eso se deduplica por contrato antes de sumar.

DECISIÓN DE MODELADO
--------------------
1. contrato
   Una fila por ID Contrato: referencia, vigencia, fecha de firma, objeto, valor, estado
   (normalizado: 'cedido' → 'Cedido', 'terminado' → 'Terminado') y enlaces públicos.
2. contrato_vinculo
   Una fila por vínculo: código de proyecto, vigencia del proyecto, código de meta, número y
   vigencia del CRP, estado del vínculo con el proyecto y con la meta, y motivo de verificación.

Los nombres de proyecto y meta se toman del modelo (meta_proyecto / proyecto), no del archivo.
Los números de CRP de este archivo NO se cruzan con la tabla crp (que solo tiene CRP de
Presupuestos Participativos).

PRIVACIDAD
----------
La columna Contratista contiene nombres de personas naturales (contratos de prestación de
servicios). NO se lee ni se carga en ninguna tabla.

ADVERTENCIAS
------------
- El valor es el valor firmado del contrato, no lo ejecutado ni lo pagado.
- Un vínculo "Pendiente de verificación" no está confirmado.
- Un contrato vinculado a varios proyectos o metas aparece en cada uno: los valores por grupo
  se solapan y no se deben sumar entre sí.

RESULTADOS ESPERADOS
--------------------
Ver manifest.json.
