import pytest

from app.application.agent_tools import AgentTools, EvidenceLedger, compute_verdict
from app.domain import ToolCall
from tests.agent_fakes import build_fixture_db


@pytest.fixture
def tools(tmp_path):
    return AgentTools(build_fixture_db(tmp_path / "agent.duckdb"))


def run(tools, name, ledger=None, **args):
    return tools.execute(ToolCall(name, args), ledger or EvidenceLedger())


def test_budget_execution_totals_rank_and_evidence(tools):
    outcome = run(tools, "get_budget_execution", year=2025)

    assert outcome.error is None
    assert [m["month"] for m in outcome.data["months"]] == [1, 2]
    assert outcome.data["months"][0]["rank_in_month"] == 3
    assert outcome.data["totals"] == {"programmed": 500.0, "executed": 300.0,
                                      "pct_executed": 60.0}
    assert "No afirmar que son pesos" in outcome.data["unit"]
    [evidence] = outcome.evidence
    assert evidence.id == "E1"
    assert evidence.source_id == "F1"
    assert evidence.data_cutoff == "2025-02"
    assert evidence.locator == "f1_pac_execution · year=2025"


def test_evidence_ids_are_assigned_by_code_and_unique(tools):
    ledger = EvidenceLedger()

    first = run(tools, "get_budget_execution", ledger, year=2025)
    second = run(tools, "compare_participatory_budget_vs_commitments", ledger, year=2025)

    ids = [e.id for e in first.evidence + second.evidence]
    assert ids == ["E1", "E2", "E3"]
    assert ledger.ids() == set(ids)


def test_pqrs_stats_grouped_by_subtema(tools):
    outcome = run(tools, "get_pqrs_stats", year=2025, group_by="subtema")

    total = outcome.data["total"]
    assert total["count"] == 4
    assert total["pct_closed"] == 75.0
    assert total["median_response_days"] == 10.0
    assert outcome.data["top"][0] == {
        "value": "MALLA VIAL", "count": 2, "median_response_days": 10.0, "pct_closed": 50.0,
    }


def test_pqrs_topic_keyword_is_accent_and_case_insensitive(tools):
    outcome = run(tools, "get_pqrs_stats", topic_keyword="malla víal")

    assert outcome.data["total"]["count"] == 3


def test_bad_group_by_is_rejected_without_evidence(tools):
    outcome = run(tools, "get_pqrs_stats", group_by="radicado; DROP TABLE f2_pqrs")

    assert outcome.error is not None
    assert "group_by" in outcome.error
    assert outcome.evidence == []


def test_unknown_parameters_and_tools_are_rejected(tools):
    assert run(tools, "get_budget_execution", sql="SELECT 1").error is not None
    assert run(tools, "get_budget_execution", month=13).error is not None
    assert run(tools, "drop_everything").error == "Herramienta desconocida: drop_everything"


def test_sql_like_keyword_is_plain_filter_text(tools, tmp_path):
    outcome = run(tools, "get_pqrs_stats", topic_keyword="x' OR '1'='1")

    assert outcome.error is None
    assert outcome.data["total"]["count"] == 0
    # The literal text is matched as a substring, and the table is still intact afterwards.
    literal = run(tools, "get_pqrs_stats", topic_keyword="'; DROP TABLE f2_pqrs; --")
    assert literal.data["total"]["count"] == 1
    assert run(tools, "get_pqrs_stats").data["total"]["count"] == 5


def test_participatory_budget_by_sector_and_status(tools):
    outcome = run(tools, "get_participatory_budget", year=2025, sector_keyword="cultura")

    assert outcome.data["proposals"] == 2
    assert outcome.data["by_status"] == {"Materializada": 1, "En ejecución": 1}
    assert outcome.data["avg_progress_pct"] == 75.0
    assert outcome.data["committed_value"] == 1000.0
    assert len(outcome.evidence) == 2

    filtered = run(tools, "get_participatory_budget", status="en ejecucion")
    assert filtered.data["proposals"] == 1
    unknown = run(tools, "get_participatory_budget", status="Cancelada")
    assert "valid_statuses" in unknown.data


def test_contrast_coherent(tools):
    outcome = run(tools, "compare_participatory_budget_vs_commitments",
                  year=2025, sector_keyword="cultura")

    assert outcome.data["verdict"] == "coherent"
    assert outcome.data["proposals_expected_funded"] == 2
    assert outcome.data["proposals_with_commitment"] == 2
    assert outcome.data["committed_value"] == 1000.0


def test_contrast_difference_detected(tools):
    outcome = run(tools, "compare_participatory_budget_vs_commitments",
                  year=2025, sector_keyword="ambiente")

    assert outcome.data["verdict"] == "difference_detected"
    assert outcome.data["proposals_expected_funded"] == 1
    assert outcome.data["proposals_without_commitment"] == 1
    assert outcome.data["missing_proposals_sample"][0]["code"] == "3"


def test_contrast_not_comparable_without_funded_proposals(tools):
    outcome = run(tools, "compare_participatory_budget_vs_commitments", year=2026)

    assert outcome.data["verdict"] == "not_comparable"


@pytest.mark.parametrize(("expected", "matched", "commitments", "verdict"), [
    (0, 0, 5, "not_comparable"),
    (3, 0, 0, "not_comparable"),
    (3, 3, 5, "coherent"),
    (3, 2, 5, "difference_detected"),
])
def test_compute_verdict(expected, matched, commitments, verdict):
    assert compute_verdict(expected, matched, commitments) == verdict


def test_list_sources_and_gap_tool(tools):
    sources = run(tools, "list_sources")
    assert [s["source_id"] for s in sources.data["sources"]] == [
        "F1", "F2", "F3-commitments", "F3-progress",
    ]
    gap = run(tools, "report_information_gap", topic="seguridad", missing_data="hurtos")
    assert gap.data["recorded"] is True
    assert gap.evidence == []


def test_missing_database_is_reported_as_unavailable(tmp_path):
    from app.adapters.duckdb import DuckDBStore

    outcome = AgentTools(DuckDBStore(tmp_path / "none.duckdb")).execute(
        ToolCall("get_budget_execution", {}), EvidenceLedger()
    )

    assert outcome.error == "La fuente de datos no está disponible."
