"""Token usage capture, pricing, storage, TRM and the usage endpoints. No network, no Gemini."""

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
import requests
from fastapi.testclient import TestClient
from google.genai import errors, types

from app.adapters.duckdb.usage_repository import DuckDBUsageRepository
from app.adapters.exchange_rate import TrmClient, TrmParseError, parse_trm
from app.adapters.llm.gemini import GeminiLLM, extract_usage
from app.api.main import create_app
from app.application import AgentTools, AskQuestion
from app.application.pricing import cost_usd, price_for
from app.application.usage_report import FREE_TIER_NOTE, build_usage_report
from app.config import Settings
from app.domain import DraftAnswer, ExchangeRate, LLMUsage, ToolCall, UsageRecord
from app.ports import LLMOutputError
from tests.agent_fakes import FixedRate, InMemoryGaps, InMemoryUsage, ScriptedLLM, build_fixture_db
from tests.conftest import InMemoryStore

BUDGET_CALL = ToolCall("get_budget_execution", {"year": 2025})
NOW = datetime(2026, 11, 23, 15, 0, tzinfo=UTC)


def metadata(prompt=100, candidates=20, thoughts=None, total=None):
    return types.GenerateContentResponseUsageMetadata(
        prompt_token_count=prompt, candidates_token_count=candidates,
        thoughts_token_count=thoughts, total_token_count=total,
    )


# --- usage extraction -------------------------------------------------------------------------

def test_sdk_usage_metadata_has_the_fields_we_read():
    fields = types.GenerateContentResponseUsageMetadata.model_fields
    for name in ("prompt_token_count", "candidates_token_count", "thoughts_token_count",
                 "total_token_count"):
        assert name in fields


def test_extract_usage_reads_all_counts():
    response = SimpleNamespace(usage_metadata=metadata(1000, 200, 50, 1250))

    assert extract_usage(response, "m") == LLMUsage("m", 1000, 200, 50, 1250)


def test_extract_usage_treats_missing_thoughts_and_total_as_zero_and_sum():
    response = SimpleNamespace(usage_metadata=metadata(1000, 200, None, None))

    usage = extract_usage(response, "m")

    assert usage.thinking_tokens == 0
    assert usage.total_tokens == 1200
    assert usage.billed_output_tokens == 200


def test_extract_usage_without_metadata_is_all_zero():
    assert extract_usage(SimpleNamespace(), "m") == LLMUsage("m", 0, 0, 0, 0)


