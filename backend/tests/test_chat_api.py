from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.rate_limit import RateLimiter
from app.application import AgentTools, AskQuestion
from app.application.prompts import DISCLAIMER
from app.config import Settings
from app.domain import DraftAnswer, ToolCall
from tests.agent_fakes import FixedRate, InMemoryGaps, ScriptedLLM, build_fixture_db
from tests.conftest import InMemoryStore


def settings(tmp_path, **overrides) -> Settings:
    values = {"gemini_api_key": None, "duckdb_path": tmp_path / "none.duckdb",
              "gap_log_path": tmp_path / "gaps.duckdb",
              "usage_log_path": tmp_path / "usage.duckdb", **overrides}
    return Settings(_env_file=None, **values)


def make_app(tmp_path, **kwargs):
    """App wired with fakes only: no network (fixed USD→COP rate) and files under tmp_path."""
    values = {"store": InMemoryStore(), "settings": settings(tmp_path),
              "exchange_rate": FixedRate(), **kwargs}
    return create_app(**values)


def agent(tmp_path) -> AskQuestion:
    llm = ScriptedLLM(
        [[ToolCall("get_budget_execution", {"year": 2025})]],
        DraftAnswer("Se ejecutó el 60 % (E1).", ["E1"], "answered"),
    )
    tools = AgentTools(build_fixture_db(tmp_path / "agent.duckdb"))
    return AskQuestion(llm, tools, InMemoryGaps())


def test_chat_returns_503_without_gemini_key(tmp_path):
    client = TestClient(make_app(tmp_path))

    response = client.post("/api/chat", json={"question": "¿Cuánto se ejecutó?"})

    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]
    assert client.get("/health").status_code == 200  # the rest of the API keeps working
    assert client.get("/api/sources").status_code == 200


def test_chat_answers_with_evidence_and_disclaimer(tmp_path):
    client = TestClient(make_app(tmp_path, ask_question=agent(tmp_path)))

    response = client.post("/api/chat", json={"question": "¿Cuánto se ejecutó en 2025?"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["disclaimer"] == DISCLAIMER
    assert body["evidence"][0]["id"] == "E1"
    assert body["evidence"][0]["locator"] == "f1_pac_execution · year=2025"


def test_chat_validates_question_length(tmp_path):
    client = TestClient(make_app(tmp_path, ask_question=agent(tmp_path)))

    assert client.post("/api/chat", json={"question": ""}).status_code == 422
    assert client.post("/api/chat", json={"question": "   "}).status_code == 422
    assert client.post("/api/chat", json={"question": "a" * 501}).status_code == 422


def test_chat_rate_limit_returns_429(tmp_path):
    client = TestClient(make_app(
        tmp_path, ask_question=agent(tmp_path), rate_limiter=RateLimiter(limit=2)
    ))

    codes = [
        client.post("/api/chat", json={"question": "¿Cuánto se ejecutó?"}).status_code
        for _ in range(3)
    ]

    assert codes == [200, 200, 429]


def test_rate_limiter_window_expires():
    now = [0.0]
    limiter = RateLimiter(limit=1, window_seconds=60, clock=lambda: now[0])

    assert limiter.allow("a") is True
    assert limiter.allow("a") is False
    assert limiter.allow("b") is True
    now[0] = 61
    assert limiter.allow("a") is True


def test_cors_allows_the_frontend_origin(tmp_path):
    client = TestClient(make_app(tmp_path))

    response = client.options("/api/chat", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
    })

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_llm_failure_returns_502(tmp_path):
    class FailingAgent:
        def run(self, question):
            raise ConnectionError("network down")

    client = TestClient(make_app(tmp_path, ask_question=FailingAgent()))

    assert client.post("/api/chat", json={"question": "hola"}).status_code == 502


def test_chat_returns_charts_built_by_code(tmp_path):
    llm = ScriptedLLM(
        [[ToolCall("get_budget_execution", {"year": 2025})]],
        DraftAnswer("Se ejecutó el 60 % (E1).", ["E1"], "answered"),
    )
    tools = AgentTools(build_fixture_db(tmp_path / "agent.duckdb"))
    client = TestClient(make_app(tmp_path, ask_question=AskQuestion(llm, tools, InMemoryGaps())))

    body = client.post("/api/chat", json={"question": "¿Cuánto se ejecutó?"}).json()

    kpis, line = body["charts"]
    assert kpis["id"] == "C1"
    assert kpis["kind"] == "kpis"
    assert kpis["evidence_id"] == "E1"
    assert kpis["kpis"][2] == {"label": "Ejecutado sobre lo programado", "value": 60.0,
                               "unit": "percent"}
    assert line["kind"] == "line"
    assert line["unit"] == "unknown"
    assert line["series"][1] == {"name": "Ejecutado", "values": [150.0, 150.0]}
    assert body["gap"] is None


def test_chat_returns_gap_kind(tmp_path):
    llm = ScriptedLLM([[]], DraftAnswer("No está publicado.", [], "information_gap",
                                        gap_topic="vías", gap_missing_data="huecos por barrio",
                                        gap_kind="unpublished_data"))
    tools = AgentTools(build_fixture_db(tmp_path / "agent.duckdb"))
    client = TestClient(make_app(tmp_path, ask_question=AskQuestion(llm, tools, InMemoryGaps())))

    body = client.post("/api/chat", json={"question": "¿Cuántos huecos hay?"}).json()

    assert body["gap"] == {"topic": "vías", "missing_data": "huecos por barrio",
                           "kind": "unpublished_data"}
    assert body["charts"] == []


def test_chat_returns_partial_gap_for_answered_questions(tmp_path):
    llm = ScriptedLLM(
        [[ToolCall("get_budget_execution", {"year": 2025})]],
        DraftAnswer("No está el número de huecos; la malla vial tiene 60 % (E1).", ["E1"],
                    "answered", gap_topic="vías", gap_missing_data="huecos tapados en 2025",
                    gap_kind="unpublished_data"),
    )
    tools = AgentTools(build_fixture_db(tmp_path / "agent.duckdb"))
    client = TestClient(make_app(tmp_path, ask_question=AskQuestion(llm, tools, InMemoryGaps())))

    body = client.post("/api/chat", json={"question": "¿Cuántos huecos se taparon?"}).json()

    assert body["status"] == "answered"
    assert body["gap"] is None
    assert body["partial_gap"] == {"topic": "vías", "missing_data": "huecos tapados en 2025",
                                   "kind": "unpublished_data"}
    assert [e["id"] for e in body["evidence"]] == ["E1"]


def test_chat_complete_answer_has_no_partial_gap(tmp_path):
    client = TestClient(make_app(tmp_path, ask_question=agent(tmp_path)))

    body = client.post("/api/chat", json={"question": "¿Cuánto se ejecutó?"}).json()

    assert body["partial_gap"] is None
