from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SourceMetadata:
    """Traceability record of one ingested table: where it came from and how fresh it is."""

    source_id: str
    title: str
    table_name: str
    portal_url: str
    resource_urls: list[str]
    data_cutoff: str | None
    rows: int
    unit: str | None
    ingested_at: datetime


@dataclass
class SourceResult:
    """Outcome of ingesting one source (F1, F2, F3...)."""

    source_id: str
    ok: bool
    tables: dict[str, int] = field(default_factory=dict)  # table name -> rows written
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class IngestionReport:
    results: list[SourceResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(result.ok for result in self.results)
