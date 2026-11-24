import json

import pytest

from app.application.agent_tools import (
    TOOL_SPECS,
    AgentTools,
    EvidenceLedger,
    compute_plan_verdict,
    compute_verdict,
)
from app.domain import ToolCall
from tests.agent_fakes import build_fixture_db
from tests.curated_fixture import OFFICIAL_NAME


@pytest.fixture(scope="module")
def tools(tmp_path_factory):
    # Tools only read: one fixture database for the whole module.
    return AgentTools(build_fixture_db(tmp_path_factory.mktemp("agent") / "agent.duckdb"))


def run(tools, name, ledger=None, **args):
    return tools.execute(ToolCall(name, args), ledger or EvidenceLedger())


# --- PAC (F1, portal) ------------------------------------------------------------------------
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
    assert evidence.portal_url.startswith("https://datosabiertos.bogota.gov.co/")


def test_evidence_ids_are_assigned_by_code_and_unique(tools):
    ledger = EvidenceLedger()

    first = run(tools, "get_budget_execution", ledger, year=2025)
    second = run(tools, "compare_participatory_budget_vs_commitments", ledger, year=2025)

    ids = [e.id for e in first.evidence + second.evidence]
    assert ids == ["E1", "E2", "E3"]
    assert ledger.ids() == set(ids)


# --- PQRS (curated) --------------------------------------------------------------------------
def test_pqrs_stats_grouped_by_subtema(tools):
    outcome = run(tools, "get_pqrs_stats", year=2025, group_by="subtema")

    total = outcome.data["total"]
    assert total["count"] == 4
    assert total["pct_closed"] == 75.0
    assert total["median_response_days"] == 10.0
    assert outcome.data["top"][0] == {
        "value": "MALLA VIAL", "count": 2, "median_response_days": 10.0, "pct_closed": 50.0,
    }
    assert outcome.data["response_status"]["Sin respuesta al peticionario"] == 1
    [evidence] = outcome.evidence
    assert evidence.source_id == "PQRS"
    assert evidence.data_cutoff == "2025-04-01"


def test_pqrs_can_group_by_response_status(tools):
    outcome = run(tools, "get_pqrs_stats", group_by="observacion_general")

    values = {item["value"]: item["count"] for item in outcome.data["top"]}
    assert values["Sin respuesta al peticionario"] == 1
    assert sum(values.values()) == 5


def test_pqrs_topic_keyword_is_accent_and_case_insensitive(tools):
    outcome = run(tools, "get_pqrs_stats", topic_keyword="malla víal")

    assert outcome.data["total"]["count"] == 3


def test_bad_group_by_is_rejected_without_evidence(tools):
    outcome = run(tools, "get_pqrs_stats", group_by="usuario_actual")

    assert outcome.error is not None
    assert "group_by" in outcome.error
    assert outcome.evidence == []


def test_unknown_parameters_and_tools_are_rejected(tools):
    assert run(tools, "get_budget_execution", sql="SELECT 1").error is not None
    assert run(tools, "get_budget_execution", month=13).error is not None
    assert run(tools, "drop_everything").error == "Herramienta desconocida: drop_everything"


def test_sql_like_keyword_is_plain_filter_text(tools):
    outcome = run(tools, "get_pqrs_stats", topic_keyword="x' OR '1'='1")

    assert outcome.error is None
    assert outcome.data["total"]["count"] == 0
    # The literal text is matched as a substring, and the table is still intact afterwards.
    literal = run(tools, "get_pqrs_stats", topic_keyword="'; DROP TABLE pqrs; --")
    assert literal.data["total"]["count"] == 1
    assert run(tools, "get_pqrs_stats").data["total"]["count"] == 5


# --- Participatory budget and CRP ----------------------------------------------------------------
def test_participatory_budget_by_sector_and_status(tools):
    outcome = run(tools, "get_participatory_budget", year=2025, sector_keyword="cultura")

    assert outcome.data["proposals"] == 2
    assert outcome.data["by_status"] == {"Materializada": 1, "En ejecución": 1}
    assert outcome.data["cutoff"] == "2026-10-01"
    assert outcome.data["commitments"]["committed_value"] == 1000.0  # both repeated lines
    assert outcome.data["commitments"]["lines"] == 2
    assert [e.source_id for e in outcome.evidence] == ["PP", "CRP"]

    filtered = run(tools, "get_participatory_budget", status="en ejecucion")
    assert filtered.data["proposals"] == 2
    unknown = run(tools, "get_participatory_budget", status="Cancelada")
    assert "valid_statuses" in unknown.data
    assert unknown.evidence == []


