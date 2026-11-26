"""Charts are built by code from tool outcomes and only when the answer cites their evidence."""

import pytest

from app.application import AgentTools, AskQuestion, EvidenceLedger
from app.application.charts import MAX_CHARTS, build_charts
from app.domain import DraftAnswer, Evidence, ToolCall, ToolOutcome
from tests.agent_fakes import InMemoryGaps, ScriptedLLM, build_fixture_db


@pytest.fixture(scope="module")
def tools(tmp_path_factory):
    return AgentTools(build_fixture_db(tmp_path_factory.mktemp("charts") / "agent.duckdb"))


def run(tools, name, args=None, ledger=None):
    return tools.execute(ToolCall(name, args or {}), ledger or EvidenceLedger())


def charts_for(outcome, cited=None):
    ids = [item.id for item in outcome.evidence] if cited is None else cited
    return build_charts([outcome], ids)


def values(chart):
    return [series.values for series in chart.series]


def kpis(chart):
    return {kpi.label: (kpi.value, kpi.unit) for kpi in chart.kpis}


# --- mapping per tool ------------------------------------------------------------------------
def test_plan_vs_execution_kpis_and_grouped_bars(tools):
    outcome = run(tools, "get_plan_vs_execution")
    kpi_chart, bars = charts_for(outcome)

    assert kpi_chart.kind == "kpis"
    assert kpi_chart.evidence_ids == ("E2",)  # PMR evidence
    assert kpis(kpi_chart)["Comprometido"] == (31.7, "percent")
    assert kpis(kpi_chart)["Compromisos"] == (3800.0, "COP")
    assert kpi_chart.data_cutoff == "2026-06-30"
    assert "presupuesto programado del PMR" in kpi_chart.note

    assert bars.kind == "grouped_bars"
    assert bars.unit == "COP"
    assert set(bars.evidence_ids) == {"E1", "E2"}  # POAI + PMR
    assert bars.categories == ("MOVILIDAD", "CULTURA, RECREACIÓN Y DEPORTE", "AMBIENTE")
    assert [s.name for s in bars.series] == ["Planeado (POAI)", "Compromisos (PMR)", "Giros (PMR)"]
    assert values(bars)[0] == (4500.0, 4000.0, 3500.0)
    # Same numbers as the tool data: nothing is recomputed.
    assert values(bars)[1] == tuple(g["compromisos"] for g in outcome.data["groups"])


def test_budget_execution_line_with_unknown_unit(tools):
    totals, line = charts_for(run(tools, "get_budget_execution", {"year": 2025}))

    assert totals.kind == "kpis"
    assert totals.unit == "unknown"
    assert kpis(totals)["Ejecutado sobre lo programado"] == (60.0, "percent")
    assert line.kind == "line"
    assert line.unit == "unknown"
    assert line.categories == ("ene 2025", "feb 2025")
    assert values(line) == [(200.0, 300.0), (150.0, 150.0)]
    assert "no documenta la unidad" in line.note


def test_single_month_budget_is_only_kpis(tools):
    charts = charts_for(run(tools, "get_budget_execution", {"year": 2025, "month": 1}))

    assert [chart.kind for chart in charts] == ["kpis"]


def test_pqrs_stats_top_topics(tools):
    summary, bars = charts_for(run(tools, "get_pqrs_stats"))

    assert kpis(summary)["PQRS radicadas"] == (5.0, "count")
    assert kpis(summary)["Mediana de días de respuesta"] == (7.5, "days")
    assert bars.kind == "bars"
    assert bars.unit == "count"
    assert bars.categories[0] == "MALLA VIAL"
    assert values(bars)[0][0] == 3.0


def test_pqrs_by_year_is_sorted_chronologically(tools):
    _, bars = charts_for(run(tools, "get_pqrs_stats", {"group_by": "vigencia"}))

    assert bars.categories == ("2024", "2025")


