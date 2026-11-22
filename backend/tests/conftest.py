import io
from pathlib import Path

import pandas as pd
import pytest

from app.domain import SourceMetadata

FIXTURES = Path(__file__).parent / "fixtures"


def build_ods(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Write DataFrames as sheets of an in-memory ODS file (like the real F3 files)."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="odf") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    return buffer.getvalue()


def pp_progress_frame() -> pd.DataFrame:
    """Small synthetic 'avance de propuestas priorizadas' sheet with raw column names."""
    return pd.DataFrame({
        "Vigencia Ejecución": [2025, 2026, 2025, 2026],
        "Código Propuestas": [101, 102, 103, 104],
        "No_Localidad": [4, 4, 5, 4],
        "Sector": [
            "Cultura, recreación y deporte",
            "CULTURA, RECREACIÓN  Y DEPORTE",
            "Ambiente",
            "Mujeres",
        ],
        "% de avance  propuesta": [0.5, 1.0, 0.2, 0.0],
    })


def pp_commitments_frame() -> pd.DataFrame:
    return pd.DataFrame({
        "Vigencia Ejecución": [2025, 2026],
        "No_Localidad": [4, 7],
        "Sector": ["Gobierno", "GOBIERNO"],
        "Valor CRP asignado presupuestos participativos": [1000.0, 2000.0],
    })


PP_PROGRESS_URL = (
    "https://datosabiertos.bogota.gov.co/dataset/x/resource/y/download/"
    "avance_propuestas_priorizadas_30-09-2026.ods"
)
PP_COMMITMENTS_URL = (
    "https://datosabiertos.bogota.gov.co/dataset/x/resource/z/download/"
    "presupuesto_comprometido_30-09-2026.ods"
)


class FakeCatalog:
    """In-memory CatalogPort built from the synthetic fixtures. No network."""

    def __init__(self, failing_datasets: set[str] | None = None) -> None:
        self.failing_datasets = failing_datasets or set()
        pac_june = (FIXTURES / "pac_junio_2025.csv").read_bytes()
        pac_may = pac_june.replace(b";MES:;JUNIO;", b";MES:;MAYO;")
        self.files = {
            "https://example.org/pac_mayo_2025.csv": pac_may,
            "https://example.org/pac_junio_2025.csv": pac_june,
            "https://example.org/pqrs.csv": (FIXTURES / "pqrs_sample.csv").read_bytes(),
            PP_PROGRESS_URL: build_ods({
                "Hoja1": pp_progress_frame(),
                "Junk": pd.DataFrame(),  # the real files carry dozens of empty sheets
            }),
            PP_COMMITMENTS_URL: build_ods({"Hoja1": pp_commitments_frame()}),
        }
        self.datasets = {
            "e130bb0d-2d92-41c8-b894-8e058519309d": {
                "title": "Ejecución PAC FDL",
                "resources": [
                    {"name": "PAC Mayo 2025", "format": "CSV",
                     "url": "https://example.org/pac_mayo_2025.csv"},
                    {"name": "PAC Junio 2025", "format": "CSV",
                     "url": "https://example.org/pac_junio_2025.csv"},
                    {"name": "Metadata PAC", "format": "CSV",
                     "url": "https://example.org/metadata.csv"},
                ],
            },
            "db9d7291-0308-475e-bd81-cd222c13fca4": {
                "title": "PQRS SDG",
                "resources": [{"name": "PQRS", "format": "CSV",
                               "url": "https://example.org/pqrs.csv"}],
            },
            "3ded79df-ec9e-4f92-a949-ca8b1ae12d7d": {
                "title": "Presupuestos Participativos",
                "resources": [
                    {"name": "Metadata", "format": "ODS",
                     "url": "https://example.org/avance_propuestas_priorizadas_metadata.ods"},
                    {"name": "Avance", "format": "ODS", "url": PP_PROGRESS_URL},
                    {"name": "Compromisos", "format": "ODS", "url": PP_COMMITMENTS_URL},
                ],
            },
        }

    def get_dataset(self, dataset_id: str) -> dict:
        if dataset_id in self.failing_datasets:
            raise ConnectionError(f"portal unavailable for {dataset_id}")
        return self.datasets[dataset_id]

    def download(self, url: str) -> bytes:
        return self.files[url]


class InMemoryStore:
    """In-memory DataStorePort."""

    def __init__(self, metadata: list[SourceMetadata] | None = None) -> None:
        self.tables: dict[str, pd.DataFrame] = {}
        self.metadata: dict[str, SourceMetadata] = {m.source_id: m for m in metadata or []}

    def write_table(self, name: str, frame: pd.DataFrame) -> None:
        self.tables[name] = frame

    def write_source_metadata(self, metadata: SourceMetadata) -> None:
        self.metadata[metadata.source_id] = metadata

    def read_source_metadata(self) -> list[SourceMetadata]:
        return sorted(self.metadata.values(), key=lambda m: m.source_id)


@pytest.fixture
def pac_bytes() -> bytes:
    return (FIXTURES / "pac_junio_2025.csv").read_bytes()


@pytest.fixture
def pqrs_bytes() -> bytes:
    return (FIXTURES / "pqrs_sample.csv").read_bytes()
