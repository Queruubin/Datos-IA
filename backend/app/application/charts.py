"""Charts built by CODE from deterministic tool outcomes (never by the LLM).

Every number in a chart is copied from a tool result, and a chart is only returned when all the
evidence records behind it are cited by the validated answer, so the chart backs what the text
says. At most `MAX_CHARTS` per answer.
"""

import logging
import math
from collections.abc import Callable, Iterable
from dataclasses import replace
from typing import Any

from app.domain import ChartKpi, ChartSeries, ChartSpec, ChartUnit, Evidence, ToolOutcome

logger = logging.getLogger(__name__)

MAX_CHARTS = 2
MAX_CATEGORIES = 8
MAX_LABEL = 48

MONTHS_ES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
PAC_UNIT_NOTE = (
    "La fuente no documenta la unidad monetaria del PAC (probablemente millones de pesos)."
)
PCT_NOTE = (
    "Los porcentajes se calculan sobre el presupuesto programado del PMR; pueden superar 100 % "
    "si la fuente reporta más compromisos que presupuesto."
)
DIFFERENCE_NOTE = (
    "Una diferencia no implica irregularidad: puede deberse a fechas de corte distintas o a "
    "datos aún no publicados."
)
PQRS_GROUP_LABELS = {
    "subtema": "subtema",
    "tipo_peticion": "tipo de petición",
    "vigencia": "año",
    "medio_recepcion": "medio de recepción",
    "observacion_general": "estado de la respuesta",
}
PLAN_GROUP_LABELS = {"sector": "sector", "proyecto": "proyecto", "meta": "meta"}

Builder = Callable[[dict[str, Any], list[Evidence]], list[ChartSpec]]


def build_charts(
    outcomes: Iterable[ToolOutcome], cited_ids: Iterable[str]
) -> tuple[ChartSpec, ...]:
    """Charts for an answered question: only those fully backed by cited evidence, max 2.

    Candidates are taken round-robin across tool outcomes (first chart of each tool, then the
    second ones) so a question that used two tools shows one chart of each.
    """
    cited = set(cited_ids)
    per_outcome: list[list[ChartSpec]] = []
    for outcome in outcomes:
        builder = BUILDERS.get(outcome.call.name)
        if builder is None or outcome.error or not outcome.evidence:
            continue
        if not isinstance(outcome.data, dict):
            continue
        try:
            candidates = builder(outcome.data, outcome.evidence)
        except (KeyError, TypeError, ValueError, IndexError, AttributeError):
            logger.warning("Could not build charts for tool %s", outcome.call.name)
            continue
        per_outcome.append([
            chart for chart in candidates
            if set(chart.evidence_ids) <= cited and _is_drawable(chart)
        ])

    chosen: list[ChartSpec] = []
    seen: set[tuple] = set()
    depth = max((len(charts) for charts in per_outcome), default=0)
    for rank in range(depth):
        for charts in per_outcome:
            if rank >= len(charts) or len(chosen) >= MAX_CHARTS:
                continue
            signature = _signature(charts[rank])
            if signature in seen:
                continue
            seen.add(signature)
            chosen.append(charts[rank])
    return tuple(replace(chart, id=f"C{index}") for index, chart in enumerate(chosen, start=1))