def test_participatory_budget_by_status_and_commitments(tools):
    by_status, commitments = charts_for(run(tools, "get_participatory_budget"))

    assert by_status.kind == "bars"
    assert by_status.evidence_ids == ("E1",)
    assert dict(zip(by_status.categories, by_status.series[0].values, strict=True))[
        "En ejecución"] == 2.0
    assert commitments.evidence_ids == ("E2",)
    assert kpis(commitments)["Valor comprometido"] == (3700.0, "COP")


def test_investment_by_ods(tools):
    [chart] = charts_for(run(tools, "get_investment_by_ods"))

    assert chart.kind == "bars"
    assert chart.unit == "COP"
    assert chart.categories[0].startswith("ODS 11")
    assert values(chart) == [(8000.0, 4000.0)]


def test_contracts_kpis_and_value_by_project(tools):
    summary, bars = charts_for(run(tools, "get_contracts"))

    assert summary.kind == "kpis"
    assert kpis(summary)["Contratos"] == (5.0, "count")
    assert kpis(summary)["Valor contratado"] == (3800.0, "COP")  # one value per contract
    assert kpis(summary)["Con vínculo verificado"] == (80.0, "percent")
    assert "no es lo ejecutado ni lo pagado" in summary.note
    assert bars.kind == "bars"
    assert bars.categories[0] == "2251 · Cultura viva"
    assert values(bars) == [(3000.0, 1500.0, 300.0)]
    assert "no se deben sumar" in bars.note


def test_contracts_by_year_has_no_overlap_note(tools):
    _, bars = charts_for(run(tools, "get_contracts", {"group_by": "vigencia"}))

    assert bars.categories == ("2025", "2026")
    assert values(bars) == [(1300.0, 2500.0)]
    assert "no se deben sumar" not in bars.note


def test_pmr_changes_before_after(tools):
    [chart] = charts_for(run(tools, "get_changes_between_cutoffs", {"domain": "pmr"}))

    assert chart.kind == "grouped_bars"
    assert [s.name for s in chart.series] == ["Corte 31-03-2026", "Corte 30-06-2026"]
    assert values(chart) == [(12000.0, 1500.0, 300.0), (12000.0, 3800.0, 1100.0)]


def test_participatory_changes_before_after(tools):
    bars, summary = charts_for(
        run(tools, "get_changes_between_cutoffs", {"domain": "participatory_budget"})
    )

    assert bars.kind == "grouped_bars"
    assert bars.unit == "count"
    assert "Materializada" in bars.categories
    assert kpis(summary)["Cambiaron de estado"] == (1.0, "count")


@pytest.mark.parametrize(("name", "args", "evidence"), [
    ("compare_poai_vs_pmr", {"year": 2026}, ("E2",)),
    ("compare_participatory_budget_vs_commitments", {"year": 2025}, ("E1",)),
])
def test_comparisons_become_kpis_with_the_code_verdict(tools, name, args, evidence):
    outcome = run(tools, name, args)
    [chart] = charts_for(outcome)

    assert chart.kind == "kpis"
    assert chart.verdict == outcome.data["verdict"] == "difference_detected"
    assert chart.evidence_ids == evidence
    assert "no implica irregularidad" in chart.note


def test_goal_detail_kpis_and_poai_by_year(tools):
    follow_up, by_year = charts_for(run(tools, "get_goal_detail", {"keyword": "malla"}))

    assert follow_up.title.startswith("Meta 25022")
    assert kpis(follow_up)["Comprometido"] == (44.4, "percent")
    assert follow_up.evidence_ids == ("E2",)
    assert by_year.categories == ("2025", "2026")
    assert by_year.evidence_ids == ("E1",)


def test_goal_with_several_matches_has_no_chart():
    evidence = Evidence("E1", "POAI", "POAI", None, None, "x", "y")
    outcome = ToolOutcome(ToolCall("get_goal_detail", {"keyword": "vía"}),
                          data={"found": 3, "candidates": []}, evidence=[evidence])

    assert build_charts([outcome], ["E1"]) == ()


