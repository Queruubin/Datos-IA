from datetime import UTC, datetime

import pytest

from app.adapters.duckdb.gap_repository import DuckDBGapRepository
from app.application import AgentTools, AskQuestion
from app.application.answer_validator import UNVERIFIED_ANSWER
from app.application.privacy import mask_pii
from app.domain import DraftAnswer, GapRecord, ToolCall
from app.ports import LLMOutputError
from tests.agent_fakes import InMemoryGaps, ScriptedLLM, build_fixture_db

BUDGET_CALL = ToolCall("get_budget_execution", {"year": 2025})
CONTRAST_CALL = ToolCall(
    "compare_participatory_budget_vs_commitments", {"year": 2025, "sector_keyword": "ambiente"}
)


@pytest.fixture(scope="module")
def tools(tmp_path_factory):
    # Tools only read: one fixture database for the whole module.
    return AgentTools(build_fixture_db(tmp_path_factory.mktemp("ask") / "agent.duckdb"))


def ask(tools, llm, gaps=None, question="¿Cuánto se ejecutó en 2025?", **kwargs):
    gaps = gaps if gaps is not None else InMemoryGaps()
    return AskQuestion(llm, tools, gaps, **kwargs).run(question), gaps


def test_answer_with_cited_evidence(tools):
    llm = ScriptedLLM(
        [[BUDGET_CALL]],
        DraftAnswer("Se ejecutó el 60 % de lo programado (E1).", ["E1"], "answered"),
    )

    result, gaps = ask(tools, llm)

    assert result.status == "answered"
    assert [e.id for e in result.evidence] == ["E1"]
    assert result.evidence[0].source_id == "F1"
    assert gaps.saved == []
    # The tool results were sent back to the model in the second round.
    assert llm.received[0] is None
    assert llm.received[1][0].evidence[0].id == "E1"


def test_numbers_without_citation_are_rejected_and_logged(tools):
    llm = ScriptedLLM([[BUDGET_CALL]], DraftAnswer("Se ejecutó el 99 %.", [], "answered"))

    result, gaps = ask(tools, llm)

    assert result.status == "information_gap"
    assert result.answer == UNVERIFIED_ANSWER
    assert result.evidence == []
    [gap] = gaps.saved
    assert gap.reason == "numbers_without_evidence"


def test_unknown_evidence_ids_are_dropped(tools):
    llm = ScriptedLLM(
        [[BUDGET_CALL]],
        DraftAnswer("Se ejecutó el 60 %.", ["E7", "E1", "E1", "X"], "answered"),
    )

    result, _ = ask(tools, llm)

    assert result.status == "answered"
    assert [e.id for e in result.evidence] == ["E1"]


def test_only_invented_ids_with_numbers_is_rejected(tools):
    llm = ScriptedLLM([[]], DraftAnswer("Hubo 300 obras.", ["E1"], "answered"))

    result, gaps = ask(tools, llm)  # no tool ran, so E1 does not exist

    assert result.status == "information_gap"
    assert len(gaps.saved) == 1


def test_information_gap_persists_masked_question(tools):
    llm = ScriptedLLM(
        [[ToolCall("report_information_gap",
                   {"topic": "seguridad", "missing_data": "hurtos por barrio"})]],
        DraftAnswer("No hay datos de seguridad en las fuentes.", [], "information_gap"),
    )
    question = (
        "Soy juan.perez@mail.com, cédula 1023456789, cel 300 123 4567: "
        "¿cuántos robos hubo en 2025?"
    )

    result, gaps = ask(tools, llm, question=question)

    assert result.status == "information_gap"
    assert result.gap.topic == "seguridad"  # taken from the tool call
    [gap] = gaps.saved
    assert gap.reason == "model_reported"
    assert gap.missing_data == "hurtos por barrio"
    assert "juan.perez" not in gap.question_masked
    assert "1023456789" not in gap.question_masked
    assert "4567" not in gap.question_masked
    assert "2025" in gap.question_masked
    # The LLM also only sees the masked question.
    assert llm.questions == [gap.question_masked]


