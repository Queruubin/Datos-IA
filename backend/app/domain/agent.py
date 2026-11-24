"""Entities of the question-answering agent: plain data, no I/O."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from app.domain.usage import LLMUsage, QuestionUsage

AnswerStatus = Literal["answered", "information_gap", "needs_clarification"]
Verdict = Literal["coherent", "difference_detected", "not_comparable"]
# Why an answer is an information gap. The model picks the first two; "unverified" is set by
# code when the model failed or its answer was rejected (no petition is suggested then).
GapKind = Literal["unpublished_data", "out_of_scope", "unverified"]
ChartKind = Literal["bars", "grouped_bars", "line", "kpis"]
ChartUnit = Literal["COP", "percent", "count", "days", "unknown"]


@dataclass(frozen=True)
class Evidence:
    """A traceable pointer to the data behind a figure. `id` (E1, E2...) is assigned by code."""

    id: str
    source_id: str
    title: str
    data_cutoff: str | None
    portal_url: str | None  # None when the source is not published on the open-data portal
    locator: str  # human-readable pointer: table + filter used
    summary: str
    origin_note: str | None = None  # where the data comes from when there is no portal URL


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
                    "summary": item.summary, "origin_note": item.origin_note,
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
    usage: LLMUsage | None = None  # tokens of the call that produced this draft
    gap_kind: GapKind | None = None


@dataclass(frozen=True)
class GapInfo:
    topic: str
    missing_data: str
    kind: GapKind = "unpublished_data"


@dataclass(frozen=True)
class ChartSeries:
    name: str
    values: tuple[float | None, ...]


@dataclass(frozen=True)
class ChartKpi:
    label: str
    value: float | None
    unit: ChartUnit


@dataclass(frozen=True)
class ChartSpec:
    """A chart built by code from one tool outcome; never by the LLM.

    Every number comes from the tool data. `evidence_ids` are all the evidence records that
    back the chart (all must be cited by the answer); `evidence_id` is the main one (badge).
    """

    id: str
    kind: ChartKind
    title: str
    unit: ChartUnit
    evidence_id: str
    evidence_ids: tuple[str, ...]
    categories: tuple[str, ...] = ()
    series: tuple[ChartSeries, ...] = ()
    kpis: tuple[ChartKpi, ...] = ()
    note: str | None = None
    data_cutoff: str | None = None
    verdict: Verdict | None = None


@dataclass(frozen=True)
class ChatAnswer:
    """Validated answer returned to the citizen."""

    answer: str
    status: AnswerStatus
    evidence: list[Evidence]
    comparison: dict[str, Any] | None = None
    gap: GapInfo | None = None  # only for status information_gap
    usage: QuestionUsage | None = None
    charts: tuple[ChartSpec, ...] = ()
    # Only for status answered: the answer gives related data but not the one asked for, which
    # is public and unpublished (kind is always "unpublished_data").
    partial_gap: GapInfo | None = None


@dataclass(frozen=True)
class GapRecord:
    """An information gap, stored with the question already masked (no PII, no IP)."""

    id: str
    created_at: datetime
    question_masked: str
    topic: str
    missing_data: str
    reason: str
