# Backend — Agente de verificación de información pública (San Cristóbal)

API en FastAPI y canal de ingesta de datos abiertos para el agente de la Alcaldía Local de San Cristóbal (código de localidad 4). Ver `../docs/PRD.md`.

Incluye la ingesta de datos, la API base y el **núcleo del agente** (fase 2): chat con Gemini que solo explica cifras calculadas por herramientas determinísticas, con evidencia trazable, contraste entre fuentes y registro de vacíos de información.

## Fuentes que se ingieren

| ID | Fuente | Origen | Tablas DuckDB | Unidad |
|---|---|---|---|---|
| `POAI` | POAI 2025–2026: objetivos, programas, proyectos, metas y valor planeado | Paquete curado (`curated_data/`) | `localidad`, `sector`, `objetivo_estrategico`, `programa`, `proyecto`, `meta_proyecto`, `poai` | COP |
| `PMR` | Seguimiento de metas, cortes 31-03-2026 y 30-06-2026 | Paquete curado | `seguimiento_meta` | COP |
| `PP` | Propuestas ciudadanas y su seguimiento, cortes 31-03-2026 y 01-10-2026 | Paquete curado | `propuesta_ciudadana`, `seguimiento_propuesta` | — |
| `CRP` | Compromisos presupuestales por meta y propuestas financiadas | Paquete curado (2025) + portal (2026) | `crp`, `crp_meta`, `crp_propuesta`, `entidad` | COP |
| `ODS` | Alineación meta ↔ meta ODS | Paquete curado | `ods`, `meta_ods`, `meta_ods_relacion` | — |
| `PQRS` | PQRS de la Alcaldía Local 2022–2026 | Paquete curado | `pqrs`, `tipo_peticion`, `medio_recepcion`, `subtema_pqrs` | — |
| `F1` | Ejecución PAC — Fondos de Desarrollo Local (un CSV por mes) | Portal | `f1_pac_execution` | No documentada |
| `F3-commitments` | Presupuesto comprometido de Presupuestos Participativos | Portal | `f3_pp_commitments` (solo como origen de los CRP 2026) | — |

Vistas (equivalentes DuckDB de las del paquete): `vw_seguimiento_meta_ultimo_corte`, `vw_calidad_poai_pmr`, `vw_crp_meta_resumen`, `vw_meta_ods_detalle`, `vw_pqrs_detalle` (**sin** `usuario_actual`) y `vw_meta_contexto` (meta → proyecto → programa → objetivo, sector y entidad).

Cada fuente tiene un registro en `source_metadata`: título, URL del portal (**solo** si los datos vienen del portal; si no, `null`), archivos de origen, fecha de corte, filas, unidad, fecha de ingesta y `origin_note` (de dónde vienen los datos). La tabla `data_version` guarda la versión de los datos y una huella de los archivos de `curated_data/`.

Decisiones de limpieza importantes:
- **Paquete curado** (`app/ingestion/curated.py`): reconstruye las tablas del modelo físico del equipo (mismos nombres de tablas y columnas; ids sustitutos generados; llaves naturales conservadas) con las transformaciones de sus scripts SQL: sector y entidad en `meta_proyecto`, corrección de los códigos 22851/22852 y 24953/24954 del POAI 2025, PMR enlazado por `codigo_indicador`, las 66 líneas CRP-meta conservadas (también los 4 pares repetidos) y pares únicos en `crp_propuesta`. Después compara **cada conteo y total con los `manifest.json`** (incluido POAI 2025 = $130.871.828.000, POAI 2026 = $127.690.480.000 y presupuesto PMR 2026 = POAI 2026); si algo no coincide, falla y no escribe nada.
- **Complemento CRP 2026:** las líneas del portal de las vigencias que no están en el paquete se agregan a `crp`, `crp_meta` y `crp_propuesta` con `source = 'portal'` y el nombre del archivo en `source_file`. Los códigos de propuesta se separan por cualquier carácter que no sea dígito. Si una meta o propuesta no existe, la fila no se carga y se informa en el reporte.
- **PQRS:** `usuario_actual` (nombres de funcionarios) se carga en `pqrs`, pero ninguna vista ni herramienta lo expone. `OBSERVACION_GENERAL` y `OBSERVACION_SAC` solo contienen estados del trámite y radicados.
- **F1:** se conservan solo las filas con código `0000-00` (se descartan la fila `Total`, las filas vacías y las tablas basura del pie). Cada mes debe tener exactamente 20 localidades; si no, la fuente falla. Las celdas vacías quedan vacías (`NULL`): nunca se imputan. La unidad de los valores **no está documentada** (probablemente millones de pesos).
- **F3:** solo se lee la primera hoja del `.ods` de compromisos y se normalizan los nombres de sector. Las fuentes del portal F2 (PQRS) y F3-avance ya no se ingieren: el paquete curado las reemplaza, y sus tablas antiguas se borran en la siguiente ingesta.

