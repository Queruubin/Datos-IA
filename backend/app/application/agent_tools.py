"""Closed set of deterministic tools the LLM may call.

The LLM never writes SQL: it picks a tool and passes parameters, which are validated here
(types, ranges, whitelists) and applied as plain pandas filters over fixed tables and views.
Every figure the agent can mention comes from these functions, together with evidence records
whose ids are assigned by code (E1, E2...), never by the model.

Sources: the curated relational package (POAI, PMR, Presupuestos Participativos, CRP, ODS,
PQRS, SECOP II contracts; see `app.ingestion.curated`) and the PAC execution of the open-data
portal (F1).

Privacy: `pqrs.usuario_actual` (names of public officials) is never read: tools only use the
`vw_pqrs_detalle` view, which leaves it out, and `_read` drops it defensively anyway. Contractor
names are never loaded into the database (see `curated.CONTRACT_COLUMNS`).
"""

import logging
import math
import re
from collections.abc import Callable
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.domain import Evidence, SourceMetadata, ToolCall, ToolOutcome, ToolSpec
from app.ingestion.curated import (
    LINK_VERIFIED,
    PMR_2025_ROUNDING_COP,
    PMR_CHANGE_COLUMNS,
    pmr_changes,
)
from app.ingestion.text import normalize_label
from app.ports import AnalyticsPort

logger = logging.getLogger(__name__)

# Tables and views (fixed names: the model never chooses them).
PAC_TABLE = "f1_pac_execution"
POAI_TABLE = "poai"
PMR_TABLE = "seguimiento_meta"
PMR_LATEST_VIEW = "vw_seguimiento_meta_ultimo_corte"
POAI_PMR_VIEW = "vw_calidad_poai_pmr"
META_VIEW = "vw_meta_contexto"
ODS_VIEW = "vw_meta_ods_detalle"
PROPOSAL_TABLE = "propuesta_ciudadana"
FOLLOW_UP_TABLE = "seguimiento_propuesta"
CRP_TABLE = "crp"
CRP_LINES_TABLE = "crp_meta"
CRP_PROPOSAL_TABLE = "crp_propuesta"
PQRS_VIEW = "vw_pqrs_detalle"
CONTRACT_TABLE = "contrato"
CONTRACT_LINK_TABLE = "contrato_vinculo"

# Columns that must never leave the database through a tool (`contratista` is never loaded;
# listed defensively).
PRIVATE_COLUMNS = frozenset({"usuario_actual", "contratista"})

PAC_UNIT_NOTE = (
    "Unidad no documentada por la fuente (probablemente millones de pesos). "
    "No afirmar que son pesos."
)
COP_NOTE = "Pesos colombianos (COP), según la documentación del paquete curado."
PAC_LOCALITIES = 20
PQRS_CLOSED_STATE = "TRAMITE CERRADO"
# Proposal states that imply the proposal should already have committed funding (CRP).
FUNDED_STATES = ("CONTRATADA", "EN EJECUCION", "MATERIALIZADA")
TOP_N = 10
MAX_SAMPLES = 10
MAX_DETAILS = 5  # proposals shown in full when a name search matches several
MAX_GROUPS = 15
MAX_DIFFERENCES = 15


# --- Parameter models (validation + whitelists) -------------------------------------------
class _Params(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


Year = int | None
Keyword = str | None


class NoParams(_Params):
    pass


class BudgetParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)


PqrsGroup = Literal[
    "subtema", "tipo_peticion", "vigencia", "medio_recepcion", "observacion_general"
]


class PqrsParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    topic_keyword: Keyword = Field(default=None, max_length=60)
    group_by: PqrsGroup = "subtema"


class ParticipatoryParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    sector_keyword: Keyword = Field(default=None, max_length=60)
    status: str | None = Field(default=None, max_length=40)
    proposal: Keyword = Field(default=None, min_length=3, max_length=80)


class ContrastParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    sector_keyword: Keyword = Field(default=None, max_length=60)


ProjectCode = str | None


class PlanParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    sector_keyword: Keyword = Field(default=None, max_length=60)
    ods_keyword: Keyword = Field(default=None, max_length=60)
    project_code: ProjectCode = Field(default=None, pattern=r"^\d{3,6}$")
    group_by: Literal["sector", "proyecto", "meta"] = "sector"


class GoalParams(_Params):
    meta_code: str | None = Field(default=None, pattern=r"^\d{3,10}$")
    keyword: Keyword = Field(default=None, min_length=3, max_length=60)

    @model_validator(mode="after")
    def _exactly_one(self) -> "GoalParams":
        if (self.meta_code is None) == (self.keyword is None):
            raise ValueError("Indica meta_code o keyword (solo uno).")
        return self


class YearParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)


class ChangesParams(_Params):
    domain: Literal["pmr", "participatory_budget"]
    year: Year = Field(default=None, ge=2000, le=2100)


class OdsParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    ods_keyword: Keyword = Field(default=None, max_length=60)


ContractGroup = Literal["proyecto", "meta", "estado", "vigencia"]


class ContractParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    project_code: ProjectCode = Field(default=None, pattern=r"^\d{3,6}$")
    meta_code: str | None = Field(default=None, pattern=r"^\d{3,10}$")
    object_keyword: Keyword = Field(default=None, min_length=3, max_length=80)
    status: str | None = Field(default=None, max_length=40)
    group_by: ContractGroup = "proyecto"
    verified_only: bool = False


class GapParams(_Params):
    topic: str = Field(min_length=1, max_length=120)
    missing_data: str = Field(min_length=1, max_length=300)


_YEAR_SCHEMA = {"type": "integer", "description": "Año (vigencia), p. ej. 2025. Omitir = todos."}
_PLAN_YEAR_SCHEMA = {
    "type": "integer",
    "description": "Vigencia del POAI (2025 o 2026). Omitir = la más reciente.",
}
_SECTOR_SCHEMA = {"type": "string", "description": "Palabra del sector, p. ej. 'cultura'."}
_ODS_SCHEMA = {
    "type": "string",
    "description": "Número u otra palabra del ODS, p. ej. '11' o 'pobreza'.",
}

TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="list_sources",
        description=(
            "Lista las fuentes de datos cargadas con su título, origen, unidad y fecha de corte."
        ),
        parameters_json_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="get_budget_execution",
        description=(
            "Ejecución del PAC (Plan Anual de Caja) del Fondo de Desarrollo Local de San "
            "Cristóbal: valor programado vs ejecutado por mes, totales y puesto entre las 20 "
            "localidades de Bogotá (2024 a junio de 2025). La unidad monetaria NO está "
            "documentada. Para inversión por metas usa get_plan_vs_execution."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": _YEAR_SCHEMA,
                "month": {"type": "integer", "minimum": 1, "maximum": 12,
                          "description": "Mes 1-12. Omitir = todos los meses."},
            },
        },
    ),
    ToolSpec(
        name="get_plan_vs_execution",
        description=(
            "Inversión planeada vs ejecutada por metas del plan local: valor del POAI "
            "(planeado, en pesos) frente al seguimiento PMR del último corte (presupuesto "
            "programado, compromisos, giros, % comprometido y % girado, y magnitudes "
            "programada/contratada/entregada). Agrupa por sector, proyecto o meta y filtra "
            "por sector, ODS o código de proyecto. Úsala para '¿cuánto se programó para el "
            "proyecto 2791?' (project_code='2791', group_by='meta')."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": _PLAN_YEAR_SCHEMA,
                "sector_keyword": _SECTOR_SCHEMA,
                "ods_keyword": _ODS_SCHEMA,
                "project_code": {
                    "type": "string",
                    "description": "Código del proyecto de inversión (3 a 6 dígitos, p. ej. "
                                   "'2791'). Las metas de un proyecto tienen códigos que "
                                   "empiezan por el del proyecto (27911, 27912...).",
                },
                "group_by": {"type": "string", "enum": ["sector", "proyecto", "meta"]},
            },
        },
    ),
    ToolSpec(
        name="get_goal_detail",
        description=(
            "Ficha completa de UNA meta del plan local: proyecto, programa, objetivo "
            "estratégico, sector, entidad, ODS, POAI por año, seguimiento PMR, propuestas "
            "ciudadanas vinculadas (estado) y compromisos CRP con sus valores. Busca por "
            "código de meta (p. ej. 22511) o por palabra (p. ej. 'malla vial'); si hay varias "
            "coincidencias devuelve la lista para elegir."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "meta_code": {"type": "string",
                              "description": "Código de meta extendido, solo dígitos."},
                "keyword": {"type": "string",
                            "description": "Palabra de la meta o del proyecto."},
            },
        },
    ),
    ToolSpec(
        name="compare_poai_vs_pmr",
        description=(
            "Contraste determinístico, meta por meta, entre lo planeado en el POAI y lo "
            "reportado en el PMR para una vigencia: presupuesto y magnitud programada. "
            "Devuelve el veredicto calculado por código y la lista de metas con diferencias."
        ),
        parameters_json_schema={"type": "object", "properties": {"year": _PLAN_YEAR_SCHEMA}},
    ),
    ToolSpec(
        name="get_changes_between_cutoffs",
        description=(
            "Qué cambió entre fechas de corte: 'pmr' (seguimiento de metas: magnitudes, "
            "compromisos y giros entre marzo y junio de 2026) o 'participatory_budget' "
            "(estados de las propuestas ciudadanas entre marzo y octubre de 2026). Devuelve "
            "conteos y ejemplos."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "enum": ["pmr", "participatory_budget"]},
                "year": {"type": "integer",
                         "description": "Vigencia. Omitir = la más reciente."},
            },
            "required": ["domain"],
        },
    ),
    ToolSpec(
        name="get_investment_by_ods",
        description=(
            "Inversión del POAI (en pesos) y compromisos/giros del PMR agrupados por Objetivo "
            "de Desarrollo Sostenible (ODS). Con ods_keyword muestra el detalle por meta ODS."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {"year": _PLAN_YEAR_SCHEMA, "ods_keyword": _ODS_SCHEMA},
        },
    ),
    ToolSpec(
        name="get_pqrs_stats",
        description=(
            "Estadísticas de PQRS (peticiones, quejas, reclamos) radicadas ante la Alcaldía "
            "Local de San Cristóbal 2022-2026: cantidad, mediana de días de respuesta, % "
            "cerradas, estado de la respuesta (p. ej. 'Sin respuesta al peticionario') y top 10."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": _YEAR_SCHEMA,
                "topic_keyword": {
                    "type": "string",
                    "description": "Palabra para filtrar por subtema, p. ej. 'vias'.",
                },
                "group_by": {
                    "type": "string",
                    "enum": ["subtema", "tipo_peticion", "vigencia", "medio_recepcion",
                             "observacion_general"],
                },
            },
        },
    ),
    ToolSpec(
        name="get_participatory_budget",
        description=(
            "Presupuestos participativos de San Cristóbal (último corte): propuestas "
            "ciudadanas por estado y metodología, población beneficiada reportada, ejemplos y "
            "valor comprometido en CRP (pesos). Con 'proposal' sigue una propuesta puntual "
            "(por nombre o código): estado en cada corte, avance y CRP asociados."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": {"type": "integer",
                         "description": "Vigencia de ejecución, p. ej. 2025. Omitir = todas."},
                "sector_keyword": _SECTOR_SCHEMA,
                "status": {"type": "string",
                           "description": "Estado de la propuesta, p. ej. 'Materializada'."},
                "proposal": {
                    "type": "string",
                    "description": (
                        "Nombre (o parte del nombre) o código de una propuesta ciudadana, "
                        "p. ej. 'Internet a mi barrio' o '41411'. Úsalo cuando la pregunta "
                        "nombra una iniciativa concreta; no lo pongas en sector_keyword."
                    ),
                },
            },
        },
    ),
    ToolSpec(
        name="compare_participatory_budget_vs_commitments",
        description=(
            "Contraste determinístico: verifica si las propuestas que deberían tener recursos "
            "(Contratada, En ejecución, Materializada) aparecen en algún compromiso "
            "presupuestal (CRP) del mismo año. Devuelve el veredicto calculado por código."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": _YEAR_SCHEMA,
                "sector_keyword": _SECTOR_SCHEMA,
            },
        },
    ),
    ToolSpec(
        name="get_contracts",
        description=(
            "Contratos de la Alcaldía Local de San Cristóbal en SECOP II (vigencias 2025 y "
            "2026) y su vínculo con proyectos y metas del plan local: cantidad de contratos, "
            "valor contratado (valor firmado, contado una vez por contrato; NO es lo ejecutado "
            "ni lo pagado), cuántos tienen el vínculo verificado o pendiente de verificación, "
            "agrupación por proyecto, meta, estado o vigencia, y ejemplos con enlace público. "
            "Úsala para preguntas sobre contratación o contratos, p. ej. '¿qué contratos tiene "
            "el proyecto 2251?' (project_code='2251') o 'contratos de la meta 22511' "
            "(meta_code='22511'). No devuelve nombres de contratistas."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": {"type": "integer",
                         "description": "Vigencia del contrato (2025 o 2026). Omitir = todas."},
                "project_code": {"type": "string",
                                 "description": "Código del proyecto (3 a 6 dígitos, p. ej. "
                                                "'2251')."},
                "meta_code": {"type": "string",
                              "description": "Código de meta extendido, solo dígitos (p. ej. "
                                             "'22511')."},
                "object_keyword": {
                    "type": "string",
                    "description": "Palabra del objeto del contrato, p. ej. 'malla vial'.",
                },
                "status": {"type": "string",
                           "description": "Estado del contrato, p. ej. 'En ejecución', "
                                          "'Cerrado', 'Modificado'."},
                "group_by": {"type": "string", "enum": ["proyecto", "meta", "estado",
                                                        "vigencia"]},
                "verified_only": {
                    "type": "boolean",
                    "description": "true = solo vínculos verificados con el proyecto (o con la "
                                   "meta si se da meta_code). Por defecto false.",
                },
            },
        },
    ),
    ToolSpec(
        name="report_information_gap",
        description=(
            "Úsala cuando ninguna otra herramienta puede responder la pregunta: registra el "
            "tema y el dato que haría falta publicar."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "topic": {"type": "string",
                          "description": "Tema, p. ej. seguridad, vías, salud, empleo."},
                "missing_data": {"type": "string", "description": "Dato que haría falta."},
            },
            "required": ["topic", "missing_data"],
        },
    ),
]

# Tools whose result carries a code-computed verdict shown to the citizen.
COMPARISON_TOOLS = frozenset({"compare_participatory_budget_vs_commitments",
                              "compare_poai_vs_pmr"})


class EvidenceLedger:
    """Assigns unique evidence ids (E1, E2...) within one question."""

    def __init__(self) -> None:
        self.items: list[Evidence] = []

    def add(self, meta: SourceMetadata | None, table: str, locator: str, summary: str) -> Evidence:
        evidence = Evidence(
            id=f"E{len(self.items) + 1}",
            source_id=meta.source_id if meta else table,
            title=meta.title if meta else table,
            data_cutoff=meta.data_cutoff if meta else None,
            portal_url=meta.portal_url if meta else None,
            locator=locator,
            summary=summary,
            origin_note=meta.origin_note if meta else None,
        )
        self.items.append(evidence)
        return evidence

    def ids(self) -> set[str]:
        return {item.id for item in self.items}


class _NoData(Exception):
    """A valid request with nothing to compute (e.g. a year without data): answered as data."""

    def __init__(self, payload: dict[str, Any]) -> None:
        super().__init__(payload.get("error", "sin datos"))
        self.payload = payload