def test_participatory_budget_2026_uses_the_portal_supplement(tools):
    outcome = run(tools, "get_participatory_budget", year=2026)

    commitments = outcome.data["commitments"]
    assert commitments["committed_value"] == 700.0
    [source] = commitments["by_source"]
    assert source["source"] == "portal"
    assert source["vigencias"] == [2026]


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
    assert outcome.data["proposals_expected_funded"] == 2
    assert outcome.data["proposals_without_commitment"] == 1
    assert outcome.data["missing_proposals_sample"][0]["code"] == "106"


def test_contrast_2026_counts_supplemented_crp_as_informative(tools):
    outcome = run(tools, "compare_participatory_budget_vs_commitments", year=2026)

    # No 2026 proposal is in a funded state, so the verdict cannot be computed...
    assert outcome.data["verdict"] == "not_comparable"
    # ...but the portal CRP that already funds proposal 105 is reported.
    assert outcome.data["proposals_with_commitment_in_other_state"] == 1
    assert outcome.data["other_state_sample"][0]["code"] == "105"
    assert outcome.data["commitment_sources"][0]["source"] == "portal"


@pytest.mark.parametrize(("expected", "matched", "commitments", "verdict"), [
    (0, 0, 5, "not_comparable"),
    (3, 0, 0, "not_comparable"),
    (3, 3, 5, "coherent"),
    (3, 2, 5, "difference_detected"),
])
def test_compute_verdict(expected, matched, commitments, verdict):
    assert compute_verdict(expected, matched, commitments) == verdict


# --- POAI / PMR / ODS ----------------------------------------------------------------------------
def test_plan_vs_execution_by_sector(tools):
    outcome = run(tools, "get_plan_vs_execution", year=2026)

    data = outcome.data
    assert data["pmr_cutoff"] == "2026-06-30"
    assert data["totals"]["valor_poai"] == 12000.0
    assert data["totals"]["presupuesto_programado"] == 12000.0
    assert data["totals"]["compromisos"] == 3800.0
    assert data["totals"]["pct_comprometido"] == 31.7
    assert data["totals"]["pct_girado"] == 9.2
    assert data["totals"]["metas_sin_entregas"] == 2
    assert [g["nombre_sector"] for g in data["groups"]] == [
        "MOVILIDAD", "CULTURA, RECREACIÓN Y DEPORTE", "AMBIENTE",
    ]
    assert [e.source_id for e in outcome.evidence] == ["POAI", "PMR"]
    assert outcome.evidence[0].portal_url is None
    assert "Alcaldía Local" in outcome.evidence[0].origin_note


def test_plan_vs_execution_by_meta_with_filters(tools):
    outcome = run(tools, "get_plan_vs_execution", year=2026, ods_keyword="ODS 11",
                  group_by="meta")

    groups = {g["codigo_meta_extendida"]: g for g in outcome.data["groups"]}
    assert set(groups) == {"25021", "25022"}
    assert groups["25021"]["magnitud_poai"] == 200.0
    assert groups["25021"]["magnitud_programada_pmr"] == 150.0
    assert groups["25021"]["pct_entregado"] == 13.3

    by_sector = run(tools, "get_plan_vs_execution", sector_keyword="ambiente", group_by="proyecto")
    assert by_sector.data["totals"]["valor_poai"] == 3500.0  # only the AMBIENTE meta of 2502


def test_plan_vs_execution_filters_by_project_code(tools):
    # Regression: "¿Cuánto se programó para el proyecto 2791 en 2026?" found nothing because no
    # tool accepted a project code.
    outcome = run(tools, "get_plan_vs_execution", year=2026, project_code="2251",
                  group_by="meta")

    groups = outcome.data["groups"]
    assert {g["codigo_meta_extendida"] for g in groups} == {"22511", "22512"}
    assert outcome.data["totals"]["valor_poai"] == sum(g["valor_poai"] for g in groups)
    assert outcome.data["totals"]["valor_poai"] < 12000.0  # not the whole plan
    assert "project_code=2251" in outcome.evidence[0].locator
    assert "None" not in outcome.evidence[1].summary


