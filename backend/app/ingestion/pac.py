"""F1 - PAC execution of the Fondos de Desarrollo Local (Secretaría Distrital de Hacienda).

The portal publishes one CSV per month. Each file is a printed *report*, not a clean table:
decorative header rows, `;` delimiter, latin-1 encoding, `.` thousands separator, percentages
as text ('99%'), a 'Total' row and, in some files, junk footer tables.
"""

import csv
import io
import re

import pandas as pd

from app.ingestion.text import strip_accents

MONTHS = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6, "JULIO": 7,
    "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12,
}
EXPECTED_LOCALITIES = 20
SAN_CRISTOBAL_CODE = "0004-01"
VALUE_UNIT = "unknown (likely millions of COP)"
ENTITY_CODE = re.compile(r"\d{4}-\d{2}")
NUMERIC_COLUMNS = [
    "pac_programmed", "pac_executed", "pct_executed_reported", "pct_deviation_reported",
]


class PacValidationError(ValueError):
    """Raised when the parsed PAC data breaks an invariant (e.g. a month without 20 localities)."""


def select_monthly_resources(resources: list[dict]) -> list[dict]:
    """Keep the monthly CSV resources of the dataset, dropping the 'Metadata' file."""
    return [
        resource for resource in resources
        if resource.get("format", "").upper() == "CSV"
        and "metadata" not in resource.get("name", "").lower()
    ]


def decode(raw: bytes) -> str:
    """Decode as UTF-8 (with or without BOM), falling back to latin-1."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def to_number(value: str | None) -> float | None:
    """Parse ' 7.980 ' -> 7980.0 and '99%' -> 99.0. Blank or invalid -> None (never imputed)."""
    text = (value or "").strip().replace("%", "").replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def to_ratio(value: str | None) -> float | None:
    """Parse a percentage cell: '99%' -> 0.99. Blank -> None."""
    number = to_number(value)
    return None if number is None else number / 100


def find_period(rows: list[list[str]], fallback_name: str) -> tuple[int, int]:
    """Return (year, month) from a header row like ';MES:;JUNIO;;AÑO;2025' or the resource name."""
    for row in rows[:12]:
        joined = strip_accents(" ".join(row)).upper()
        if "MES" in joined:
            month = _find_month(joined)
            year = re.search(r"20\d{2}", joined)
            if month and year:
                return int(year.group()), month
    name = strip_accents(fallback_name).upper()
    month = _find_month(name)
    year = re.search(r"20\d{2}", name)
    if not (month and year):
        raise PacValidationError(f"Cannot find the month/year of PAC file '{fallback_name}'")
    return int(year.group()), month


def _find_month(text: str) -> int | None:
    return next((number for name, number in MONTHS.items() if name in text), None)


def parse_pac_file(raw: bytes, resource_name: str) -> pd.DataFrame:
    """Parse one monthly PAC report into one row per locality (entity)."""
    text = decode(raw)
    delimiter = ";" if text.count(";") > text.count(",") else ","
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    year, month = find_period(rows, resource_name)

    header_index = next(
        (i for i, row in enumerate(rows)
         if any(strip_accents(cell).strip().upper() == "CODIGO" for cell in row)),
        None,
    )
    if header_index is None:
        raise PacValidationError(f"No 'CÓDIGO' header row in PAC file '{resource_name}'")
    header = [strip_accents(cell).strip().upper() for cell in rows[header_index]]
    code_col = header.index("CODIGO")
    entity_col = header.index("ENTIDAD")

    records = []
    for row in rows[header_index + 1:]:
        # Keep only entity rows like '0004-01': skips blanks, the 'Total' row and footer tables.
        if len(row) <= entity_col + 4 or not ENTITY_CODE.fullmatch(row[code_col].strip()):
            continue
        records.append({
            "year": year,
            "month": month,
            "entity_code": row[code_col].strip(),
            "locality": strip_accents(row[entity_col]).strip(),
            "pac_programmed": to_number(row[entity_col + 1]),
            "pac_executed": to_number(row[entity_col + 2]),
            "pct_executed_reported": to_ratio(row[entity_col + 3]),
            "pct_deviation_reported": to_ratio(row[entity_col + 4]),
        })
    if not records:
        raise PacValidationError(f"No locality rows found in PAC file '{resource_name}'")
    # Nullable floats keep blank cells as real NULLs (also once stored in DuckDB).
    frame = pd.DataFrame.from_records(records)
    return frame.astype({column: "Float64" for column in NUMERIC_COLUMNS})


def combine_months(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Join monthly frames, validate 20 localities per month and add derived columns."""
    pac = pd.concat(frames, ignore_index=True)
    per_month = pac.groupby(["year", "month"]).size()
    wrong = per_month[per_month != EXPECTED_LOCALITIES]
    if not wrong.empty:
        detail = {f"{year}-{month:02d}": int(count) for (year, month), count in wrong.items()}
        raise PacValidationError(
            f"Months without exactly {EXPECTED_LOCALITIES} localities: {detail}"
        )

    programmed = pac["pac_programmed"].where(pac["pac_programmed"] > 0)
    pac["pct_executed_calc"] = (pac["pac_executed"] / programmed).round(2)
    # 1 = best execution of the month; NA when the source value is blank.
    pac["rank_in_month"] = (
        pac.groupby(["year", "month"])["pct_executed_calc"]
        .rank(ascending=False, method="min")
        .astype("Int64")
    )
    return pac.sort_values(["year", "month", "entity_code"]).reset_index(drop=True)


def select_locality(pac: pd.DataFrame, entity_code: str = SAN_CRISTOBAL_CODE) -> pd.DataFrame:
    """Rows of a single locality, ordered by period."""
    rows = pac[pac["entity_code"] == entity_code]
    return rows.sort_values(["year", "month"]).reset_index(drop=True)


def data_cutoff(pac: pd.DataFrame) -> str:
    """Latest published month as 'YYYY-MM'."""
    year, month = max(zip(pac["year"], pac["month"], strict=True))
    return f"{int(year)}-{int(month):02d}"
