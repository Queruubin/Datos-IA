# Hallazgos de calidad en los datos · Alcaldía Local de San Cristóbal

| Campo | Valor |
|---|---|
| Fecha del análisis | 2026-11-22 |
| Portal | [Datos Abiertos Bogotá](https://datosabiertos.bogota.gov.co/) (API CKAN) |
| Notebook de análisis | `notebooks/01_fase0_fuentes_san_cristobal.ipynb` |
| Limpieza en producción | `backend/app/ingestion/` |

## Resumen

Se analizaron tres conjuntos de datos del portal, filtrados para San Cristóbal. **Los tres tienen datos, pero ninguno se puede usar directamente**: hay que extraer tablas de formatos de reporte, unificar categorías escritas de forma distinta, descartar columnas con posibles datos personales y decidir qué hacer con valores vacíos o imposibles. Además, la fuente central de la propuesta (el POAI) **no está publicada como dato abierto**.

Esto respalda el problema planteado por el reto de la Secretaría General: *el dato existe, pero no es accesible, comprensible ni utilizable para la ciudadanía.*

| Fuente | Registros de San Cristóbal | Fecha de corte | Hallazgos |
|---|---|---|---|
| F1 · Ejecución PAC de los Fondos de Desarrollo Local | 18 meses | junio de 2025 | 5 |
| F2 · PQRS de la Secretaría de Gobierno | 4.026 solicitudes | 10 de agosto de 2026 | 6 |
| F3 · Presupuestos Participativos | 232 propuestas y 78 compromisos | 30 de septiembre de 2026 | 3 |
| POAI de San Cristóbal | no publicado | — | vacío de información |

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

---

## Vacíos de información

| Dato | Situación | Impacto |
|---|---|---|
| **POAI de San Cristóbal** (metas, recursos y avance) | No está en el portal: la búsqueda "POAI" devuelve 0 resultados | No se puede contrastar lo **planeado** con lo **ejecutado**, que era el eje de la propuesta original |
| **Seguridad por localidad** (por ejemplo, homicidios) | No está incluido en las fuentes del proyecto | Cuando alguien lo pregunta, el agente lo registra como vacío de información |
| **Ejecución del PAC después de junio de 2025** | No publicada | No se puede responder sobre la ejecución reciente |

## Recomendaciones para las entidades publicadoras

1. Publicar los datos como **tablas planas** (una fila por registro, un encabezado), no como reportes con formato.
2. **Documentar la unidad** de todo valor monetario en los metadatos.
3. Usar **catálogos controlados** para las categorías (sectores, subtemas) y evitar valores como "¿OTRO?".
4. **Revisar los archivos antes de publicarlos**: eliminar hojas vacías y rutas internas.
5. No publicar columnas de **texto libre** que puedan contener datos personales.
6. Publicar el **POAI local** como dato abierto y mantener la **periodicidad** declarada.
