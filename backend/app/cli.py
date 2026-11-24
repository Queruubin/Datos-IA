"""Command line entry point.

    python -m app.cli ingest                  # all sources (portal F1, F3 and the curated package)
    python -m app.cli ingest --source F1      # a single source (F1, F3 or CURADO)
    python -m app.cli ingest --if-outdated    # only when the database is missing or outdated
"""

import argparse
import logging
import sys

from app.adapters.ckan import CkanClient
from app.adapters.duckdb import DuckDBStore
from app.application import SOURCE_IDS, IngestSources
from app.application.ingest_sources import is_outdated, missing_after_failure
from app.config import get_settings
from app.domain import IngestionReport


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser(
        "ingest", help="Load the curated package and download the portal sources"
    )
    ingest.add_argument("--source", choices=SOURCE_IDS, help="Ingest only this source")
    ingest.add_argument(
        "--if-outdated",
        action="store_true",
        help="Do nothing when the database already has the current data version",
    )
    args = parser.parse_args(argv)
    # Windows consoles/pipes may not be UTF-8: never crash on an accent or an arrow.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    store = DuckDBStore(settings.duckdb_path)
    print(f"Database: {settings.duckdb_path.resolve()}")

    if args.if_outdated:
        reason = is_outdated(store, settings.curated_data_dir)
        if reason is None:
            print("[OK] Los datos están al día; no se reingiere.")
            return 0
        print(f"[..] Se reingieren los datos: {reason}.")

    catalog = CkanClient(
        settings.ckan_api_url,
        cache_dir=settings.raw_cache_dir,
        timeout_seconds=settings.http_timeout_seconds,
    )
    report = IngestSources(catalog, store, curated_root=settings.curated_data_dir).run(
        [args.source] if args.source else None
    )
    print_report(report)
    if report.ok:
        return 0
    missing = missing_after_failure(report, store)
    if missing:
        print(f"[X] Sin datos utilizables para: {', '.join(missing)}")
        return 1
    print("[!] Algunas descargas fallaron, pero se conservan los datos de la ingesta anterior.")
    return 0


def print_report(report: IngestionReport) -> None:
    for result in report.results:
        status = "OK" if result.ok else "FAILED"
        print(f"[{status}] {result.source_id}")
        for table, rows in result.tables.items():
            print(f"    {table}: {rows} rows")
        for warning in result.warnings:
            print(f"    warning: {warning}")
        if result.error:
            print(f"    error: {result.error}")


if __name__ == "__main__":
    sys.exit(main())
