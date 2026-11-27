"""FastAPI application. Run with: uvicorn app.api.main:app --reload"""

import logging
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.duckdb import DuckDBStore
from app.adapters.duckdb.gap_repository import DuckDBGapRepository
from app.adapters.duckdb.usage_repository import DuckDBUsageRepository
from app.adapters.exchange_rate import TrmClient
from app.api.rate_limit import RateLimiter
from app.application import AgentTools, AskQuestion
from app.application.prompts import DISCLAIMER, SYSTEM_PROMPT
from app.application.usage_report import UsageReport, build_usage_report
from app.config import Settings, get_settings
from app.domain import ChartSpec, ChatAnswer, ExchangeRate, QuestionUsage, SourceMetadata
from app.ports import DataStorePort, ExchangeRatePort, UsageRepositoryPort

logger = logging.getLogger(__name__)

NO_KEY_MESSAGE = (
    "El chat no está disponible: falta configurar GEMINI_API_KEY en el servidor."
)
RATE_LIMIT_MESSAGE = "Demasiadas preguntas en poco tiempo. Intenta de nuevo en un minuto."
LLM_FAILURE_MESSAGE = "El servicio de lenguaje no respondió. Intenta de nuevo más tarde."


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=500)


class EvidenceOut(BaseModel):
    id: str
    source_id: str
    title: str
    data_cutoff: str | None
    portal_url: str | None  # None when the source is not on the open-data portal
    locator: str
    summary: str
    origin_note: str | None = None


class GapOut(BaseModel):
    topic: str
    missing_data: str
    # unpublished_data: public data not published (the UI suggests a right-of-petition draft);
    # out_of_scope: personal data, opinions or unrelated topics; unverified: the model failed.
    kind: Literal["unpublished_data", "out_of_scope", "unverified"] = "unpublished_data"


class ChartSeriesOut(BaseModel):
    name: str
    values: list[float | None]


class ChartKpiOut(BaseModel):
    label: str
    value: float | None
    unit: Literal["COP", "percent", "count", "days", "unknown"]


class ChartOut(BaseModel):
    """Chart built by code from tool results (never by the LLM); backed by cited evidence."""

    id: str
    kind: Literal["bars", "grouped_bars", "line", "kpis"]
    title: str
    unit: Literal["COP", "percent", "count", "days", "unknown"]
    evidence_id: str
    evidence_ids: list[str]
    categories: list[str] = []
    series: list[ChartSeriesOut] = []
    kpis: list[ChartKpiOut] = []
    note: str | None = None
    data_cutoff: str | None = None
    verdict: Literal["coherent", "difference_detected", "not_comparable"] | None = None


class UsageOut(BaseModel):
    """Tokens and paid-tier equivalent cost of one question (all its Gemini calls)."""

    input_tokens: int
    output_tokens: int  # visible answer tokens
    thinking_tokens: int  # reasoning tokens (billed as output)
    total_tokens: int
    calls: int
    models: list[str]
    cost_usd: float | None  # None if a model has no known price
    cost_cop: float | None  # None if cost_usd is None or no USD→COP rate is available
    unpriced_models: list[str] = []


class ChatResponse(BaseModel):
    answer: str
    status: Literal["answered", "information_gap", "needs_clarification"]
    evidence: list[EvidenceOut]
    comparison: dict[str, Any] | None = None
    gap: GapOut | None = None  # only for status information_gap
    disclaimer: str = DISCLAIMER
    usage: UsageOut | None = None
    charts: list[ChartOut] = []
    # Only for status answered: the answer gives related data but the specific data asked for
    # is not published (kind is always unpublished_data; the UI suggests a petition draft).
    partial_gap: GapOut | None = None


def build_ask_question(
    settings: Settings, store: DuckDBStore, usage: UsageRepositoryPort | None = None
) -> AskQuestion | None:
    """Wire the real agent, or None when no Gemini key is configured."""
    if settings.gemini_api_key is None or not settings.gemini_api_key.get_secret_value():
        return None
    from app.adapters.llm.gemini import GeminiLLM  # imported only when the agent is enabled

    llm = GeminiLLM(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.gemini_model,
        fallback_models=settings.gemini_fallback_models,
        timeout_seconds=settings.gemini_timeout_seconds,
        system_instruction=SYSTEM_PROMPT,
        temperature=settings.gemini_temperature,
    )
    return AskQuestion(
        llm, AgentTools(store), DuckDBGapRepository(settings.gap_log_path), usage=usage
    )


