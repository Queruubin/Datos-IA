# Hallazgos de calidad en los datos · Alcaldía Local de San Cristóbal

| Campo | Valor |
|---|---|
| Fecha del análisis | 2026-11-22 (portal) y 2026-11-23 (paquete curado) |
| Portal | [Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co/) (API CKAN) |
| Notebook de análisis | `notebooks/01_fase0_fuentes_san_cristobal.ipynb` |
| Limpieza en producción | `backend/app/ingestion/` |
| Paquete curado del equipo | `curated_data/` (ver la sección al final) |

## Resumen

Se analizaron tres conjuntos de datos del portal, filtrados para San Cristóbal. **Los tres tienen datos, pero ninguno se puede usar directamente**: hay que extraer tablas de formatos de reporte, unificar categorías escritas de forma distinta, descartar columnas con posibles datos personales y decidir qué hacer con valores vacíos o imposibles. Además, la fuente central de la propuesta (el POAI) **no está publicada como dato abierto**: el equipo la obtuvo de la Alcaldía Local y la integró, junto con el PMR, los ODS, los presupuestos participativos, los CRP y las PQRS, en un paquete curado (sección final).

Esto respalda el problema planteado por el reto de la Secretaría General: *el dato existe, pero no es accesible, comprensible ni utilizable para la ciudadanía.*

| Fuente | Registros de San Cristóbal | Fecha de corte | Hallazgos |
|---|---|---|---|
| F1 · Ejecución PAC de los Fondos de Desarrollo Local | 18 meses | junio de 2025 | 5 |
| F2 · PQRS de la Secretaría de Gobierno | 4.026 solicitudes | 10 de agosto de 2026 | 6 |
| F3 · Presupuestos Participativos | 232 propuestas y 78 compromisos | 30 de septiembre de 2026 | 3 |
| Paquete curado del equipo (POAI, PMR, presupuestos participativos, CRP, ODS, PQRS) | 83 metas, 232 propuestas, 4.026 PQRS | 30 de junio de 2026 (PMR) y 1 de octubre de 2026 (propuestas) | 8 (sección final) |

**Severidad:** 🔴 alta (impide verificar o puede inducir a error) · 🟠 media (exige limpieza o limita el análisis) · 🟢 baja (fricción de formato).

---

## F1 · Ejecución del PAC de los Fondos de Desarrollo Local

**Publicador:** Secretaría Distrital de Hacienda
**Dataset:** `e130bb0d-2d92-41c8-b894-8e058519309d`

| # | Hallazgo | Severidad | Evidencia | Tratamiento |
|---|---|---|---|---|
| 1.1 | **La unidad de los valores no está documentada.** Ni el archivo ni sus metadatos indican si los montos están en pesos, miles o millones | 🔴 | El metadato describe las columnas, pero no la unidad. Ejemplo: San Cristóbal, junio de 2025: programado `7.980`, ejecutado `7.939` | Se guarda tal cual, con la etiqueta "unidad no documentada". El agente tiene prohibido decir que son pesos |
| 1.2 | **Valor ejecutado vacío con porcentaje reportado.** Kennedy, diciembre de 2024, reporta 105 % de ejecución, pero el valor ejecutado está en blanco | 🔴 | Fila: `0008-01;Kennedy; 16.070 ; ;105%;5%` | Se deja vacío (`NULL`). No se rellena ni se calcula |
| 1.3 | **Fuente desactualizada.** El último mes publicado es junio de 2025 | 🟠 | 18 archivos mensuales: enero de 2024 a junio de 2025 | El agente siempre muestra la fecha de corte |
| 1.4 | **Formato de reporte, no de tabla.** Cada mes es un CSV aparte, con unas 10 filas decorativas, una fila "Total" y, en algunos archivos, una tabla adicional al final | 🟠 | Una primera lectura sin filtros generó 576 filas en vez de 360 (20 localidades × 18 meses) | Solo se aceptan filas con código de entidad válido (`0004-01`) y se verifica que cada mes tenga exactamente 20 localidades |
| 1.5 | **Codificación y formato numérico.** Archivos en `latin-1`, punto como separador de miles y porcentajes como texto (`99%`) | 🟢 | Las tildes aparecen dañadas si se leen como UTF-8 | Detección de codificación y conversión numérica |

**Validación positiva:** en las 360 filas, el porcentaje publicado coincide con el calculado (ejecutado / programado), con una tolerancia de ±1,5 puntos.

---

## F2 · PQRS de la Secretaría Distrital de Gobierno (2022–2026)

**Publicador:** Secretaría Distrital de Gobierno
**Dataset:** `db9d7291-0308-475e-bd81-cd222c13fca4`

