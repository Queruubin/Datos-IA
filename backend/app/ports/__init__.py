"""Ports: the interfaces the application needs from the outside world."""

from typing import Protocol

import pandas as pd

from app.domain import (
    DraftAnswer,
    GapRecord,
    SourceMetadata,
    ToolCall,
    ToolOutcome,
    ToolSpec,
)


class CatalogPort(Protocol):
    """An open-data catalog (e.g. the CKAN portal of Datos Abiertos Bogotá)."""

    def get_dataset(self, dataset_id: str) -> dict:
        """Dataset description, including its `resources` (each with `name`, `url`, `format`)."""
        ...

    def download(self, url: str) -> bytes:
        """Raw bytes of one resource file."""
        ...


class DataStorePort(Protocol):
    """Where cleaned tables and their traceability metadata are stored."""

    def write_table(self, name: str, frame: pd.DataFrame) -> None:
        """Create or replace a table with the given rows."""
        ...

    def write_source_metadata(self, metadata: SourceMetadata) -> None:
        """Create or replace the metadata record of one source."""
        ...

    def read_source_metadata(self) -> list[SourceMetadata]:
        """All metadata records (empty list when nothing was ingested yet)."""
        ...


class AnalyticsPort(Protocol):
    """Read-only access to the cleaned tables (implemented by `DuckDBStore`)."""

    def read_table(self, name: str) -> pd.DataFrame:
        """All rows of one table. Raises if the table does not exist."""
        ...

    def read_source_metadata(self) -> list[SourceMetadata]:
        ...


class PlanningSession(Protocol):
    """One tool-planning conversation with the LLM about a single question."""

    def next_tool_calls(self, results: list[ToolOutcome] | None) -> list[ToolCall]:
        """Send the results of the previous calls (None on the first round) and return the next
        calls the model wants. An empty list means the model needs no more data."""
        ...


class LLMPort(Protocol):
    """The language model. It plans tool calls and writes the final answer; it never computes."""

    def start_planning(self, question: str, tools: list[ToolSpec]) -> PlanningSession:
        ...

    def compose_answer(self, question: str, results: list[ToolOutcome]) -> DraftAnswer:
        """Final structured answer from the question and the collected tool results.
        Raises `LLMOutputError` when the model output cannot be parsed."""
        ...


class LLMOutputError(RuntimeError):
    """The model returned something that does not match the expected structured output."""


class GapRepositoryPort(Protocol):
    """Where information gaps are recorded for the Alcaldía panel."""

    def save(self, gap: GapRecord) -> None:
        ...

    def list_gaps(self) -> list[GapRecord]:
        ...
