CARGA PMR - SAN CRISTÓBAL
=========================

FUENTES
-------
- archivo_plano_pmr_fdl_corte_31_marzo_2026.xlsx
- archivo_plano_pmr_fdl_corte_30_junio_2026.xlsx

PERFILAMIENTO
-------------
Cada archivo contiene 83 registros para San Cristóbal y 83 códigos de indicador
distintos. Los 83 indicadores existen en meta_proyecto.

DECISIÓN DE MODELADO
--------------------
No se requiere una nueva tabla ni una modificación estructural.

seguimiento_meta funciona como una FACT TABLE DE SNAPSHOT PERIÓDICO:
- Meta
- Vigencia
- Fecha de corte
- Magnitudes
- Presupuesto
- Compromisos
- Giros

Se cargan ambos cortes y ambas vigencias que trae cada archivo:
83 metas x 2 vigencias x 2 cortes = 332 registros.

Esto conserva el linaje de cada archivo y permite medir evolución.
Para consumo analítico se crea vw_seguimiento_meta_ultimo_corte, evitando
sumar dos cortes al mismo tiempo.

UNIDADES MONETARIAS
-------------------
La fuente tiene una inconsistencia de rotulado que NO se corrigió de manera
silenciosa:

1. Presupuesto programado 2025:
   El encabezado dice "millones de pesos" y los valores sí vienen en millones.
   Ejemplo: 2.356,45 representa $2.356.450.000.
   Regla aplicada: valor fuente x 1.000.000.

2. Compromisos 2025:
   Aunque el encabezado también dice "millones de pesos", los valores ya
   vienen en pesos. NO se multiplican.

3. Presupuesto programado, Compromisos y Giros 2026:
   Los encabezados dicen "millones de pesos", pero los valores ya vienen
   en pesos. NO se multiplican.
   El presupuesto programado 2026 suma exactamente $127.690.480.000,
   igual al POAI 2026 cargado.

HALLAZGO DE CALIDAD: POAI 2025
-------------------------------
El cruce PMR permitió detectar que la homologación inicial del POAI 2025
había asignado al código contrario 4 registros, debido a descripciones
intercambiadas en el POAI 2026 usado como maestro:

- 22851 / 22852
- 24953 / 24954

El script 00 corrige únicamente la capa integrada PostgreSQL.
No altera los archivos fuente originales.

HALLAZGO DE CALIDAD: POAI 2026 vs PMR 2026
-------------------------------------------
El presupuesto coincide exactamente en las 83 metas.

Sin embargo, existen 6 diferencias en magnitud programada entre POAI y PMR.
Se preservan ambos valores; NO se fuerza una corrección porque las fuentes
no permiten determinar automáticamente cuál versión debe prevalecer.

La vista vw_calidad_poai_pmr deja estas diferencias visibles para Gobierno
de Datos y futura validación con el responsable funcional.

EVOLUCIÓN MARZO -> JUNIO 2026
-----------------------------
Metas con cambio en magnitud contratada: 17
Metas con cambio en magnitud entregada: 14
Metas con cambio en compromisos: 9
Metas con cambio en giros: 57

Los campos 2025 no cambiaron entre ambos archivos.

ORDEN DE EJECUCIÓN
------------------
1. sql/00_correccion_integracion_poai_2025.sql
2. sql/01_carga_pmr.sql
3. sql/02_validar_pmr.sql

AJUSTE EN DBDIAGRAM.IO
----------------------
Ninguno.

POSIBLE ENRIQUECIMIENTO FUTURO
------------------------------
PMR trae ID_producto, descripción del producto, naturaleza, periodicidad y
unidad de medida. Se preservan como metadatos de fuente, pero no se incorporan
al modelo V1 porque no son necesarios para las preguntas actuales y crearían
una nueva entidad Producto PMR. Si el alcance posterior requiere análisis por
producto, puede normalizarse en una segunda fase.
