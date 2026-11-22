"""F2 - PQRS (petitions, complaints, claims) of the Secretaría Distrital de Gobierno 2022-2026.

Privacy: free-text columns (OBSERVACION_*) and internal-user columns may contain personal data.
They are never loaded: only the columns in KEEP_COLUMNS are read from the CSV.
"""

import io

import pandas as pd

from app.ingestion.text import normalize_column, normalize_label

KEEP_COLUMNS = [
    "RADICADO", "VIGENCIA", "MES_REGISTRO", "RADI_FECH_RADI", "FECHA_RESPUESTA", "MEDIO_RECEPCION",
    "TIPO_PETICION", "TIEMPO_TRAMITE", "ESTADO_ORFEO", "SUBTEMA", "ULTIMA_DEPENDENCIA",
]
LOCALITY_COLUMN = "NOMBRE_LOCALIDAD"
SAN_CRISTOBAL = "SAN CRISTOBAL"
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"


def parse_pqrs(raw: bytes, locality: str = SAN_CRISTOBAL) -> pd.DataFrame:
    """Read the PQRS CSV, keep one locality and the allowed columns, and derive response times.

    - `legal_term_days`: legal term in *business* days (TIEMPO_TRAMITE). On-time compliance is
      not computed yet: it needs a business-day calendar with Colombian holidays.
    - `response_days`: answered_at - filed_at in *calendar* days. Negative values are source
      errors and become null (the row itself is kept).
    """
    frame = pd.read_csv(
        io.BytesIO(raw),
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        usecols=[*KEEP_COLUMNS, LOCALITY_COLUMN],
    )
    in_locality = frame[LOCALITY_COLUMN].fillna("").map(normalize_label).str.contains(locality)
    pqrs = frame.loc[in_locality, KEEP_COLUMNS].copy()
    pqrs.columns = [normalize_column(column) for column in pqrs.columns]
    for column in pqrs.columns:
        pqrs[column] = pqrs[column].str.strip()

    pqrs["filed_at"] = _to_datetime(pqrs.pop("radi_fech_radi"))
    pqrs["answered_at"] = _to_datetime(pqrs.pop("fecha_respuesta"))
    pqrs["vigencia"] = pd.to_numeric(pqrs["vigencia"], errors="coerce").astype("Int64")
    pqrs["legal_term_days"] = pd.to_numeric(pqrs.pop("tiempo_tramite"), errors="coerce").astype(
        "Int64"
    )
    response_days = (pqrs["answered_at"] - pqrs["filed_at"]).dt.days.astype("Int64")
    pqrs["response_days"] = response_days.mask(response_days < 0)
    return pqrs.reset_index(drop=True)


def _to_datetime(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, format=DATE_FORMAT, errors="coerce")


def data_cutoff(pqrs: pd.DataFrame) -> str | None:
    """Most recent filing date as 'YYYY-MM-DD'."""
    latest = pqrs["filed_at"].max()
    return None if pd.isna(latest) else latest.date().isoformat()
