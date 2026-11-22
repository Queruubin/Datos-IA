# PRD — Agente de Verificación de Información Pública · Alcaldía Local de San Cristóbal

| Campo | Valor |
|---|---|
| Versión | 0.1 (borrador) |
| Fecha | 2026-11-22 |
| Equipo | Jonathan Smit Morera Linares, Sergio Aramis Villanue, Hernán Stiben Paipilla, Samuel Felipe Castelblanco, Miguel Iván Piragua Padilla |
| Reto de origen | Ficha Reto Datos DDIPEA — Secretaría General: *"¿Cómo puede el Distrito usar los datos que ya produce como palanca para fortalecer la confianza ciudadana?"* |
| Documento base | `Proyecto Datos & inteligencia artificial San Cristobal.pdf` |

---

## 1. Resumen

Aplicación web con un agente de IA (Gemini) que permite a cualquier ciudadano preguntar en lenguaje natural sobre la gestión de la Alcaldía Local de San Cristóbal (inversión, ejecución presupuestal, presupuestos participativos, PQRS) y recibir una respuesta **sustentada en datos oficiales, con la fuente citada**. Cuando el dato no existe, el agente lo dice y registra el vacío. La Alcaldía recibe un panel con los vacíos de información y los temas más consultados.

**Propuesta de valor para la Alcaldía:** convierte datos que ya publica en confianza verificable, y le entrega un mapa basado en evidencia de qué información debería empezar a medir o publicar.

## 2. Problema

1. La información de gestión de San Cristóbal está dispersa: portal de Datos Abiertos Bogotá (datasets distritales filtrables por localidad), sitio web de la Alcaldía Local (POAI, informes en PDF) y tableros.
2. El ciudadano no tiene la alfabetización de datos para leer un CSV de ejecución PAC o un POAI.
3. No hay forma sencilla de verificar si lo planeado (POAI) coincide con lo ejecutado (PAC) o lo priorizado por la comunidad (presupuestos participativos).
4. La Alcaldía no sabe qué preguntas ciudadanas quedan sin respuesta por falta de datos.

## 3. Usuarios

| Persona | Necesidad | Uso principal |
|---|---|---|
| **Ciudadano/a de San Cristóbal** | Entender en qué se invierte y si se cumple, sin conocimientos técnicos | Chat de preguntas |
| **Líder comunitario / JAL / veedor** | Verificar avance de proyectos y propuestas priorizadas | Chat + vista de contraste |
| **Funcionario de la Alcaldía Local** | Saber qué preguntan, qué falta y dónde hay inconsistencias | Panel de vacíos e insights |

## 4. Objetivos y no-objetivos

### Objetivos (MVP)
- **O1.** Responder preguntas sobre la gestión local con evidencia trazable (dataset, archivo, fila/página, fecha de corte).
- **O2.** Contrastar automáticamente al menos un par de fuentes equivalentes (p. ej. presupuesto planeado vs. ejecutado).
- **O3.** Detectar, registrar y agrupar preguntas sin respuesta como vacíos de información.
- **O4.** Ofrecer a la Alcaldía un panel con vacíos, temas frecuentes e inconsistencias.

### No-objetivos
- No es vocero oficial ni emite juicios de valor sobre la gestión.
- No modifica datos fuente.
- No cubre otras localidades en el MVP (la arquitectura sí debe permitirlo después).
- No maneja datos personales: no se piden ni se guardan datos que identifiquen al ciudadano.
- No incluye autenticación ciudadana.

## 5. Fuentes de datos

Verificado contra la API CKAN de `datosabiertos.bogota.gov.co` el 2026-11-22.

**Hallazgo clave:** el portal **no publica el POAI** de San Cristóbal (0 resultados). Casi todos los datasets son distritales y se filtran por localidad. El POAI y los informes de gestión se toman del sitio de la Alcaldía Local, cargados manualmente.

| # | Fuente | Origen | Formato | Filtro San Cristóbal | Uso |
|---|---|---|---|---|---|
| F1 | Ranking mensual de recursos ejecutados de PAC — Fondos de Desarrollo Local (SDH) | Portal | CSV mensual | Fila `0004 San Cristobal` ✅ verificado | Ejecución presupuestal |
| F2 | PQRS Secretaría Distrital de Gobierno 2022–2026 | Portal | CSV | `NOMBRE_LOCALIDAD = ALCALDIA LOCAL DE SAN CRISTOBAL` ✅ columna verificada | Qué pide la ciudadanía, tiempos de respuesta |
| F3 | Presupuestos Participativos Bogotá (SDP) — avance de propuestas priorizadas y presupuesto comprometido por meta | Portal | ODS | `No_Localidad = 4` ✅ verificado (232 propuestas, 78 compromisos) | Lo que priorizó la comunidad y su avance |
| F4 | Hábitat en cifras en las localidades (indicadores demográficos y urbanos) | Portal | XLSX | Por localidad | Contexto territorial |
| F5 | POAI e informes de gestión de la Alcaldía Local | Sitio web de la Alcaldía Local | PDF/XLSX | Nativo | Lo planeado (metas, recursos) |
| F6 | Encuesta Multipropósito 2021/2025 (opcional, fase 2) | Portal | CSV | Por localidad | Percepción y contexto |

