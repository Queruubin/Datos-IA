from dataclasses import replace
from datetime import UTC, datetime

import duckdb
import pandas as pd
import pytest

from app.adapters.duckdb import DuckDBStore
from app.domain import DataVersion, SourceMetadata


def metadata(source_id="F1", rows=18):
    return SourceMetadata(
        source_id=source_id, title="PAC", table_name="f1_pac_execution",
        portal_url="https://datosabiertos.bogota.gov.co/dataset/x", resource_urls=["a", "b"],
        data_cutoff="2025-06", rows=rows, unit="unknown",
        ingested_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_missing_database_returns_no_sources(tmp_path):
    assert DuckDBStore(tmp_path / "none.duckdb").read_source_metadata() == []


def test_metadata_round_trip_and_replace(tmp_path):
    store = DuckDBStore(tmp_path / "db.duckdb")

    store.write_source_metadata(metadata(rows=10))
    store.write_source_metadata(metadata(rows=18))  # re-ingestion replaces the record

    assert store.read_source_metadata() == [metadata(rows=18)]


def test_blank_values_are_stored_as_null(tmp_path):
    store = DuckDBStore(tmp_path / "db.duckdb")
    frame = pd.DataFrame({"value": pd.array([1.5, None], dtype="Float64"),
                          "mixed": [1, "a"]})

    store.write_table("example", frame)
    stored = store.read_table("example")

    assert stored["value"].isna().tolist() == [False, True]
    assert stored["mixed"].tolist() == ["1", "a"]


def test_metadata_without_portal_url_and_with_origin_note(tmp_path):
    store = DuckDBStore(tmp_path / "db.duckdb")
    curated = replace(metadata("POAI"), portal_url=None, origin_note="Archivo de la Alcaldía")

    store.write_source_metadata(curated)

    assert store.read_source_metadata() == [curated]


def test_old_metadata_table_without_origin_note_is_read_and_migrated(tmp_path):
    path = tmp_path / "old.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            "CREATE TABLE source_metadata (source_id VARCHAR PRIMARY KEY, title VARCHAR, "
            "table_name VARCHAR, portal_url VARCHAR, resource_urls VARCHAR[], "
            "data_cutoff VARCHAR, rows BIGINT, unit VARCHAR, ingested_at TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO source_metadata VALUES ('F2', 't', 'f2_pqrs', 'u', ['a'], '2026', 1, "
            "NULL, TIMESTAMP '2026-01-01')"
        )
    store = DuckDBStore(path)

    assert store.read_source_metadata()[0].origin_note is None  # API keeps working
    store.write_source_metadata(metadata("POAI"))
    store.delete_source_metadata(["F2"])
    assert [m.source_id for m in store.read_source_metadata()] == ["POAI"]


def test_relational_model_is_written_atomically(tmp_path):
    store = DuckDBStore(tmp_path / "db.duckdb")

    # The views need the whole model: with a single table their creation fails...
    with pytest.raises(duckdb.Error):
        store.write_relational_model({"poai": pd.DataFrame({"id_meta": [1]})})

    # ...and nothing is left behind.
    with duckdb.connect(str(tmp_path / "db.duckdb")) as connection:
        tables = connection.execute("SELECT table_name FROM information_schema.tables").fetchall()
    assert ("poai",) not in tables


def test_data_version_round_trip_and_drop_tables(tmp_path):
    store = DuckDBStore(tmp_path / "db.duckdb")
    assert store.read_data_version() is None

    version = DataVersion(2, "abc", datetime(2026, 1, 1, tzinfo=UTC))
    store.write_data_version(version)
    store.write_data_version(version)  # replaces, never accumulates
    store.write_table("f2_pqrs", pd.DataFrame({"a": [1]}))
    store.drop_tables(["f2_pqrs", "never_existed"])

    assert store.read_data_version() == version
    with pytest.raises(duckdb.Error):
        store.read_table("f2_pqrs")