## Estructura (arquitectura hexagonal)

```
app/
  domain/          entidades (SourceMetadata, Evidence, ChatAnswer, GapRecord...)
  ports/           interfaces: CatalogPort, DataStorePort, AnalyticsPort, LLMPort, GapRepositoryPort,
                   UsageRepositoryPort, ExchangeRatePort
  adapters/ckan/   cliente HTTP del portal CKAN con caché en disco
  adapters/duckdb/ almacenamiento en DuckDB (+ curated_views.py: vistas del paquete curado;
                   gap_repository.py: tabla gap_log; usage_repository.py: tabla usage_log)
  adapters/exchange_rate.py  TRM oficial (USD → COP) desde datos.gov.co, con caché en memoria
  adapters/llm/    adaptador de Gemini (google-genai, function calling manual)
  ingestion/       funciones puras de limpieza por fuente (sin red); curated.py: paquete curado,
                   validación contra manifiestos y complemento CRP 2026
  application/     casos de uso IngestSources y AskQuestion; herramientas del agente,
                   validador de respuestas, enmascarado de datos personales y prompts;
                   pricing.py (tabla de precios de Gemini) y usage_report.py (resumen de consumo)
  api/             aplicación FastAPI (+ rate_limit.py)
  cli.py           línea de comandos
tests/             pruebas sin red, con archivos sintéticos en tests/fixtures
```

## Instalación

Requiere Python 3.12 o superior. Ejecutar los comandos desde la carpeta `backend/`.

### Opción A: venv + pip

```bash
python -m venv .venv
# Windows (Git Bash):  source .venv/Scripts/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# Linux / macOS:        source .venv/bin/activate
python -m pip install -e ".[dev]"
```

### Opción B: uv

```bash
uv venv
uv pip install -e ".[dev]"
# o, para ejecutar sin activar el entorno: uv run pytest
```

### Configuración

La configuración se lee de variables de entorno o de un archivo `.env` en `backend/`. Variables disponibles (todas opcionales):

| Variable | Valor por defecto | Uso |
|---|---|---|
| `DATA_DIR` | `data` | Carpeta de datos; los archivos descargados se guardan en `data/raw` |
| `DUCKDB_PATH` | `data/san_cristobal.duckdb` | Base de datos con las tablas limpias |
| `CURATED_DATA_DIR` | `../curated_data` (raíz del repositorio) | Carpeta del paquete curado del equipo |
| `GEMINI_API_KEY` | (vacía) | Clave de Gemini. Sin ella `POST /api/chat` responde 503; el resto de la API funciona |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Modelo principal de Gemini usado por el chat |
| `GEMINI_FALLBACK_MODELS` | `["gemini-3.1-flash-lite", "gemini-3.8-flash"]` | Modelos de respaldo (formato JSON) cuando el actual está saturado (503), limitado (429) o no responde a tiempo (504) |
| `GEMINI_TIMEOUT_SECONDS` | `30` | Tiempo máximo por llamada a Gemini |
| `GEMINI_TEMPERATURE` | `0.2` | Temperatura del modelo (baja: respuestas estables) |
| `GAP_LOG_PATH` | `data/gap_log.duckdb` | Base DuckDB con la tabla `gap_log` (vacíos de información) |
| `USAGE_LOG_PATH` | `data/usage_log.duckdb` | Base DuckDB con la tabla `usage_log` (tokens y costo de cada llamada a Gemini) |
| `TRM_API_URL` | `https://www.datos.gov.co/resource/32sa-8pi3.json` | API de la TRM oficial (USD → COP) |
| `TRM_TIMEOUT_SECONDS` | `5` | Tiempo máximo para consultar la TRM |
| `USD_TO_COP_FALLBACK` | (vacía) | Tasa de respaldo si la TRM no se puede consultar. Sin ella, los costos en pesos salen como no disponibles |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `20` | Preguntas por minuto permitidas por cliente (en memoria) |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Orígenes permitidos (formato JSON), p. ej. el frontend de Vite |

