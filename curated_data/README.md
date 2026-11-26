# Datos curados de San Cristóbal

Esta carpeta contiene el **conjunto de datos limpio del equipo**: archivos oficiales sobre la Alcaldía Local de San Cristóbal que el equipo perfiló, normalizó y organizó en un modelo relacional. Es la fuente principal de la aplicación para el POAI, el seguimiento de metas (PMR), los presupuestos participativos, los compromisos presupuestales (CRP), la alineación con los ODS y las PQRS.

Los archivos se versionan tal cual se entregaron (`.gitattributes` evita que Git cambie sus finales de línea). No se editan a mano: si llega una versión nueva, se reemplaza la carpeta completa del dominio y se actualiza su `manifest.json`.

## Contenido

| Carpeta | Dominio | Archivos de origen |
|---|---|---|
| `Carga_Base_POAI_SC/` | POAI 2025–2026: objetivos, programas, proyectos, metas y valores planeados (pesos) | POAI entregado por la Alcaldía Local |
| `Carga_PMR_SC/` | Seguimiento de metas: magnitudes, presupuesto, compromisos y giros (cortes 31-03-2026 y 30-06-2026) | Archivos planos del PMR de los Fondos de Desarrollo Local |
| `Carga_PP_SC/` | Propuestas ciudadanas de presupuestos participativos y su seguimiento (cortes 31-03-2026 y 01-10-2026) | Conjunto de Presupuestos Participativos |
| `Carga_CRP_SC/` | Compromisos presupuestales (CRP) por meta y propuestas financiadas (vigencia 2025) | Conjunto de presupuesto comprometido de Presupuestos Participativos |
| `Carga_ODS_SC/` | Alineación de cada meta con una meta de los Objetivos de Desarrollo Sostenible | Archivo plano ODS (corte 30-06-2026) |
| `Carga_PQRS_SC/` | 4.026 PQRS de la Alcaldía Local, 2022–2026, con sus catálogos | Archivo PQRS de la Secretaría Distrital de Gobierno |
| `Carga_Contratos_SC/` | 1.936 contratos SECOP II 2025–2026 con 3.853 vínculos a proyectos, metas y CRP (verificados o pendientes). La columna `Contratista` no se carga | Consulta SECOP II consolidada por el equipo (sin scripts SQL) |

Cada carpeta tiene:

- `csv/`: las tablas normalizadas que lee la aplicación.
- `manifest.json`: los conteos y totales esperados. La ingesta los comprueba y **se detiene si algo no coincide**.
- `README_*.txt`: las decisiones de limpieza y los hallazgos del equipo.
- `sql/`: los scripts originales de carga para PostgreSQL (referencia; la aplicación no los ejecuta).

En la raíz están los modelos del equipo: `Modelo_Conceptual_SC.drawio.svg`, `Modelo_Lógico_SC.svg` y `Modelo_Físico_SC.sql`.

## Cómo la usa la aplicación

El comando `python -m app.cli ingest` (desde `backend/`) lee estos CSV y construye en DuckDB las mismas tablas del modelo físico, con las transformaciones de los scripts SQL (sector y entidad por meta, corrección del POAI 2025 y vistas de consulta). Los CRP de la vigencia 2026, que no están en esta carpeta, se complementan con el archivo del portal de Datos Abiertos y quedan marcados con `source = 'portal'`.

La base se vuelve a construir sola cuando cambia cualquier CSV o `manifest.json` de esta carpeta: los scripts `iniciar.bat` e `iniciar.sh` ejecutan `ingest --if-outdated`.

## Privacidad

El campo `usuario_actual` de las PQRS contiene nombres de funcionarios. Se carga en la base para conservar el modelo completo, pero **ninguna herramienta, respuesta ni pantalla lo muestra**.