def test_plan_vs_execution_unknown_project_code_says_so(tools):
    outcome = run(tools, "get_plan_vs_execution", project_code="9999")

    assert outcome.error is None
    assert outcome.data["found"] == 0
    assert "9999" in outcome.data["message"]
    assert outcome.evidence == []


@pytest.mark.parametrize("code", ["22", "2251; DROP", "abcd"])
def test_project_code_must_be_digits(tools, code):
    assert run(tools, "get_plan_vs_execution", project_code=code).error is not None


def test_goal_detail_recognizes_a_project_code(tools):
    outcome = run(tools, "get_goal_detail", meta_code="2251")

    data = outcome.data
    assert data["is_project_code"] is True
    assert data["proyecto"] == {"codigo": "2251", "nombre": "Cultura viva"}
    assert {c["meta_code"] for c in data["candidates"]} == {"22511", "22512"}
    assert "project_code" in data["message"]


def test_plan_vs_execution_unknown_year_lists_available_years(tools):
    outcome = run(tools, "get_plan_vs_execution", year=2030)

    assert outcome.error is None
    assert outcome.data["available_years"] == [2025, 2026]
    assert outcome.evidence == []


def test_poai_2025_correction_and_tolerance(tools):
    outcome = run(tools, "compare_poai_vs_pmr", year=2025)

    # The swapped 22511/22512 rows were corrected, so 2025 matches the PMR.
    assert outcome.data["verdict"] == "coherent"
    assert outcome.data["metas_compared"] == 4
    assert outcome.data["total_poai"] == 10000.0


def test_compare_poai_vs_pmr_detects_magnitude_difference(tools):
    outcome = run(tools, "compare_poai_vs_pmr")

    data = outcome.data
    assert data["year"] == 2026
    assert data["verdict"] == "difference_detected"
    assert data["budget_differences"] == 0
    assert data["magnitude_differences"] == 1
    [meta] = data["differing_metas"]
    assert meta["meta_code"] == "25021"
    assert meta["diferencia_magnitud"] == -50.0
    assert "Veredicto: difference_detected" in outcome.evidence[1].summary


@pytest.mark.parametrize(("compared", "differing", "verdict"), [
    (0, 0, "not_comparable"), (4, 0, "coherent"), (4, 1, "difference_detected"),
])
def test_compute_plan_verdict(compared, differing, verdict):
    assert compute_plan_verdict(compared, differing) == verdict


def test_goal_detail_by_code(tools):
    outcome = run(tools, "get_goal_detail", meta_code="22511")

    data = outcome.data
    assert data["found"] == 1
    meta = data["meta"]
    assert meta["proyecto"] == {"codigo": "2251", "nombre": "Cultura viva"}
    assert meta["programa"]["nombre"] == "Programa uno"
    assert meta["objetivo_estrategico"]["nombre"] == "Objetivo uno"
    assert meta["sector"] == "CULTURA, RECREACIÓN Y DEPORTE"
    assert meta["entidad"] == "Secretaría de Cultura"
    assert data["ods"][0]["codigo_meta_ods"] == "8.3"
    assert [p["valor_poai"] for p in data["poai"]] == [1000.0, 1500.0]
    assert data["proposals"]["by_status"] == {"Materializada": 1, "En ejecución": 1}
    assert data["crp"]["total_value"] == 1000.0
    assert data["crp"]["items"][0]["lineas"] == 2
    assert [e.source_id for e in outcome.evidence] == ["POAI", "PMR", "ODS", "PP", "CRP"]


def test_goal_detail_by_keyword_single_and_multiple(tools):
    single = run(tools, "get_goal_detail", keyword="festivales")
    assert single.data["meta"]["meta_code"] == "22512"
    assert single.data["crp"]["items"][0]["source"] == "portal"

    multiple = run(tools, "get_goal_detail", keyword="cultura viva")
    assert multiple.data["found"] == 2
    assert {c["meta_code"] for c in multiple.data["candidates"]} == {"22511", "22512"}

    none = run(tools, "get_goal_detail", keyword="hospital")
    assert none.data["found"] == 0
    assert none.evidence == []