def test_comparison_is_attached_with_code_computed_verdict(tools):
    llm = ScriptedLLM(
        [[CONTRAST_CALL]],
        DraftAnswer("Una propuesta no aparece en los compromisos (E2).", ["E2"], "answered"),
    )

    result, _ = ask(tools, llm)

    assert result.comparison["verdict"] == "difference_detected"
    assert result.comparison["evidence_ids"] == ["E1", "E2"]


def test_poai_vs_pmr_comparison_is_attached(tools):
    llm = ScriptedLLM(
        [[ToolCall("compare_poai_vs_pmr", {"year": 2026})]],
        DraftAnswer("Una meta tiene magnitud distinta (E2).", ["E2"], "answered"),
    )

    result, _ = ask(tools, llm)

    assert result.comparison["verdict"] == "difference_detected"
    assert result.comparison["magnitude_differences"] == 1
    assert [e.source_id for e in result.evidence] == ["PMR"]


def test_tool_answer_without_verdict_is_not_a_comparison(tools):
    llm = ScriptedLLM(
        [[ToolCall("compare_poai_vs_pmr", {"year": 2030})]],
        DraftAnswer("No hay datos de 2030.", [], "answered"),
    )

    result, _ = ask(tools, llm)

    assert result.comparison is None


def test_loop_stops_at_max_rounds(tools):
    llm = ScriptedLLM(
        [[ToolCall("list_sources", {})]],
        lambda outcomes: DraftAnswer(f"{len(outcomes)} consultas", ["E1"], "answered"),
        repeat_last_round=True,
    )

    result, _ = ask(tools, llm, max_rounds=5)

    assert len(llm.received) == 5
    assert result.answer == "5 consultas"


def test_invalid_model_output_becomes_gap(tools):
    class BrokenLLM(ScriptedLLM):
        def compose_answer(self, question, results):
            raise LLMOutputError("bad json")

    result, gaps = ask(tools, BrokenLLM([[BUDGET_CALL]], DraftAnswer("", [], "answered")))

    assert result.status == "information_gap"
    assert gaps.saved[0].reason == "invalid_model_output"


def test_clarification_is_not_logged_as_gap(tools):
    llm = ScriptedLLM([[]], DraftAnswer("¿De qué año?", [], "needs_clarification"))

    result, gaps = ask(tools, llm)

    assert result.status == "needs_clarification"
    assert gaps.saved == []


@pytest.mark.parametrize(("text", "expected"), [
    ("escribe a ana@correo.co", "escribe a [CORREO]"),
    ("mi cédula es 52.123.456", "mi cédula es [NUMERO]"),
    ("llamar al +57 310 555 1234", "llamar al [NUMERO]"),
    ("ejecución 2024-2025 y 2025", "ejecución 2024-2025 y 2025"),
    ("contrato de $ 1.000.000", "contrato de $ 1.000.000"),
    ("propuesta 37646", "propuesta 37646"),
])
def test_mask_pii(text, expected):
    assert mask_pii(text) == expected


def test_gap_repository_round_trip(tmp_path):
    repository = DuckDBGapRepository(tmp_path / "gaps.duckdb")
    record = GapRecord("abc", datetime(2026, 11, 22, tzinfo=UTC), "pregunta [NUMERO]",
                       "seguridad", "hurtos", "model_reported")

    repository.save(record)

    assert repository.list_gaps() == [record]


# --- gap kind (right-of-petition suggestion only for unpublished data) ----------------------
def test_unpublished_data_gap_is_logged_as_missing_data(tools):
    llm = ScriptedLLM(
        [[ToolCall("report_information_gap",
                   {"topic": "seguridad", "missing_data": "hurtos por barrio"})]],
        DraftAnswer("No hay datos de hurtos.", [], "information_gap",
                    gap_kind="unpublished_data"),
    )

    result, gaps = ask(tools, llm)

    assert result.gap.kind == "unpublished_data"
    assert gaps.saved[0].reason == "model_reported"


