import json
from datetime import UTC, datetime

import pytest

from app.adapters.duckdb import DuckDBStore
from app.application import IngestSources
from app.application.ingest_sources import (
    DATA_VERSION,
    PARTICIPATORY_BUDGET_DATASET_ID,
    is_outdated,
    missing_after_failure,
)
from app.domain import DataVersion
from app.ingestion.pac import VALUE_UNIT
from tests.conftest import PP_COMMITMENTS_URL, FakeCatalog, InMemoryStore
from tests.curated_fixture import write_mini_package

NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


@pytest.fixture
def package(tmp_path):
    return write_mini_package(tmp_path / "curated_data")


def run(catalog, package, sources=None, store=None):
    store = store if store is not None else InMemoryStore()
    report = IngestSources(catalog, store, curated_root=package, clock=lambda: NOW).run(sources)
    return report, store


def test_ingests_every_source_with_metadata(package):
    report, store = run(FakeCatalog(), package)

    assert report.ok
    assert [r.source_id for r in report.results] == ["F1", "F3", "CURADO"]
    assert {"f1_pac_execution", "f3_pp_commitments", "poai", "seguimiento_meta", "pqrs",
            "crp_meta", "meta_ods_relacion"} <= set(store.tables)
    metadata = {m.source_id: m for m in store.read_source_metadata()}
    assert set(metadata) == {"F1", "F3-commitments", "POAI", "PMR", "PP", "CRP", "ODS", "PQRS"}

    f1 = metadata["F1"]
    assert f1.rows == 2  # San Cristóbal, May and June
    assert f1.data_cutoff == "2025-06"
    assert f1.unit == VALUE_UNIT
    assert len(f1.resource_urls) == 2  # the metadata CSV is excluded
    assert f1.portal_url.endswith("e130bb0d-2d92-41c8-b894-8e058519309d")
    assert f1.ingested_at == NOW

    assert metadata["F3-commitments"].rows == 2  # locality 4 only
    assert metadata["F3-commitments"].resource_urls == [PP_COMMITMENTS_URL]

    poai = metadata["POAI"]
    assert poai.portal_url is None
    assert "Alcaldía Local" in poai.origin_note
    assert poai.unit == "COP (pesos colombianos)"
    assert poai.rows == 8
    assert metadata["PQRS"].data_cutoff == "2025-04-01"
    assert metadata["PQRS"].portal_url.endswith("db9d7291-0308-475e-bd81-cd222c13fca4")
    assert metadata["PP"].portal_url.endswith(PARTICIPATORY_BUDGET_DATASET_ID)
    crp = metadata["CRP"]
    assert "presupuesto_comprometido_30-09-2026.ods" in crp.origin_note
    assert crp.resource_urls[-1] == "presupuesto_comprometido_30-09-2026.ods"
    assert crp.rows == 4  # 3 curated lines + 1 portal line of 2026

    assert store.version.schema_version == DATA_VERSION
    assert is_outdated(store, package) is None


def test_curated_report_lists_the_crp_supplement(package):
    report, store = run(FakeCatalog(), package)

    curated = report.results[-1]
    assert curated.tables["crp_meta"] == 4
    assert "1 CRP, 1 líneas, 1 propuestas" in curated.warnings[0]
    lines = store.tables["crp_meta"]
    assert lines.groupby("source")["valor_asignado_pp"].sum().to_dict() == {
        "curated": 3000.0, "portal": 700.0,
    }


def test_retired_portal_tables_and_metadata_are_removed(package):
    store = InMemoryStore()
    store.tables["f2_pqrs"] = store.tables["f3_pp_progress"] = None
    for source_id in ("F2", "F3-progress"):
        store.metadata[source_id] = None

    report, store = run(FakeCatalog(), package, ["CURADO"], store)

    assert report.ok
    assert "f2_pqrs" not in store.tables and "f3_pp_progress" not in store.tables
    assert "F2" not in store.metadata and "F3-progress" not in store.metadata


def test_one_failing_portal_source_does_not_stop_the_others(package):
    report, store = run(FakeCatalog(failing_datasets={PARTICIPATORY_BUDGET_DATASET_ID}), package)

    results = {r.source_id: r for r in report.results}
    assert not report.ok
    assert not results["F3"].ok
    assert "portal unavailable" in results["F3"].error
    assert results["F1"].ok and results["CURADO"].ok
    # Without the portal commitments the curated CRP are loaded alone, with a warning.
    assert any("no se complementaron" in w for w in results["CURADO"].warnings)
    assert set(store.tables["crp_meta"]["source"]) == {"curated"}
    assert missing_after_failure(report, store) == ["F3"]
    assert is_outdated(store, package) == "faltan fuentes del portal: F3-commitments"


def test_failed_download_keeps_previous_table_and_is_not_missing(package):
    _, store = run(FakeCatalog(), package)

    report, store = run(FakeCatalog(failing_datasets={PARTICIPATORY_BUDGET_DATASET_ID}),
                        package, store=store)

    assert not report.ok
    assert missing_after_failure(report, store) == []
    assert set(store.tables["crp_meta"]["source"]) == {"curated", "portal"}


def test_manifest_mismatch_fails_loudly_and_writes_nothing(package):
    path = package / "Carga_Base_POAI_SC" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["totales_poai"]["2026"] = 999
    path.write_text(json.dumps(manifest), encoding="utf-8")

    report, store = run(FakeCatalog(), package, ["CURADO"])

    [result] = report.results
    assert not result.ok
    assert "POAI total 2026: se obtuvo 12000.0, el manifiesto dice 999.0" in result.error
    assert "poai" not in store.tables
    assert store.version is None
    assert missing_after_failure(report, store) == ["CURADO"]


def test_a_broken_monthly_pac_file_is_skipped_with_a_warning(package):
    catalog = FakeCatalog()
    catalog.files["https://example.org/pac_mayo_2025.csv"] = b"not a report"

    report, store = run(catalog, package, ["F1"])

    result = report.results[0]
    assert result.ok
    assert result.tables == {"f1_pac_execution": 1}
    assert any("PAC Mayo 2025" in warning for warning in result.warnings)


def test_runs_only_the_requested_source(package):
    report, store = run(FakeCatalog(), package, ["F3"])

    assert [r.source_id for r in report.results] == ["F3"]
    assert set(store.tables) == {"f3_pp_commitments"}


def test_unknown_source_is_reported_as_failure(package):
    report, _ = run(FakeCatalog(), package, ["F9"])

    assert not report.results[0].ok


def test_is_outdated_reasons(package, tmp_path):
    store = DuckDBStore(tmp_path / "db.duckdb")
    assert "marcador" in is_outdated(store, package)

    IngestSources(FakeCatalog(), store, curated_root=package, clock=lambda: NOW).run()
    assert is_outdated(store, package) is None

    store.write_data_version(DataVersion(DATA_VERSION - 1, "x", NOW))
    assert "versión de datos" in is_outdated(store, package)

    store.write_data_version(DataVersion(DATA_VERSION, "old-fingerprint", NOW))
    assert is_outdated(store, package) == "los archivos de curated_data cambiaron"
