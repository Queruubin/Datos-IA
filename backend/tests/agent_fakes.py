"""Small DuckDB fixture database and a scripted fake LLM for the agent tests. No network."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from app.adapters.duckdb import DuckDBStore
from app.domain import DraftAnswer, GapRecord, SourceMetadata, ToolCall, ToolOutcome, ToolSpec

PORTAL = "https://datosabiertos.bogota.gov.co/dataset/{}"


def _meta(source_id: str, table: str, cutoff: str, rows: int) -> SourceMetadata:
    return SourceMetadata(
        source_id=source_id, title=f"Fuente {source_id}", table_name=table,
        portal_url=PORTAL.format(source_id.lower()), resource_urls=["u"], data_cutoff=cutoff,
        rows=rows, unit=None, ingested_at=datetime(2026, 11, 1, tzinfo=UTC),
    )


def build_fixture_db(path: Path) -> DuckDBStore:
    store = DuckDBStore(path)
    tables = {
        "f1_pac_execution": pd.DataFrame({
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
        }),
        "f2_pqrs": pd.DataFrame({
            "radicado": ["1", "2", "3", "4", "5"],
            "vigencia": [2025, 2025, 2025, 2024, 2025],
            "subtema": ["MALLA VIAL", "MALLA VIAL", "PARQUES", "MALLA VIAL",
                        "'; DROP TABLE f2_pqrs; --"],
            "tipo_peticion": ["GENERAL", "PARTICULAR", "GENERAL", "GENERAL", "GENERAL"],
            "estado_orfeo": ["TRAMITE CERRADO", "RADICADO EN GESTION", "TRAMITE CERRADO",
                             "TRAMITE CERRADO", "TRAMITE CERRADO"],
            "response_days": [10, None, 20, 5, 1],
        }),
        "f3_pp_progress": pd.DataFrame({
            "vigencia_ejecucion": [2025, 2025, 2025, 2025, 2026],
            "codigo_propuestas": [1, 2, 3, 4, 5],
            "sector": ["CULTURA, RECREACION Y DEPORTE", "CULTURA, RECREACION Y DEPORTE",
                       "AMBIENTE", "AMBIENTE", "CULTURA, RECREACION Y DEPORTE"],
            "nombre_propuesta_ciudadana": ["Festival", "Escuela de rock", "Huerta",
                                           "Sendero", "Mural"],
            "estado_de_la_propuesta": ["Materializada", "En ejecución", "Materializada",
                                       "No ejecutada", "En formulación"],
            "pct_de_avance_propuesta": [100.0, 50.0, 100.0, 0.0, 0.0],
        }),
        "f3_pp_commitments": pd.DataFrame({
            "vigencia_ejecucion": [2025, 2025],
            "sector": ["CULTURA, RECREACION Y DEPORTE", "AMBIENTE"],
            "valor_crp_asignado_presupuestos_participativos": [1000.0, 500.0],
            "codigo_propuestas_financiadas_crp": ["1;2", "99"],
        }),
    }
    for name, frame in tables.items():
        store.write_table(name, frame)
    for meta in [
        _meta("F1", "f1_pac_execution", "2025-02", 3),
        _meta("F2", "f2_pqrs", "2025-12-31", 5),
        _meta("F3-progress", "f3_pp_progress", "2026-09-30", 5),
        _meta("F3-commitments", "f3_pp_commitments", "2026-09-30", 2),
    ]:
        store.write_source_metadata(meta)
    return store


class ScriptedSession:
    def __init__(self, llm: "ScriptedLLM") -> None:
        self._llm = llm
        self._round = 0

    def next_tool_calls(self, results: list[ToolOutcome] | None) -> list[ToolCall]:
        self._llm.received.append(results)
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
    ) -> None:
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
        return self.answer(results) if callable(self.answer) else self.answer


class _EndlessSession(ScriptedSession):
    def next_tool_calls(self, results):
        self._llm.received.append(results)
        return self._llm.rounds[-1]


class InMemoryGaps:
    def __init__(self) -> None:
        self.saved: list[GapRecord] = []

    def save(self, gap: GapRecord) -> None:
        self.saved.append(gap)

    def list_gaps(self) -> list[GapRecord]:
        return list(self.saved)
