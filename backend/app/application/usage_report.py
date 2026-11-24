"""Aggregates stored usage rows into the report served by `GET /api/usage`. Pure: no I/O."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from app.application.pricing import (
    PRICES,
    PRICING_READ_ON,
    PRICING_SOURCE_URL,
    PRICING_TIER,
    ModelPrice,
)
from app.domain import ExchangeRate, UsageRecord

BOGOTA = timezone(timedelta(hours=-5), "America/Bogota")  # days are counted in Colombian time
DAYS_IN_REPORT = 30

FREE_TIER_NOTE = (
    "Con el plan gratuito de Gemini el costo real es $0; estas cifras son el equivalente en el "
    "plan pagado (Standard). En el plan gratuito Google puede usar el contenido para mejorar sus "
    "productos."
)


@dataclass(frozen=True)
class UsageTotals:
    questions: int
    calls: int
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    total_tokens: int
    cost_usd: float | None  # sum of the priced calls; None if no call could be priced
    cost_cop: float | None
    unpriced_calls: int  # calls whose model has no known price (not included in the cost)


@dataclass(frozen=True)
class ModelUsage(UsageTotals):
    model: str = ""


@dataclass(frozen=True)
class DayUsage(UsageTotals):
    day: date | None = None


@dataclass(frozen=True)
class PricingInfo:
    source_url: str
    read_on: date
    tier: str
    unit: str
    prices: list[ModelPrice]


@dataclass(frozen=True)
class UsageReport:
    note: str
    all_time: UsageTotals
    today: UsageTotals
    avg_tokens_per_question: float | None
    avg_cost_usd_per_question: float | None
    avg_cost_cop_per_question: float | None
    by_model: list[ModelUsage]
    by_day: list[DayUsage]  # last 30 days with activity, oldest first
    exchange_rate: ExchangeRate
    pricing: PricingInfo


def _to_cop(usd: float | None, rate: ExchangeRate) -> float | None:
    return usd * rate.value if usd is not None and rate.value is not None else None


def _totals(records: list[UsageRecord], rate: ExchangeRate) -> dict:
    priced = [r.cost_usd for r in records if r.cost_usd is not None]
    unpriced = len(records) - len(priced)
    cost = sum(priced) if priced or not records else None
    return {
        "questions": len({r.question_id for r in records}),
        "calls": len(records),
        "input_tokens": sum(r.input_tokens for r in records),
        "output_tokens": sum(r.output_tokens for r in records),
        "thinking_tokens": sum(r.thinking_tokens for r in records),
        "total_tokens": sum(r.total_tokens for r in records),
        "cost_usd": cost,
        "cost_cop": _to_cop(cost, rate),
        "unpriced_calls": unpriced,
    }


def _local_day(moment: datetime) -> date:
    return moment.astimezone(BOGOTA).date()


def build_usage_report(
    records: Iterable[UsageRecord], now: datetime, rate: ExchangeRate
) -> UsageReport:
    records = list(records)
    today = _local_day(now)
    first_day = today - timedelta(days=DAYS_IN_REPORT - 1)

    by_model: dict[str, list[UsageRecord]] = defaultdict(list)
    by_day: dict[date, list[UsageRecord]] = defaultdict(list)
    for record in records:
        by_model[record.model].append(record)
        day = _local_day(record.created_at)
        if first_day <= day <= today:
            by_day[day].append(record)

    all_time = UsageTotals(**_totals(records, rate))
    questions = all_time.questions
    return UsageReport(
        note=FREE_TIER_NOTE,
        all_time=all_time,
        today=UsageTotals(**_totals(by_day.get(today, []), rate)),
        avg_tokens_per_question=all_time.total_tokens / questions if questions else None,
        avg_cost_usd_per_question=(
            all_time.cost_usd / questions if questions and all_time.cost_usd is not None else None
        ),
        avg_cost_cop_per_question=(
            all_time.cost_cop / questions if questions and all_time.cost_cop is not None else None
        ),
        by_model=[
            ModelUsage(model=model, **_totals(rows, rate))
            for model, rows in sorted(by_model.items(), key=lambda item: -len(item[1]))
        ],
        by_day=[DayUsage(day=day, **_totals(by_day[day], rate)) for day in sorted(by_day)],
        exchange_rate=rate,
        pricing=PricingInfo(
            source_url=PRICING_SOURCE_URL,
            read_on=PRICING_READ_ON,
            tier=PRICING_TIER,
            unit="USD por 1 millón de tokens (la salida incluye los tokens de razonamiento)",
            prices=list(PRICES),
        ),
    )