class FakeModels:
    """Primary model is overloaded (503); the fallback answers with usage metadata."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[str] = []

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        if model == "primary":
            raise errors.ServerError(503, {"error": {"code": 503, "message": "x", "status": "U"}})
        return SimpleNamespace(
            text=self.text, function_calls=[], candidates=[],
            usage_metadata=metadata(300, 40, 10, 350),
        )


def test_fallback_model_is_the_one_recorded():
    answer = '{"answer": "ok", "cited_evidence_ids": [], "status": "needs_clarification"}'
    client = SimpleNamespace(models=FakeModels(answer))
    llm = GeminiLLM("k", "primary", "sys", fallback_models=["lite"], client=client)

    session = llm.start_planning("q", [])
    assert session.next_tool_calls(None) == []
    draft = llm.compose_answer("q", [])

    assert [u.model for u in session.usage] == ["lite"]
    assert draft.usage == LLMUsage("lite", 300, 40, 10, 350)
    assert client.models.calls == ["primary", "lite", "primary", "lite"]


def test_invalid_output_still_reports_usage():
    client = SimpleNamespace(models=FakeModels("not json"))
    llm = GeminiLLM("k", "primary", "sys", fallback_models=["lite"], client=client)

    with pytest.raises(LLMOutputError) as raised:
        llm.compose_answer("q", [])

    assert raised.value.usage.model == "lite"


# --- pricing ----------------------------------------------------------------------------------

def test_cost_uses_input_and_output_plus_thinking_prices():
    usage = LLMUsage("gemini-3.5-flash-lite", 1_000_000, 600_000, 400_000, 2_000_000)

    assert cost_usd(usage, NOW) == pytest.approx(0.30 + 2.50)


def test_cost_accepts_resource_style_model_names():
    usage = LLMUsage("models/gemini-3.1-flash-lite", 2_000_000, 1_000_000, 0, 3_000_000)

    assert cost_usd(usage, NOW) == pytest.approx(2 * 0.25 + 1.50)


@pytest.mark.parametrize(("moment", "expected"), [
    (datetime(2026, 12, 31, 23, 59, tzinfo=UTC), 0.75 + 3.75),
    (datetime(2027, 1, 1, 0, 0, tzinfo=UTC), 1.50 + 7.50),
])
def test_gemini_38_flash_price_depends_on_the_call_date(moment, expected):
    usage = LLMUsage("gemini-3.8-flash", 1_000_000, 1_000_000, 0, 2_000_000)

    assert cost_usd(usage, moment) == pytest.approx(expected)


def test_unknown_model_has_no_price():
    usage = LLMUsage("gemini-9-ultra", 10, 10, 0, 20)

    assert price_for("gemini-9-ultra", NOW) is None
    assert cost_usd(usage, NOW) is None


# --- repository -------------------------------------------------------------------------------

def record(question_id="q1", model="gemini-3.5-flash-lite", cost=0.001, at=NOW, total=100,
           record_id=None):
    return UsageRecord(
        id=record_id or f"{question_id}-{model}-{at.isoformat()}", created_at=at,
        question_id=question_id, model=model, input_tokens=60, output_tokens=30,
        thinking_tokens=10, total_tokens=total, cost_usd=cost,
    )


def test_usage_repository_round_trip(tmp_path):
    repository = DuckDBUsageRepository(tmp_path / "usage.duckdb")
    rows = [record(record_id="a"), record(model="unknown", cost=None, record_id="b")]

    assert repository.list_records() == []
    repository.save_many(rows)
    repository.save_many([])

    assert repository.list_records() == rows


# --- AskQuestion aggregation ------------------------------------------------------------------

@pytest.fixture
def tools(tmp_path):
    return AgentTools(build_fixture_db(tmp_path / "agent.duckdb"))


def test_question_usage_adds_every_call_and_is_stored(tools):
    call = LLMUsage("gemini-3.5-flash-lite", 1000, 100, 50, 1150)
    llm = ScriptedLLM([[BUDGET_CALL]], DraftAnswer("Ok (E1).", ["E1"], "answered"), usage=call)
    usage_log = InMemoryUsage()

    result = AskQuestion(llm, tools, InMemoryGaps(), usage=usage_log, clock=lambda: NOW).run("x")

    # Two planning rounds (tool calls, then "no more calls") plus the compose call.
    assert len(result.usage.calls) == 3
    assert result.usage.input_tokens == 3000
    assert result.usage.thinking_tokens == 150
    assert result.usage.total_tokens == 3450
    assert result.usage.models == ["gemini-3.5-flash-lite"]
    assert result.usage.cost_usd == pytest.approx(3 * (1000 * 0.30 + 150 * 2.50) / 1e6)
    assert len(usage_log.saved) == 3
    assert {r.question_id for r in usage_log.saved} == {result.usage.question_id}


def test_unknown_model_makes_question_cost_null(tools):
    llm = ScriptedLLM([[]], DraftAnswer("¿De qué año?", [], "needs_clarification"),
                      usage=LLMUsage("mystery", 10, 1, 0, 11))

    result = AskQuestion(llm, tools, InMemoryGaps(), clock=lambda: NOW).run("x")

    assert result.usage.cost_usd is None
    assert result.usage.unpriced_models == ("mystery",)


def test_failing_usage_storage_never_breaks_the_answer(tools):
    llm = ScriptedLLM([[]], DraftAnswer("¿De qué año?", [], "needs_clarification"),
                      usage=LLMUsage("gemini-3.5-flash-lite", 10, 1, 0, 11))

    result = AskQuestion(llm, tools, InMemoryGaps(), usage=InMemoryUsage(failing=True)).run("x")

    assert result.status == "needs_clarification"
    assert len(result.usage.calls) == 2


def test_usage_of_invalid_output_and_of_failed_questions_is_stored(tools):
    call = LLMUsage("gemini-3.5-flash-lite", 10, 1, 0, 11)

    class BrokenLLM(ScriptedLLM):
        def compose_answer(self, question, results):
            raise LLMOutputError("bad json", usage=call)

    usage_log = InMemoryUsage()
    result = AskQuestion(
        BrokenLLM([[]], DraftAnswer("", [], "answered"), usage=call), tools, InMemoryGaps(),
        usage=usage_log,
    ).run("x")
    assert result.status == "information_gap"
    assert len(usage_log.saved) == 2  # planning + the unusable compose call

    class NetworkDownLLM(ScriptedLLM):
        def compose_answer(self, question, results):
            raise ConnectionError("down")

    usage_log = InMemoryUsage()
    with pytest.raises(ConnectionError):
        AskQuestion(NetworkDownLLM([[]], DraftAnswer("", [], "answered"), usage=call), tools,
                    InMemoryGaps(), usage=usage_log).run("x")
    assert len(usage_log.saved) == 1  # the planning call was consumed before the failure


# --- usage report -----------------------------------------------------------------------------

def test_report_totals_by_model_and_by_day():
    yesterday = NOW - timedelta(days=1)
    rows = [
        record("q1", cost=0.002, total=100, record_id="1"),
        record("q1", cost=0.001, total=50, record_id="2"),
        record("q2", model="gemini-3.8-flash", cost=0.01, total=300, at=yesterday, record_id="3"),
        record("q3", model="mystery", cost=None, total=10, at=yesterday, record_id="4"),
        record("q0", cost=1.0, total=999, at=NOW - timedelta(days=40), record_id="5"),
    ]
    rate = ExchangeRate(4000.0, date(2026, 11, 21), "datos.gov.co")

    report = build_usage_report(rows, NOW, rate)

    assert report.note == FREE_TIER_NOTE
    assert report.all_time.questions == 4
    assert report.all_time.calls == 5
    assert report.all_time.unpriced_calls == 1
    assert report.all_time.cost_usd == pytest.approx(1.013)
    assert report.all_time.cost_cop == pytest.approx(4052.0)
    assert report.today.questions == 1
    assert report.today.total_tokens == 150
    assert report.avg_tokens_per_question == pytest.approx(1459 / 4)
    assert report.avg_cost_usd_per_question == pytest.approx(1.013 / 4)
    assert [m.model for m in report.by_model][0] == "gemini-3.5-flash-lite"
    mystery = next(m for m in report.by_model if m.model == "mystery")
    assert mystery.cost_usd is None and mystery.unpriced_calls == 1
    # Older than 30 days is left out of the daily breakdown.
    assert [d.day for d in report.by_day] == [date(2026, 11, 22), date(2026, 11, 23)]


def test_report_days_use_bogota_time():
    # 02:00 UTC on Nov 24 is still Nov 23 in Bogotá (UTC-5).
    late = datetime(2026, 11, 24, 2, 0, tzinfo=UTC)
    report = build_usage_report([record(at=late)], late, ExchangeRate(None, None, "unavailable"))

    assert report.by_day[0].day == date(2026, 11, 23)
    assert report.all_time.cost_cop is None


def test_empty_report():
    report = build_usage_report([], NOW, ExchangeRate(None, None, "unavailable"))

    assert report.all_time.questions == 0
    assert report.all_time.cost_usd == 0
    assert report.avg_cost_usd_per_question is None
    assert report.by_day == []


# --- TRM client -------------------------------------------------------------------------------

TRM_ROW = [{"valor": "3461.92", "unidad": "COP", "vigenciadesde": "2026-11-21T00:00:00.000",
            "vigenciahasta": "2026-11-23T00:00:00.000"}]


class FakeHttp:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.requests: list[dict] = []

    def get(self, url, params, timeout):
        self.requests.append({"url": url, "params": params, "timeout": timeout})
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: payload)


def trm(payloads, fallback=None):
    clock = [0.0]
    http = FakeHttp(payloads)
    client = TrmClient(session=http, fallback=fallback, monotonic=lambda: clock[0],
                       now=lambda: NOW)
    return client, http, clock


def test_parse_trm():
    assert parse_trm(TRM_ROW) == ExchangeRate(3461.92, date(2026, 11, 21), "datos.gov.co")
    for bad in ([], [{"valor": "x", "vigenciadesde": "2026-11-21"}], [{"valor": "1"}],
                [{"valor": "0", "vigenciadesde": "2026-11-21"}], {"error": True}):
        with pytest.raises(TrmParseError):
            parse_trm(bad)


def test_trm_is_cached_for_twelve_hours_and_asks_for_todays_rate():
    client, http, clock = trm([TRM_ROW, TRM_ROW])

    assert client.usd_to_cop().value == 3461.92
    clock[0] = 11 * 3600
    client.usd_to_cop()
    assert len(http.requests) == 1
    clock[0] = 13 * 3600
    client.usd_to_cop()
    assert len(http.requests) == 2
    params = http.requests[0]["params"]
    assert params["$where"] == "vigenciadesde <= '2026-11-23T00:00:00'"
    assert params["$order"] == "vigenciadesde DESC"
    assert http.requests[0]["timeout"] == 5


def test_trm_falls_back_to_setting_then_unavailable():
    client, _, _ = trm([requests.ConnectionError("down")], fallback=4100.0)
    assert client.usd_to_cop() == ExchangeRate(4100.0, None, "fallback_setting")

    client, http, _ = trm([[]])
    assert client.usd_to_cop() == ExchangeRate(None, None, "unavailable")
    client.usd_to_cop()  # recent failure: does not ask again right away
    assert len(http.requests) == 1


def test_trm_keeps_last_good_value_when_refresh_fails():
    client, _, clock = trm([TRM_ROW, requests.Timeout("slow")], fallback=1.0)
    client.usd_to_cop()
    clock[0] = 13 * 3600

    assert client.usd_to_cop().value == 3461.92


# --- API --------------------------------------------------------------------------------------

def settings(tmp_path) -> Settings:
    return Settings(_env_file=None, gemini_api_key=None, duckdb_path=tmp_path / "none.duckdb",
                    gap_log_path=tmp_path / "gaps.duckdb", usage_log_path=tmp_path / "u.duckdb")


def test_chat_response_includes_usage(tmp_path):
    call = LLMUsage("gemini-3.5-flash-lite", 1000, 100, 50, 1150)
    llm = ScriptedLLM([[BUDGET_CALL]], DraftAnswer("Ok (E1).", ["E1"], "answered"), usage=call)
    tools = AgentTools(build_fixture_db(tmp_path / "agent.duckdb"))
    usage_log = InMemoryUsage()
    app = create_app(
        store=InMemoryStore(), settings=settings(tmp_path), exchange_rate=FixedRate(4000.0),
        ask_question=AskQuestion(llm, tools, InMemoryGaps(), usage=usage_log),
        usage_repository=usage_log,
    )
    client = TestClient(app)

    usage = client.post("/api/chat", json={"question": "¿Cuánto?"}).json()["usage"]

    expected_usd = 3 * (1000 * 0.30 + 150 * 2.50) / 1e6
    assert usage["calls"] == 3
    assert usage["input_tokens"] == 3000
    assert usage["output_tokens"] == 300
    assert usage["thinking_tokens"] == 150
    assert usage["total_tokens"] == 3450
    assert usage["models"] == ["gemini-3.5-flash-lite"]
    assert usage["cost_usd"] == pytest.approx(expected_usd)
    assert usage["cost_cop"] == pytest.approx(expected_usd * 4000)

    report = client.get("/api/usage").json()
    assert report["all_time"]["questions"] == 1
    assert report["all_time"]["calls"] == 3


def test_usage_endpoint_reports_rate_pricing_and_note(tmp_path):
    usage_log = InMemoryUsage()
    usage_log.save_many([record(at=datetime.now(UTC))])
    client = TestClient(create_app(
        store=InMemoryStore(), settings=settings(tmp_path), usage_repository=usage_log,
        exchange_rate=FixedRate(None, "unavailable"),
    ))

    body = client.get("/api/usage").json()

    assert "costo real es $0" in body["note"]
    assert body["exchange_rate"] == {"value": None, "valid_from": None, "source": "unavailable"}
    assert body["pricing"]["source_url"] == "https://aistudio.google.com/docs/pricing"
    assert body["pricing"]["read_on"] == "2026-11-23"
    models = {(p["model"], p["valid_from"]) for p in body["pricing"]["prices"]}
    assert ("gemini-3.8-flash", "2027-01-01") in models
    assert body["today"]["calls"] == 1
    assert body["by_model"][0]["cost_cop"] is None
    assert body["by_day"][0]["day"]


def test_usage_endpoint_works_without_gemini_key_and_without_data(tmp_path):
    client = TestClient(create_app(
        store=InMemoryStore(), settings=settings(tmp_path), exchange_rate=FixedRate(),
    ))

    body = client.get("/api/usage").json()

    assert body["all_time"]["questions"] == 0
    assert body["exchange_rate"]["value"] == 4000.0