Ejemplo de `.env`:

```bash
GEMINI_API_KEY=tu-clave
```

Las claves nuevas de AI Studio no tienen acceso a modelos antiguos como `gemini-2.5-flash` (responden 404). Para ver qué modelos tiene disponible tu clave, usa `client.models.list()` del SDK `google-genai`.

La clave solo vive en el backend; nunca se envía al frontend.

Nunca subas el archivo `.env` al repositorio.

## Ingesta de datos

```bash
python -m app.cli ingest                  # todas las fuentes: F1, F3 y el paquete curado (CURADO)
python -m app.cli ingest --source CURADO  # una sola fuente (F1, F3 o CURADO)
python -m app.cli ingest --if-outdated    # solo si la base falta o está desactualizada
```

- El paquete curado se lee de `curated_data/` (sin red). F1 y F3 se descargan de https://datosabiertos.bogota.gov.co y se guardan en `data/raw` (caché). Para forzar una descarga nueva, borra esa carpeta.
- El paquete curado corre al final porque usa la tabla de F3 para el complemento CRP 2026.
- `--if-outdated` reingiere cuando no hay marcador de versión, la versión del código (`DATA_VERSION`) cambió, cambió algún CSV o `manifest.json` de `curated_data/`, o falta una fuente del portal. Si todo está al día, termina enseguida. Es lo que ejecutan `iniciar.bat` e `iniciar.sh`.
- Si una fuente falla, las demás se ingieren igual. El comando termina con código 1 solo si una fuente quedó **sin datos utilizables** (por ejemplo, el paquete curado no pasa la validación, o el portal falla en la primera ingesta). Si una descarga falla pero la tabla de una ingesta anterior sigue en la base, se conserva y el código es 0.

## API

```bash
uvicorn app.api.main:app --reload
```

- `GET /health` → `{"status": "ok"}`
- `GET /api/sources` → fuentes cargadas con su fecha de corte (`data_cutoff`) y metadatos de trazabilidad
- `POST /api/chat` → pregunta ciudadana (ver abajo)
- `GET /api/usage` → consumo de tokens y costo equivalente (ver "Consumo y costos")
- Documentación interactiva: http://127.0.0.1:8000/docs

## Chat con evidencia (`POST /api/chat`)

```bash
curl -X POST http://127.0.0.1:8000/api/chat   -H "Content-Type: application/json"   -d '{"question": "¿Cuánto se ejecutó del PAC en 2025?"}'
```

Respuesta:

```json
{
  "answer": "…texto en lenguaje claro que cita E1…",
  "status": "answered",
  "evidence": [{"id": "E1", "source_id": "F1", "title": "…", "data_cutoff": "2025-06",
                "portal_url": "https://datosabiertos.bogota.gov.co/dataset/…",
                "locator": "f1_pac_execution · year=2025", "summary": "…"}],
  "comparison": null,
  "gap": null,
  "disclaimer": "Este asistente no es vocero oficial de la Alcaldía. …",
  "usage": {"input_tokens": 2900, "output_tokens": 240, "thinking_tokens": 100,
            "total_tokens": 3240, "calls": 3, "models": ["gemini-3.5-flash-lite"],
            "cost_usd": 0.0021, "cost_cop": 7.3, "unpriced_models": []}
}
```