@pytest.mark.parametrize(("name", "args"), [
    ("list_sources", {}),
    ("report_information_gap", {"topic": "seguridad", "missing_data": "hurtos"}),
    ("compare_poai_vs_pmr", {"year": 2030}),  # no data: answered as data, no evidence
])
def test_tools_without_charts(tools, name, args):
    assert charts_for(run(tools, name, args)) == ()


def test_failed_tool_has_no_chart():
    outcome = ToolOutcome(ToolCall("get_pqrs_stats", {}), data=None, error="caída")
    assert build_charts([outcome], ["E1"]) == ()


def test_malformed_tool_data_is_skipped_not_raised():
    evidence = Evidence("E1", "PQRS", "PQRS", None, None, "x", "y")
    outcome = ToolOutcome(ToolCall("get_pqrs_stats", {}), data={"unexpected": 1},
                          evidence=[evidence])
    assert build_charts([outcome], ["E1"]) == ()


# --- citation rule and caps ------------------------------------------------------------------
def test_chart_needs_all_its_evidence_cited(tools):
    outcome = run(tools, "get_plan_vs_execution")

    only_pmr = charts_for(outcome, cited=["E2"])
    only_poai = charts_for(outcome, cited=["E1"])

    assert [chart.kind for chart in only_pmr] == ["kpis"]  # grouped bars also need E1
    assert only_poai == ()
    assert charts_for(outcome, cited=[]) == ()


def test_at_most_two_charts_round_robin_across_tools(tools):
    ledger = EvidenceLedger()
    outcomes = [
        run(tools, "get_plan_vs_execution", ledger=ledger),
        run(tools, "get_pqrs_stats", ledger=ledger),
        run(tools, "get_participatory_budget", ledger=ledger),
    ]
    cited = [item.id for item in ledger.items]

    charts = build_charts(outcomes, cited)

    assert len(charts) == MAX_CHARTS
    # First chart of the first two tools, not two charts of the first tool.
    assert [chart.title for chart in charts] == [
        "Seguimiento de la inversión 2026 (PMR)", "PQRS radicadas ante la Alcaldía Local",
    ]
    assert [chart.id for chart in charts] == ["C1", "C2"]


def test_repeated_tool_call_does_not_duplicate_charts(tools):
    ledger = EvidenceLedger()
    outcomes = [run(tools, "get_investment_by_ods", ledger=ledger) for _ in range(2)]

    charts = build_charts(outcomes, [item.id for item in ledger.items])

    assert len(charts) == 1


# --- integration with AskQuestion ------------------------------------------------------------
def ask(tools, draft, calls):
    llm = ScriptedLLM([calls], draft)
    return AskQuestion(llm, tools, InMemoryGaps()).run("¿Cuánto se invirtió?")


def test_answer_carries_charts_backed_by_cited_evidence(tools):
    result = ask(
        tools,
        DraftAnswer("Se comprometió el 31,7 % (E2), de lo planeado (E1).", ["E1", "E2"],
                    "answered"),
        [ToolCall("get_plan_vs_execution", {})],
    )

    assert [chart.kind for chart in result.charts] == ["kpis", "grouped_bars"]


@pytest.mark.parametrize("draft", [
    DraftAnswer("No hay datos de seguridad.", [], "information_gap"),
    DraftAnswer("¿De qué año?", [], "needs_clarification"),
])
def test_no_charts_for_gaps_or_clarifications(tools, draft):
    result = ask(tools, draft, [ToolCall("get_plan_vs_execution", {})])

    assert result.charts == ()


def test_rejected_answer_has_no_charts(tools):
    result = ask(tools, DraftAnswer("Se ejecutó el 99 %.", [], "answered"),
                 [ToolCall("get_budget_execution", {"year": 2025})])

    assert result.status == "information_gap"
    assert result.charts == ()
