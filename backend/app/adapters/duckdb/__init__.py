"""DuckDB storage: one table per source plus a `source_metadata` table."""

import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC
from pathlib import Path

import duckdb
import pandas as pd

from app.domain import SourceMetadata

METADATA_TABLE = "source_metadata"
TABLE_NAME = re.compile(r"[a-z][a-z0-9_]*")

_CREATE_METADATA = f"""
CREATE TABLE IF NOT EXISTS {METADATA_TABLE} (
    source_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    table_name VARCHAR,
    portal_url VARCHAR,
    resource_urls VARCHAR[],
    data_cutoff VARCHAR,
    rows BIGINT,
    unit VARCHAR,
    ingested_at TIMESTAMP  -- stored in UTC
)
"""


class DuckDBStore:
    """Implements `DataStorePort`. Opens a short-lived connection per operation so the API and
    the ingestion CLI do not keep the database file locked."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @contextmanager
    def _connect(self, read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
        if not read_only:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = duckdb.connect(str(self._path), read_only=read_only)
        try:
            yield connection
        finally:
            connection.close()

    def write_table(self, name: str, frame: pd.DataFrame) -> None:
        if not TABLE_NAME.fullmatch(name):
            raise ValueError(f"Invalid table name: {name!r}")
        prepared = _prepare_for_duckdb(frame)
        with self._connect() as connection:
            connection.register("incoming_frame", prepared)
            connection.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM incoming_frame')

    def read_table(self, name: str) -> pd.DataFrame:
        if not TABLE_NAME.fullmatch(name):
            raise ValueError(f"Invalid table name: {name!r}")
        with self._connect(read_only=True) as connection:
            return connection.execute(f'SELECT * FROM "{name}"').df()

    def write_source_metadata(self, metadata: SourceMetadata) -> None:
        ingested_at = metadata.ingested_at.astimezone(UTC).replace(tzinfo=None)
        with self._connect() as connection:
            connection.execute(_CREATE_METADATA)
            connection.execute(
                f"INSERT OR REPLACE INTO {METADATA_TABLE} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    metadata.source_id, metadata.title, metadata.table_name, metadata.portal_url,
                    list(metadata.resource_urls), metadata.data_cutoff, metadata.rows,
                    metadata.unit, ingested_at,
                ],
            )

    def read_source_metadata(self) -> list[SourceMetadata]:
        if not self._path.exists():
            return []
        with self._connect(read_only=True) as connection:
            exists = connection.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_name = ?",
                [METADATA_TABLE],
            ).fetchone()[0]
            if not exists:
                return []
            rows = connection.execute(
                f"SELECT source_id, title, table_name, portal_url, resource_urls, data_cutoff, "
                f"rows, unit, ingested_at FROM {METADATA_TABLE} ORDER BY source_id"
            ).fetchall()
        return [
            SourceMetadata(
                source_id=row[0], title=row[1], table_name=row[2], portal_url=row[3],
                resource_urls=list(row[4] or []), data_cutoff=row[5], rows=int(row[6]),
                unit=row[7], ingested_at=row[8].replace(tzinfo=UTC),
            )
            for row in rows
        ]


def _prepare_for_duckdb(frame: pd.DataFrame) -> pd.DataFrame:
    """Object columns mixing Python types (common in spreadsheets) are stored as text."""
    prepared = frame.copy()
    for column in prepared.columns:
        if prepared[column].dtype != object:
            continue
        kinds = {type(value) for value in prepared[column].dropna()}
        if len(kinds) > 1:
            prepared[column] = prepared[column].map(str, na_action="ignore")
    return prepared
