"""Entities of the question-answering agent: plain data, no I/O."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

AnswerStatus = Literal["answered", "information_gap", "needs_clarification"]
Verdict = Literal["coherent", "difference_detected", "not_comparable"]


@dataclass(frozen=True)
class Evidence:
    """A traceable pointer to the data behind a figure. `id` (E1, E2...) is assigned by code."""

    id: str
    source_id: str
    title: str
    data_cutoff: str | None
    portal_url: str
    locator: str  # human-readable pointer: table + filter used
    summary: str


@dataclass(frozen=True)
class ToolSpec:
    """Provider-agnostic description of a tool the LLM may call."""

    name: str
    description: str
    parameters_json_schema: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]
    call_id: str | None = None


@dataclass
class ToolOutcome:
    """Result of executing one tool call: the data plus the evidence that backs it."""

    call: ToolCall
    data: Any
    evidence: list[Evidence] = field(default_factory=list)
    error: str | None = None

    def to_model_payload(self) -> dict[str, Any]:
        """What the LLM sees: the data and the evidence ids it may cite."""
        if self.error:
            return {"error": self.error}
        return {
            "data": self.data,
            "evidence": [
                {
                    "id": item.id, "source_id": item.source_id, "title": item.title,
                    "data_cutoff": item.data_cutoff, "locator": item.locator,
                    "summary": item.summary,
                }
                for item in self.evidence
            ],
        }


@dataclass(frozen=True)
class DraftAnswer:
    """The LLM's final structured answer, before deterministic validation."""

    answer: str
    cited_evidence_ids: list[str]
    status: AnswerStatus
    gap_topic: str | None = None
    gap_missing_data: str | None = None


@dataclass(frozen=True)
class GapInfo:
    topic: str
    missing_data: str


@dataclass(frozen=True)
class ChatAnswer:
    """Validated answer returned to the citizen."""

    answer: str
    status: AnswerStatus
    evidence: list[Evidence]
    comparison: dict[str, Any] | None = None
    gap: GapInfo | None = None


@dataclass(frozen=True)
class GapRecord:
    """An information gap, stored with the question already masked (no PII, no IP)."""

    id: str
    created_at: datetime
    question_masked: str
    topic: str
    missing_data: str
    reason: str
