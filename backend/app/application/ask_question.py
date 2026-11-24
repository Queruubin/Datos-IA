"""AskQuestion use case (PRD 8.2): plan tool calls with the LLM, run them deterministically,
let the LLM write the answer and validate it before returning it."""

import logging
import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from app.application.agent_tools import COMPARISON_TOOLS, AgentTools, EvidenceLedger
from app.application.answer_validator import UNVERIFIED_ANSWER, validate_answer
from app.application.charts import build_charts
from app.application.pricing import cost_usd
from app.application.privacy import mask_pii
from app.domain import (
    ChatAnswer,
    DraftAnswer,
    GapInfo,
    GapRecord,
    LLMUsage,
    QuestionUsage,
    ToolOutcome,
    UsageRecord,
)
from app.ports import GapRepositoryPort, LLMOutputError, LLMPort, UsageRepositoryPort

logger = logging.getLogger(__name__)

MAX_ROUNDS = 5
MAX_CALLS_PER_ROUND = 6
GAP_TOOL = "report_information_gap"
# Gaps caused by the model failing or by a rejected answer: the data may well be published.
UNVERIFIED_REASONS = frozenset({"invalid_model_output", "numbers_without_evidence"})
# Answered with related data, but the specific data asked for is not published.
PARTIAL_REASON = "partial_answer"


class AskQuestion:
    def __init__(
        self,
        llm: LLMPort,
        tools: AgentTools,
        gaps: GapRepositoryPort,
        max_rounds: int = MAX_ROUNDS,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        usage: UsageRepositoryPort | None = None,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._gaps = gaps
        self._usage = usage
        self._max_rounds = max_rounds
        self._clock = clock

    def run(self, question: str) -> ChatAnswer:
        calls: list[LLMUsage] = []  # filled by every model call, even if a later one fails
        try:
            answer = self._answer(question, calls)
        finally:
            # Runs on errors too: tokens of the calls that did succeed were consumed anyway.
            usage = self._record_usage(calls)
        return replace(answer, usage=usage)

    def _answer(self, question: str, calls: list[LLMUsage]) -> ChatAnswer:
        masked = mask_pii(question)  # the LLM and the logs only ever see the masked question
        ledger = EvidenceLedger()
        outcomes = self._collect(masked, ledger, calls)

        reported = _reported_gap(outcomes)
        try:
            draft = self._llm.compose_answer(masked, outcomes)
        except LLMOutputError as error:
            logger.warning("Model returned an invalid structured answer; answering with a gap")
            if error.usage is not None:
                calls.append(error.usage)
            draft = DraftAnswer(UNVERIFIED_ANSWER, [], "information_gap")
            reason = "invalid_model_output"
        else:
            if draft.usage is not None:
                calls.append(draft.usage)
            reason = "model_reported"

        result = validate_answer(draft, ledger.items)
        if result.rejected_reason:
            logger.warning("Answer rejected: %s", result.rejected_reason)
            reason = result.rejected_reason
        final = result.draft

        gap = None
        if final.status == "information_gap":
            if reason in UNVERIFIED_REASONS:
                kind = "unverified"
            else:
                kind = final.gap_kind or "unpublished_data"
                if kind == "out_of_scope":
                    reason = "out_of_scope"  # kept apart from data that is missing
            gap = GapInfo(
                topic=final.gap_topic or (reported.topic if reported else "sin clasificar"),
                missing_data=final.gap_missing_data
                or (reported.missing_data if reported else "No especificado"),
                kind=kind,
            )
            self._record_gap(masked, gap, reason)

        answered = final.status == "answered"
        partial_gap = _partial_gap(final) if answered else None
        if partial_gap is not None:
            self._record_gap(masked, partial_gap, PARTIAL_REASON)

        return ChatAnswer(
            answer=final.answer,
            status=final.status,
            evidence=result.evidence,
            comparison=_last_comparison(outcomes) if answered else None,
            gap=gap,
            # Built by code from the tool results, only from evidence the answer cites.
            charts=build_charts(outcomes, final.cited_evidence_ids) if answered else (),
            partial_gap=partial_gap,
        )

    def _collect(
        self, question: str, ledger: EvidenceLedger, usage: list[LLMUsage]
    ) -> list[ToolOutcome]:
        session = self._llm.start_planning(question, self._tools.specs())
        collected: list[ToolOutcome] = []
        last_round: list[ToolOutcome] | None = None
        try:
            for _ in range(self._max_rounds):
                calls = session.next_tool_calls(last_round)
                if not calls:
                    break
                last_round = [self._tools.execute(c, ledger) for c in calls[:MAX_CALLS_PER_ROUND]]
                collected.extend(last_round)
            else:
                logger.info("Tool loop stopped after %d rounds", self._max_rounds)
        finally:
            usage.extend(session.usage)
        return collected

    def _record_usage(self, calls: list[LLMUsage]) -> QuestionUsage:
        """Price every call at the paid-tier table and store one row per call. Storing usage
        must never break the answer."""
        question_id = uuid.uuid4().hex
        now = self._clock()
        records = [
            UsageRecord(
                id=uuid.uuid4().hex,
                created_at=now,
                question_id=question_id,
                model=call.model,
                input_tokens=call.input_tokens,
                output_tokens=call.output_tokens,
                thinking_tokens=call.thinking_tokens,
                total_tokens=call.total_tokens,
                cost_usd=cost_usd(call, now),
            )
            for call in calls
        ]
        if self._usage is not None and records:
            try:
                self._usage.save_many(records)
            except Exception:
                logger.exception("Could not store the token usage")
        unpriced = tuple(dict.fromkeys(r.model for r in records if r.cost_usd is None))
        total_cost = None if unpriced else sum(r.cost_usd or 0.0 for r in records)
        return QuestionUsage(
            question_id=question_id,
            calls=tuple(calls),
            cost_usd=total_cost,
            unpriced_models=unpriced,
        )

    def _record_gap(self, masked_question: str, gap: GapInfo, reason: str) -> None:
        try:
            self._gaps.save(GapRecord(
                id=uuid.uuid4().hex,
                created_at=self._clock(),
                question_masked=masked_question,
                topic=gap.topic[:120],
                missing_data=gap.missing_data[:300],
                reason=reason,
            ))
        except Exception:  # recording a gap must never break the answer
            logger.exception("Could not store the information gap")


def _reported_gap(outcomes: list[ToolOutcome]) -> GapInfo | None:
    for outcome in reversed(outcomes):
        if outcome.call.name == GAP_TOOL and not outcome.error:
            return GapInfo(outcome.data["topic"], outcome.data["missing_data"])
    return None


def _partial_gap(draft: DraftAnswer) -> GapInfo | None:
    """Missing data the model flagged on an answered draft. Only public, unpublished data counts:
    out-of-scope leftovers (names, opinions) are not something to request from the Alcaldía."""
    missing = (draft.gap_missing_data or "").strip()
    if draft.gap_kind != "unpublished_data" or not missing:
        return None
    topic = (draft.gap_topic or "").strip() or "sin clasificar"
    return GapInfo(topic=topic, missing_data=missing, kind="unpublished_data")


def _has_verdict(outcome: ToolOutcome) -> bool:
    return isinstance(outcome.data, dict) and "verdict" in outcome.data


def _last_comparison(outcomes: list[ToolOutcome]) -> dict | None:
    for outcome in reversed(outcomes):
        if outcome.call.name in COMPARISON_TOOLS and not outcome.error and _has_verdict(outcome):
            return {
                **outcome.data,
                "evidence_ids": [item.id for item in outcome.evidence],
            }
    return None
