"""IngestSources use case: download each source, clean it and store it with its metadata."""

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import pandas as pd

from app.domain import IngestionReport, SourceMetadata, SourceResult
from app.ingestion import pac, participatory_budget, pqrs
from app.ports import CatalogPort, DataStorePort

logger = logging.getLogger(__name__)

PORTAL_DATASET_URL = "https://datosabiertos.bogota.gov.co/dataset/{dataset_id}"
PAC_DATASET_ID = "e130bb0d-2d92-41c8-b894-8e058519309d"
PQRS_DATASET_ID = "db9d7291-0308-475e-bd81-cd222c13fca4"
PARTICIPATORY_BUDGET_DATASET_ID = "3ded79df-ec9e-4f92-a949-ca8b1ae12d7d"
SOURCE_IDS = ("F1", "F2", "F3")


@dataclass
class _Table:
    """A cleaned table ready to be stored, with its metadata (minus `rows`/`ingested_at`)."""

    source_id: str
    title: str
    table_name: str
    dataset_id: str
    resource_urls: list[str]
    data_cutoff: str | None
    frame: pd.DataFrame
    unit: str | None = None


@dataclass
class _Output:
    tables: list[_Table]
    warnings: list[str] = field(default_factory=list)


class IngestSources:
    """Runs the ingestion of the requested sources.

    Each source is independent: if one fails (network, format change...) the error is recorded in
    the report and the remaining sources are still ingested.
    """

    def __init__(
        self,
        catalog: CatalogPort,
        store: DataStorePort,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._catalog = catalog
        self._store = store
        self._clock = clock
        self._ingestors: dict[str, Callable[[], _Output]] = {
            "F1": self._ingest_pac,
            "F2": self._ingest_pqrs,
            "F3": self._ingest_participatory_budget,
        }

    def run(self, source_ids: Iterable[str] | None = None) -> IngestionReport:
        report = IngestionReport()
        for source_id in source_ids or SOURCE_IDS:
            report.results.append(self._run_one(source_id))
        return report

    def _run_one(self, source_id: str) -> SourceResult:
        ingestor = self._ingestors.get(source_id)
        if ingestor is None:
            return SourceResult(source_id, ok=False, error=f"Unknown source '{source_id}'")
        try:
            # Build every table first, so a failure never leaves a source half-written.
            output = ingestor()
            result = SourceResult(source_id, ok=True, warnings=output.warnings)
            for table in output.tables:
                self._store.write_table(table.table_name, table.frame)
                self._store.write_source_metadata(self._metadata(table))
                result.tables[table.table_name] = len(table.frame)
            return result
        except Exception as error:  # one failing source must not abort the others
            logger.exception("Ingestion of %s failed", source_id)
            return SourceResult(source_id, ok=False, error=f"{type(error).__name__}: {error}")

    def _metadata(self, table: _Table) -> SourceMetadata:
        return SourceMetadata(
            source_id=table.source_id,
            title=table.title,
            table_name=table.table_name,
            portal_url=PORTAL_DATASET_URL.format(dataset_id=table.dataset_id),
            resource_urls=table.resource_urls,
            data_cutoff=table.data_cutoff,
            rows=len(table.frame),
            unit=table.unit,
            ingested_at=self._clock(),
        )

    # --- F1 -------------------------------------------------------------------------------
    def _ingest_pac(self) -> _Output:
        dataset = self._catalog.get_dataset(PAC_DATASET_ID)
        resources = pac.select_monthly_resources(dataset["resources"])
        frames, warnings, used_urls = [], [], []
        for resource in resources:
            try:
                raw = self._catalog.download(resource["url"])
                frames.append(pac.parse_pac_file(raw, resource["name"]))
                used_urls.append(resource["url"])
            except Exception as error:  # a broken monthly file is reported, not fatal
                warnings.append(f"Skipped PAC file '{resource['name']}': {error}")
        if not frames:
            raise pac.PacValidationError("No PAC file could be parsed")

        all_localities = pac.combine_months(frames)
        san_cristobal = pac.select_locality(all_localities)
        table = _Table(
            source_id="F1",
            title=dataset["title"],
            table_name="f1_pac_execution",
            dataset_id=PAC_DATASET_ID,
            resource_urls=used_urls,
            data_cutoff=pac.data_cutoff(san_cristobal),
            frame=san_cristobal,
            unit=pac.VALUE_UNIT,
        )
        return _Output([table], warnings)

    # --- F2 -------------------------------------------------------------------------------
    def _ingest_pqrs(self) -> _Output:
        dataset = self._catalog.get_dataset(PQRS_DATASET_ID)
        resource = next(r for r in dataset["resources"] if r.get("format", "").upper() == "CSV")
        frame = pqrs.parse_pqrs(self._catalog.download(resource["url"]))
        table = _Table(
            source_id="F2",
            title=dataset["title"],
            table_name="f2_pqrs",
            dataset_id=PQRS_DATASET_ID,
            resource_urls=[resource["url"]],
            data_cutoff=pqrs.data_cutoff(frame),
            frame=frame,
        )
        return _Output([table])

    # --- F3 -------------------------------------------------------------------------------
    def _ingest_participatory_budget(self) -> _Output:
        dataset = self._catalog.get_dataset(PARTICIPATORY_BUDGET_DATASET_ID)
        parts = [
            ("F3-progress", "avance", "f3_pp_progress", participatory_budget.PROGRESS_KEYWORD),
            (
                "F3-commitments", "compromisos", "f3_pp_commitments",
                participatory_budget.COMMITMENTS_KEYWORD,
            ),
        ]
        tables = []
        for source_id, label, table_name, keyword in parts:
            resource = participatory_budget.pick_resource(dataset["resources"], keyword)
            raw = self._catalog.download(resource["url"])
            tables.append(_Table(
                source_id=source_id,
                title=f"{dataset['title']} — {label}",
                table_name=table_name,
                dataset_id=PARTICIPATORY_BUDGET_DATASET_ID,
                resource_urls=[resource["url"]],
                data_cutoff=participatory_budget.cutoff_from_url(resource["url"]),
                frame=participatory_budget.parse_participatory_file(raw),
            ))
        return _Output(tables)