class AgentTools:
    """Executes tool calls over the read-only analytics port."""

    def __init__(self, analytics: AnalyticsPort) -> None:
        self._analytics = analytics
        self._handlers: dict[str, tuple[type[_Params], Callable[..., Any]]] = {
            "list_sources": (NoParams, self._list_sources),
            "get_budget_execution": (BudgetParams, self._budget_execution),
            "get_plan_vs_execution": (PlanParams, self._plan_vs_execution),
            "get_goal_detail": (GoalParams, self._goal_detail),
            "compare_poai_vs_pmr": (YearParams, self._poai_vs_pmr),
            "get_changes_between_cutoffs": (ChangesParams, self._changes_between_cutoffs),
            "get_investment_by_ods": (OdsParams, self._investment_by_ods),
            "get_pqrs_stats": (PqrsParams, self._pqrs_stats),
            "get_participatory_budget": (ParticipatoryParams, self._participatory_budget),
            "compare_participatory_budget_vs_commitments": (ContrastParams, self._contrast),
            "get_contracts": (ContractParams, self._contracts),
            "report_information_gap": (GapParams, self._report_gap),
        }

    @staticmethod
    def specs() -> list[ToolSpec]:
        return list(TOOL_SPECS)

    def execute(self, call: ToolCall, ledger: EvidenceLedger) -> ToolOutcome:
        handler = self._handlers.get(call.name)
        if handler is None:
            return ToolOutcome(call, data=None, error=f"Herramienta desconocida: {call.name}")
        params_model, function = handler
        try:
            params = params_model.model_validate(call.args or {})
        except ValidationError as error:
            fields = sorted({".".join(map(str, e["loc"])) or "args" for e in error.errors()})
            return ToolOutcome(call, data=None, error=f"Parámetros inválidos: {', '.join(fields)}")
        try:
            data, evidence = function(params, ledger)
        except _NoData as empty:
            return ToolOutcome(call, data=_jsonable(empty.payload))
        except Exception:  # missing table, unreadable database...
            logger.exception("Tool %s failed", call.name)
            return ToolOutcome(call, data=None, error="La fuente de datos no está disponible.")
        return ToolOutcome(call, data=_jsonable(data), evidence=evidence)

    # --- helpers ---------------------------------------------------------------------------
    def _read(self, name: str) -> pd.DataFrame:
        frame = self._analytics.read_table(name)
        return frame.drop(columns=[c for c in frame.columns if c in PRIVATE_COLUMNS])

    def _sources(self) -> dict[str, SourceMetadata]:
        return {meta.source_id: meta for meta in self._analytics.read_source_metadata()}

    def _year(self, requested: int | None, available: pd.Series) -> int:
        """The requested vigencia, or the latest one; unknown years are answered as data."""
        years = sorted({int(y) for y in available.dropna()})
        if not years:
            raise _NoData({"error": "No hay datos cargados para esta consulta."})
        if requested is None:
            return years[-1]
        if requested not in years:
            raise _NoData({"error": "Vigencia sin datos", "available_years": years})
        return requested

    def _metas(self, sector: str | None = None, ods: str | None = None) -> pd.DataFrame:
        """Meta context (proyecto, programa, objetivo, sector, entidad) with optional filters."""
        metas = self._read(META_VIEW)
        if sector:
            metas = metas[_contains(metas["nombre_sector"], sector)]
        if ods:
            alignment = self._read(ODS_VIEW)
            metas = metas[metas["id_meta"].isin(
                alignment.loc[_ods_match(alignment, ods), "id_meta"]
            )]
        return metas

    def _plan_rows(self, year: int, metas: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
        """POAI planned value + latest PMR follow-up of `year`, one row per meta."""
        poai = self._read(POAI_TABLE)
        poai = poai[poai["vigencia"] == year][["id_meta", "valor_poai", "magnitud_programada"]]
        pmr = self._read(PMR_LATEST_VIEW)
        pmr = pmr[pmr["vigencia"] == year].drop(columns=["vigencia", "id_seguimiento_meta"])
        rows = metas.merge(poai, on="id_meta").merge(
            pmr, on="id_meta", how="left", suffixes=("_poai", "_pmr")
        )
        cutoff = _date_text(rows["fecha_corte"].max()) if len(rows) else None
        return rows, cutoff

    # --- tools -----------------------------------------------------------------------------
    def _list_sources(self, _: NoParams, ledger: EvidenceLedger):
        sources, evidence = [], []
        for meta in self._analytics.read_source_metadata():
            sources.append({
                "source_id": meta.source_id, "title": meta.title,
                "data_cutoff": meta.data_cutoff, "rows": meta.rows, "unit": meta.unit,
                "origin_note": meta.origin_note, "on_open_data_portal": bool(meta.portal_url),
            })
            evidence.append(ledger.add(
                meta, meta.table_name, f"{meta.table_name} (tabla completa)",
                f"Fuente cargada con {meta.rows} filas; fecha de corte {meta.data_cutoff}.",
            ))
        return {"sources": sources}, evidence

    def _budget_execution(self, params: BudgetParams, ledger: EvidenceLedger):
        frame = self._read(PAC_TABLE)
        available = sorted(
            f"{int(y)}-{int(m):02d}" for y, m in zip(frame["year"], frame["month"], strict=True)
        )
        rows = frame
        if params.year is not None:
            rows = rows[rows["year"] == params.year]
        if params.month is not None:
            rows = rows[rows["month"] == params.month]
        rows = rows.sort_values(["year", "month"])

        months = [
            {
                "year": int(row.year), "month": int(row.month),
                "programmed": row.pac_programmed, "executed": row.pac_executed,
                "pct_executed": _pct(row.pac_executed, row.pac_programmed),
                "rank_in_month": row.rank_in_month,
                "rank_note": f"1 = mejor ejecución entre {PAC_LOCALITIES} localidades",
            }
            for row in rows.itertuples()
        ]
        programmed = float(rows["pac_programmed"].sum(skipna=True))
        executed = float(rows["pac_executed"].sum(skipna=True))
        data = {
            "locality": "San Cristóbal",
            "unit": PAC_UNIT_NOTE,
            "months": months,
            "totals": {
                "programmed": programmed, "executed": executed,
                "pct_executed": _pct(executed, programmed),
            } if months else None,
            "available_periods": f"{available[0]} a {available[-1]}" if available else None,
        }
        locator = f"{PAC_TABLE} · {_filters(year=params.year, month=params.month)}"
        if months:
            summary = (
                f"{len(months)} mes(es): programado {programmed:,.0f}, ejecutado {executed:,.0f} "
                f"({data['totals']['pct_executed']}%). Unidad no documentada."
            )
        else:
            summary = "Sin registros para el filtro."
        return data, [ledger.add(self._sources().get("F1"), PAC_TABLE, locator, summary)]

    def _plan_vs_execution(self, params: PlanParams, ledger: EvidenceLedger):
        year = self._year(params.year, self._read(POAI_TABLE)["vigencia"])
        metas = self._metas(params.sector_keyword, params.ods_keyword)
        if params.project_code:
            metas = metas[metas["codigo_proyecto"].astype(str) == params.project_code]
            if metas.empty:
                raise _NoData({
                    "found": 0,
                    "message": f"No hay ningún proyecto con el código {params.project_code} "
                               "en el plan local de San Cristóbal.",
                    "search": _filters(project_code=params.project_code),
                })
        rows, cutoff = self._plan_rows(year, metas)

        if params.group_by == "meta":
            keys = ["codigo_meta_extendida", "descripcion_meta", "nombre_sector"]
        elif params.group_by == "proyecto":
            keys = ["codigo_proyecto", "nombre_proyecto"]
        else:
            keys = ["nombre_sector"]
        groups = []
        for key, group in rows.groupby(keys, sort=False, dropna=False):
            item = dict(zip(keys, key if isinstance(key, tuple) else (key,), strict=True))
            item.update(_money_block(group))
            if params.group_by == "meta":
                row = group.iloc[0]
                item.update({
                    "magnitud_poai": row["magnitud_programada_poai"],
                    "magnitud_programada_pmr": row["magnitud_programada_pmr"],
                    "magnitud_contratada": row["magnitud_contratada"],
                    "magnitud_entregada": row["magnitud_entregada"],
                    "pct_entregado": _pct(row["magnitud_entregada"],
                                          row["magnitud_programada_pmr"]),
                })
            else:
                item.update(_delivery_counts(group))
            groups.append(item)
        groups.sort(key=lambda item: -(item["valor_poai"] or 0))

        totals = {**_money_block(rows), **_delivery_counts(rows)}
        data = {
            "year": year,
            "group_by": params.group_by,
            "unit": COP_NOTE,
            "pmr_cutoff": cutoff,
            "totals": totals,
            "groups": groups[:MAX_GROUPS],
            "groups_total": len(groups),
            "notes": [
                "valor_poai = planeado en el POAI; presupuesto_programado, compromisos y giros "
                "= seguimiento PMR en su último corte.",
                "pct_comprometido y pct_girado se calculan sobre el presupuesto programado "
                "del PMR; pueden superar 100 % si la fuente reporta más compromisos que "
                "presupuesto.",
                "Las magnitudes tienen unidades distintas por meta: solo se muestran por meta; "
                "en grupos se cuentan metas con entrega completa o sin entregas.",
            ],
        }
        filters = _filters(year=year, sector_keyword=params.sector_keyword,
                           ods_keyword=params.ods_keyword, project_code=params.project_code,
                           group_by=params.group_by)
        sources = self._sources()
        evidence = [
            ledger.add(
                sources.get("POAI"), POAI_TABLE, f"{POAI_TABLE} + {META_VIEW} · {filters}",
                f"{totals['metas']} metas; valor POAI {year}: {_cop(totals['valor_poai'])}.",
            ),
            ledger.add(
                sources.get("PMR"), PMR_LATEST_VIEW,
                f"{PMR_LATEST_VIEW} · {filters} · corte {cutoff}",
                f"Presupuesto programado {_cop(totals['presupuesto_programado'])}; compromisos "
                f"{_cop(totals['compromisos'])}{_pct_text(totals['pct_comprometido'])}; giros "
                f"{_cop(totals['giros'])}{_pct_text(totals['pct_girado'])}.",
            ),
        ]
        return data, evidence

    def _goal_detail(self, params: GoalParams, ledger: EvidenceLedger):
        metas = self._read(META_VIEW)
        sources = self._sources()
        if params.meta_code:
            matches = metas[metas["codigo_meta_extendida"].astype(str) == params.meta_code]
        else:
            matches = metas[
                _contains(metas["descripcion_meta"], params.keyword)
                | _contains(metas["indicador_producto"], params.keyword)
                | _contains(metas["nombre_proyecto"], params.keyword)
            ]
        search = _filters(meta_code=params.meta_code, keyword=params.keyword)
        if matches.empty and params.meta_code:
            # People often type the project code (e.g. 2791) instead of a meta code (27911).
            project_metas = metas[metas["codigo_proyecto"].astype(str) == params.meta_code]
            if not project_metas.empty:
                candidates = [
                    {"meta_code": row.codigo_meta_extendida, "descripcion": row.descripcion_meta,
                     "sector": row.nombre_sector}
                    for row in project_metas.head(MAX_SAMPLES).itertuples()
                ]
                data = {
                    "found": len(project_metas),
                    "is_project_code": True,
                    "proyecto": {"codigo": params.meta_code,
                                 "nombre": project_metas.iloc[0]["nombre_proyecto"]},
                    "candidates": candidates,
                    "message": "El código corresponde a un PROYECTO, no a una meta. Para cifras "
                               "del proyecto usa get_plan_vs_execution con project_code.",
                }
                evidence = [ledger.add(
                    sources.get("POAI"), META_VIEW,
                    f"{META_VIEW} · {_filters(project_code=params.meta_code)}",
                    f"Proyecto {params.meta_code}: {len(project_metas)} metas.",
                )]
                return data, evidence
        if matches.empty:
            raise _NoData({"found": 0, "message": "Ninguna meta coincide con la búsqueda.",
                           "search": search})
        if len(matches) > 1:
            candidates = [
                {"meta_code": row.codigo_meta_extendida, "descripcion": row.descripcion_meta,
                 "proyecto": row.nombre_proyecto, "sector": row.nombre_sector}
                for row in matches.head(MAX_SAMPLES).itertuples()
            ]
            data = {"found": len(matches), "candidates": candidates,
                    "message": "Varias metas coinciden: pide a la persona que elija una."}
            evidence = [ledger.add(sources.get("POAI"), META_VIEW, f"{META_VIEW} · {search}",
                                   f"{len(matches)} metas coinciden con la búsqueda.")]
            return data, evidence

        meta = matches.iloc[0]
        id_meta = meta["id_meta"]
        code = str(meta["codigo_meta_extendida"])
        evidence = []

        poai = self._read(POAI_TABLE)
        poai = poai[poai["id_meta"] == id_meta].sort_values("vigencia")
        poai_rows = [
            {"vigencia": int(r.vigencia), "valor_poai": r.valor_poai,
             "magnitud_programada": r.magnitud_programada}
            for r in poai.itertuples()
        ]
        evidence.append(ledger.add(
            sources.get("POAI"), POAI_TABLE, f"{POAI_TABLE} + {META_VIEW} · meta {code}",
            "POAI: " + "; ".join(f"{r['vigencia']} {_cop(r['valor_poai'])}" for r in poai_rows),
        ))

        pmr = self._read(PMR_LATEST_VIEW)
        pmr = pmr[pmr["id_meta"] == id_meta].sort_values("vigencia")
        pmr_rows = [
            {"vigencia": int(r.vigencia), "fecha_corte": _date_text(r.fecha_corte),
             "magnitud_programada": r.magnitud_programada,
             "magnitud_contratada": r.magnitud_contratada,
             "magnitud_entregada": r.magnitud_entregada,
             "presupuesto_programado": r.presupuesto_programado,
             "compromisos": r.compromisos, "giros": r.giros,
             "pct_comprometido": _pct(r.compromisos, r.presupuesto_programado),
             "pct_girado": _pct(r.giros, r.presupuesto_programado)}
            for r in pmr.itertuples()
        ]
        if pmr_rows:
            evidence.append(ledger.add(
                sources.get("PMR"), PMR_LATEST_VIEW, f"{PMR_LATEST_VIEW} · meta {code}",
                "PMR último corte: " + "; ".join(
                    f"{r['vigencia']} compromisos {_cop(r['compromisos'])}, magnitud entregada "
                    f"{r['magnitud_entregada']}" for r in pmr_rows
                ),
            ))

        alignment = self._read(ODS_VIEW)
        alignment = alignment[alignment["id_meta"] == id_meta]
        ods_rows = [
            {"codigo_ods": r.codigo_ods, "nombre_ods": r.nombre_ods, "esfera": r.esfera_ods,
             "codigo_meta_ods": r.codigo_meta_ods}
            for r in alignment.itertuples()
        ]
        if ods_rows:
            evidence.append(ledger.add(
                sources.get("ODS"), ODS_VIEW, f"{ODS_VIEW} · meta {code}",
                "ODS: " + ", ".join(f"{r['codigo_ods']} {r['nombre_ods']}" for r in ods_rows),
            ))

        proposals, cut = self._latest_proposals()
        proposals = proposals[proposals["id_meta"] == id_meta]
        proposal_block = None
        if len(proposals):
            proposal_block = {
                "total": len(proposals),
                "cutoff": cut,
                "by_status": _counts(proposals["estado_propuesta"]),
                "items": [
                    {"code": r.codigo_propuesta, "name": r.nombre_propuesta,
                     "metodologia": r.metodologia, "status": r.estado_propuesta,
                     "vigencia_ejecucion": r.vigencia_ejecucion}
                    for r in proposals.head(MAX_GROUPS).itertuples()
                ],
            }
            evidence.append(ledger.add(
                sources.get("PP"), FOLLOW_UP_TABLE,
                f"{PROPOSAL_TABLE} + {FOLLOW_UP_TABLE} · meta {code} · corte {cut}",
                f"{len(proposals)} propuestas ciudadanas vinculadas a la meta.",
            ))

        lines = self._crp_lines()
        lines = lines[lines["id_meta"] == id_meta]
        crp_block = None
        if len(lines):
            per_crp = (
                lines.groupby(["numero_crp", "vigencia", "source"], sort=True)
                .agg(valor=("valor_asignado_pp", "sum"), lineas=("id_crp_meta", "count"),
                     tipo_compromiso=("tipo_compromiso", "first"),
                     fecha_registro=("fecha_registro", "first"))
                .reset_index()
            )
            crp_block = {
                "crp_count": len(per_crp),
                "lines": len(lines),
                "total_value": float(lines["valor_asignado_pp"].sum()),
                "by_vigencia": {
                    str(int(year)): float(value) for year, value
                    in lines.groupby("vigencia")["valor_asignado_pp"].sum().items()
                },
                "items": [
                    {"numero_crp": r.numero_crp, "vigencia": int(r.vigencia), "valor": r.valor,
                     "lineas": int(r.lineas), "tipo_compromiso": r.tipo_compromiso,
                     "fecha_registro": _date_text(r.fecha_registro), "source": r.source}
                    for r in per_crp.head(MAX_GROUPS).itertuples()
                ],
            }
            evidence.append(ledger.add(
                sources.get("CRP"), CRP_LINES_TABLE,
                f"{CRP_LINES_TABLE} + {CRP_TABLE} · meta {code}",
                f"{crp_block['crp_count']} CRP ({crp_block['lines']} líneas) por "
                f"{_cop(crp_block['total_value'])}.",
            ))

        data = {
            "found": 1,
            "unit": COP_NOTE,
            "meta": {
                "meta_code": code,
                "descripcion": meta["descripcion_meta"],
                "indicador": meta["indicador_producto"],
                "codigo_indicador": meta["codigo_indicador"],
                "meta_total_2025_2028": meta["meta_total_2025_2028"],
                "tipo_anualizacion": meta["tipo_anualizacion"],
                "componente": meta["componente_proyecto"],
                "linea_inversion": meta["linea_inversion"],
                "proyecto": {"codigo": meta["codigo_proyecto"], "nombre": meta["nombre_proyecto"]},
                "programa": {"codigo": meta["codigo_programa"], "nombre": meta["nombre_programa"]},
                "objetivo_estrategico": {"codigo": meta["codigo_objetivo"],
                                         "nombre": meta["nombre_objetivo"]},
                "sector": meta["nombre_sector"],
                "entidad": meta["nombre_entidad"],
            },
            "ods": ods_rows,
            "poai": poai_rows,
            "pmr_latest": pmr_rows,
            "proposals": proposal_block,
            "crp": crp_block,
        }
        return data, evidence

    def _poai_vs_pmr(self, params: YearParams, ledger: EvidenceLedger):
        quality = self._read(POAI_PMR_VIEW)
        year = self._year(params.year, quality["vigencia"])
        rows = quality[quality["vigencia"] == year].copy()
        tolerance = PMR_2025_ROUNDING_COP if year == 2025 else 0.5
        rows["budget_differs"] = rows["diferencia_presupuesto"].abs().fillna(math.inf) > tolerance
        rows["magnitude_differs"] = rows["diferencia_magnitud"].abs().fillna(math.inf) > 1e-9
        differing = rows[rows["budget_differs"] | rows["magnitude_differs"]]
        descriptions = self._read(META_VIEW).set_index("codigo_meta_extendida")["descripcion_meta"]
        verdict = compute_plan_verdict(len(rows), len(differing))
        cutoff = _date_text(rows["fecha_corte_pmr"].max()) if len(rows) else None
        data = {
            "verdict": verdict,
            "year": year,
            "rule": " ".join(filter(None, [
                "Para cada meta se compara el POAI con el PMR (último corte): presupuesto "
                "(valor POAI vs presupuesto programado PMR) y magnitud programada. Coherente = "
                "ninguna meta difiere; Diferencia detectada = al menos una difiere; No "
                "comparable = no hay metas con datos en ambas fuentes.",
                f"En 2025 se toleran diferencias de presupuesto de hasta "
                f"{PMR_2025_ROUNDING_COP:,} pesos porque el PMR 2025 venía en millones con dos "
                "decimales." if year == 2025 else None,
                "Una diferencia no implica irregularidad: las fuentes no permiten saber cuál "
                "valor debe prevalecer.",
            ])),
            "unit": COP_NOTE,
            "pmr_cutoff": cutoff,
            "metas_compared": len(rows),
            "budget_differences": int(rows["budget_differs"].sum()),
            "magnitude_differences": int(rows["magnitude_differs"].sum()),
            "total_poai": float(rows["valor_poai"].sum()),
            "total_pmr": float(rows["presupuesto_pmr"].sum()),
            "differing_metas": [
                {"meta_code": r.codigo_meta_extendida,
                 "descripcion": descriptions.get(r.codigo_meta_extendida),
                 "magnitud_poai": r.magnitud_poai, "magnitud_pmr": r.magnitud_pmr,
                 "diferencia_magnitud": _round4(r.diferencia_magnitud),
                 "valor_poai": r.valor_poai, "presupuesto_pmr": r.presupuesto_pmr,
                 "diferencia_presupuesto": r.diferencia_presupuesto}
                for r in differing.sort_values("codigo_meta_extendida")
                .head(MAX_DIFFERENCES).itertuples()
            ],
        }
        sources = self._sources()
        evidence = [
            ledger.add(
                sources.get("POAI"), POAI_TABLE, f"{POAI_PMR_VIEW} · vigencia={year} · POAI",
                f"{len(rows)} metas; valor POAI {_cop(data['total_poai'])}.",
            ),
            ledger.add(
                sources.get("PMR"), PMR_LATEST_VIEW,
                f"{POAI_PMR_VIEW} · vigencia={year} · PMR corte {cutoff}",
                f"Presupuesto PMR {_cop(data['total_pmr'])}; {data['budget_differences']} "
                f"diferencias de presupuesto y {data['magnitude_differences']} de magnitud. "
                f"Veredicto: {verdict}.",
            ),
        ]
        return data, evidence

    def _changes_between_cutoffs(self, params: ChangesParams, ledger: EvidenceLedger):
        if params.domain == "pmr":
            return self._pmr_changes(params.year, ledger)
        return self._pp_changes(params.year, ledger)

    def _pmr_changes(self, requested: int | None, ledger: EvidenceLedger):
        pmr = self._read(PMR_TABLE)
        year = self._year(requested, pmr["vigencia"])
        rows = pmr[pmr["vigencia"] == year]
        cuts = sorted(rows["fecha_corte"].unique())
        if len(cuts) < 2:
            raise _NoData({"error": "Solo hay un corte para esta vigencia",
                           "cutoffs": [_date_text(c) for c in cuts]})
        first = rows[rows["fecha_corte"] == cuts[0]].set_index("id_meta")
        last = rows[rows["fecha_corte"] == cuts[-1]].set_index("id_meta")
        both = first.index.intersection(last.index)
        descriptions = self._read(META_VIEW).set_index("id_meta")

        def top_increases(column: str) -> list[dict[str, Any]]:
            delta = (last.loc[both, column].fillna(0) - first.loc[both, column].fillna(0))
            delta = delta[delta != 0].sort_values(ascending=False).head(5)
            return [
                {"meta_code": descriptions.at[i, "codigo_meta_extendida"],
                 "descripcion": descriptions.at[i, "descripcion_meta"],
                 "antes": first.at[i, column], "despues": last.at[i, column],
                 "cambio": float(value)}
                for i, value in delta.items()
            ]

        totals = {
            _date_text(cut): {
                column: float(rows.loc[rows["fecha_corte"] == cut, column].sum())
                for column in ("presupuesto_programado", "compromisos", "giros")
            }
            for cut in (cuts[0], cuts[-1])
        }
        changed = pmr_changes(pmr, year)
        data = {
            "domain": "pmr",
            "year": year,
            "from_cutoff": _date_text(cuts[0]),
            "to_cutoff": _date_text(cuts[-1]),
            "unit": COP_NOTE,
            "metas_compared": len(both),
            "metas_with_change": changed,
            "totals_by_cutoff": totals,
            "top_giros_increase": top_increases("giros"),
            "top_compromisos_increase": top_increases("compromisos"),
            "top_entregada_increase": top_increases("magnitud_entregada"),
        }
        summary = ", ".join(f"{column} {changed.get(column, 0)}" for column in PMR_CHANGE_COLUMNS)
        evidence = [ledger.add(
            self._sources().get("PMR"), PMR_TABLE,
            f"{PMR_TABLE} · vigencia={year} · cortes {data['from_cutoff']} y {data['to_cutoff']}",
            f"Metas con cambios: {summary}. Giros: "
            f"{_cop(totals[data['from_cutoff']]['giros'])} → "
            f"{_cop(totals[data['to_cutoff']]['giros'])}.",
        )]
        return data, evidence

    def _pp_changes(self, year: int | None, ledger: EvidenceLedger):
        follow_up = self._read(FOLLOW_UP_TABLE)
        proposals = self._read(PROPOSAL_TABLE).set_index("id_propuesta")
        cuts = sorted(follow_up["fecha_corte"].unique())
        if len(cuts) < 2:
            raise _NoData({"error": "Solo hay un corte de seguimiento",
                           "cutoffs": [_date_text(c) for c in cuts]})
        first = follow_up[follow_up["fecha_corte"] == cuts[0]].set_index("id_propuesta")
        last = follow_up[follow_up["fecha_corte"] == cuts[-1]].set_index("id_propuesta")
        both = first.index.intersection(last.index)
        if year is not None:
            both = both[last.loc[both, "vigencia_ejecucion"] == year]
        before = first.loc[both, "estado_propuesta"].fillna("Sin dato")
        after = last.loc[both, "estado_propuesta"].fillna("Sin dato")
        changed = before != after
        progress = (
            first.loc[both, "avance_gestion"].fillna("") != last.loc[both, "avance_gestion"]
            .fillna("")
        )
        transitions = (
            pd.DataFrame({"from": before[changed], "to": after[changed]})
            .value_counts().reset_index(name="count")
        )
        examples = [
            {"code": proposals.at[i, "codigo_propuesta"],
             "name": proposals.at[i, "nombre_propuesta"],
             "from": before[i], "to": after[i],
             "vigencia_ejecucion": last.at[i, "vigencia_ejecucion"]}
            for i in before[changed].index[:MAX_SAMPLES]
        ]
        data = {
            "domain": "participatory_budget",
            "year": year,
            "from_cutoff": _date_text(cuts[0]),
            "to_cutoff": _date_text(cuts[-1]),
            "proposals_compared": len(both),
            "status_changes": int(changed.sum()),
            "progress_text_changes": int(progress.sum()),
            "transitions": [
                {"from": r["from"], "to": r["to"], "count": int(r["count"])}
                for _, r in transitions.iterrows()
            ],
            "status_by_cutoff": {
                _date_text(cuts[0]): _counts(before), _date_text(cuts[-1]): _counts(after),
            },
            "examples": examples,
        }
        evidence = [ledger.add(
            self._sources().get("PP"), FOLLOW_UP_TABLE,
            f"{FOLLOW_UP_TABLE} · {_filters(year=year)} · cortes {data['from_cutoff']} y "
            f"{data['to_cutoff']}",
            f"{len(both)} propuestas comparadas; {data['status_changes']} cambiaron de estado "
            f"y {data['progress_text_changes']} cambiaron el texto de avance.",
        )]
        return data, evidence

    def _investment_by_ods(self, params: OdsParams, ledger: EvidenceLedger):
        year = self._year(params.year, self._read(POAI_TABLE)["vigencia"])
        metas = self._read(META_VIEW)[["id_meta"]]
        rows, cutoff = self._plan_rows(year, metas)
        alignment = self._read(ODS_VIEW).drop(columns=["codigo_meta_extendida",
                                                       "descripcion_meta"])
        if params.ods_keyword:
            alignment = alignment[_ods_match(alignment, params.ods_keyword)]
            keys = ["codigo_ods", "nombre_ods", "codigo_meta_ods", "descripcion_meta_ods"]
        else:
            keys = ["codigo_ods", "nombre_ods", "esfera_ods"]
        joined = alignment.merge(rows, on="id_meta")
        total_poai = float(rows["valor_poai"].sum())
        groups = []
        for key, group in joined.groupby(keys, sort=False):
            item = dict(zip(keys, key, strict=True))
            item.update(_money_block(group))
            item["pct_del_poai"] = _pct(item["valor_poai"], total_poai)
            groups.append(item)
        groups.sort(key=lambda item: -(item["valor_poai"] or 0))
        multi = int((alignment.groupby("id_meta").size() > 1).sum())
        data = {
            "year": year,
            "unit": COP_NOTE,
            "pmr_cutoff": cutoff,
            "total_poai_year": total_poai,
            "groups": groups[:MAX_GROUPS],
            "groups_total": len(groups),
            "metas_aligned": int(joined["id_meta"].nunique()),
            "note": (
                "Cada meta se alinea hoy con una sola meta ODS. Si una meta tuviera varias, su "
                f"valor se contaría en cada una (metas con varias: {multi})."
            ),
        }
        filters = _filters(year=year, ods_keyword=params.ods_keyword)
        sources = self._sources()
        top = groups[0] if groups else None
        evidence = [
            ledger.add(
                sources.get("ODS"), ODS_VIEW, f"{ODS_VIEW} + {POAI_TABLE} · {filters}",
                f"{data['metas_aligned']} metas en {len(groups)} grupos ODS; mayor valor: "
                + (f"{top.get('codigo_meta_ods') or top['nombre_ods']} "
                   f"{_cop(top['valor_poai'])}." if top else "ninguno."),
            ),
            ledger.add(
                sources.get("PMR"), PMR_LATEST_VIEW,
                f"{PMR_LATEST_VIEW} · {filters} · corte {cutoff}",
                f"Compromisos {_cop(joined['compromisos'].sum())}; giros "
                f"{_cop(joined['giros'].sum())}.",
            ),
        ]
        return data, evidence

    def _pqrs_stats(self, params: PqrsParams, ledger: EvidenceLedger):
        rows = self._read(PQRS_VIEW)
        rows["response_days"] = _response_days(rows["fecha_radicacion"], rows["fecha_respuesta"])
        if params.year is not None:
            rows = rows[rows["vigencia"] == params.year]
        if params.topic_keyword:
            rows = rows[_contains(rows["nombre_subtema"], params.topic_keyword)]

        def stats(group: pd.DataFrame) -> dict[str, Any]:
            closed = (group["estado_orfeo"].map(_label) == PQRS_CLOSED_STATE).sum()
            return {
                "count": len(group),
                "median_response_days": _median(group["response_days"]),
                "pct_closed": _pct(closed, len(group)),
            }

        column = {
            "subtema": "nombre_subtema", "tipo_peticion": "nombre_tipo_peticion",
            "vigencia": "vigencia", "medio_recepcion": "medio_recepcion",
            "observacion_general": "observacion_general",
        }[params.group_by]
        key = rows[column].astype("string").fillna("Sin dato")
        groups = [
            {"value": str(value), **stats(group)}
            for value, group in rows.groupby(key, sort=False)
        ]
        groups.sort(key=lambda item: (-item["count"], item["value"]))
        data = {
            "total": stats(rows),
            "group_by": params.group_by,
            "top": groups[:TOP_N],
            "response_status": _counts(rows["observacion_general"], TOP_N),
            "response_days_note": "Días calendario entre radicación y respuesta.",
            "quality_note": (
                "Se usa la vigencia que trae la fuente; en 4 radicados no coincide con el año "
                "de la fecha de registro."
            ),
        }
        locator = f"{PQRS_VIEW} · " + _filters(
            year=params.year, topic_keyword=params.topic_keyword, group_by=params.group_by
        )
        median = data["total"]["median_response_days"]
        closed = data["total"]["pct_closed"]
        parts = [f"{len(rows)} PQRS"]
        if median is not None:
            parts.append(f"mediana {median} días")
        if closed is not None:
            parts.append(f"{closed}% cerradas")
        summary = "; ".join(parts) + "."  # never 'None días' when the filter leaves no data
        return data, [ledger.add(self._sources().get("PQRS"), PQRS_VIEW, locator, summary)]

    def _participatory_budget(self, params: ParticipatoryParams, ledger: EvidenceLedger):
        if params.proposal:
            return self._proposal_detail(params, ledger)
        proposals, cut = self._latest_proposals(params.year, params.sector_keyword)
        if params.status:
            states = proposals["estado_propuesta"].map(_label)
            known = sorted(set(proposals["estado_propuesta"].dropna()))
            if _label(params.status) not in {_label(state) for state in known}:
                raise _NoData({"error": "Estado desconocido", "valid_statuses": known})
            proposals = proposals[states == _label(params.status)]

        lines = self._crp_lines(params.year, params.sector_keyword)
        committed = float(lines["valor_asignado_pp"].sum())
        population = pd.to_numeric(proposals["poblacion_beneficiada"], errors="coerce")
        data = {
            "locality": "San Cristóbal",
            "cutoff": cut,
            "proposals": len(proposals),
            "by_status": _counts(proposals["estado_propuesta"]),
            "by_metodologia": _counts(proposals["metodologia"]),
            "reported_population_sum": float(population.sum()) if population.notna().any()
            else None,
            "population_note": "Suma de la población beneficiada reportada por propuesta; una "
                               "misma persona puede estar en varias propuestas.",
            "sample_proposals": [
                str(name) for name in proposals["nombre_propuesta"].dropna().head(MAX_SAMPLES)
            ],
            "commitments": {
                "crp": int(lines["id_crp"].nunique()),
                "lines": len(lines),
                "committed_value": committed,
                "by_source": _source_breakdown(lines),
            },
            "unit": COP_NOTE,
        }
        filters = _filters(year=params.year, sector_keyword=params.sector_keyword)
        proposal_filters = _filters(year=params.year, sector_keyword=params.sector_keyword,
                                    status=params.status)
        sources = self._sources()
        evidence = [
            ledger.add(
                sources.get("PP"), FOLLOW_UP_TABLE,
                f"{PROPOSAL_TABLE} + {FOLLOW_UP_TABLE} · {proposal_filters} · corte {cut}",
                f"{data['proposals']} propuestas; estados: "
                + ", ".join(f"{k} {v}" for k, v in data["by_status"].items()) + ".",
            ),
            ledger.add(
                sources.get("CRP"), CRP_LINES_TABLE, f"{CRP_LINES_TABLE} + {CRP_TABLE} · {filters}",
                f"{data['commitments']['crp']} CRP ({len(lines)} líneas); valor comprometido "
                f"{_cop(committed)}.",
            ),
        ]
        return data, evidence

    def _proposal_detail(self, params: ParticipatoryParams, ledger: EvidenceLedger):
        """One citizen proposal by code or name: state per cut-off, progress and its CRP.

        Never returns 'tipo_acuerdo': in the source it sometimes holds a person's name.
        """
        proposals, cut = self._latest_proposals(params.year, params.sector_keyword)
        query = params.proposal or ""
        matches = _match_proposals(proposals, query)
        search = _filters(proposal=query, year=params.year, sector_keyword=params.sector_keyword)
        if matches.empty:
            raise _NoData({
                "found": 0,
                "message": f"No hay ninguna propuesta de presupuestos participativos de San "
                           f"Cristóbal cuyo nombre o código coincida con '{query}'.",
                "search": search,
            })

        shown = matches.head(MAX_DETAILS)
        ids = set(shown["id_propuesta"])
        metas = self._read(META_VIEW)[
            ["id_meta", "codigo_meta_extendida", "descripcion_meta", "codigo_proyecto",
             "nombre_proyecto"]
        ]
        shown = shown.merge(metas, on="id_meta", how="left")
        follow_up = self._read(FOLLOW_UP_TABLE)
        follow_up = follow_up[follow_up["id_propuesta"].isin(ids)].sort_values("fecha_corte")
        crp = self._read(CRP_TABLE)
        relations = self._read(CRP_PROPOSAL_TABLE)[["id_crp", "id_propuesta"]]
        lines = self._read(CRP_LINES_TABLE)
        sharing = relations.groupby("id_crp")["id_propuesta"].nunique()
        linked = relations[relations["id_propuesta"].isin(ids)].merge(crp, on="id_crp")

        details = []
        for row in shown.itertuples():
            own = linked[linked["id_propuesta"] == row.id_propuesta]
            details.append({
                "code": row.codigo_propuesta,
                "name": row.nombre_propuesta,
                "metodologia": row.metodologia,
                "vigencia_ejecucion": row.vigencia_ejecucion,
                "status": row.estado_propuesta,
                "progress": row.avance_gestion,
                "difficulties": row.dificultades,
                "funded_with_resources": row.se_ejecuta_con_recursos,
                "reported_population": row.poblacion_beneficiada,
                "sector": row.nombre_sector,
                "meta": {"code": row.codigo_meta_extendida, "description": row.descripcion_meta},
                "project": {"code": row.codigo_proyecto, "name": row.nombre_proyecto},
                "history": [
                    {"cutoff": _date_text(h.fecha_corte), "status": h.estado_propuesta,
                     "progress": h.avance_gestion}
                    for h in follow_up[follow_up["id_propuesta"] == row.id_propuesta]
                    .itertuples()
                ],
                "commitments": [
                    {
                        "crp": c.numero_crp,
                        "vigencia": c.vigencia,
                        "registered": _date_text(c.fecha_registro),
                        "type": c.tipo_compromiso,
                        "object": _truncate(c.objeto),
                        "value_for_this_meta": _sum(lines.loc[
                            (lines["id_crp"] == c.id_crp) & (lines["id_meta"] == row.id_meta),
                            "valor_asignado_pp",
                        ]),
                        "proposals_in_this_crp": int(sharing.get(c.id_crp, 0)),
                    }
                    for c in own.itertuples()
                ],
            })

        data = {
            "locality": "San Cristóbal",
            "cutoff": cut,
            "found": len(matches),
            "matches": details,
            "value_note": (
                "value_for_this_meta es lo que el CRP asigna a la meta de la propuesta; un "
                "mismo CRP puede financiar varias propuestas (proposals_in_this_crp), así que "
                "no es el valor exclusivo de esta propuesta."
            ),
            "unit": COP_NOTE,
        }
        if len(matches) > MAX_DETAILS:
            data["more_matches"] = [
                {"code": r.codigo_propuesta, "name": r.nombre_propuesta}
                for r in matches.iloc[MAX_DETAILS:MAX_DETAILS + MAX_SAMPLES].itertuples()
            ]

        sources = self._sources()
        evidence = [ledger.add(
            sources.get("PP"), FOLLOW_UP_TABLE,
            f"{PROPOSAL_TABLE} + {FOLLOW_UP_TABLE} · {search} · corte {cut}",
            f"{len(matches)} propuesta(s): "
            + "; ".join(f"{d['code']} '{d['name']}' — {d['status']}" for d in details) + ".",
        )]
        crps = [(d["code"], c) for d in details for c in d["commitments"]]
        if crps:
            evidence.append(ledger.add(
                sources.get("CRP"), CRP_PROPOSAL_TABLE,
                f"{CRP_PROPOSAL_TABLE} + {CRP_TABLE} · {search}",
                "; ".join(f"propuesta {code}: CRP {c['crp']} ({c['vigencia']}), "
                          f"{_cop(c['value_for_this_meta'])} para su meta"
                          for code, c in crps) + ".",
            ))
        return data, evidence

    def _contrast(self, params: ContrastParams, ledger: EvidenceLedger):
        proposals, cut = self._latest_proposals(params.year, params.sector_keyword)
        relations = self._read(CRP_PROPOSAL_TABLE).merge(
            self._read(CRP_TABLE)[["id_crp", "vigencia"]], on="id_crp"
        )
        referenced = set(zip(relations["id_propuesta"], relations["vigencia"].astype(int),
                             strict=True))
        has_commitment = pd.Series(
            [(i, int(y)) in referenced if pd.notna(y) else False
             for i, y in zip(proposals["id_propuesta"], proposals["vigencia_ejecucion"],
                             strict=True)],
            index=proposals.index, dtype=bool,
        )
        funded_state = proposals["estado_propuesta"].map(_label).isin(FUNDED_STATES)
        expected = proposals[funded_state]
        with_commitment = int((funded_state & has_commitment).sum())
        missing = proposals[funded_state & ~has_commitment]
        early = proposals[~funded_state & has_commitment]

        year_lines = self._crp_lines(params.year, None)
        sector_lines = self._crp_lines(params.year, params.sector_keyword)
        verdict = compute_verdict(len(expected), with_commitment, len(year_lines))
        data = {
            "verdict": verdict,
            "rule": (
                "Se esperan compromisos (CRP) para las propuestas en estado Contratada, "
                "En ejecución o Materializada (último corte) del mismo año. Coherente = todas "
                "aparecen en algún CRP; Diferencia detectada = al menos una no aparece; No "
                "comparable = no hay propuestas en esos estados o no hay compromisos publicados."
            ),
            "cutoff": cut,
            "proposals_expected_funded": len(expected),
            "proposals_with_commitment": with_commitment,
            "proposals_without_commitment": len(expected) - with_commitment,
            "missing_proposals_sample": [
                {"code": r.codigo_propuesta, "name": r.nombre_propuesta,
                 "status": r.estado_propuesta}
                for r in missing.head(MAX_SAMPLES).itertuples()
            ],
            "proposals_with_commitment_in_other_state": len(early),
            "other_state_note": (
                "Propuestas que ya tienen CRP aunque su estado no es Contratada, En ejecución "
                "ni Materializada (p. ej. En formulación). Es informativo: no cambia el "
                "veredicto."
            ),
            "other_state_sample": [
                {"code": r.codigo_propuesta, "name": r.nombre_propuesta,
                 "status": r.estado_propuesta}
                for r in early.head(MAX_SAMPLES).itertuples()
            ],
            "commitments": len(sector_lines),
            "committed_value": float(sector_lines["valor_asignado_pp"].sum()),
            "commitment_sources": _source_breakdown(sector_lines),
            "unit": COP_NOTE,
        }
        filters = _filters(year=params.year, sector_keyword=params.sector_keyword)
        sources = self._sources()
        evidence = [
            ledger.add(
                sources.get("PP"), FOLLOW_UP_TABLE,
                f"{FOLLOW_UP_TABLE} · {filters} · corte {cut} · estados "
                f"{', '.join(FUNDED_STATES)}",
                f"{len(expected)} propuestas que deberían tener recursos; "
                f"{with_commitment} con CRP.",
            ),
            ledger.add(
                sources.get("CRP"), CRP_PROPOSAL_TABLE,
                f"{CRP_PROPOSAL_TABLE} + {CRP_LINES_TABLE} · {filters} · columna source",
                f"{len(sector_lines)} líneas CRP; valor {_cop(data['committed_value'])}. "
                f"Veredicto: {verdict}.",
            ),
        ]
        return data, evidence

    def _contracts(self, params: ContractParams, ledger: EvidenceLedger):
        """SECOP II contracts. Links (contract-project-meta) are filtered first, then the result
        is deduplicated to distinct contracts BEFORE adding values: the source repeats the full
        contract value on every link."""
        contracts = self._read(CONTRACT_TABLE)
        links = self._read(CONTRACT_LINK_TABLE)
        metas = self._read(META_VIEW)
        search = _filters(
            year=params.year, project_code=params.project_code, meta_code=params.meta_code,
            object_keyword=params.object_keyword, status=params.status,
            verified_only=params.verified_only or None, group_by=params.group_by,
        )
        first = metas.drop_duplicates("codigo_proyecto")
        projects = pd.Series(first["nombre_proyecto"].to_numpy(),
                             index=first["codigo_proyecto"].astype(str))
        goals = metas.set_index(metas["codigo_meta_extendida"].astype(str))
        if params.project_code and params.project_code not in projects.index:
            raise _NoData({
                "found": 0,
                "message": f"No hay ningún proyecto con el código {params.project_code} en el "
                           "plan local de San Cristóbal.",
                "search": search,
            })
        if params.meta_code and params.meta_code not in goals.index:
            raise _NoData({
                "found": 0,
                "message": f"No hay ninguna meta con el código {params.meta_code} en el plan "
                           "local de San Cristóbal.",
                "search": search,
            })
        if params.year is not None:
            years = sorted({int(y) for y in contracts["vigencia"].dropna()})
            if params.year not in years:
                raise _NoData({"error": "Vigencia sin datos", "available_years": years})
            contracts = contracts[contracts["vigencia"] == params.year]
        if params.status:
            known = sorted(set(contracts["estado_contrato"].dropna()))
            if _label(params.status) not in {_label(state) for state in known}:
                raise _NoData({"error": "Estado desconocido", "valid_statuses": known})
            contracts = contracts[contracts["estado_contrato"].map(_label) == _label(params.status)]
        if params.object_keyword:
            contracts = contracts[_contains(contracts["objeto"], params.object_keyword)]

        # "Relevant" link level: the meta when filtering by meta, otherwise the project.
        level = "meta" if params.meta_code else "proyecto"
        status_column = f"estado_vinculo_{level}"
        matched = links[links["id_contrato"].isin(contracts["id_contrato"])]
        if params.project_code:
            matched = matched[matched["codigo_proyecto"].astype(str) == params.project_code]
        if params.meta_code:
            matched = matched[matched["codigo_meta"].astype(str) == params.meta_code]
        if params.verified_only:
            matched = matched[matched[status_column] == LINK_VERIFIED]
        pending_only = contracts[~contracts["id_contrato"].isin(
            links.loc[links["estado_vinculo_proyecto"] == LINK_VERIFIED, "id_contrato"]
        )]
        contracts = contracts[contracts["id_contrato"].isin(matched["id_contrato"])]
        if contracts.empty:
            payload: dict[str, Any] = {
                "found": 0,
                "message": "Ningún contrato coincide con los filtros.",
                "search": search,
            }
            if params.project_code or params.meta_code:
                payload["message"] = (
                    "No hay contratos con un vínculo verificado a ese proyecto o meta con estos "
                    "filtros."
                )
                if len(pending_only):
                    payload["message"] += (
                        f" Hay {len(pending_only)} contratos (con los demás filtros) cuyo vínculo "
                        "con un proyecto está pendiente de verificación: alguno podría "
                        "pertenecer a él."
                    )
                payload["contracts_with_pending_project_link"] = len(pending_only)
            raise _NoData(payload)

        ids = contracts["id_contrato"]
        values = pd.to_numeric(contracts["valor_contrato"], errors="coerce")
        total = float(values.sum())

        def verified_at(column: str) -> pd.Series:
            return ids.isin(matched.loc[matched[column] == LINK_VERIFIED, "id_contrato"])

        verified = verified_at(status_column)
        link_status = {
            name: {"verified": int(flags.sum()), "pending": int((~flags).sum())}
            for name, flags in (("proyecto", verified_at("estado_vinculo_proyecto")),
                                ("meta", verified_at("estado_vinculo_meta")))
        }
        groups = _contract_groups(params.group_by, contracts, matched, projects, goals)
        statuses = matched.groupby("id_contrato").agg(
            proyectos=("codigo_proyecto", lambda s: sorted(set(s.dropna().astype(str)))),
            metas=("codigo_meta", lambda s: sorted(set(s.dropna().astype(str)))),
            proyecto_verificado=("estado_vinculo_proyecto", lambda s: (s == LINK_VERIFIED).any()),
            meta_verificada=("estado_vinculo_meta", lambda s: (s == LINK_VERIFIED).any()),
        )
        pending_text = "Pendiente de verificación"
        sample = [
            {
                "reference": row.referencia_contrato,
                "object": _truncate(row.objeto),
                "value": row.valor_contrato,
                "status": row.estado_contrato,
                "signed": _date_text(row.fecha_firma),
                "year": row.vigencia,
                "projects": statuses.at[row.id_contrato, "proyectos"],
                "metas": statuses.at[row.id_contrato, "metas"],
                "project_link": LINK_VERIFIED
                if statuses.at[row.id_contrato, "proyecto_verificado"] else pending_text,
                "meta_link": LINK_VERIFIED
                if statuses.at[row.id_contrato, "meta_verificada"] else pending_text,
                "public_url": row.url_contrato,
            }
            for row in contracts.assign(sort_value=values)
            .sort_values(["sort_value", "referencia_contrato"], ascending=[False, True])
            .head(MAX_SAMPLES).itertuples()
        ]
        zero = int((values == 0).sum())
        level_text = "la meta" if level == "meta" else "el proyecto"
        data = {
            "locality": "San Cristóbal",
            "unit": COP_NOTE,
            "search": search,
            "contracts": len(contracts),
            "total_value": total,
            "zero_value_contracts": zero,
            "verification": {
                "level": level,
                "verified_contracts": int(verified.sum()),
                "pending_contracts": int((~verified).sum()),
                "pct_verified": _pct(int(verified.sum()), len(contracts)),
                "verified_value": float(values[verified].sum()),
                "pending_value": float(values[~verified].sum()),
                "rule": (
                    f"Un contrato cuenta como verificado si al menos uno de sus vínculos (con "
                    f"los filtros aplicados) tiene {level_text} en estado 'Verificado'; si todos "
                    "están 'Pendiente de verificación', cuenta como pendiente."
                ),
            },
            "link_status_by_level": link_status,
            "group_by": params.group_by,
            "groups": groups[:MAX_GROUPS],
            "groups_total": len(groups),
            "sample_contracts": sample,
            "notes": [n for n in (
                "total_value y valor_contratado son el valor firmado de cada contrato, contado "
                "una sola vez por contrato: no es lo ejecutado ni lo pagado.",
                "Un contrato puede estar vinculado a varios proyectos o metas: en la agrupación "
                "por proyecto o meta aparece en cada uno con su valor completo, así que esos "
                "valores se solapan y no se deben sumar entre sí."
                if params.group_by in ("proyecto", "meta") else None,
                "Un vínculo 'Pendiente de verificación' no está confirmado: no afirmes que ese "
                "contrato pertenece al proyecto o a la meta.",
                f"{zero} contrato(s) tienen valor 0 en la fuente." if zero else None,
                "No se publican nombres de contratistas.",
            ) if n],
        }
        summary = (
            f"{len(contracts)} contratos; valor contratado {_cop(total)} (valor firmado, una vez "
            f"por contrato); {int(verified.sum())} con vínculo verificado con {level_text} y "
            f"{int((~verified).sum())} pendientes."
        )
        evidence = [ledger.add(
            self._sources().get("CTR"), CONTRACT_TABLE,
            f"{CONTRACT_TABLE} + {CONTRACT_LINK_TABLE} · {search}", summary,
        )]
        return data, evidence

    def _report_gap(self, params: GapParams, _: EvidenceLedger):
        return {"recorded": True, "topic": params.topic, "missing_data": params.missing_data}, []

    # --- shared readers ----------------------------------------------------------------------
    def _latest_proposals(
        self, year: int | None = None, sector: str | None = None
    ) -> tuple[pd.DataFrame, str | None]:
        """Proposals with their follow-up at the latest cut-off, plus meta sector."""
        follow_up = self._read(FOLLOW_UP_TABLE)
        cut = follow_up["fecha_corte"].max()
        latest = follow_up[follow_up["fecha_corte"] == cut]
        metas = self._read(META_VIEW)[["id_meta", "nombre_sector"]]
        rows = (
            self._read(PROPOSAL_TABLE)
            .merge(latest.drop(columns=["id_seguimiento"]), on="id_propuesta")
            .merge(metas, on="id_meta", how="left")
        )
        if year is not None:
            rows = rows[rows["vigencia_ejecucion"] == year]
        if sector:
            rows = rows[_contains(rows["nombre_sector"], sector)]
        return rows, _date_text(cut)

    def _crp_lines(self, year: int | None = None, sector: str | None = None) -> pd.DataFrame:
        """Every CRP-meta line (duplicated pairs kept) with CRP data and meta sector."""
        crp = self._read(CRP_TABLE).drop(columns=["source", "source_file"])
        metas = self._read(META_VIEW)[["id_meta", "nombre_sector"]]
        lines = self._read(CRP_LINES_TABLE).merge(crp, on="id_crp").merge(metas, on="id_meta")
        if year is not None:
            lines = lines[lines["vigencia"] == year]
        if sector:
            lines = lines[_contains(lines["nombre_sector"], sector)]
        return lines


def compute_verdict(expected: int, with_commitment: int, commitments: int) -> str:
    """RF2 verdict (proposals vs CRP), computed in code: never by the LLM."""
    if expected == 0 or commitments == 0:
        return "not_comparable"
    return "coherent" if with_commitment == expected else "difference_detected"


def compute_plan_verdict(compared: int, differing: int) -> str:
    """POAI vs PMR verdict, computed in code: never by the LLM."""
    if compared == 0:
        return "not_comparable"
    return "coherent" if differing == 0 else "difference_detected"


# --- pure helpers --------------------------------------------------------------------------
def _money_block(rows: pd.DataFrame) -> dict[str, Any]:
    programmed = _sum(rows["presupuesto_programado"])
    committed = _sum(rows["compromisos"])
    paid = _sum(rows["giros"])
    return {
        "metas": int(rows["id_meta"].nunique()),
        "valor_poai": _sum(rows["valor_poai"]),
        "presupuesto_programado": programmed,
        "compromisos": committed,
        "giros": paid,
        "pct_comprometido": _pct(committed, programmed),
        "pct_girado": _pct(paid, programmed),
    }


def _delivery_counts(rows: pd.DataFrame) -> dict[str, int]:
    planned = pd.to_numeric(rows["magnitud_programada_pmr"], errors="coerce")
    delivered = pd.to_numeric(rows["magnitud_entregada"], errors="coerce").fillna(0)
    with_plan = planned > 0
    return {
        "metas_entrega_completa": int((with_plan & (delivered >= planned)).sum()),
        "metas_sin_entregas": int((with_plan & (delivered <= 0)).sum()),
    }


def _contract_groups(
    group_by: str, contracts: pd.DataFrame, links: pd.DataFrame, projects: pd.Series,
    goals: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Contracts and value per group, always over DISTINCT contracts. By project or meta a
    contract counts in every group it is linked to; contracts without any identified
    project/meta (pending links) form their own group."""
    values = contracts.set_index("id_contrato")["valor_contrato"]

    def block(ids: set) -> dict[str, Any]:
        chosen = pd.to_numeric(values[values.index.isin(ids)], errors="coerce")
        return {"contratos": len(chosen), "valor_contratado": float(chosen.sum())}

    groups = []
    if group_by in ("estado", "vigencia"):
        column = "estado_contrato" if group_by == "estado" else "vigencia"
        key = contracts[column].astype("string").fillna("Sin dato")
        for value, group in contracts.groupby(key, sort=False):
            groups.append({"codigo": None, "nombre": str(value),
                           **block(set(group["id_contrato"]))})
        if group_by == "vigencia":
            return sorted(groups, key=lambda item: item["nombre"])
    else:
        code_column = "codigo_proyecto" if group_by == "proyecto" else "codigo_meta"
        coded = links.dropna(subset=[code_column])
        for code, group in coded.groupby(coded[code_column].astype(str), sort=False):
            item = {"codigo": code}
            if group_by == "proyecto":
                item["nombre"] = projects.get(code)
            else:
                item["nombre"] = goals["descripcion_meta"].get(code)
                item["codigo_proyecto"] = goals["codigo_proyecto"].get(code)
            groups.append({**item, **block(set(group["id_contrato"]))})
        without = set(contracts["id_contrato"]) - set(coded["id_contrato"])
        if without:
            label = ("Sin proyecto verificado (vínculo pendiente)" if group_by == "proyecto"
                     else "Sin meta verificada (vínculo pendiente)")
            groups.append({"codigo": None, "nombre": label, **block(without)})
    return sorted(groups, key=lambda item: (-item["valor_contratado"], str(item["nombre"])))


def _source_breakdown(lines: pd.DataFrame) -> list[dict[str, Any]]:
    """Value of the CRP lines by provenance (curated file vs portal supplement)."""
    out = []
    for (source, source_file), group in lines.groupby(["source", "source_file"], sort=True):
        out.append({
            "source": source, "file": source_file,
            "vigencias": sorted(int(v) for v in group["vigencia"].unique()),
            "lines": len(group), "value": float(group["valor_asignado_pp"].sum()),
        })
    return out


def _ods_match(alignment: pd.DataFrame, keyword: str) -> pd.Series:
    """'11', 'ODS 11' or 'ods11' match the ODS number; any other text matches its name."""
    digits = re.fullmatch(r"(?:ODS\s*)?(\d{1,2})", normalize_label(keyword))
    if digits:
        return alignment["codigo_ods"].astype(str) == digits.group(1)
    return _contains(alignment["nombre_ods"], keyword)


def _response_days(filed: pd.Series, answered: pd.Series) -> pd.Series:
    """Calendar days between filing and answer; negative values (source errors) become null."""
    days = (pd.to_datetime(answered) - pd.to_datetime(filed)).dt.days
    return days.mask(days < 0)


def _counts(values: pd.Series, limit: int | None = None) -> dict[str, int]:
    counts = values.fillna("Sin dato").astype(str).value_counts()
    if limit:
        counts = counts.head(limit)
    return {str(k): int(v) for k, v in counts.items()}


def _sum(column: pd.Series) -> float | None:
    values = pd.to_numeric(column, errors="coerce")
    return float(values.sum()) if values.notna().any() else None


def _pct_text(value: object) -> str:
    """' (31.9%)' for a percentage, '' when it can't be computed (avoids 'None%')."""
    return "" if value is None else f" ({value}%)"


def _cop(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "sin dato"
    return "sin dato" if math.isnan(number) else f"${number:,.0f} COP"


def _date_text(value: object) -> str | None:
    if value is None or value is pd.NaT or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        return pd.Timestamp(value).date().isoformat()
    except (TypeError, ValueError):
        return str(value)


def _label(value: object) -> str | None:
    return None if value is None or pd.isna(value) else normalize_label(value)


def _contains(column: pd.Series, keyword: str) -> pd.Series:
    """Accent/case-insensitive substring match. Plain text, never a regex or SQL."""
    needle = normalize_label(keyword)
    return column.map(lambda value: needle in (_label(value) or ""))


def _match_proposals(proposals: pd.DataFrame, query: str) -> pd.DataFrame:
    """Exact code, else name substring, else every word of 4+ letters in the name.

    The word fallback finds 'Internet a mi barrio' for 'internet en mi barrio'.
    """
    if query.isdigit():
        return proposals[proposals["codigo_propuesta"].astype(str) == query]
    by_phrase = proposals[_contains(proposals["nombre_propuesta"], query)]
    if not by_phrase.empty:
        return by_phrase
    words = [word for word in normalize_label(query).split() if len(word) >= 4]
    if not words:
        return by_phrase
    names = proposals["nombre_propuesta"].map(lambda value: _label(value) or "")
    return proposals[names.map(lambda name: all(word in name for word in words))]


def _truncate(value: object, limit: int = 200) -> str | None:
    text = _label_text(value)
    return text if text is None or len(text) <= limit else text[: limit - 1] + "…"


def _label_text(value: object) -> str | None:
    return None if value is None or pd.isna(value) else str(value).strip()


def _pct(part: object, whole: object) -> float | None:
    try:
        part, whole = float(part), float(whole)
    except (TypeError, ValueError):
        return None
    if math.isnan(part) or math.isnan(whole) or whole <= 0:
        return None
    return round(100 * part / whole, 1)


def _median(column: pd.Series) -> float | None:
    return _round(pd.to_numeric(column, errors="coerce").median())


def _round4(value: object) -> float | None:
    """Magnitudes may carry float noise (1.3 - 1.25 = 0.0500000001)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else round(number, 4)


def _round(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else round(number, 1)


def _filters(**values: object) -> str:
    shown = [f"{key}={value}" for key, value in values.items() if value not in (None, "")]
    return ", ".join(shown) if shown else "sin filtro"


def _jsonable(value: Any) -> Any:
    """Convert numpy/pandas scalars, dates and NaN to plain JSON values."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value.isoformat()
    if hasattr(value, "item") and not isinstance(value, str):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value
