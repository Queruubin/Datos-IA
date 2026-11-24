"""Token usage and cost entities: plain data, no I/O."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class LLMUsage:
    """Tokens reported by the provider for ONE model call.

    `output_tokens` are the visible answer tokens; `thinking_tokens` are reasoning tokens. Both are
    billed at the output price, so `billed_output_tokens` adds them up.
    """

    model: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    total_tokens: int

    @property
    def billed_output_tokens(self) -> int:
        return self.output_tokens + self.thinking_tokens


@dataclass(frozen=True)
class UsageRecord:
    """One stored model call. Never contains the question text or any personal data."""

    id: str
    created_at: datetime
    question_id: str
    model: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    total_tokens: int
    cost_usd: float | None  # None when the model has no known price


@dataclass(frozen=True)
class QuestionUsage:
    """All model calls made to answer one question."""

    question_id: str
    calls: tuple[LLMUsage, ...]
    # None when at least one call used a model without a known price (never a partial guess).
    cost_usd: float | None
    unpriced_models: tuple[str, ...] = ()

    @property
    def input_tokens(self) -> int:
        return sum(call.input_tokens for call in self.calls)

    @property
    def output_tokens(self) -> int:
        return sum(call.output_tokens for call in self.calls)

    @property
    def thinking_tokens(self) -> int:
        return sum(call.thinking_tokens for call in self.calls)

    @property
    def total_tokens(self) -> int:
        return sum(call.total_tokens for call in self.calls)

    @property
    def models(self) -> list[str]:
        return list(dict.fromkeys(call.model for call in self.calls))


@dataclass(frozen=True)
class ExchangeRate:
    """USD → COP rate. `value` is None when no rate is available (`source="unavailable"`)."""

    value: float | None
    valid_from: date | None
    source: str  # "datos.gov.co", "fallback_setting" or "unavailable"