@pytest.mark.parametrize("args", [{}, {"meta_code": "22511", "keyword": "cultura"},
                                  {"meta_code": "22511; DROP"}, {"keyword": "ab"}])
def test_goal_detail_parameter_validation(tools, args):
    assert run(tools, "get_goal_detail", **args).error is not None


def test_changes_between_cutoffs_pmr(tools):
    outcome = run(tools, "get_changes_between_cutoffs", domain="pmr")

    data = outcome.data
    assert (data["from_cutoff"], data["to_cutoff"]) == ("2026-03-31", "2026-06-30")
    assert data["metas_with_change"] == {"magnitud_contratada": 2, "magnitud_entregada": 2,
                                         "compromisos": 2, "giros": 3}
    assert data["totals_by_cutoff"]["2026-06-30"]["giros"] == 1100.0
    assert data["top_compromisos_increase"][0]["meta_code"] == "25022"


def test_changes_between_cutoffs_participatory_budget(tools):
    outcome = run(tools, "get_changes_between_cutoffs", domain="participatory_budget")

    data = outcome.data
    assert data["status_changes"] == 1
    assert data["progress_text_changes"] == 2
    assert data["transitions"] == [{"from": "En ejecución", "to": "Materializada", "count": 1}]
    assert data["examples"][0]["code"] == "101"
    assert run(tools, "get_changes_between_cutoffs", domain="crp").error is not None


def test_investment_by_ods(tools):
    outcome = run(tools, "get_investment_by_ods", year=2026)

    groups = {g["codigo_ods"]: g for g in outcome.data["groups"]}
    assert groups["11"]["valor_poai"] == 8000.0
    assert groups["8"]["valor_poai"] == 4000.0
    assert groups["11"]["pct_del_poai"] == 66.7

    detail = run(tools, "get_investment_by_ods", ods_keyword="trabajo")
    assert [g["codigo_meta_ods"] for g in detail.data["groups"]] == ["8.3"]


# --- sources, gaps, privacy ------------------------------------------------------------------
def test_list_sources_and_gap_tool(tools):
    sources = run(tools, "list_sources")
    ids = [s["source_id"] for s in sources.data["sources"]]
    assert ids == ["CRP", "F1", "F3-commitments", "ODS", "PMR", "POAI", "PP", "PQRS"]
    poai = next(s for s in sources.data["sources"] if s["source_id"] == "POAI")
    assert poai["on_open_data_portal"] is False
    assert poai["unit"] == "COP (pesos colombianos)"
    gap = run(tools, "report_information_gap", topic="seguridad", missing_data="hurtos")
    assert gap.data["recorded"] is True
    assert gap.evidence == []


def test_official_names_never_leave_any_tool(tools):
    calls = {
        "list_sources": {}, "get_pqrs_stats": {}, "get_participatory_budget": {},
        "compare_participatory_budget_vs_commitments": {}, "get_plan_vs_execution": {},
        "get_goal_detail": {"meta_code": "22511"}, "compare_poai_vs_pmr": {},
        "get_changes_between_cutoffs": {"domain": "participatory_budget"},
        "get_investment_by_ods": {},
    }
    for group in ("subtema", "tipo_peticion", "vigencia", "medio_recepcion",
                  "observacion_general"):
        outcome = run(tools, "get_pqrs_stats", group_by=group)
        assert OFFICIAL_NAME not in json.dumps(outcome.to_model_payload(), ensure_ascii=False)
    for name, args in calls.items():
        outcome = run(tools, name, **args)
        assert outcome.error is None, name
        payload = json.dumps(outcome.to_model_payload(), ensure_ascii=False)
        assert OFFICIAL_NAME not in payload
        assert "usuario_actual" not in payload
    assert {spec.name for spec in TOOL_SPECS} >= set(calls)


def test_missing_database_is_reported_as_unavailable(tmp_path):
    from app.adapters.duckdb import DuckDBStore

    outcome = AgentTools(DuckDBStore(tmp_path / "none.duckdb")).execute(
        ToolCall("get_budget_execution", {}), EvidenceLedger()
    )

    assert outcome.error == "La fuente de datos no está disponible."
