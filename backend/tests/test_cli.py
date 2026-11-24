import pytest

from app import cli
from app.adapters.duckdb import DuckDBStore
from app.config import Settings
from tests.conftest import FakeCatalog
from tests.curated_fixture import write_mini_package


@pytest.fixture
def settings(tmp_path, monkeypatch):
    settings = Settings(
        _env_file=None,
        data_dir=tmp_path / "data",
        duckdb_path=tmp_path / "data" / "db.duckdb",
        curated_data_dir=write_mini_package(tmp_path / "curated_data"),
    )
    monkeypatch.setattr(cli, "get_settings", lambda: settings)
    return settings


def use_catalog(monkeypatch, catalog):
    downloads = []

    def factory(*args, **kwargs):
        downloads.append(args)
        return catalog

    monkeypatch.setattr(cli, "CkanClient", factory)
    return downloads


def test_if_outdated_ingests_a_missing_database(settings, monkeypatch, capsys):
    use_catalog(monkeypatch, FakeCatalog())

    assert cli.main(["ingest", "--if-outdated"]) == 0

    output = capsys.readouterr().out
    assert "Se reingieren los datos" in output
    assert "[OK] CURADO" in output
    assert DuckDBStore(settings.duckdb_path).read_data_version() is not None


def test_if_outdated_does_nothing_when_up_to_date(settings, monkeypatch, capsys):
    use_catalog(monkeypatch, FakeCatalog())
    assert cli.main(["ingest"]) == 0
    capsys.readouterr()

    downloads = use_catalog(monkeypatch, None)  # any portal access would fail
    assert cli.main(["ingest", "--if-outdated"]) == 0

    assert "al día" in capsys.readouterr().out
    assert downloads == []


def test_if_outdated_reingests_when_curated_files_change(settings, monkeypatch, capsys):
    use_catalog(monkeypatch, FakeCatalog())
    assert cli.main(["ingest"]) == 0
    path = settings.curated_data_dir / "Carga_ODS_SC" / "csv" / "ods.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    capsys.readouterr()

    assert cli.main(["ingest", "--if-outdated"]) == 0

    assert "curated_data cambiaron" in capsys.readouterr().out


def test_portal_failure_keeps_previous_data_and_exits_zero(settings, monkeypatch, capsys):
    use_catalog(monkeypatch, FakeCatalog())
    assert cli.main(["ingest"]) == 0

    use_catalog(monkeypatch, FakeCatalog(failing_datasets={
        "e130bb0d-2d92-41c8-b894-8e058519309d", "3ded79df-ec9e-4f92-a949-ca8b1ae12d7d",
    }))
    assert cli.main(["ingest"]) == 0
    assert "se conservan los datos" in capsys.readouterr().out


def test_first_run_without_portal_fails(settings, monkeypatch, capsys):
    use_catalog(monkeypatch, FakeCatalog(failing_datasets={
        "e130bb0d-2d92-41c8-b894-8e058519309d",
    }))

    assert cli.main(["ingest", "--if-outdated"]) == 1
    assert "Sin datos utilizables para: F1" in capsys.readouterr().out