**Contraste del MVP:** F5 (planeado) ↔ F1 (ejecutado) ↔ F3 (priorizado y comprometido). Sobre este eje se demuestra la capacidad de verificación.

Cada registro ingerido guarda **metadatos de trazabilidad**: `source_id`, URL de origen, nombre del archivo, fecha de corte, fecha de ingesta y número de fila o página.

## 6. Requisitos funcionales

### RF1 — Chat ciudadano con evidencia
- El usuario escribe una pregunta en español coloquial.
- El agente responde en lenguaje claro y **siempre** adjunta tarjetas de evidencia: fuente, fecha de corte, enlace y valor citado.
- Si la confianza es baja, pide aclaración en vez de inventar.
- **Criterio de aceptación:** el 100 % de las respuestas con cifras incluye al menos una cita trazable. Una respuesta con cifra sin cita es un fallo.

### RF2 — Contraste entre fuentes
- Para preguntas de tipo *"¿se cumplió / cuánto se ejecutó de X?"*, el agente compara las fuentes equivalentes y muestra un veredicto neutral: **Coherente / Diferencia detectada / No comparable**, con ambos valores lado a lado.
- La comparación numérica es **determinística (código)**, no la hace el LLM. Gemini solo la explica.
- **Criterio:** en un set de prueba de contrastes conocidos, el veredicto coincide con el cálculo manual en el 100 % de los casos.

### RF3 — Detección de vacíos de información
- Si ninguna fuente responde la pregunta, el agente lo dice explícitamente, sugiere qué dato haría falta y registra el evento (pregunta anonimizada, tema, dato faltante sugerido).
- Gemini clasifica los vacíos en una taxonomía de temas (p. ej. seguridad, vías, salud, cultura, contratación).
- **Criterio:** las preguntas fuera de las fuentes no reciben una respuesta inventada. Se mide con un set adversarial.

### RF4 — Panel de la Alcaldía
- Temas más consultados, vacíos agrupados con su frecuencia, contrastes con diferencia detectada y preguntas de ejemplo.
- Exportación CSV.
- Acceso protegido con una credencial simple de administrador en el MVP.

### RF5 — Ingesta y actualización de datos
- Script/CLI que descarga F1–F4 desde la API CKAN, filtra San Cristóbal, normaliza y carga.
- Carga manual de los PDF/XLSX de F5.
- Muestra en la UI la fecha de corte de cada fuente.

### RF6 — Transparencia del agente
- Aviso visible: *"Este asistente no es vocero oficial de la Alcaldía. Las respuestas se basan en datos públicos con la fecha de corte indicada."*

## 7. Requisitos no funcionales

| Área | Requisito |
|---|---|
| Latencia | p95 < 8 s por respuesta |
| Costo | Uso de un modelo Gemini de baja latencia y bajo costo (familia Flash) para el chat; cache de respuestas frecuentes |
| Privacidad | Sin login ciudadano; las preguntas se guardan sin IP ni datos personales; si la pregunta contiene PII (nombres, cédulas), se enmascara antes de guardarla |
| Seguridad | API key de Gemini solo en el backend (variables de entorno); rate limiting por IP; defensa contra prompt injection (el LLM no ejecuta SQL libre, solo herramientas predefinidas) |
| Accesibilidad | WCAG 2.1 AA básico, mobile-first (gran parte del acceso es desde celular) |
| Idioma | Español neutro, lenguaje claro |
| Mantenibilidad | Arquitectura hexagonal: las fuentes y el proveedor LLM son adaptadores intercambiables |

## 8. Diseño de la solución

### 8.1 Decisión clave: herramientas sobre datos estructurados + RAG solo para documentos

La propuesta original habla de RAG. Pero la mayoría de las fuentes (F1–F4) son **tablas con cifras**, y hacer RAG con embeddings sobre números da respuestas imprecisas. Por eso:

- **Datos tabulares → function calling de Gemini** sobre herramientas predefinidas que consultan una base analítica (DuckDB/SQLite). Ejemplos: `get_budget_execution(year, month)`, `get_participatory_projects(status)`, `get_pqrs_stats(topic, year)`, `compare_planned_vs_executed(year, sector)`.
- **Documentos (POAI, informes en PDF) → RAG** con embeddings de Gemini y un vector store (ChromaDB), guardando página y fragmento para citar.
- **Contraste → código determinístico** que devuelve valores y veredicto; el LLM solo redacta la explicación.

### 8.2 Flujo de una pregunta
```
Pregunta → [Guardrails + enmascarado de PII]
        → Gemini (planner con function calling)
            ├─ tools de datos estructurados (DuckDB)
            ├─ tool de búsqueda documental (RAG / Chroma)
            └─ tool de contraste (determinístico)
        → Gemini (redacción con citas obligatorias, salida JSON estructurada)
        → Validador: ¿cada cifra tiene cita? ¿hay evidencia?
            ├─ sí → respuesta + tarjetas de evidencia
            └─ no → respuesta de "vacío de información" + registro en gap_log
```

