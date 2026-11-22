"""Command line entry point.

    python -m app.cli ingest              # all sources
    python -m app.cli ingest --source F1  # a single source
"""

import argparse
import logging
import sys

from app.adapters.ckan import CkanClient
from app.adapters.duckdb import DuckDBStore
from app.application import SOURCE_IDS, IngestSources
from app.config import get_settings
from app.domain import IngestionReport


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", help="Download, clean and store the open-data sources")
    ingest.add_argument("--source", choices=SOURCE_IDS, help="Ingest only this source")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    catalog = CkanClient(
        settings.ckan_api_url,
        cache_dir=settings.raw_cache_dir,
        timeout_seconds=settings.http_timeout_seconds,
    )
    store = DuckDBStore(settings.duckdb_path)
    report = IngestSources(catalog, store).run([args.source] if args.source else None)
    print_report(report)
    print(f"Database: {settings.duckdb_path.resolve()}")
    return 0 if report.ok else 1


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
