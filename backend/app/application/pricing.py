"""Gemini price table (paid "Standard" tier) and cost calculation.

Source: https://aistudio.google.com/docs/pricing, read on 2026-11-23. Prices are USD per 1M tokens.
The output price includes thinking (reasoning) tokens. On the free tier these three models are
"Free of charge" (and the content may be used to improve Google's products), so the costs computed
here are what the same usage WOULD cost on the paid tier.

To update: add a new `ModelPrice` row with `valid_from` set to the date the change takes effect
and close the previous row with `valid_until` (exclusive). A model missing from the table has no
cost (None): the code never guesses a price.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.domain import LLMUsage

PRICING_SOURCE_URL = "https://aistudio.google.com/docs/pricing"
PRICING_READ_ON = date(2026, 11, 23)
PRICING_TIER = "Standard (plan pagado)"
TOKENS_PER_PRICE_UNIT = 1_000_000


@dataclass(frozen=True)
class ModelPrice:
    model: str
    input_usd_per_million: float
    output_usd_per_million: float  # includes thinking tokens
    valid_from: date | None = None  # inclusive; None = since always
    valid_until: date | None = None  # exclusive; None = until further notice
    note: str | None = None

    def applies_on(self, day: date) -> bool:
        starts = self.valid_from is None or day >= self.valid_from
        ends = self.valid_until is None or day < self.valid_until
        return starts and ends


PRICES: tuple[ModelPrice, ...] = (
    ModelPrice("gemini-3.5-flash-lite", 0.30, 2.50),
    ModelPrice("gemini-3.1-flash-lite", 0.25, 1.50, note="Precio de entrada para texto."),
    ModelPrice("gemini-3.8-flash", 0.75, 3.75, valid_until=date(2027, 1, 1)),
    ModelPrice("gemini-3.8-flash", 1.50, 7.50, valid_from=date(2027, 1, 1)),
)


def normalize_model(model: str) -> str:
    """'models/gemini-x' → 'gemini-x' (the API sometimes reports the resource name)."""
    return model.strip().removeprefix("models/")


def price_for(
    model: str, at: datetime, prices: tuple[ModelPrice, ...] = PRICES
) -> ModelPrice | None:
    """The price in effect for `model` on the UTC date of `at`, or None if unknown."""
    day = at.astimezone(UTC).date() if at.tzinfo else at.date()
    name = normalize_model(model)
    for price in prices:
        if price.model == name and price.applies_on(day):
            return price
    return None


def cost_usd(
    usage: LLMUsage, at: datetime, prices: tuple[ModelPrice, ...] = PRICES
) -> float | None:
    """USD cost of one call at paid-tier prices. Input = prompt tokens; output = answer +
    thinking tokens. None when the model has no known price."""
    price = price_for(usage.model, at, prices)
    if price is None:
        return None
    return (
        usage.input_tokens * price.input_usd_per_million
        + usage.billed_output_tokens * price.output_usd_per_million
    ) / TOKENS_PER_PRICE_UNIT
