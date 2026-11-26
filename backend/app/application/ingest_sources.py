"""IngestSources use case: store each source with its metadata.

Sources:
- F1: PAC execution, downloaded from the open-data portal (not in the curated package).
- F3: Presupuestos Participativos commitments (CRP), downloaded from the portal ONLY as the
  source of the CRP lines of vigencias missing from the curated package (2026).
- CURADO: the curated relational package of the team (`curated_data/`): POAI, PMR,
  Presupuestos Participativos, CRP, ODS, PQRS and SECOP II contracts. It is the single source
  of truth for those domains and is validated against its manifests before anything is written.
"""

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import pandas as pd

from app.domain import DataVersion, IngestionReport, SourceMetadata, SourceResult
from app.ingestion import curated, pac, participatory_budget
from app.ports import CatalogPort, DataStorePort

logger = logging.getLogger(__name__)

PORTAL_DATASET_URL = "https://datosabiertos.bogota.gov.co/dataset/{dataset_id}"
PAC_DATASET_ID = "e130bb0d-2d92-41c8-b894-8e058519309d"
PQRS_DATASET_ID = "db9d7291-0308-475e-bd81-cd222c13fca4"
PARTICIPATORY_BUDGET_DATASET_ID = "3ded79df-ec9e-4f92-a949-ca8b1ae12d7d"
CURATED_SOURCE = "CURADO"
SOURCE_IDS = ("F1", "F3", CURATED_SOURCE)
PP_COMMITMENTS_TABLE = "f3_pp_commitments"

# Bump when the tables, views or transformations change: older databases get re-ingested.
DATA_VERSION = 3
# Portal sources the database must hold to be considered complete.
REQUIRED_PORTAL_SOURCES = ("F1", "F3-commitments")
# Sources replaced by the curated package: their tables and metadata are removed.
RETIRED_SOURCES = {"F2": "f2_pqrs", "F3-progress": "f3_pp_progress"}

COP = "COP (pesos colombianos)"


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


@dataclass(frozen=True)
class _CuratedDomain:
    source_id: str
    title: str
    table_name: str  # main table (used to count rows)
    files: tuple[str, ...]  # original files named by the README / manifest
    data_cutoff: str | None
    origin_note: str
    unit: str | None = None
    portal_dataset_id: str | None = None  # only when the data really comes from the portal


CURATED_DOMAINS = (
    _CuratedDomain(
        "POAI", "POAI San Cristóbal 2025–2026 (plan operativo anual de inversiones)", "poai",
        ("POAI_San_Cristobal_2025_Homologado.xlsx", "POAI_San_Cristobal_2026(2).xlsx"),
        None,
        "Archivo POAI entregado por la Alcaldía Local, consolidado por el equipo "
        "(curated_data/Carga_Base_POAI_SC). Incluye la corrección de los códigos 22851/22852 y "
        "24953/24954 de 2025. Valores en pesos.",
        unit=COP,
    ),
    _CuratedDomain(
        "PMR", "PMR San Cristóbal: seguimiento de metas (cortes 31-03-2026 y 30-06-2026)",
        "seguimiento_meta",
        ("archivo_plano_pmr_fdl_corte_31_marzo_2026.xlsx",
         "archivo_plano_pmr_fdl_corte_30_junio_2026.xlsx"),
        "2026-06-30",
        "Archivos planos del PMR de los Fondos de Desarrollo Local, consolidados por el equipo "
        "(curated_data/Carga_PMR_SC). Presupuesto 2025 convertido de millones a pesos; el "
        "resto ya venía en pesos aunque el encabezado dijera millones.",
        unit=COP,
    ),
    _CuratedDomain(
        "PP", "Presupuestos Participativos San Cristóbal: propuestas y seguimiento",
        "seguimiento_propuesta",
        ("datos_abiertos_presupuestos_participativos_corte_31-marzo_2026.xlsx",
         "datos_abiertos_avance_propuestas_priorizadas_pp_01-10-2026.ods"),
        "2026-10-01",
        "Archivos del conjunto de Presupuestos Participativos (cortes 31-03-2026 y 01-10-2026), "
        "normalizados por el equipo (curated_data/Carga_PP_SC).",
        portal_dataset_id=PARTICIPATORY_BUDGET_DATASET_ID,
    ),
    _CuratedDomain(
        "CRP", "Compromisos presupuestales (CRP) de Presupuestos Participativos", "crp_meta",
        ("datos_abiertos_presupuesto_comprometido_xmeta_pp_01-10-2026.ods",),
        "2026-10-01",
        "Vigencia 2025: archivo del conjunto de Presupuestos Participativos cargado por el "
        "equipo (curated_data/Carga_CRP_SC). {supplement}",
        unit=COP,
        portal_dataset_id=PARTICIPATORY_BUDGET_DATASET_ID,
    ),
    _CuratedDomain(
        "ODS", "Alineación de metas con los Objetivos de Desarrollo Sostenible (ODS)",
        "meta_ods_relacion",
        ("archivo_plano_ods_fdl_corte_30_junio_2026.xlsx",),
        "2026-06-30",
        "Archivo plano ODS de los Fondos de Desarrollo Local (corte 30-06-2026), consolidado por "
        "el equipo (curated_data/Carga_ODS_SC). Solo la alineación: las cifras vienen del "
        "POAI y del PMR.",
    ),
    _CuratedDomain(
        "PQRS", "PQRS de la Alcaldía Local de San Cristóbal 2022–2026", "pqrs",
        ("pqrs_sdg_2022_2026.csv",),
        None,  # computed: last fecha_registro
        "Archivo PQRS 2022-2026 de la Secretaría Distrital de Gobierno, normalizado por el "
        "equipo (curated_data/Carga_PQRS_SC).",
        portal_dataset_id=PQRS_DATASET_ID,
    ),
    _CuratedDomain(
        "CTR", "Contratos SECOP II vinculados a proyectos y metas (consolidado por el equipo)",
        "contrato",
        (curated.CONTRACTS_FILE,),
        None,  # computed: last signing date
        "Contratos de la Alcaldía Local de San Cristóbal publicados en SECOP II (vigencias 2025 "
        "y 2026), vinculados por el equipo a proyectos, metas y CRP "
        "(curated_data/Carga_Contratos_SC). Valor = valor firmado del contrato (no ejecutado ni "
        "pagado). Parte de los vínculos está pendiente de verificación. No incluye nombres de "
        "contratistas.",
        unit=COP,
    ),
)


