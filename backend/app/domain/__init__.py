"""Domain entities: plain data, no I/O."""

from app.domain.agent import (
    AnswerStatus,
    ChatAnswer,
    DraftAnswer,
    Evidence,
    GapInfo,
    GapRecord,
    ToolCall,
    ToolOutcome,
    ToolSpec,
    Verdict,
)
from app.domain.models import IngestionReport, SourceMetadata, SourceResult

__all__ = [
    "AnswerStatus",
    "ChatAnswer",
    "DraftAnswer",
    "Evidence",
    "GapInfo",
    "GapRecord",
    "IngestionReport",
    "SourceMetadata",
    "SourceResult",
    "ToolCall",
    "ToolOutcome",
    "ToolSpec",
    "Verdict",
]
