import pandas as pd

from app.ingestion import pqrs


def test_keeps_only_san_cristobal_rows(pqrs_bytes):
    frame = pqrs.parse_pqrs(pqrs_bytes)

    # 3 San Cristóbal rows (one spelled with accents); the Usme row is dropped.
    assert len(frame) == 3
    assert "20254200000078" not in set(frame["radicado"])


def test_personal_data_columns_are_never_kept(pqrs_bytes):
    frame = pqrs.parse_pqrs(pqrs_bytes)

    assert not any(column.startswith("observacion") for column in frame.columns)
    assert "usuario_actual" not in frame.columns
    assert "nombre_localidad" not in frame.columns
    all_values = frame.to_csv(index=False)
    for fake_pii in ("Juana", "1012345678", "3001234567", "ana@example.com", "jperez"):
        assert fake_pii not in all_values


def test_parses_dates_and_computes_calendar_response_days(pqrs_bytes):
    frame = pqrs.parse_pqrs(pqrs_bytes).set_index("radicado")

    first = frame.loc["20254200000012"]
    assert first["filed_at"] == pd.Timestamp("2025-01-02 08:15:00")
    assert first["response_days"] == 8
    assert first["legal_term_days"] == 15
    assert first["vigencia"] == 2025


def test_negative_response_time_becomes_null_but_row_is_kept(pqrs_bytes):
    frame = pqrs.parse_pqrs(pqrs_bytes).set_index("radicado")

    answered_before_filed = frame.loc["20254200000034"]
    assert pd.isna(answered_before_filed["response_days"])
    assert answered_before_filed["subtema"] == "OBRAS"


def test_unanswered_request_has_null_response(pqrs_bytes):
    frame = pqrs.parse_pqrs(pqrs_bytes).set_index("radicado")

    assert pd.isna(frame.loc["20254200000056", "answered_at"])
    assert pd.isna(frame.loc["20254200000056", "response_days"])


def test_cutoff_is_latest_filing_date(pqrs_bytes):
    assert pqrs.data_cutoff(pqrs.parse_pqrs(pqrs_bytes)) == "2026-03-15"