class IngestSources:
    """Runs the ingestion of the requested sources.

    Each source is independent: if one fails (network, format change...) the error is recorded in
    the report and the remaining sources are still ingested. The curated package runs last
    because it reads the F3 commitments table for the CRP supplement.
    """

    def __init__(
        self,
        catalog: CatalogPort,
        store: DataStorePort,
        curated_root: Path | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._catalog = catalog
        self._store = store
        self._curated_root = curated_root
        self._clock = clock
        self._ingestors: dict[str, Callable[[], _Output]] = {
            "F1": self._ingest_pac,
            "F3": self._ingest_participatory_budget,
        }

    def run(self, source_ids: Iterable[str] | None = None) -> IngestionReport:
        report = IngestionReport()
        requested = list(source_ids or SOURCE_IDS)
        for source_id in sorted(requested, key=_run_order):
            if source_id == CURATED_SOURCE:
                report.results.append(self._run_curated())
            else:
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

    # --- F3 -------------------------------------------------------------------------------
    def _ingest_participatory_budget(self) -> _Output:
        """Only the commitments file: it feeds the CRP lines missing from the curated package.
        Proposals and their progress come from the curated package."""
        dataset = self._catalog.get_dataset(PARTICIPATORY_BUDGET_DATASET_ID)
        resource = participatory_budget.pick_resource(
            dataset["resources"], participatory_budget.COMMITMENTS_KEYWORD
        )
        raw = self._catalog.download(resource["url"])
        table = _Table(
            source_id="F3-commitments",
            title=f"{dataset['title']} — compromisos (fuente del complemento CRP)",
            table_name=PP_COMMITMENTS_TABLE,
            dataset_id=PARTICIPATORY_BUDGET_DATASET_ID,
            resource_urls=[resource["url"]],
            data_cutoff=participatory_budget.cutoff_from_url(resource["url"]),
            frame=participatory_budget.parse_participatory_file(raw),
        )
        return _Output([table])

    # --- curated package ------------------------------------------------------------------
    def _run_curated(self) -> SourceResult:
        if self._curated_root is None:
            return SourceResult(CURATED_SOURCE, ok=False, error="No curated_data folder set")
        try:
            model = curated.load_curated_package(self._curated_root)
            warnings: list[str] = []
            supplement, source_file = self._crp_supplement(model, warnings)
            self._store.write_relational_model(model.tables)
            now = self._clock()
            for domain in CURATED_DOMAINS:
                self._store.write_source_metadata(
                    self._curated_metadata(domain, model, supplement, source_file, now)
                )
            self._retire_old_sources()
            self._store.write_data_version(DataVersion(
                DATA_VERSION, curated.fingerprint(self._curated_root), now
            ))
        except Exception as error:
            logger.exception("Ingestion of the curated package failed")
            return SourceResult(CURATED_SOURCE, ok=False, error=f"{type(error).__name__}: {error}")
        result = SourceResult(CURATED_SOURCE, ok=True, warnings=warnings)
        result.tables = {name: len(frame) for name, frame in model.tables.items()}
        if supplement is not None:
            result.warnings.insert(0, (
                f"Complemento CRP desde el portal (vigencias {supplement.vigencias}): "
                f"{supplement.crp} CRP, {supplement.lines} líneas, {supplement.proposals} "
                f"propuestas, valor {supplement.value:,.0f} COP."
            ))
        return result

    def _crp_supplement(
        self, model: curated.CuratedModel, warnings: list[str]
    ) -> tuple[curated.CrpSupplement | None, str | None]:
        try:
            portal = self._store.read_table(PP_COMMITMENTS_TABLE)
        except Exception:  # table missing (F3 never ingested)
            warnings.append(
                "No hay compromisos del portal (F3): los CRP de 2026 no se complementaron."
            )
            return None, None
        meta = {m.source_id: m for m in self._store.read_source_metadata()}.get("F3-commitments")
        urls = meta.resource_urls if meta else []
        source_file = PurePosixPath(urlparse(urls[0]).path).name if urls else PP_COMMITMENTS_TABLE
        try:
            supplement = curated.add_portal_crp_supplement(model, portal, source_file)
        except Exception as error:  # e.g. the portal renamed a column: keep the curated data
            logger.exception("CRP supplement failed")
            warnings.append(
                f"No se pudo aplicar el complemento CRP del portal ({type(error).__name__}: "
                f"{error}); se cargan solo los CRP del paquete curado."
            )
            return None, None
        warnings.extend(supplement.issues)
        return supplement, source_file

    def _curated_metadata(
        self,
        domain: _CuratedDomain,
        model: curated.CuratedModel,
        supplement: curated.CrpSupplement | None,
        source_file: str | None,
        now: datetime,
    ) -> SourceMetadata:
        note = domain.origin_note
        files = [*domain.files]
        if domain.source_id == "CRP":
            if supplement is not None and supplement.lines:
                note = note.format(supplement=(
                    f"Vigencia {', '.join(map(str, supplement.vigencias))}: complementada con "
                    f"{supplement.lines} líneas del portal de Datos Abiertos ({source_file}), "
                    "marcadas con source='portal'."
                ))
                files.append(source_file)
            else:
                note = note.format(supplement="Sin complemento del portal.")
        cutoff = domain.data_cutoff
        if domain.source_id == "PQRS":
            cutoff = str(model.tables["pqrs"]["fecha_registro"].max().date())
        elif domain.source_id == "CTR":
            cutoff = str(model.tables["contrato"]["fecha_firma"].max())
        return SourceMetadata(
            source_id=domain.source_id,
            title=domain.title,
            table_name=domain.table_name,
            portal_url=PORTAL_DATASET_URL.format(dataset_id=domain.portal_dataset_id)
            if domain.portal_dataset_id else None,
            resource_urls=files,
            data_cutoff=cutoff,
            rows=len(model.tables[domain.table_name]),
            unit=domain.unit,
            ingested_at=now,
            origin_note=note,
        )

    def _retire_old_sources(self) -> None:
        self._store.drop_tables(RETIRED_SOURCES.values())
        self._store.delete_source_metadata(RETIRED_SOURCES)


def _run_order(source_id: str) -> int:
    return SOURCE_IDS.index(source_id) if source_id in SOURCE_IDS else -1


def is_outdated(store: DataStorePort, curated_root: Path) -> str | None:
    """Why the database must be (re)ingested, or None when it is up to date."""
    version = store.read_data_version()
    if version is None:
        return "la base no tiene marcador de versión (falta el paquete curado)"
    if version.schema_version != DATA_VERSION:
        return f"versión de datos {version.schema_version}, se requiere {DATA_VERSION}"
    if version.curated_fingerprint != curated.fingerprint(curated_root):
        return "los archivos de curated_data cambiaron"
    present = {meta.source_id for meta in store.read_source_metadata()}
    missing = [source for source in REQUIRED_PORTAL_SOURCES if source not in present]
    if missing:
        return f"faltan fuentes del portal: {', '.join(missing)}"
    return None


def missing_after_failure(report: IngestionReport, store: DataStorePort) -> list[str]:
    """Failed sources that left NO usable data behind (a failed re-download keeps the previous
    table). The curated package has no previous fallback: if it fails, it is missing."""
    present = {meta.source_id for meta in store.read_source_metadata()}
    expected = {"F1": ["F1"], "F3": ["F3-commitments"]}
    missing = []
    for result in report.results:
        if result.ok:
            continue
        if result.source_id == CURATED_SOURCE or any(
            source not in present for source in expected.get(result.source_id, [result.source_id])
        ):
            missing.append(result.source_id)
    return missing
