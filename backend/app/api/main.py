"""FastAPI application. Run with: uvicorn app.api.main:app --reload"""

import logging
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app.adapters.duckdb import DuckDBStore
from app.adapters.duckdb.gap_repository import DuckDBGapRepository
from app.api.rate_limit import RateLimiter
from app.application import AgentTools, AskQuestion
from app.application.prompts import DISCLAIMER, SYSTEM_PROMPT
from app.config import Settings, get_settings
from app.domain import ChatAnswer, SourceMetadata
from app.ports import DataStorePort

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
    portal_url: str
    locator: str
    summary: str


class GapOut(BaseModel):
    topic: str
    missing_data: str


class ChatResponse(BaseModel):
    answer: str
    status: Literal["answered", "information_gap", "needs_clarification"]
    evidence: list[EvidenceOut]
    comparison: dict[str, Any] | None = None
    gap: GapOut | None = None
    disclaimer: str = DISCLAIMER


def build_ask_question(settings: Settings, store: DuckDBStore) -> AskQuestion | None:
    """Wire the real agent, or None when no Gemini key is configured."""
    if settings.gemini_api_key is None or not settings.gemini_api_key.get_secret_value():
        return None
    from app.adapters.llm.gemini import GeminiLLM  # imported only when the agent is enabled

    llm = GeminiLLM(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.gemini_model,
        system_instruction=SYSTEM_PROMPT,
        temperature=settings.gemini_temperature,
    )
    return AskQuestion(llm, AgentTools(store), DuckDBGapRepository(settings.gap_log_path))


def create_app(
    store: DataStorePort | None = None,
    ask_question: AskQuestion | None = None,
    settings: Settings | None = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    """Build the app. Tests pass fakes; by default everything is wired from settings.

    `ask_question=None` with no Gemini key leaves the chat disabled (503).
    """
    settings = settings or get_settings()
    duckdb_store = DuckDBStore(settings.duckdb_path)
    data_store = store or duckdb_store
    agent = ask_question if ask_question is not None else build_ask_question(
        settings, duckdb_store
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
            logger.error("Chat failed: %s", type(error).__name__)
            raise HTTPException(status_code=502, detail=LLM_FAILURE_MESSAGE) from error
        return _to_response(result)

    return app


def _to_response(result: ChatAnswer) -> ChatResponse:
    return ChatResponse(
        answer=result.answer,
        status=result.status,
        evidence=[EvidenceOut(**vars(item)) for item in result.evidence],
        comparison=result.comparison,
        gap=GapOut(**vars(result.gap)) if result.gap else None,
        disclaimer=DISCLAIMER,
    )


app = create_app()