# --- per-tool builders -----------------------------------------------------------------------
def _plan_vs_execution(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    poai_ev, pmr_ev = evidence[0], evidence[1]
    year, cutoff, totals = data["year"], data.get("pmr_cutoff"), data["totals"]
    charts = [_chart(
        "kpis", f"Seguimiento de la inversión {year} (PMR)", "COP", [pmr_ev],
        kpis=(
            ChartKpi("Presupuesto programado", _num(totals.get("presupuesto_programado")), "COP"),
            ChartKpi("Comprometido", _num(totals.get("pct_comprometido")), "percent"),
            ChartKpi("Girado", _num(totals.get("pct_girado")), "percent"),
            ChartKpi("Compromisos", _num(totals.get("compromisos")), "COP"),
            ChartKpi("Giros", _num(totals.get("giros")), "COP"),
        ),
        note=PCT_NOTE, data_cutoff=cutoff,
    )]
    group_by = data.get("group_by", "sector")
    groups = data.get("groups") or []
    shown = groups[:MAX_CATEGORIES]
    group_label = PLAN_GROUP_LABELS.get(group_by, group_by)
    charts.append(_chart(
        "grouped_bars", f"Planeado vs comprometido vs girado {year} por {group_label}",
        "COP", [pmr_ev, poai_ev],
        categories=tuple(_plan_label(group, group_by) for group in shown),
        series=(
            ChartSeries("Planeado (POAI)", tuple(_num(g.get("valor_poai")) for g in shown)),
            ChartSeries("Compromisos (PMR)", tuple(_num(g.get("compromisos")) for g in shown)),
            ChartSeries("Giros (PMR)", tuple(_num(g.get("giros")) for g in shown)),
        ),
        note=_join(
            "Planeado = POAI; compromisos y giros = seguimiento PMR en su último corte.",
            _top_note(len(shown), data.get("groups_total", len(groups)), "mayor valor POAI"),
        ),
        data_cutoff=cutoff,
    ))
    return charts


def _budget_execution(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    months = data.get("months") or []
    totals = data.get("totals")
    if not months or not totals:
        return []
    [pac_ev] = evidence[:1]
    period = _month_label(months[0]) if len(months) == 1 else (
        f"{_month_label(months[0])} a {_month_label(months[-1])}"
    )
    charts = [_chart(
        "kpis", f"Plan Anual de Caja (PAC), {period}", "unknown", [pac_ev],
        kpis=(
            ChartKpi("Programado", _num(totals.get("programmed")), "unknown"),
            ChartKpi("Ejecutado", _num(totals.get("executed")), "unknown"),
            ChartKpi("Ejecutado sobre lo programado", _num(totals.get("pct_executed")),
                     "percent"),
        ),
        note=PAC_UNIT_NOTE,
    )]
    charts.append(_chart(
        "line", "PAC: programado vs ejecutado por mes", "unknown", [pac_ev],
        categories=tuple(_month_label(month) for month in months),
        series=(
            ChartSeries("Programado", tuple(_num(m.get("programmed")) for m in months)),
            ChartSeries("Ejecutado", tuple(_num(m.get("executed")) for m in months)),
        ),
        note=PAC_UNIT_NOTE,
    ))
    return charts


def _pqrs_stats(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    total = data["total"]
    if not total.get("count"):
        return []
    [pqrs_ev] = evidence[:1]
    group_by = data.get("group_by", "subtema")
    top = list(data.get("top") or [])
    if group_by == "vigencia":
        top.sort(key=lambda item: str(item["value"]))
    shown = top[:MAX_CATEGORIES]
    return [
        _chart(
            "kpis", "PQRS radicadas ante la Alcaldía Local", "count", [pqrs_ev],
            kpis=(
                ChartKpi("PQRS radicadas", _num(total.get("count")), "count"),
                ChartKpi("Mediana de días de respuesta", _num(total.get("median_response_days")),
                         "days"),
                ChartKpi("Cerradas", _num(total.get("pct_closed")), "percent"),
            ),
            note=data.get("response_days_note"),
        ),
        _chart(
            "bars", f"PQRS por {PQRS_GROUP_LABELS.get(group_by, group_by)}", "count", [pqrs_ev],
            categories=tuple(_short(item["value"]) for item in shown),
            series=(ChartSeries("PQRS", tuple(_num(item.get("count")) for item in shown)),),
            note=None if group_by == "vigencia" else
            f"Los {len(shown)} grupos con más PQRS.",
        ),
    ]


def _participatory_budget(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    pp_ev, crp_ev = evidence[0], evidence[1]
    by_status = _top_items(data.get("by_status") or {})
    commitments = data.get("commitments") or {}
    return [
        _chart(
            "bars", "Propuestas ciudadanas por estado", "count", [pp_ev],
            categories=tuple(_short(name) for name, _ in by_status),
            series=(ChartSeries("Propuestas", tuple(_num(count) for _, count in by_status)),),
            note=f"Total de propuestas: {_int_text(data.get('proposals'))}.",
            data_cutoff=data.get("cutoff"),
        ),
        _chart(
            "kpis", "Compromisos presupuestales (CRP)", "COP", [crp_ev],
            kpis=(
                ChartKpi("Valor comprometido", _num(commitments.get("committed_value")), "COP"),
                ChartKpi("CRP", _num(commitments.get("crp")), "count"),
            ),
        ),
    ]


def _investment_by_ods(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    [ods_ev] = evidence[:1]
    groups = data.get("groups") or []
    shown = groups[:MAX_CATEGORIES]
    return [_chart(
        "bars", f"Inversión planeada {data['year']} por ODS (POAI)", "COP", [ods_ev],
        categories=tuple(_ods_label(group) for group in shown),
        series=(ChartSeries("Planeado (POAI)", tuple(_num(g.get("valor_poai")) for g in shown)),),
        note=_join(data.get("note"),
                   _top_note(len(shown), data.get("groups_total", len(groups)), "mayor valor")),
    )]


def _changes_between_cutoffs(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    [ev] = evidence[:1]
    first, last = data["from_cutoff"], data["to_cutoff"]
    names = (f"Corte {_date_label(first)}", f"Corte {_date_label(last)}")
    if data.get("domain") == "pmr":
        totals = data["totals_by_cutoff"]
        columns = (("Presupuesto programado", "presupuesto_programado"),
                   ("Compromisos", "compromisos"), ("Giros", "giros"))
        return [_chart(
            "grouped_bars", f"Seguimiento de metas {data['year']}: antes y después", "COP", [ev],
            categories=tuple(label for label, _ in columns),
            series=tuple(
                ChartSeries(name, tuple(_num(totals[cut].get(key)) for _, key in columns))
                for name, cut in zip(names, (first, last), strict=True)
            ),
            data_cutoff=last,
        )]
    by_cut = data["status_by_cutoff"]
    statuses = [name for name, _ in _top_items(by_cut.get(last) or {})]
    for name, _ in _top_items(by_cut.get(first) or {}, limit=None):
        if name not in statuses and len(statuses) < MAX_CATEGORIES:
            statuses.append(name)
    return [
        _chart(
            "grouped_bars", "Propuestas ciudadanas por estado en cada corte", "count", [ev],
            categories=tuple(_short(name) for name in statuses),
            series=tuple(
                ChartSeries(name, tuple(_num((by_cut.get(cut) or {}).get(s, 0)) for s in statuses))
                for name, cut in zip(names, (first, last), strict=True)
            ),
            data_cutoff=last,
        ),
        _chart(
            "kpis", "Cambios entre cortes", "count", [ev],
            kpis=(
                ChartKpi("Propuestas comparadas", _num(data.get("proposals_compared")), "count"),
                ChartKpi("Cambiaron de estado", _num(data.get("status_changes")), "count"),
            ),
            data_cutoff=last,
        ),
    ]


def _poai_vs_pmr(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    pmr_ev = evidence[1]
    return [_chart(
        "kpis", f"Contraste POAI vs PMR {data['year']}", "count", [pmr_ev],
        kpis=(
            ChartKpi("Metas comparadas", _num(data.get("metas_compared")), "count"),
            ChartKpi("Diferencias de presupuesto", _num(data.get("budget_differences")), "count"),
            ChartKpi("Diferencias de magnitud", _num(data.get("magnitude_differences")), "count"),
        ),
        note=DIFFERENCE_NOTE, data_cutoff=data.get("pmr_cutoff"), verdict=data.get("verdict"),
    )]


def _contrast(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    pp_ev = evidence[0]
    return [_chart(
        "kpis", "Propuestas con recursos vs compromisos (CRP)", "count", [pp_ev],
        kpis=(
            ChartKpi("Deberían tener recursos", _num(data.get("proposals_expected_funded")),
                     "count"),
            ChartKpi("Con compromiso (CRP)", _num(data.get("proposals_with_commitment")), "count"),
            ChartKpi("Sin compromiso", _num(data.get("proposals_without_commitment")), "count"),
        ),
        note=DIFFERENCE_NOTE, data_cutoff=data.get("cutoff"), verdict=data.get("verdict"),
    )]


def _goal_detail(data: dict[str, Any], evidence: list[Evidence]) -> list[ChartSpec]:
    if data.get("found") != 1 or "meta" not in data:
        return []
    code = data["meta"]["meta_code"]
    charts = []
    pmr_rows = data.get("pmr_latest") or []
    if pmr_rows and len(evidence) > 1:
        row = pmr_rows[-1]
        charts.append(_chart(
            "kpis", f"Meta {code}: seguimiento {row['vigencia']} (PMR)", "COP", [evidence[1]],
            kpis=(
                ChartKpi("Presupuesto programado", _num(row.get("presupuesto_programado")), "COP"),
                ChartKpi("Compromisos", _num(row.get("compromisos")), "COP"),
                ChartKpi("Comprometido", _num(row.get("pct_comprometido")), "percent"),
                ChartKpi("Girado", _num(row.get("pct_girado")), "percent"),
            ),
            note=PCT_NOTE, data_cutoff=row.get("fecha_corte"),
        ))
    poai_rows = data.get("poai") or []
    charts.append(_chart(
        "bars", f"Meta {code}: valor planeado por año (POAI)", "COP", [evidence[0]],
        categories=tuple(str(row["vigencia"]) for row in poai_rows),
        series=(ChartSeries("Planeado (POAI)",
                            tuple(_num(row.get("valor_poai")) for row in poai_rows)),),
    ))
    return charts


BUILDERS: dict[str, Builder] = {
    "get_plan_vs_execution": _plan_vs_execution,
    "get_budget_execution": _budget_execution,
    "get_pqrs_stats": _pqrs_stats,
    "get_participatory_budget": _participatory_budget,
    "get_investment_by_ods": _investment_by_ods,
    "get_changes_between_cutoffs": _changes_between_cutoffs,
    "compare_poai_vs_pmr": _poai_vs_pmr,
    "compare_participatory_budget_vs_commitments": _contrast,
    "get_goal_detail": _goal_detail,
}


# --- helpers ---------------------------------------------------------------------------------
def _chart(
    kind: str, title: str, unit: ChartUnit, evidence: list[Evidence], *,
    data_cutoff: str | None = None, **fields: Any,
) -> ChartSpec:
    return ChartSpec(
        id="", kind=kind, title=title, unit=unit,  # type: ignore[arg-type]
        evidence_id=evidence[0].id,
        evidence_ids=tuple(item.id for item in evidence),
        data_cutoff=data_cutoff or evidence[0].data_cutoff,
        **fields,
    )


def _is_drawable(chart: ChartSpec) -> bool:
    """A chart needs real numbers; bars and lines need at least two categories (a one-bar
    chart is a KPI, not a chart)."""
    if chart.kind == "kpis":
        return any(kpi.value is not None for kpi in chart.kpis)
    if len(chart.categories) < 2 or not chart.series:
        return False
    return any(value is not None for series in chart.series for value in series.values)


def _signature(chart: ChartSpec) -> tuple:
    return (chart.kind, chart.title, chart.categories, chart.series, chart.kpis)


def _num(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) or math.isinf(number) else number


def _int_text(value: Any) -> str:
    number = _num(value)
    return "sin dato" if number is None else f"{number:,.0f}".replace(",", ".")


def _short(value: Any) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= MAX_LABEL else text[: MAX_LABEL - 1].rstrip() + "…"


def _top_items(counts: dict[str, Any], limit: int | None = MAX_CATEGORIES) -> list[tuple[str, Any]]:
    items = sorted(counts.items(), key=lambda item: (-(_num(item[1]) or 0), item[0]))
    return items[:limit] if limit else items


def _top_note(shown: int, total: int, criterion: str) -> str | None:
    return f"Se muestran {shown} de {total}, los de {criterion}." if total > shown else None


def _join(*parts: str | None) -> str | None:
    text = " ".join(part for part in parts if part)
    return text or None


def _plan_label(group: dict[str, Any], group_by: str) -> str:
    if group_by == "meta":
        return _short(f"{group.get('codigo_meta_extendida')} · {group.get('descripcion_meta')}")
    if group_by == "proyecto":
        return _short(f"{group.get('codigo_proyecto')} · {group.get('nombre_proyecto')}")
    return _short(group.get("nombre_sector") or "Sin sector")


def _ods_label(group: dict[str, Any]) -> str:
    if group.get("codigo_meta_ods"):
        return _short(f"Meta ODS {group['codigo_meta_ods']}")
    return _short(f"ODS {group.get('codigo_ods')} · {group.get('nombre_ods')}")


def _month_label(month: dict[str, Any]) -> str:
    return f"{MONTHS_ES[int(month['month']) - 1]} {int(month['year'])}"


def _date_label(value: str | None) -> str:
    """'2026-03-31' → '31-03-2026' (the format used in the prompts and the sources)."""
    if not value or len(value) < 10:
        return value or "sin fecha"
    return f"{value[8:10]}-{value[5:7]}-{value[0:4]}"
