"""F3 - Presupuestos Participativos (Secretaría Distrital de Planeación).

Two ODS files are used: progress of the prioritized proposals and the budget committed to them.
Only the FIRST sheet has data; the files also carry dozens of empty junk sheets.
"""

import io
import re
from datetime import datetime

import pandas as pd

from app.ingestion.text import normalize_column, normalize_label

SAN_CRISTOBAL_CODE = 4
PROGRESS_KEYWORD = "avance_propuestas_priorizadas"
COMMITMENTS_KEYWORD = "presupuesto_comprometido"


def pick_resource(resources: list[dict], keyword: str) -> dict:
    """First resource whose URL contains `keyword` and is not a metadata file."""
    for resource in resources:
        url = resource.get("url", "").lower()
        if keyword in url and "metadata" not in url:
            return resource
    raise LookupError(f"No resource URL contains '{keyword}'")


def read_first_sheet(raw: bytes) -> pd.DataFrame:
    """Read only the first sheet of an ODS file and normalize its column names."""
    frame = pd.read_excel(io.BytesIO(raw), sheet_name=0, engine="odf")
    frame.columns = [normalize_column(column) for column in frame.columns]
    return frame


def filter_locality(frame: pd.DataFrame, code: int = SAN_CRISTOBAL_CODE) -> pd.DataFrame:
    """Keep one locality and unify sector labels.

    The 2025 records write 'Cultura, recreación y deporte' and the 2026 ones
    'CULTURA, RECREACIÓN Y DEPORTE'; without normalization the same sector appears twice.
    """
    locality = pd.to_numeric(frame["no_localidad"], errors="coerce")
    rows = frame[locality == code].copy()
    if "sector" in rows.columns:
        rows["sector"] = rows["sector"].map(normalize_label, na_action="ignore")
    return rows.reset_index(drop=True)


def parse_participatory_file(raw: bytes, code: int = SAN_CRISTOBAL_CODE) -> pd.DataFrame:
    """Bytes of one ODS resource -> cleaned rows of one locality."""
    return filter_locality(read_first_sheet(raw), code)


def cutoff_from_url(url: str) -> str | None:
    """The data cutoff is embedded in the file URL as dd-mm-yyyy; return it as 'YYYY-MM-DD'."""
    match = re.search(r"(\d{2}-\d{2}-\d{4})", url)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%d-%m-%Y").date().isoformat()
