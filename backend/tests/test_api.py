from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.main import create_app
from app.domain import SourceMetadata
from tests.conftest import InMemoryStore


def test_health():
    client = TestClient(create_app(store=InMemoryStore()))

    assert client.get("/health").json() == {"status": "ok"}


def test_sources_include_data_cutoff():
    store = InMemoryStore([
        SourceMetadata(
            source_id="F1", title="PAC FDL", table_name="f1_pac_execution",
            portal_url="https://datosabiertos.bogota.gov.co/dataset/e130", resource_urls=["u"],
            data_cutoff="2025-06", rows=18, unit="unknown (likely millions of COP)",
            ingested_at=datetime(2026, 11, 22, tzinfo=UTC),
        )
    ])
    client = TestClient(create_app(store=store))

    response = client.get("/api/sources")

    assert response.status_code == 200
    [source] = response.json()
    assert source["source_id"] == "F1"
    assert source["data_cutoff"] == "2025-06"
    assert source["rows"] == 18


def test_sources_empty_before_ingestion():
    client = TestClient(create_app(store=InMemoryStore()))

    assert client.get("/api/sources").json() == []
