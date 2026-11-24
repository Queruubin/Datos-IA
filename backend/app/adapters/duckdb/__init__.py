"""DuckDB storage: one table per source, the curated relational model, a `source_metadata` table
and a `data_version` marker."""

import re
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from datetime import UTC
from pathlib import Path

import duckdb
import pandas as pd

from app.adapters.duckdb.curated_views import CURATED_VIEWS
from app.domain import DataVersion, SourceMetadata

METADATA_TABLE = "source_metadata"
VERSION_TABLE = "data_version"
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
    ingested_at TIMESTAMP,  -- stored in UTC
    origin_note VARCHAR
)
"""
# Databases created before the curated package have no `origin_note` column.
_MIGRATE_METADATA = (
    f"ALTER TABLE {METADATA_TABLE} ADD COLUMN IF NOT EXISTS origin_note VARCHAR"
)
_METADATA_COLUMNS = (
    "source_id, title, table_name, portal_url, resource_urls, data_cutoff, rows, unit, "
    "ingested_at, origin_note"
)
_CREATE_VERSION = f"""
CREATE TABLE IF NOT EXISTS {VERSION_TABLE} (
    schema_version INTEGER,
    curated_fingerprint VARCHAR,
    ingested_at TIMESTAMP  -- stored in UTC
)
"""


class DuckDBStore:
    """Implements `DataStorePort` and `AnalyticsPort`. Opens a short-lived connection per
    operation so the API and the ingestion CLI do not keep the database file locked."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    @contextmanager
    def _connect(self, read_only: bool = False) -> Iterator[duckdb.DuckDBPyConnection]:
        if not read_only:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = duckdb.connect(str(self._path), read_only=read_only)
        try:
            yield connection
        finally:
            connection.close()

    # --- writes ----------------------------------------------------------------------------
    def write_table(self, name: str, frame: pd.DataFrame) -> None:
        _check_name(name)
        prepared = _prepare_for_duckdb(frame)
        with self._connect() as connection:
            connection.register("incoming_frame", prepared)
            connection.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM incoming_frame')

    def write_relational_model(self, tables: Mapping[str, pd.DataFrame]) -> None:
        """Replace every table of the curated model and recreate its views in ONE transaction:
        a failure leaves the previous model untouched."""
        for name in tables:
            _check_name(name)
        with self._connect() as connection:
            connection.execute("BEGIN TRANSACTION")
            try:
                for view in CURATED_VIEWS:
                    connection.execute(f'DROP VIEW IF EXISTS "{view}"')
                for name, frame in tables.items():
                    connection.register("incoming_frame", _prepare_for_duckdb(frame))
                    connection.execute(
                        f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM incoming_frame'
                    )
                    connection.unregister("incoming_frame")
                for view, sql in CURATED_VIEWS.items():
                    connection.execute(f'CREATE VIEW "{view}" AS {sql}')
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

    def drop_tables(self, names: Iterable[str]) -> None:
        names = list(names)
        for name in names:
            _check_name(name)
        if not self._path.exists():
            return
        with self._connect() as connection:
            for name in names:
                connection.execute(f'DROP TABLE IF EXISTS "{name}"')

    def write_source_metadata(self, metadata: SourceMetadata) -> None:
        ingested_at = metadata.ingested_at.astimezone(UTC).replace(tzinfo=None)
        with self._connect() as connection:
            connection.execute(_CREATE_METADATA)
            connection.execute(_MIGRATE_METADATA)
            connection.execute(
                f"INSERT OR REPLACE INTO {METADATA_TABLE} ({_METADATA_COLUMNS}) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    metadata.source_id, metadata.title, metadata.table_name, metadata.portal_url,
                    list(metadata.resource_urls), metadata.data_cutoff, metadata.rows,
                    metadata.unit, ingested_at, metadata.origin_note,
                ],
            )

    def delete_source_metadata(self, source_ids: Iterable[str]) -> None:
        source_ids = list(source_ids)
        if not source_ids or not self._path.exists():
            return
        with self._connect() as connection:
            if not _table_exists(connection, METADATA_TABLE):
                return
            connection.execute(
                f"DELETE FROM {METADATA_TABLE} WHERE source_id IN "
                f"({', '.join('?' for _ in source_ids)})",
                source_ids,
            )

    def write_data_version(self, version: DataVersion) -> None:
        ingested_at = version.ingested_at.astimezone(UTC).replace(tzinfo=None)
        with self._connect() as connection:
            connection.execute(_CREATE_VERSION)
            connection.execute(f"DELETE FROM {VERSION_TABLE}")
            connection.execute(
                f"INSERT INTO {VERSION_TABLE} VALUES (?, ?, ?)",
                [version.schema_version, version.curated_fingerprint, ingested_at],
            )

    # --- reads -----------------------------------------------------------------------------
    def read_table(self, name: str) -> pd.DataFrame:
        """All rows of one table or view. Raises if it does not exist."""
        _check_name(name)
        with self._connect(read_only=True) as connection:
            return connection.execute(f'SELECT * FROM "{name}"').df()

    def read_source_metadata(self) -> list[SourceMetadata]:
        if not self._path.exists():
            return []
        with self._connect(read_only=True) as connection:
            if not _table_exists(connection, METADATA_TABLE):
                return []
            has_note = connection.execute(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_name = ? AND column_name = 'origin_note'",
                [METADATA_TABLE],
            ).fetchone()[0]
            columns = _METADATA_COLUMNS if has_note else _METADATA_COLUMNS.replace(
                "origin_note", "NULL AS origin_note"
            )
            rows = connection.execute(
                f"SELECT {columns} FROM {METADATA_TABLE} ORDER BY source_id"
            ).fetchall()
        return [
            SourceMetadata(
                source_id=row[0], title=row[1], table_name=row[2], portal_url=row[3] or None,
                resource_urls=list(row[4] or []), data_cutoff=row[5], rows=int(row[6]),
                unit=row[7], ingested_at=row[8].replace(tzinfo=UTC), origin_note=row[9],
            )
            for row in rows
        ]

    def read_data_version(self) -> DataVersion | None:
        """The marker written by the last successful curated ingestion, or None."""
        if not self._path.exists():
            return None
        with self._connect(read_only=True) as connection:
            if not _table_exists(connection, VERSION_TABLE):
                return None
            row = connection.execute(
                f"SELECT schema_version, curated_fingerprint, ingested_at FROM {VERSION_TABLE}"
            ).fetchone()
        if row is None:
            return None
        return DataVersion(int(row[0]), row[1], row[2].replace(tzinfo=UTC))


def _check_name(name: str) -> None:
    if not TABLE_NAME.fullmatch(name):
        raise ValueError(f"Invalid table name: {name!r}")


def _table_exists(connection: duckdb.DuckDBPyConnection, name: str) -> bool:
    return bool(connection.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [name]
    ).fetchone()[0])


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