def test_gap_without_kind_defaults_to_unpublished_data(tools):
    llm = ScriptedLLM([[]], DraftAnswer("No está publicado.", [], "information_gap",
                                        gap_topic="salud", gap_missing_data="camas"))

    result, _ = ask(tools, llm)

    assert result.gap.kind == "unpublished_data"


def test_out_of_scope_gap_is_logged_apart(tools):
    llm = ScriptedLLM([[]], DraftAnswer(
        "No doy nombres de funcionarios.", [], "information_gap",
        gap_topic="funcionarios", gap_missing_data="nombre del alcalde", gap_kind="out_of_scope",
    ))

    result, gaps = ask(tools, llm, question="¿Cómo se llama el alcalde local?")

    assert result.gap.kind == "out_of_scope"
    [gap] = gaps.saved
    assert gap.reason == "out_of_scope"  # not counted as missing published data


@pytest.mark.parametrize("broken", ["invalid_output", "numbers_without_evidence"])
def test_failed_or_rejected_answers_are_unverified_gaps(tools, broken):
    if broken == "invalid_output":
        class BrokenLLM(ScriptedLLM):
            def compose_answer(self, question, results):
                raise LLMOutputError("bad json")
        llm = BrokenLLM([[BUDGET_CALL]], DraftAnswer("", [], "answered"))
    else:
        llm = ScriptedLLM([[BUDGET_CALL]], DraftAnswer("Se ejecutó el 99 %.", [], "answered",
                                                       gap_kind="unpublished_data"))

    result, _ = ask(tools, llm)

    assert result.status == "information_gap"
    assert result.gap.kind == "unverified"


# --- partial answers (answered with related data; the data asked for is not published) -----
def partial_draft(**overrides):
    values = {"answer": "No está el número de huecos; la meta de malla vial tiene 60 % (E1).",
              "cited_evidence_ids": ["E1"], "status": "answered", "gap_topic": "vías",
              "gap_missing_data": "número de huecos tapados en 2025",
              "gap_kind": "unpublished_data", **overrides}
    return DraftAnswer(**values)


def test_partial_answer_keeps_answer_and_logs_partial_gap(tools):
    llm = ScriptedLLM([[BUDGET_CALL]], partial_draft())
    question = "Soy juan.perez@mail.com: ¿cuántos huecos se taparon en 2025?"

    result, gaps = ask(tools, llm, question=question)

    assert result.status == "answered"
    assert result.gap is None
    assert [e.id for e in result.evidence] == ["E1"]
    assert result.partial_gap.topic == "vías"
    assert result.partial_gap.missing_data == "número de huecos tapados en 2025"
    assert result.partial_gap.kind == "unpublished_data"
    [gap] = gaps.saved
    assert gap.reason == "partial_answer"
    assert gap.missing_data == "número de huecos tapados en 2025"
    assert "juan.perez" not in gap.question_masked


def test_complete_answer_has_no_partial_gap(tools):
    llm = ScriptedLLM([[BUDGET_CALL]], partial_draft(gap_topic=None, gap_missing_data=None,
                                                     gap_kind=None))

    result, gaps = ask(tools, llm)

    assert result.partial_gap is None
    assert gaps.saved == []


def test_out_of_scope_partial_gap_is_ignored(tools):
    llm = ScriptedLLM([[BUDGET_CALL]], partial_draft(gap_topic="funcionarios",
                                                     gap_missing_data="nombre del contratista",
                                                     gap_kind="out_of_scope"))

    result, gaps = ask(tools, llm)

    assert result.status == "answered"
    assert result.partial_gap is None
    assert gaps.saved == []


def test_rejected_answer_never_produces_partial_gap(tools):
    llm = ScriptedLLM([[BUDGET_CALL]], partial_draft(answer="Se taparon 300 huecos.",
                                                     cited_evidence_ids=[]))

    result, gaps = ask(tools, llm)

    assert result.status == "information_gap"
    assert result.partial_gap is None
    assert result.gap.kind == "unverified"
    assert [g.reason for g in gaps.saved] == ["numbers_without_evidence"]
