"""DuckDB `usage_log` table implementing `UsageRepositoryPort` (one row per Gemini call)."""

from datetime import UTC
from pathlib import Path

import duckdb

from app.domain import UsageRecord

USAGE_TABLE = "usage_log"

_CREATE_USAGE_LOG = f"""
CREATE TABLE IF NOT EXISTS {USAGE_TABLE} (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP,  -- stored in UTC
    question_id VARCHAR,
    model VARCHAR,
    input_tokens BIGINT,
    output_tokens BIGINT,
    thinking_tokens BIGINT,
    total_tokens BIGINT,
    cost_usd DOUBLE  -- NULL when the model has no known price
)
"""

_COLUMNS = (
    "id, created_at, question_id, model, input_tokens, output_tokens, thinking_tokens, "
    "total_tokens, cost_usd"
)


class DuckDBUsageRepository:
    """Stores token usage only: no question text, no IP, no personal data."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def save_many(self, records: list[UsageRecord]) -> None:
        if not records:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            [
                record.id, record.created_at.astimezone(UTC).replace(tzinfo=None),
                record.question_id, record.model, record.input_tokens, record.output_tokens,
                record.thinking_tokens, record.total_tokens, record.cost_usd,
            ]
            for record in records
        ]
        with duckdb.connect(str(self._path)) as connection:
            connection.execute(_CREATE_USAGE_LOG)
            connection.executemany(
                f"INSERT INTO {USAGE_TABLE} ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
            )

    def list_records(self) -> list[UsageRecord]:
        if not self._path.exists():
            return []
        with duckdb.connect(str(self._path)) as connection:
            connection.execute(_CREATE_USAGE_LOG)
            rows = connection.execute(
                f"SELECT {_COLUMNS} FROM {USAGE_TABLE} ORDER BY created_at, id"
            ).fetchall()
        return [
            UsageRecord(
                id=row[0], created_at=row[1].replace(tzinfo=UTC), question_id=row[2],
                model=row[3], input_tokens=int(row[4]), output_tokens=int(row[5]),
                thinking_tokens=int(row[6]), total_tokens=int(row[7]), cost_usd=row[8],
            )
            for row in rows
        ]
