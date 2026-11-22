from datetime import UTC, datetime

import pandas as pd

from app.adapters.duckdb import DuckDBStore
from app.domain import SourceMetadata


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