| # | Hallazgo | Severidad | Evidencia | Tratamiento |
|---|---|---|---|---|
| 2.1 | **Columnas de texto libre con posibles datos personales** (`OBSERVACION_GENERAL`, `OBSERVACION_SAC`) y usuarios internos | 🔴 | Columnas publicadas en el dataset abierto | No se cargan: solo se leen 11 columnas permitidas. El texto libre nunca entra a la aplicación |
| 2.2 | **Fechas de respuesta anteriores a la radicación** | 🟠 | 8 solicitudes | Se excluyen del cálculo de tiempos de respuesta; la fila se conserva |
| 2.3 | **Solicitudes sin tipo de petición ni plazo legal** | 🟠 | 448 de 4.026 (11 %) | Quedan vacías. No se puede evaluar si se respondieron a tiempo |
| 2.4 | **Solicitudes sin fecha de respuesta** | 🟢 | 144 de 4.026 | Corresponden en su mayoría a trámites abiertos (188 en estado "RADICADO EN GESTION") |
| 2.5 | **Clasificación temática poco informativa.** El subtema más frecuente es genérico, y en 2025 aparece uno llamado "¿OTRO?" | 🟠 | "INFORMACIÓN DE TRÁMITES Y SERVICIOS": 1.743 (43 %). "¿OTRO?": 163 en 2025 | Se muestra tal cual. Limita saber qué pidió realmente la ciudadanía |
| 2.6 | **Plazo en días hábiles y fechas en días calendario** | 🟢 | `TIEMPO_TRAMITE` = 15 días hábiles para un derecho de petición | Todavía no se calcula el cumplimiento del plazo; requiere un calendario de festivos |

> **Actualización (2026-11-23):** las PQRS ya no se leen del portal sino del paquete curado, que normaliza el mismo archivo (`pqrs_sdg_2022_2026.csv`). Se revisó que `OBSERVACION_GENERAL` y `OBSERVACION_SAC` solo contienen estados del trámite y números de radicado, así que ahora se usan (p. ej. "Sin respuesta al peticionario"). `USUARIO_ACTUAL` sí tiene nombres de funcionarios: se carga en la base, pero ninguna herramienta ni pantalla lo muestra.

---

## F3 · Presupuestos Participativos

**Publicador:** Secretaría Distrital de Planeación
**Dataset:** `3ded79df-ec9e-4f92-a949-ca8b1ae12d7d`

| # | Hallazgo | Severidad | Evidencia | Tratamiento |
|---|---|---|---|---|
| 3.1 | **Mismo sector escrito de dos formas** entre vigencias | 🟠 | 2025: "Cultura, recreación y deporte". 2026: "CULTURA, RECREACIÓN Y DEPORTE". Sin normalizar hay 22 sectores; normalizados, 11 | Se unifican en mayúsculas y sin tildes |
| 3.2 | **Archivos con decenas de hojas vacías** que exponen rutas internas de equipos de la entidad | 🟠 | Nombres de hojas como `file:///T:/Particion%201/ESCRITORIO/...` y `file:///C:/Users/User/Documents/...` | Solo se lee la primera hoja |
| 3.3 | **Fecha de corte solo en el nombre del archivo** | 🟢 | `..._30-09-2026.ods` | Se extrae del nombre y se convierte a formato ISO |

**Validación positiva:** el contraste entre propuestas y compromisos es **coherente**. Las 169 propuestas en estado *Contratada*, *En ejecución* o *Materializada* (133 en 2025 y 36 en 2026) tienen al menos un compromiso presupuestal (CRP) asociado. Las 54 propuestas *En formulación* de 2026 no tienen compromiso, lo cual es esperado.

> **Actualización (2026-11-23):** las propuestas y sus estados ahora vienen del paquete curado (corte 01-10-2026); del portal solo se usa el archivo de compromisos, para completar los CRP de 2026. Ver el hallazgo C.6: los estados del paquete curado no coinciden con los del archivo del portal de 30-09-2026.

---

## Vacíos de información

| Dato | Situación | Impacto |
|---|---|---|
| **POAI de San Cristóbal** (metas, recursos y avance) | No está en el portal: la búsqueda "POAI" devuelve 0 resultados. Para el proyecto, el equipo obtuvo el archivo de la Alcaldía Local y lo integró en `curated_data/` | Con el paquete curado ya se contrasta lo planeado (POAI) con lo ejecutado (PMR). Sigue siendo un vacío para quien lo busque en el portal |
| **Seguridad por localidad** (por ejemplo, homicidios) | No está incluido en las fuentes del proyecto | Cuando alguien lo pregunta, el agente lo registra como vacío de información |
| **Ejecución del PAC después de junio de 2025** | No publicada | No se puede responder sobre la ejecución reciente |

## Recomendaciones para las entidades publicadoras

1. Publicar los datos como **tablas planas** (una fila por registro, un encabezado), no como reportes con formato.
2. **Documentar la unidad** de todo valor monetario en los metadatos.
3. Usar **catálogos controlados** para las categorías (sectores, subtemas) y evitar valores como "¿OTRO?".
4. **Revisar los archivos antes de publicarlos**: eliminar hojas vacías y rutas internas.
5. No publicar columnas de **texto libre** que puedan contener datos personales.
6. Publicar el **POAI local** como dato abierto y mantener la **periodicidad** declarada.

---

## Paquete curado del equipo (`curated_data/`)

**Fecha de revisión:** 2026-11-23
**Contenido:** POAI 2025–2026, PMR (cortes 31-03-2026 y 30-06-2026), presupuestos participativos (cortes 31-03-2026 y 01-10-2026), CRP de presupuestos participativos, alineación ODS y PQRS 2022–2026, con un `manifest.json` por dominio.