def create_app(
    store: DataStorePort | None = None,
    ask_question: AskQuestion | None = None,
    settings: Settings | None = None,
    rate_limiter: RateLimiter | None = None,
    usage_repository: UsageRepositoryPort | None = None,
    exchange_rate: ExchangeRatePort | None = None,
) -> FastAPI:
    """Build the app. Tests pass fakes; by default everything is wired from settings.

    `ask_question=None` with no Gemini key leaves the chat disabled (503).
    """
    settings = settings or get_settings()
    duckdb_store = DuckDBStore(settings.duckdb_path)
    data_store = store or duckdb_store
    usage_log = usage_repository or DuckDBUsageRepository(settings.usage_log_path)
    rates = exchange_rate or TrmClient(
        url=settings.trm_api_url,
        timeout_seconds=settings.trm_timeout_seconds,
        fallback=settings.usd_to_cop_fallback,
    )
    agent = ask_question if ask_question is not None else build_ask_question(
        settings, duckdb_store, usage_log
    )
    limiter = rate_limiter or RateLimiter(settings.chat_rate_limit_per_minute)

    app = FastAPI(
        title="San Cristóbal — Agente de verificación de información pública",
        version="0.2.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/sources", response_model=list[SourceMetadata])
    def list_sources() -> list[SourceMetadata]:
        """Ingested sources with their data cutoff date and traceability metadata."""
        return data_store.read_source_metadata()

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, request: Request) -> ChatResponse:
        """Answer a citizen question with evidence. The client address is used only in memory
        for rate limiting; it is never logged or stored."""
        client_key = request.client.host if request.client else "unknown"
        if not limiter.allow(client_key):
            raise HTTPException(status_code=429, detail=RATE_LIMIT_MESSAGE)
        if agent is None:
            raise HTTPException(status_code=503, detail=NO_KEY_MESSAGE)
        try:
            result = agent.run(body.question)
        except Exception as error:  # network/quota errors of the LLM provider
            # Provider errors carry an HTTP code and status (e.g. 429 RESOURCE_EXHAUSTED);
            # they never include the API key, and the question is not logged.
            logger.error(
                "Chat failed: %s code=%s status=%s message=%s",
                type(error).__name__,
                getattr(error, "code", None),
                getattr(error, "status", None),
                str(getattr(error, "message", "") or "")[:300],
            )
            raise HTTPException(status_code=502, detail=LLM_FAILURE_MESSAGE) from error
        rate = rates.usd_to_cop() if result.usage is not None else None
        return _to_response(result, rate)

    @app.get("/api/usage", response_model=UsageReport)
    def usage() -> UsageReport:
        """Token usage and its paid-tier equivalent cost (USD and COP). On Gemini's free tier
        the real charge is 0."""
        return build_usage_report(
            usage_log.list_records(), datetime.now(UTC), rates.usd_to_cop()
        )

    # Mounted last so every /api route above wins. The app uses hash routing (#/fuentes),
    # so serving index.html for "/" is enough; no SPA fallback is needed.
    if settings.frontend_dist_dir and settings.frontend_dist_dir.is_dir():
        app.mount(
            "/", StaticFiles(directory=settings.frontend_dist_dir, html=True), name="frontend"
        )

    return app


def _to_response(result: ChatAnswer, rate: ExchangeRate | None = None) -> ChatResponse:
    return ChatResponse(
        answer=result.answer,
        status=result.status,
        evidence=[EvidenceOut(**vars(item)) for item in result.evidence],
        comparison=result.comparison,
        gap=GapOut(**vars(result.gap)) if result.gap else None,
        disclaimer=DISCLAIMER,
        usage=_usage_out(result.usage, rate) if result.usage else None,
        charts=[_chart_out(chart) for chart in result.charts],
        partial_gap=GapOut(**vars(result.partial_gap)) if result.partial_gap else None,
    )


def _chart_out(chart: ChartSpec) -> ChartOut:
    return ChartOut(
        id=chart.id, kind=chart.kind, title=chart.title, unit=chart.unit,
        evidence_id=chart.evidence_id, evidence_ids=list(chart.evidence_ids),
        categories=list(chart.categories),
        series=[ChartSeriesOut(name=s.name, values=list(s.values)) for s in chart.series],
        kpis=[ChartKpiOut(label=k.label, value=k.value, unit=k.unit) for k in chart.kpis],
        note=chart.note, data_cutoff=chart.data_cutoff, verdict=chart.verdict,
    )


def _usage_out(usage: QuestionUsage, rate: ExchangeRate | None) -> UsageOut:
    cost_cop = (
        usage.cost_usd * rate.value
        if usage.cost_usd is not None and rate is not None and rate.value is not None
        else None
    )
    return UsageOut(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        thinking_tokens=usage.thinking_tokens,
        total_tokens=usage.total_tokens,
        calls=len(usage.calls),
        models=usage.models,
        cost_usd=usage.cost_usd,
        cost_cop=cost_cop,
        unpriced_models=list(usage.unpriced_models),
    )


app = create_app()