### 8.3 Arquitectura (hexagonal)
```
backend/
  app/
    domain/          # entidades: Source, Evidence, Answer, Gap, Comparison
    application/     # casos de uso: AskQuestion, CompareSources, DetectGap, IngestSource
    ports/           # LLMPort, DataRepositoryPort, DocumentIndexPort, GapRepositoryPort
    adapters/
      llm/gemini/
      data/duckdb/
      documents/chroma/
      sources/ckan/  # cliente de la API de Datos Abiertos Bogotá
    api/             # routers FastAPI
  ingestion/         # CLI de ingesta
frontend/            # React + Vite + TypeScript + TailwindCSS
```

### 8.4 Stack
| Capa | Tecnología |
|---|---|
| LLM | Google Gemini (SDK `google-genai`); modelo Flash para chat, modelo de embeddings de Gemini para RAG. Versiones exactas a fijar al iniciar |
| Backend | Python 3.12, FastAPI, Pydantic v2, uv |
| Datos | DuckDB (analítica) + SQLite (logs de vacíos y consultas) |
| Vector store | ChromaDB (local) |
| Frontend | React + Vite + TypeScript + TailwindCSS, Recharts para gráficos |
| Testing | pytest (backend), Vitest + Testing Library (frontend), set de evaluación de preguntas |
| Despliegue (demo) | Docker Compose; opcional Render/Railway (back) + Vercel (front) |

### 8.5 API (borrador)
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/chat` | `{question, session_id}` → `{answer, evidence[], comparison?, gap?}` |
| GET | `/api/sources` | Fuentes cargadas con fecha de corte |
| GET | `/api/admin/gaps` | Vacíos agrupados por tema (requiere auth) |
| GET | `/api/admin/insights` | Temas frecuentes, contrastes con diferencia |
| POST | `/api/admin/ingest` | Dispara la ingesta (requiere auth) |

## 9. Evaluación del agente

Set de evaluación versionado en el repo (`eval/questions.yaml`), mínimo 50 preguntas:
- 25 con respuesta conocida en las fuentes (se evalúa exactitud y cita correcta).
- 10 de contraste (se evalúa el veredicto).
- 15 fuera del alcance o sin datos (se evalúa que no alucine y que registre el vacío).

| Métrica | Meta MVP |
|---|---|
| Exactitud en preguntas con respuesta | ≥ 85 % |
| Respuestas con cifra y cita válida | 100 % |
| Alucinación en preguntas sin datos | ≤ 5 % |
| Veredicto de contraste correcto | 100 % |
| Latencia p95 | < 8 s |

Lo ideal es validar además con 5–10 personas reales de San Cristóbal (objetivo específico 5 de la propuesta).

## 10. Roadmap

| Fase | Entregable |
|---|---|
| **0. Datos** | Cliente CKAN, ingesta de F1–F3 filtradas a San Cristóbal, carga manual de F5, verificación de columnas |
| **1. Núcleo del agente** | Function calling con Gemini + tools de datos + citas obligatorias + validador |
| **2. RAG documental** | Indexación del POAI/informes y tool de búsqueda |
| **3. Contraste** | Planeado vs. ejecutado vs. priorizado, con veredicto |
| **4. Vacíos + panel** | Registro, clasificación por tema y panel de la Alcaldía |
| **5. Frontend** | Chat mobile-first con tarjetas de evidencia, panel admin |
| **6. Evaluación y demo** | Correr el set de evaluación, ajustar, Docker Compose, demo |

## 11. Riesgos

| Riesgo | Mitigación |
|---|---|
| El POAI no está en formato estructurado (solo PDF) | RAG sobre el PDF + extracción manual asistida de las tablas clave |
| Las fuentes usan nombres y cortes distintos y no se pueden emparejar | Tabla de mapeo manual (sector/meta ↔ concepto de gasto); veredicto "No comparable" cuando no hay equivalencia |
| Alucinación del LLM | Tools cerradas, citas obligatorias, validador post-respuesta, temperatura baja |
| Datos desactualizados | Mostrar siempre la fecha de corte; reingesta programada |
| Cuota/costo de la API de Gemini | Cache, modelo Flash, rate limiting |
| Se percibe como vocero oficial | Aviso permanente y tono neutral sin juicios de valor |

## 12. Preguntas abiertas
1. ~~¿F3 trae columna de localidad?~~ Sí (resuelto en la fase 0). Nueva: ¿en qué unidad están los valores de F1 (¿millones de pesos?), y hay datos de PAC posteriores a junio de 2025?
2. ¿Hay URL estable del POAI vigente de San Cristóbal, y de qué vigencia (2025/2026)?
3. ¿Cuál es el plazo de entrega y la fecha de la demo?
4. ¿Se puede conseguir un contacto en la Alcaldía Local para validar el panel?