- `question`: texto de 1 a 500 caracteres. `status`: `answered`, `information_gap` o `needs_clarification`.
- `comparison` aparece cuando se usó un contraste (`compare_participatory_budget_vs_commitments` o `compare_poai_vs_pmr`); trae el veredicto `coherent` / `difference_detected` / `not_comparable`, la regla y los valores comparados.
- Cada evidencia trae `portal_url` (o `null` si la fuente no está en el portal) y `origin_note` con el origen del archivo.
- Códigos: `429` si se superan las preguntas por minuto, `503` si falta `GEMINI_API_KEY`, `502` si Gemini no responde.

Cómo funciona (PRD 8.1–8.2):
1. Se enmascaran datos personales de la pregunta (correos, teléfonos, números tipo cédula; los años se conservan). Gemini y los registros solo ven la versión enmascarada.
2. Gemini elige herramientas de una lista cerrada de 11 (`list_sources`, `get_budget_execution`, `get_plan_vs_execution`, `get_goal_detail`, `compare_poai_vs_pmr`, `get_changes_between_cutoffs`, `get_investment_by_ods`, `get_pqrs_stats`, `get_participatory_budget`, `compare_participatory_budget_vs_commitments`, `report_information_gap`). **No escribe SQL**: los parámetros se validan y se aplican como filtros de texto plano. Máximo 5 rondas.
3. Las herramientas calculan todas las cifras y el veredicto del contraste, y entregan evidencia con ids `E1, E2…` asignados por el código.
4. Gemini redacta la respuesta final en JSON estructurado citando esos ids.
5. Un validador descarta ids inexistentes y rechaza respuestas con cifras sin evidencia ("No pude verificar esta respuesta…"). Todo vacío de información se guarda en `gap_log` (pregunta enmascarada, tema, dato faltante, motivo; nunca la IP).

## Consumo y costos (`GET /api/usage`)

Cada llamada a Gemini (rondas de planeación y redacción final) registra los tokens que reporta `usage_metadata` y el modelo que respondió (incluido el de respaldo). Se guarda una fila por llamada en `usage_log` (`USAGE_LOG_PATH`): id, fecha (UTC), id de pregunta, modelo, tokens de entrada, salida, razonamiento y total, y costo en USD. **No se guarda el texto de la pregunta ni datos personales.** Si guardar falla, la respuesta se entrega igual.

- Costo = tokens de entrada × precio de entrada + (salida + razonamiento) × precio de salida.
- Precios: `app/application/pricing.py`, tomados de https://aistudio.google.com/docs/pricing (consultados el 2026-11-23, plan pagado "Standard", USD por millón de tokens). Admite precios con fecha de vigencia (p. ej. `gemini-3.8-flash` sube el 2027-01-01) y se usa el vigente en la fecha de cada llamada. Un modelo sin precio conocido queda con costo `null`; nunca se estima.
- **Con el plan gratuito de Gemini el costo real es $0**: las cifras son el equivalente en el plan pagado.
- Pesos colombianos: se usa la TRM oficial vigente hoy (dataset `32sa-8pi3` de datos.gov.co), guardada en memoria 12 horas. Si no se puede consultar, se usa el último valor obtenido, luego `USD_TO_COP_FALLBACK`; si no hay ninguno, `cost_cop` es `null` y la fuente es `unavailable`.

`GET /api/usage` devuelve: totales históricos y de hoy (`all_time`, `today`), promedio de tokens y de costo por pregunta, desglose por modelo (`by_model`) y por día de los últimos 30 días en hora de Colombia (`by_day`), la tasa usada (`exchange_rate`: valor, fecha y fuente), la tabla de precios (`pricing`, con enlace y fecha de consulta) y la nota sobre el plan gratuito (`note`). `unpriced_calls` cuenta las llamadas sin precio conocido, que no se suman al costo.

## Pruebas y calidad

```bash
pytest
ruff check .
```

Las pruebas no usan internet ni Gemini: trabajan con archivos sintéticos, bases DuckDB pequeñas creadas en cada prueba y un modelo de lenguaje falso con respuestas programadas.