La ingesta reconstruye el modelo físico del equipo en DuckDB y **compara cada conteo y total con los manifiestos**: si algo no coincide, no se carga nada. Con los archivos actuales todo coincide: 83 metas, 166 registros POAI, 332 de PMR, 232 propuestas con 464 seguimientos, 31 CRP con 66 líneas, 83 relaciones ODS y 4.026 PQRS.

| # | Hallazgo | Severidad | Evidencia | Tratamiento |
|---|---|---|---|---|
| C.1 | **Códigos cruzados en el POAI 2025.** La homologación de 2025 usó las descripciones del POAI 2026, que están cruzadas en dos pares de metas | 🔴 | 22851/22852 y 24953/24954: el valor y la magnitud de 2025 quedaron en el código contrario (p. ej. 22851 tenía $1.500.000.000 y debía tener $2.500.000.000) | La ingesta aplica la corrección del equipo (`correccion_integracion_poai_2025.csv`) y recalcula el porcentaje de cada meta. El total no cambia: $130.871.828.000 |
| C.2 | **Unidades mal rotuladas en el PMR.** Todos los encabezados dicen "millones de pesos", pero solo el presupuesto programado 2025 viene en millones | 🔴 | Compromisos 2025 y todo 2026 ya vienen en pesos. El presupuesto 2026 suma exactamente $127.690.480.000, igual al POAI | El paquete ya trae todo en pesos (COP). La ingesta verifica que el presupuesto PMR 2026 de cada corte sea igual al POAI 2026 |
| C.3 | **6 metas con magnitud distinta entre POAI y PMR en 2026.** El presupuesto coincide en las 83 metas | 🟠 | 22851 (3 vs 1), 22852 (1 vs 3), 24953 (3.300 vs 30), 24954 (30 vs 3.300), 25061 (75 vs 150) y 28054 (2,5 vs 5). Cuatro son los mismos pares de C.1 con los valores intercambiados, lo que sugiere el mismo cruce de descripciones en el POAI 2026 | Se conservan ambos valores. `compare_poai_vs_pmr` devuelve **Diferencia detectada** con la lista de metas; no se decide cuál prevalece |
| C.4 | **2025: tres diferencias de magnitud que el script de validación no esperaba** | 🟢 | `02_validar_pmr.sql` espera 0 diferencias en 2025 tras la corrección, pero quedan 22852 (2 vs 3), 23163 (800 vs 650) y 28052 (1,25 vs 1,3). El presupuesto 2025 difiere como máximo $5.000 por redondeo, porque el PMR venía en millones con dos decimales | No es un valor del manifiesto: se informa en el contraste. En 2025 se toleran diferencias de presupuesto de hasta $5.000 |
| C.5 | **El sector depende de la meta, no del proyecto** | 🟠 | El proyecto 2502 tiene metas de AMBIENTE y HÁBITAT; el 2802, de INTEGRACIÓN SOCIAL y MUJERES | El sector se guarda en `meta_proyecto`, como en el modelo del equipo. Los filtros por sector usan el sector de cada meta |
| C.6 | **Faltan los CRP de 2026 y los estados de las propuestas no coinciden con el portal** | 🔴 | El paquete solo trae CRP de 2025: 66 líneas, 31 CRP y $39.514.916.879, idénticos al portal. El portal (corte 30-09-2026) tiene además 12 líneas de 2026 en 7 CRP por $6.962.956.715, que financian 36 propuestas. Esas 36 están *Contratada* en el archivo de avance del portal (30-09-2026), pero *En formulación* en el corte curado (01-10-2026), donde las 90 propuestas de 2026 están *En formulación* | Los CRP de 2026 se agregan desde el portal, marcados con `source = 'portal'`; todas sus metas y propuestas existen en el modelo. El contraste de 2026 da **No comparable** (ninguna propuesta en un estado que exija CRP) e informa aparte las 36 propuestas que ya tienen CRP. Hay que confirmar con la fuente cuál archivo de avance es el vigente |
| C.7 | **PQRS: 4 radicados con vigencia distinta al año de registro** | 🟢 | Por ejemplo, vigencia 2023 con fecha de registro 10-01-2024. El archivo `vigencia_fecha_registro_inconsistencias.csv` los lista | Se conserva la vigencia de la fuente; la herramienta de PQRS lo advierte |
| C.8 | **`USUARIO_ACTUAL` de las PQRS contiene nombres de funcionarios** | 🔴 | 105 valores distintos | Se carga en la tabla `pqrs` para no alterar el modelo, pero la vista `vw_pqrs_detalle` y las herramientas lo excluyen. Una prueba automática verifica que no aparezca en ninguna respuesta |

**Validaciones positivas:** las 46 metas con propuestas, las 133 propuestas financiadas con CRP y las 83 metas alineadas con ODS existen en el POAI; ninguna propuesta financiada apunta a una meta distinta de la de su CRP; y el contraste de 2025 entre propuestas y CRP es **coherente** (133 de 133).
