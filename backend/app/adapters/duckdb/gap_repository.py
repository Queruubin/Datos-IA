"""DuckDB `gap_log` table implementing `GapRepositoryPort`."""

from datetime import UTC
from pathlib import Path

import duckdb

from app.domain import GapRecord

GAP_TABLE = "gap_log"

_CREATE_GAP_LOG = f"""
CREATE TABLE IF NOT EXISTS {GAP_TABLE} (
    id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP,  -- stored in UTC
    question_masked VARCHAR,
    topic VARCHAR,
    missing_data VARCHAR,
    reason VARCHAR
)
"""


class DuckDBGapRepository:
    """Stores information gaps. The question is already masked; no IP is ever stored."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def save(self, gap: GapRecord) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        created_at = gap.created_at.astimezone(UTC).replace(tzinfo=None)
        with duckdb.connect(str(self._path)) as connection:
            connection.execute(_CREATE_GAP_LOG)
            connection.execute(
                f"INSERT INTO {GAP_TABLE} VALUES (?, ?, ?, ?, ?, ?)",
                [gap.id, created_at, gap.question_masked, gap.topic, gap.missing_data,
                 gap.reason],
            )

    def list_gaps(self) -> list[GapRecord]:
        if not self._path.exists():
            return []
        with duckdb.connect(str(self._path)) as connection:
            connection.execute(_CREATE_GAP_LOG)
            rows = connection.execute(
                f"SELECT id, created_at, question_masked, topic, missing_data, reason "
                f"FROM {GAP_TABLE} ORDER BY created_at"
            ).fetchall()
        return [
            GapRecord(
                id=row[0], created_at=row[1].replace(tzinfo=UTC), question_masked=row[2],
                topic=row[3], missing_data=row[4], reason=row[5],
            )
            for row in rows
        ]
