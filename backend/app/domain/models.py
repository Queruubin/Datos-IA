from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SourceMetadata:
    """Traceability record of one ingested table: where it came from and how fresh it is.

    `portal_url` is set only when the data really comes from the open-data portal; curated
    files delivered by the Alcaldía or the team have `portal_url=None` and an `origin_note`."""

    source_id: str
    title: str
    table_name: str
    portal_url: str | None
    resource_urls: list[str]
    data_cutoff: str | None
    rows: int
    unit: str | None
    ingested_at: datetime
    origin_note: str | None = None


@dataclass(frozen=True)
class DataVersion:
    """Marker of what the database holds: the code's schema version and a fingerprint of the
    curated files. A different value means the database is outdated and must be re-ingested."""

    schema_version: int
    curated_fingerprint: str
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
