CARGA BASE POAI - SAN CRISTÓBAL
================================

FUENTES
-------
- POAI_San_Cristobal_2025_Homologado.xlsx
- POAI_San_Cristobal_2026(2).xlsx

HALLAZGO PREVIO A LA CARGA
--------------------------
El perfilamiento mostró que el campo Sector NO depende funcionalmente de Proyecto:
- Proyecto 2502: AMBIENTE / HÁBITAT
- Proyecto 2802: INTEGRACIÓN SOCIAL / MUJERES

Por esta razón, id_sector se mueve de proyecto a meta_proyecto.

ORDEN DE EJECUCIÓN EN DBEAVER
-----------------------------
1. sql/00_ajuste_sector_meta.sql
2. sql/01_carga_base_poai.sql
3. sql/02_validar_carga_base_poai.sql

RESULTADOS ESPERADOS
--------------------
Localidades: 1
Sectores: 12
Objetivos estratégicos: 5
Programas: 23
Proyectos: 31
Metas: 83
POAI 2025: 83 registros
POAI 2026: 83 registros
Total POAI 2025: $130,871,828,000
Total POAI 2026: $127,690,480,000

REGLA FINANCIERA APLICADA
-------------------------
El campo de fuente 2026 "Recurso Indicativo 2026 (Plan Plurianual- cifras en millones)"
se estandarizó a PESOS COLOMBIANOS en la columna poai.recurso_indicativo, multiplicando
el valor fuente por 1.000.000. El campo valor_poai ya viene en pesos.

CSV
---
La carpeta csv contiene las versiones normalizadas usadas para construir el script SQL.
Sirven como evidencia de transformación y control, aunque la carga recomendada en esta
etapa es ejecutar 01_carga_base_poai.sql directamente en DBeaver.

NOTA PARA DBDIAGRAM.IO
----------------------
Actualizar también el modelo lógico:
- Eliminar id_sector de proyecto.
- Agregar id_sector smallint [not null] a meta_proyecto.
- Reemplazar:
    Ref: proyecto.id_sector > sector.id_sector
  por:
    Ref: meta_proyecto.id_sector > sector.id_sector
