"""Ports: the interfaces the application needs from the outside world."""

from collections.abc import Iterable, Mapping
from typing import Protocol

import pandas as pd

from app.domain import (
    DataVersion,
    DraftAnswer,
    ExchangeRate,
    GapRecord,
    LLMUsage,
    SourceMetadata,
    ToolCall,
    ToolOutcome,
    ToolSpec,
    UsageRecord,
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

    def read_table(self, name: str) -> pd.DataFrame:
        """All rows of one table. Raises if the table does not exist."""
        ...

    def write_relational_model(self, tables: Mapping[str, pd.DataFrame]) -> None:
        """Replace all tables of the curated relational model (and its analytic views) at once:
        either everything is written or nothing changes."""
        ...

    def drop_tables(self, names: Iterable[str]) -> None:
        """Drop tables of retired sources (missing tables are ignored)."""
        ...

    def delete_source_metadata(self, source_ids: Iterable[str]) -> None:
        """Remove the metadata records of retired sources."""
        ...

    def read_data_version(self) -> DataVersion | None:
        """Marker of the last successful curated ingestion (None if never ingested)."""
        ...

    def write_data_version(self, version: DataVersion) -> None:
        ...


class AnalyticsPort(Protocol):
    """Read-only access to the cleaned tables and views (implemented by `DuckDBStore`)."""

    def read_table(self, name: str) -> pd.DataFrame:
        """All rows of one table or view. Raises if it does not exist."""
        ...

    def read_source_metadata(self) -> list[SourceMetadata]:
        ...


class PlanningSession(Protocol):
    """One tool-planning conversation with the LLM about a single question."""

    usage: list[LLMUsage]
    """Tokens of every model call made so far in this conversation (one entry per call)."""

    def next_tool_calls(self, results: list[ToolOutcome] | None) -> list[ToolCall]:
        """Send the results of the previous calls (None on the first round) and return the next
        calls the model wants. An empty list means the model needs no more data."""
        ...


class LLMPort(Protocol):
    """The language model. It plans tool calls and writes the final answer; it never computes."""

    def start_planning(self, question: str, tools: list[ToolSpec]) -> PlanningSession:
        ...

    def compose_answer(self, question: str, results: list[ToolOutcome]) -> DraftAnswer:
        """Final structured answer (with the call's `usage`) from the question and the collected
        tool results. Raises `LLMOutputError` when the model output cannot be parsed."""
        ...


class LLMOutputError(RuntimeError):
    """The model returned something that does not match the expected structured output.

    `usage` keeps the tokens of that call: they were consumed even if the output is unusable."""

    def __init__(self, message: str, usage: LLMUsage | None = None) -> None:
        super().__init__(message)
        self.usage = usage


class GapRepositoryPort(Protocol):
    """Where information gaps are recorded for the Alcaldía panel."""

    def save(self, gap: GapRecord) -> None:
        ...

    def list_gaps(self) -> list[GapRecord]:
        ...


class UsageRepositoryPort(Protocol):
    """Where the token usage of every model call is recorded (no question text, no PII)."""

    def save_many(self, records: list[UsageRecord]) -> None:
        ...

    def list_records(self) -> list[UsageRecord]:
        ...


class ExchangeRatePort(Protocol):
    """Official USD → COP rate. Never raises: returns `source="unavailable"` instead."""

    def usd_to_cop(self) -> ExchangeRate:
        ...
