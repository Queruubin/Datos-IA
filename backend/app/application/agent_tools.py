"""Closed set of deterministic tools the LLM may call.

The LLM never writes SQL: it picks a tool and passes parameters, which are validated here
(types, ranges, whitelists) and applied as plain pandas filters. Every figure the agent can
mention comes from these functions, together with evidence records whose ids are assigned by
code (E1, E2...), never by the model.
"""

import logging
import math
from collections.abc import Callable
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain import Evidence, SourceMetadata, ToolCall, ToolOutcome, ToolSpec
from app.ingestion.text import normalize_label
from app.ports import AnalyticsPort

logger = logging.getLogger(__name__)

PAC_TABLE = "f1_pac_execution"
PQRS_TABLE = "f2_pqrs"
PP_PROGRESS_TABLE = "f3_pp_progress"
PP_COMMITMENTS_TABLE = "f3_pp_commitments"

PAC_UNIT_NOTE = (
    "Unidad no documentada por la fuente (probablemente millones de pesos). "
    "No afirmar que son pesos."
)
PAC_LOCALITIES = 20
PQRS_CLOSED_STATE = "TRAMITE CERRADO"
# Proposal states that imply the proposal should already have committed funding (CRP).
FUNDED_STATES = ("CONTRATADA", "EN EJECUCION", "MATERIALIZADA")
TOP_N = 10
MAX_SAMPLES = 10


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


class PqrsParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    topic_keyword: Keyword = Field(default=None, max_length=60)
    group_by: Literal["subtema", "tipo_peticion", "vigencia"] = "subtema"


class ParticipatoryParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    sector_keyword: Keyword = Field(default=None, max_length=60)
    status: str | None = Field(default=None, max_length=40)


class ContrastParams(_Params):
    year: Year = Field(default=None, ge=2000, le=2100)
    sector_keyword: Keyword = Field(default=None, max_length=60)


class GapParams(_Params):
    topic: str = Field(min_length=1, max_length=120)
    missing_data: str = Field(min_length=1, max_length=300)


_YEAR_SCHEMA = {"type": "integer", "description": "Año (vigencia), p. ej. 2025. Omitir = todos."}

TOOL_SPECS: list[ToolSpec] = [
    ToolSpec(
        name="list_sources",
        description="Lista las fuentes de datos cargadas con su título y fecha de corte.",
        parameters_json_schema={"type": "object", "properties": {}},
    ),
    ToolSpec(
        name="get_budget_execution",
        description=(
            "Ejecución del PAC (Plan Anual de Caja) del Fondo de Desarrollo Local de San "
            "Cristóbal: valor programado vs ejecutado por mes, totales y puesto entre las 20 "
            "localidades de Bogotá. La unidad monetaria NO está documentada."
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
        name="get_pqrs_stats",
        description=(
            "Estadísticas de PQRS (peticiones, quejas, reclamos) radicadas ante la Alcaldía "
            "Local de San Cristóbal: cantidad, mediana de días de respuesta, % cerradas y top 10."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": _YEAR_SCHEMA,
                "topic_keyword": {
                    "type": "string",
                    "description": "Palabra para filtrar por subtema, p. ej. 'vias'.",
                },
                "group_by": {"type": "string", "enum": ["subtema", "tipo_peticion", "vigencia"]},
            },
        },
    ),
    ToolSpec(
        name="get_participatory_budget",
        description=(
            "Presupuestos participativos de San Cristóbal: propuestas priorizadas por estado, "
            "avance promedio, valor comprometido (CRP) y ejemplos de propuestas."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": _YEAR_SCHEMA,
                "sector_keyword": {"type": "string",
                                   "description": "Palabra del sector, p. ej. 'cultura'."},
                "status": {"type": "string",
                           "description": "Estado de la propuesta, p. ej. 'Materializada'."},
            },
        },
    ),
    ToolSpec(
        name="compare_participatory_budget_vs_commitments",
        description=(
            "Contraste determinístico: verifica si las propuestas que deberían tener recursos "
            "(Contratada, En ejecución, Materializada) aparecen en algún compromiso "
            "presupuestal (CRP). Devuelve el veredicto calculado por código."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "year": _YEAR_SCHEMA,
                "sector_keyword": {"type": "string", "description": "Palabra del sector."},
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
                          "description": "Tema, p. ej. seguridad, vías, salud, contratación."},
                "missing_data": {"type": "string", "description": "Dato que haría falta."},
            },
            "required": ["topic", "missing_data"],
        },
    ),
]


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
            portal_url=meta.portal_url if meta else "",
            locator=locator,
            summary=summary,
        )
        self.items.append(evidence)
        return evidence

    def ids(self) -> set[str]:
        return {item.id for item in self.items}


