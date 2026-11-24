"""Small DuckDB fixture database and a scripted fake LLM for the agent tests. No network."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from app.adapters.duckdb import DuckDBStore
from app.application import IngestSources
from app.domain import (
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
from tests.curated_fixture import portal_commitments_frame, write_mini_package

PORTAL = "https://datosabiertos.bogota.gov.co/dataset/{}"


def _meta(source_id: str, table: str, cutoff: str, rows: int) -> SourceMetadata:
    return SourceMetadata(
        source_id=source_id, title=f"Fuente {source_id}", table_name=table,
        portal_url=PORTAL.format(source_id.lower()), resource_urls=["u"], data_cutoff=cutoff,
        rows=rows, unit=None, ingested_at=datetime(2026, 11, 1, tzinfo=UTC),
    )


def build_fixture_db(path: Path) -> DuckDBStore:
    """PAC table (F1), portal commitments (F3) and the miniature curated package, loaded through
    the real ingestion use case."""
    store = DuckDBStore(path)
    store.write_table("f1_pac_execution", pd.DataFrame({
        "year": [2024, 2025, 2025],
        "month": [12, 1, 2],
        "entity_code": ["0004-01"] * 3,
        "locality": ["San Cristobal"] * 3,
        "pac_programmed": [100.0, 200.0, 300.0],
        "pac_executed": [50.0, 150.0, 150.0],
        "pct_executed_reported": [0.5, 0.75, 0.5],
        "pct_deviation_reported": [0.5, 0.25, 0.5],
        "pct_executed_calc": [0.5, 0.75, 0.5],
        "rank_in_month": [10, 3, 12],
    }))
    store.write_source_metadata(_meta("F1", "f1_pac_execution", "2025-02", 3))
    portal = portal_commitments_frame()
    store.write_table("f3_pp_commitments", portal)
    store.write_source_metadata(_meta("F3-commitments", "f3_pp_commitments", "2026-09-30",
                                      len(portal)))
    package = write_mini_package(Path(path).parent / f"{Path(path).stem}_curated")
    report = IngestSources(
        catalog=None, store=store, curated_root=package,
        clock=lambda: datetime(2026, 11, 1, tzinfo=UTC),
    ).run(["CURADO"])
    assert report.ok, report.results[0].error
    return store


class ScriptedSession:
    def __init__(self, llm: "ScriptedLLM") -> None:
        self._llm = llm
        self._round = 0
        self.usage: list[LLMUsage] = []

    def _record_call(self) -> None:
        if self._llm.usage is not None:
            self.usage.append(self._llm.usage)

    def next_tool_calls(self, results: list[ToolOutcome] | None) -> list[ToolCall]:
        self._llm.received.append(results)
        self._record_call()
        calls = self._llm.rounds[self._round] if self._round < len(self._llm.rounds) else []
        self._round += 1
        return calls


class ScriptedLLM:
    """Fake LLMPort: returns predefined tool calls per round, then a draft built by `answer`."""

    def __init__(
        self,
        rounds: list[list[ToolCall]],
        answer: Callable[[list[ToolOutcome]], DraftAnswer] | DraftAnswer,
        repeat_last_round: bool = False,
        usage: LLMUsage | None = None,
    ) -> None:
        self.usage = usage  # reported for every planning call and for the compose call
        self.rounds = rounds
        self.answer = answer
        self.repeat_last_round = repeat_last_round
        self.received: list[list[ToolOutcome] | None] = []
        self.questions: list[str] = []
        self.tool_names: list[str] = []

    def start_planning(self, question: str, tools: list[ToolSpec]):
        self.questions.append(question)
        self.tool_names = [tool.name for tool in tools]
        if self.repeat_last_round:
            return _EndlessSession(self)
        return ScriptedSession(self)

    def compose_answer(self, question: str, results: list[ToolOutcome]) -> DraftAnswer:
        draft = self.answer(results) if callable(self.answer) else self.answer
        return replace(draft, usage=self.usage)


class _EndlessSession(ScriptedSession):
    def next_tool_calls(self, results):
        self._llm.received.append(results)
        self._record_call()
        return self._llm.rounds[-1]


class InMemoryGaps:
    def __init__(self) -> None:
        self.saved: list[GapRecord] = []

    def save(self, gap: GapRecord) -> None:
        self.saved.append(gap)

    def list_gaps(self) -> list[GapRecord]:
        return list(self.saved)


class InMemoryUsage:
    def __init__(self, failing: bool = False) -> None:
        self.saved: list[UsageRecord] = []
        self.failing = failing

    def save_many(self, records: list[UsageRecord]) -> None:
        if self.failing:
            raise OSError("disk full")
        self.saved.extend(records)

    def list_records(self) -> list[UsageRecord]:
        return list(self.saved)


class FixedRate:
    """Fake ExchangeRatePort: no network."""

    def __init__(self, value: float | None = 4000.0, source: str = "datos.gov.co") -> None:
        self.rate = ExchangeRate(value, date(2026, 11, 21) if value else None, source)

    def usd_to_cop(self) -> ExchangeRate:
        return self.rate
