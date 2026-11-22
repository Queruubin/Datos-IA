from datetime import UTC, datetime

from app.application import IngestSources
from app.application.ingest_sources import PQRS_DATASET_ID
from app.ingestion.pac import VALUE_UNIT
from tests.conftest import PP_PROGRESS_URL, FakeCatalog, InMemoryStore

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


def run(catalog, sources=None):
    store = InMemoryStore()
    report = IngestSources(catalog, store, clock=lambda: NOW).run(sources)
    return report, store


def test_ingests_every_source_with_metadata():
    report, store = run(FakeCatalog())

    assert report.ok
    assert set(store.tables) == {
        "f1_pac_execution", "f2_pqrs", "f3_pp_progress", "f3_pp_commitments",
    }
    metadata = {m.source_id: m for m in store.read_source_metadata()}
    assert set(metadata) == {"F1", "F2", "F3-progress", "F3-commitments"}

    f1 = metadata["F1"]
    assert f1.rows == 2  # San Cristóbal, May and June
    assert f1.data_cutoff == "2025-06"
    assert f1.unit == VALUE_UNIT
    assert len(f1.resource_urls) == 2  # the metadata CSV is excluded
    assert f1.portal_url.endswith("e130bb0d-2d92-41c8-b894-8e058519309d")
    assert f1.ingested_at == NOW

    assert metadata["F2"].rows == 3
    assert metadata["F2"].data_cutoff == "2026-03-15"
    assert metadata["F3-progress"].rows == 3
    assert metadata["F3-progress"].resource_urls == [PP_PROGRESS_URL]
    assert metadata["F3-progress"].data_cutoff == "2026-09-30"
    assert metadata["F3-commitments"].rows == 1


def test_one_failing_source_does_not_stop_the_others():
    report, store = run(FakeCatalog(failing_datasets={PQRS_DATASET_ID}))

    results = {r.source_id: r for r in report.results}
    assert not report.ok
    assert not results["F2"].ok
    assert "portal unavailable" in results["F2"].error
    assert results["F1"].ok and results["F3"].ok
    assert "f2_pqrs" not in store.tables
    assert {"f1_pac_execution", "f3_pp_progress", "f3_pp_commitments"} <= set(store.tables)


def test_a_broken_monthly_pac_file_is_skipped_with_a_warning():
    catalog = FakeCatalog()
    catalog.files["https://example.org/pac_mayo_2025.csv"] = b"not a report"

    report, store = run(catalog, ["F1"])

    result = report.results[0]
    assert result.ok
    assert result.tables == {"f1_pac_execution": 1}
    assert any("PAC Mayo 2025" in warning for warning in result.warnings)


def test_runs_only_the_requested_source():
    report, store = run(FakeCatalog(), ["F3"])

    assert [r.source_id for r in report.results] == ["F3"]
    assert set(store.tables) == {"f3_pp_progress", "f3_pp_commitments"}


def test_unknown_source_is_reported_as_failure():
    report, _ = run(FakeCatalog(), ["F9"])

    assert not report.results[0].ok
