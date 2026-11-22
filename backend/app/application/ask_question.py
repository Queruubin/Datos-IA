"""AskQuestion use case (PRD 8.2): plan tool calls with the LLM, run them deterministically,
let the LLM write the answer and validate it before returning it."""

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from app.application.agent_tools import AgentTools, EvidenceLedger
from app.application.answer_validator import UNVERIFIED_ANSWER, validate_answer
from app.application.privacy import mask_pii
from app.domain import ChatAnswer, DraftAnswer, GapInfo, GapRecord, ToolOutcome
from app.ports import GapRepositoryPort, LLMOutputError, LLMPort

logger = logging.getLogger(__name__)

MAX_ROUNDS = 5
MAX_CALLS_PER_ROUND = 6
COMPARISON_TOOL = "compare_participatory_budget_vs_commitments"
GAP_TOOL = "report_information_gap"


class AskQuestion:
    def __init__(
        self,
        llm: LLMPort,
        tools: AgentTools,
        gaps: GapRepositoryPort,
        max_rounds: int = MAX_ROUNDS,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._gaps = gaps
        self._max_rounds = max_rounds
        self._clock = clock

    def run(self, question: str) -> ChatAnswer:
        masked = mask_pii(question)  # the LLM and the logs only ever see the masked question
        ledger = EvidenceLedger()
        outcomes = self._collect(masked, ledger)

        reported = _reported_gap(outcomes)
        try:
            draft = self._llm.compose_answer(masked, outcomes)
        except LLMOutputError:
            logger.warning("Model returned an invalid structured answer; answering with a gap")
            draft = DraftAnswer(UNVERIFIED_ANSWER, [], "information_gap")
            reason = "invalid_model_output"
        else:
            reason = "model_reported"

        result = validate_answer(draft, ledger.items)
        if result.rejected_reason:
            logger.warning("Answer rejected: %s", result.rejected_reason)
            reason = result.rejected_reason
        final = result.draft

        gap = None
        if final.status == "information_gap":
            gap = GapInfo(
                topic=final.gap_topic or (reported.topic if reported else "sin clasificar"),
                missing_data=final.gap_missing_data
                or (reported.missing_data if reported else "No especificado"),
            )
            self._record_gap(masked, gap, reason)

        comparison = _last_comparison(outcomes) if final.status == "answered" else None
        return ChatAnswer(
            answer=final.answer,
            status=final.status,
            evidence=result.evidence,
            comparison=comparison,
            gap=gap,
        )

    def _collect(self, question: str, ledger: EvidenceLedger) -> list[ToolOutcome]:
        session = self._llm.start_planning(question, self._tools.specs())
        collected: list[ToolOutcome] = []
        last_round: list[ToolOutcome] | None = None
        for _ in range(self._max_rounds):
            calls = session.next_tool_calls(last_round)
            if not calls:
                break
            last_round = [self._tools.execute(c, ledger) for c in calls[:MAX_CALLS_PER_ROUND]]
            collected.extend(last_round)
        else:
            logger.info("Tool loop stopped after %d rounds", self._max_rounds)
        return collected

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


def _last_comparison(outcomes: list[ToolOutcome]) -> dict | None:
    for outcome in reversed(outcomes):
        if outcome.call.name == COMPARISON_TOOL and not outcome.error:
            return {
                **outcome.data,
                "evidence_ids": [item.id for item in outcome.evidence],
            }
    return None
