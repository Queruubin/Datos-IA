"""Deterministic checks applied to the LLM's final answer (PRD RF1 and RF3)."""

import re
from dataclasses import dataclass

from app.domain import DraftAnswer, Evidence

UNVERIFIED_ANSWER = (
    "No pude verificar esta respuesta con las fuentes disponibles. "
    "Prueba reformulando la pregunta o consulta directamente el portal de Datos Abiertos Bogotá."
)
DIGIT = re.compile(r"\d")


@dataclass(frozen=True)
class ValidationResult:
    draft: DraftAnswer
    evidence: list[Evidence]  # only the cited evidence that really exists
    rejected_reason: str | None = None


def validate_answer(draft: DraftAnswer, collected: list[Evidence]) -> ValidationResult:
    """Drop unknown evidence ids and reject answers with figures that cite no evidence."""
    by_id = {item.id: item for item in collected}
    cited: list[Evidence] = []
    for evidence_id in draft.cited_evidence_ids:
        item = by_id.get(evidence_id)
        if item is not None and item not in cited:
            cited.append(item)

    if draft.status == "answered" and DIGIT.search(draft.answer) and not cited:
        safe = DraftAnswer(
            answer=UNVERIFIED_ANSWER,
            cited_evidence_ids=[],
            status="information_gap",
            gap_topic=draft.gap_topic or "sin clasificar",
            gap_missing_data=draft.gap_missing_data or "Cifra sin evidencia verificable",
        )
        return ValidationResult(safe, [], rejected_reason="numbers_without_evidence")

    clean = DraftAnswer(
        answer=draft.answer,
        cited_evidence_ids=[item.id for item in cited],
        status=draft.status,
        gap_topic=draft.gap_topic,
        gap_missing_data=draft.gap_missing_data,
    )
    return ValidationResult(clean, cited)
