# Backend — Agente de verificación de información pública (San Cristóbal)

API en FastAPI y canal de ingesta de datos abiertos para el agente de la Alcaldía Local de San Cristóbal (código de localidad 4). Ver `../docs/PRD.md`.

Incluye la ingesta de datos, la API base y el **núcleo del agente** (fase 2): chat con Gemini que solo explica cifras calculadas por herramientas determinísticas, con evidencia trazable, contraste entre fuentes y registro de vacíos de información.

## Fuentes que se ingieren

| ID | Fuente | Tabla DuckDB | Fecha de corte |
|---|---|---|---|
| F1 | Ejecución PAC — Fondos de Desarrollo Local (un CSV por mes) | `f1_pac_execution` | Último mes publicado (`AAAA-MM`) |
| F2 | PQRS Secretaría Distrital de Gobierno 2022–2026 | `f2_pqrs` | Última fecha de radicación |
| F3 | Presupuestos Participativos — avance de propuestas | `f3_pp_progress` | Fecha incluida en la URL del archivo |
| F3 | Presupuestos Participativos — presupuesto comprometido | `f3_pp_commitments` | Fecha incluida en la URL del archivo |

Cada tabla tiene un registro en `source_metadata` (fuente, URL del portal, URLs de los archivos, fecha de corte, filas, unidad y fecha de ingesta).

Decisiones de limpieza importantes:
- **F1:** se conservan solo las filas con código `0000-00` (se descartan la fila `Total`, las filas vacías y las tablas basura del pie). Cada mes debe tener exactamente 20 localidades; si no, la fuente falla. Las celdas vacías quedan vacías (`NULL`): nunca se imputan. La unidad de los valores **no está documentada** (probablemente millones de pesos).
- **F2:** por privacidad, solo se leen 11 columnas; las de texto libre (`OBSERVACION_*`) y las de usuarios nunca se cargan. `response_days` está en días calendario; los valores negativos (errores de la fuente) quedan en `NULL`.
- **F3:** solo se lee la primera hoja de cada `.ods` y se normalizan los nombres de sector (mayúsculas, sin tildes).

## Estructura (arquitectura hexagonal)

```
app/
  domain/          entidades (SourceMetadata, Evidence, ChatAnswer, GapRecord...)
  ports/           interfaces: CatalogPort, DataStorePort, AnalyticsPort, LLMPort, GapRepositoryPort
  adapters/ckan/   cliente HTTP del portal CKAN con caché en disco
  adapters/duckdb/ almacenamiento en DuckDB (+ gap_repository.py: tabla gap_log)
  adapters/llm/    adaptador de Gemini (google-genai, function calling manual)
  ingestion/       funciones puras de limpieza por fuente (sin red)
  application/     casos de uso IngestSources y AskQuestion; herramientas del agente,
                   validador de respuestas, enmascarado de datos personales y prompts
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
| `GEMINI_API_KEY` | (vacía) | Clave de Gemini. Sin ella `POST /api/chat` responde 503; el resto de la API funciona |
| `GEMINI_MODEL` | `gemini-flash-latest` | Modelo de Gemini usado por el chat |
| `GEMINI_TEMPERATURE` | `0.2` | Temperatura del modelo (baja: respuestas estables) |
| `GAP_LOG_PATH` | `data/gap_log.duckdb` | Base DuckDB con la tabla `gap_log` (vacíos de información) |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `20` | Preguntas por minuto permitidas por cliente (en memoria) |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Orígenes permitidos (formato JSON), p. ej. el frontend de Vite |

Ejemplo de `.env`:

```bash
GEMINI_API_KEY=tu-clave
GEMINI_MODEL=gemini-flash-latest
```

La clave solo vive en el backend; nunca se envía al frontend.

Nunca subas el archivo `.env` al repositorio.

## Ingesta de datos

```bash
python -m app.cli ingest              # todas las fuentes
python -m app.cli ingest --source F1  # una sola fuente (F1, F2 o F3)
```

- Descarga los archivos desde https://datosabiertos.bogota.gov.co y los guarda en `data/raw` (caché). Para forzar una descarga nueva, borra esa carpeta.
- Si una fuente falla, las demás se ingieren igual; el comando muestra el reporte y termina con código 1.

## API

```bash
uvicorn app.api.main:app --reload
```

- `GET /health` → `{"status": "ok"}`
- `GET /api/sources` → fuentes cargadas con su fecha de corte (`data_cutoff`) y metadatos de trazabilidad
- `POST /api/chat` → pregunta ciudadana (ver abajo)
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
  "disclaimer": "Este asistente no es vocero oficial de la Alcaldía. …"
}
```

- `question`: texto de 1 a 500 caracteres. `status`: `answered`, `information_gap` o `needs_clarification`.
- `comparison` aparece cuando se usó el contraste entre presupuestos participativos y compromisos; trae el veredicto `coherent` / `difference_detected` / `not_comparable` y ambos valores.
- Códigos: `429` si se superan las preguntas por minuto, `503` si falta `GEMINI_API_KEY`, `502` si Gemini no responde.

Cómo funciona (PRD 8.1–8.2):
1. Se enmascaran datos personales de la pregunta (correos, teléfonos, números tipo cédula; los años se conservan). Gemini y los registros solo ven la versión enmascarada.
2. Gemini elige herramientas de una lista cerrada (`list_sources`, `get_budget_execution`, `get_pqrs_stats`, `get_participatory_budget`, `compare_participatory_budget_vs_commitments`, `report_information_gap`). **No escribe SQL**: los parámetros se validan y se aplican como filtros de texto plano. Máximo 5 rondas.
3. Las herramientas calculan todas las cifras y el veredicto del contraste, y entregan evidencia con ids `E1, E2…` asignados por el código.
4. Gemini redacta la respuesta final en JSON estructurado citando esos ids.
5. Un validador descarta ids inexistentes y rechaza respuestas con cifras sin evidencia ("No pude verificar esta respuesta…"). Todo vacío de información se guarda en `gap_log` (pregunta enmascarada, tema, dato faltante, motivo; nunca la IP).

## Pruebas y calidad

```bash
pytest
ruff check .
```

Las pruebas no usan internet ni Gemini: trabajan con archivos sintéticos, bases DuckDB pequeñas creadas en cada prueba y un modelo de lenguaje falso con respuestas programadas.