class AgentTools:
    """Executes tool calls over the read-only analytics port."""

    def __init__(self, analytics: AnalyticsPort) -> None:
        self._analytics = analytics
        self._handlers: dict[str, tuple[type[_Params], Callable[..., Any]]] = {
            "list_sources": (NoParams, self._list_sources),
            "get_budget_execution": (BudgetParams, self._budget_execution),
            "get_pqrs_stats": (PqrsParams, self._pqrs_stats),
            "get_participatory_budget": (ParticipatoryParams, self._participatory_budget),
            "compare_participatory_budget_vs_commitments": (ContrastParams, self._contrast),
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
        except Exception:  # missing table, unreadable database...
            logger.exception("Tool %s failed", call.name)
            return ToolOutcome(call, data=None, error="La fuente de datos no está disponible.")
        return ToolOutcome(call, data=_jsonable(data), evidence=evidence)

    # --- helpers ---------------------------------------------------------------------------
    def _metadata(self) -> dict[str, SourceMetadata]:
        return {meta.table_name: meta for meta in self._analytics.read_source_metadata()}

    # --- tools -----------------------------------------------------------------------------
    def _list_sources(self, _: NoParams, ledger: EvidenceLedger):
        sources, evidence = [], []
        for meta in self._analytics.read_source_metadata():
            sources.append({
                "source_id": meta.source_id, "title": meta.title,
                "data_cutoff": meta.data_cutoff, "rows": meta.rows, "unit": meta.unit,
            })
            evidence.append(ledger.add(
                meta, meta.table_name, f"{meta.table_name} (tabla completa)",
                f"Fuente cargada con {meta.rows} filas; fecha de corte {meta.data_cutoff}.",
            ))
        return {"sources": sources}, evidence

    def _budget_execution(self, params: BudgetParams, ledger: EvidenceLedger):
        frame = self._analytics.read_table(PAC_TABLE)
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
        meta = self._metadata().get(PAC_TABLE)
        return data, [ledger.add(meta, PAC_TABLE, locator, summary)]

    def _pqrs_stats(self, params: PqrsParams, ledger: EvidenceLedger):
        rows = self._analytics.read_table(PQRS_TABLE)
        if params.year is not None:
            rows = rows[rows["vigencia"] == params.year]
        if params.topic_keyword:
            rows = rows[_contains(rows["subtema"], params.topic_keyword)]

        def stats(group: pd.DataFrame) -> dict[str, Any]:
            closed = (group["estado_orfeo"].map(_label) == PQRS_CLOSED_STATE).sum()
            return {
                "count": len(group),
                "median_response_days": _median(group["response_days"]),
                "pct_closed": _pct(closed, len(group)),
            }

        key = rows[params.group_by].astype("string").fillna("Sin dato")
        groups = [
            {"value": str(value), **stats(group)}
            for value, group in rows.groupby(key, sort=False)
        ]
        groups.sort(key=lambda item: (-item["count"], item["value"]))
        data = {
            "total": stats(rows),
            "group_by": params.group_by,
            "top": groups[:TOP_N],
            "response_days_note": "Días calendario entre radicación y respuesta.",
        }
        locator = f"{PQRS_TABLE} · " + _filters(
            year=params.year, topic_keyword=params.topic_keyword, group_by=params.group_by
        )
        summary = (
            f"{len(rows)} PQRS; mediana {data['total']['median_response_days']} días; "
            f"{data['total']['pct_closed']}% cerradas."
        )
        meta = self._metadata().get(PQRS_TABLE)
        return data, [ledger.add(meta, PQRS_TABLE, locator, summary)]

    def _participatory_budget(self, params: ParticipatoryParams, ledger: EvidenceLedger):
        progress = self._filter_pp(
            self._analytics.read_table(PP_PROGRESS_TABLE), params.year, params.sector_keyword
        )
        commitments = self._filter_pp(
            self._analytics.read_table(PP_COMMITMENTS_TABLE), params.year, params.sector_keyword
        )
        if params.status:
            states = progress["estado_de_la_propuesta"].map(_label)
            known = sorted(set(states.dropna()))
            wanted = _label(params.status)
            if wanted not in known:
                return {"error": "Estado desconocido", "valid_statuses": known}, []
            progress = progress[states == wanted]

        by_status = progress["estado_de_la_propuesta"].fillna("Sin dato").value_counts()
        committed = float(
            commitments["valor_crp_asignado_presupuestos_participativos"].sum(skipna=True)
        )
        data = {
            "locality": "San Cristóbal",
            "proposals": len(progress),
            "by_status": {str(k): int(v) for k, v in by_status.items()},
            "avg_progress_pct": _round(progress["pct_de_avance_propuesta"].mean()),
            "sample_proposals": [
                str(name) for name in
                progress["nombre_propuesta_ciudadana"].dropna().head(MAX_SAMPLES)
            ],
            "commitments": len(commitments),
            "committed_value": committed,
            "unit": "Valor del CRP tal como lo publica la fuente (pesos según el dataset).",
        }
        filters = _filters(year=params.year, sector_keyword=params.sector_keyword)
        progress_filters = _filters(
            year=params.year, sector_keyword=params.sector_keyword, status=params.status
        )
        meta = self._metadata()
        evidence = [
            ledger.add(
                meta.get(PP_PROGRESS_TABLE), PP_PROGRESS_TABLE,
                f"{PP_PROGRESS_TABLE} · {progress_filters}",
                f"{data['proposals']} propuestas; avance promedio {data['avg_progress_pct']}%.",
            ),
            ledger.add(
                meta.get(PP_COMMITMENTS_TABLE), PP_COMMITMENTS_TABLE,
                f"{PP_COMMITMENTS_TABLE} · {filters}",
                f"{len(commitments)} compromisos; valor CRP sumado {committed:,.0f}.",
            ),
        ]
        return data, evidence

    def _contrast(self, params: ContrastParams, ledger: EvidenceLedger):
        progress = self._filter_pp(
            self._analytics.read_table(PP_PROGRESS_TABLE), params.year, params.sector_keyword
        )
        all_commitments = self._analytics.read_table(PP_COMMITMENTS_TABLE)
        year_commitments = self._filter_pp(all_commitments, params.year, None)
        sector_commitments = self._filter_pp(all_commitments, params.year, params.sector_keyword)

        # (year, proposal code) pairs referenced by any commitment of the same year.
        referenced: set[tuple[int, str]] = set()
        for year, codes in zip(
            year_commitments["vigencia_ejecucion"],
            year_commitments["codigo_propuestas_financiadas_crp"], strict=True,
        ):
            for code in str(codes if codes is not None else "").split(";"):
                if code.strip() and not pd.isna(year):
                    referenced.add((int(year), _code(code)))

        expected = progress[progress["estado_de_la_propuesta"].map(_label).isin(FUNDED_STATES)]
        has_commitment = [
            (int(year), _code(code)) in referenced
            for year, code in zip(
                expected["vigencia_ejecucion"], expected["codigo_propuestas"], strict=True
            )
        ]
        with_commitment = sum(has_commitment)
        missing = expected[[not flag for flag in has_commitment]]
        verdict = compute_verdict(len(expected), with_commitment, len(year_commitments))
        data = {
            "verdict": verdict,
            "rule": (
                "Se esperan compromisos (CRP) para las propuestas en estado Contratada, "
                "En ejecución o Materializada del mismo año. Coherente = todas aparecen en "
                "algún CRP; Diferencia detectada = al menos una no aparece; No comparable = "
                "no hay propuestas en esos estados o no hay compromisos publicados."
            ),
            "proposals_expected_funded": len(expected),
            "proposals_with_commitment": with_commitment,
            "proposals_without_commitment": len(expected) - with_commitment,
            "missing_proposals_sample": [
                {"code": _code(row.codigo_propuestas), "name": row.nombre_propuesta_ciudadana,
                 "status": row.estado_de_la_propuesta}
                for row in missing.head(MAX_SAMPLES).itertuples()
            ],
            "commitments": len(sector_commitments),
            "committed_value": float(
                sector_commitments["valor_crp_asignado_presupuestos_participativos"]
                .sum(skipna=True)
            ),
        }
        filters = _filters(year=params.year, sector_keyword=params.sector_keyword)
        meta = self._metadata()
        evidence = [
            ledger.add(
                meta.get(PP_PROGRESS_TABLE), PP_PROGRESS_TABLE,
                f"{PP_PROGRESS_TABLE} · {filters} · estados {', '.join(FUNDED_STATES)}",
                f"{len(expected)} propuestas que deberían tener recursos; "
                f"{with_commitment} con CRP.",
            ),
            ledger.add(
                meta.get(PP_COMMITMENTS_TABLE), PP_COMMITMENTS_TABLE,
                f"{PP_COMMITMENTS_TABLE} · {filters} · columna codigo_propuestas_financiadas_crp",
                f"{len(sector_commitments)} compromisos; valor CRP sumado "
                f"{data['committed_value']:,.0f}. Veredicto: {verdict}.",
            ),
        ]
        return data, evidence

    def _report_gap(self, params: GapParams, _: EvidenceLedger):
        return {"recorded": True, "topic": params.topic, "missing_data": params.missing_data}, []

    @staticmethod
    def _filter_pp(frame: pd.DataFrame, year: int | None, sector: str | None) -> pd.DataFrame:
        if year is not None:
            frame = frame[frame["vigencia_ejecucion"] == year]
        if sector:
            frame = frame[_contains(frame["sector"], sector)]
        return frame


def compute_verdict(expected: int, with_commitment: int, commitments: int) -> str:
    """RF2 verdict, computed in code: never by the LLM."""
    if expected == 0 or commitments == 0:
        return "not_comparable"
    return "coherent" if with_commitment == expected else "difference_detected"


# --- pure helpers --------------------------------------------------------------------------
def _label(value: object) -> str | None:
    return None if value is None or pd.isna(value) else normalize_label(value)


def _contains(column: pd.Series, keyword: str) -> pd.Series:
    """Accent/case-insensitive substring match. Plain text, never a regex or SQL."""
    needle = normalize_label(keyword)
    return column.map(lambda value: needle in (_label(value) or ""))


def _code(value: object) -> str:
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") else text


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
    """Convert numpy/pandas scalars and NaN to plain JSON values."""
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if value is None or value is pd.NA:
        return None
    if hasattr(value, "item") and not isinstance(value, str):
        value = value.item()
    if isinstance(value, float) and math.isnan(value):
        return None
    return value
