import pandas as pd
import pytest

from app.ingestion import pac


def test_keeps_only_the_20_locality_rows(pac_bytes):
    frame = pac.parse_pac_file(pac_bytes, "any name")

    # The 'Total' row, blank rows and the junk footer table are skipped.
    assert len(frame) == 20
    assert frame["entity_code"].str.fullmatch(r"\d{4}-\d{2}").all()
    assert "Total" not in set(frame["locality"])


def test_reads_period_from_the_header_row(pac_bytes):
    frame = pac.parse_pac_file(pac_bytes, "Ranking Enero 2024")  # header wins over the name

    assert set(zip(frame["year"], frame["month"], strict=True)) == {(2025, 6)}


def test_falls_back_to_the_resource_name_for_the_period(pac_bytes):
    without_period = pac_bytes.replace(b";MES:;JUNIO;;A\xd1O;2025", b";;;;;")

    frame = pac.parse_pac_file(without_period, "Ranking mensual PAC-FDL. Diciembre 2024. Bogotá")

    assert set(zip(frame["year"], frame["month"], strict=True)) == {(2024, 12)}


def test_parses_numbers_percentages_and_latin1_accents(pac_bytes):
    frame = pac.parse_pac_file(pac_bytes, "x").set_index("entity_code")

    san_cristobal = frame.loc["0004-01"]
    assert san_cristobal["pac_programmed"] == 7980.0
    assert san_cristobal["pac_executed"] == 7939.0
    assert san_cristobal["pct_executed_reported"] == pytest.approx(0.99)
    assert frame.loc["0009-01", "locality"] == "Fontibon"
    assert frame.loc["0001-01", "locality"] == "Usaquen"


def test_blank_cell_stays_null_and_is_not_imputed(pac_bytes):
    frame = pac.parse_pac_file(pac_bytes, "x").set_index("entity_code")

    kennedy = frame.loc["0008-01"]
    assert pd.isna(kennedy["pac_executed"])
    assert kennedy["pct_executed_reported"] == pytest.approx(1.05)  # reported value is kept


def test_to_number_helpers():
    assert pac.to_number(" 7.980 ") == 7980.0
    assert pac.to_number("") is None
    assert pac.to_ratio("99%") == pytest.approx(0.99)
    assert pac.to_ratio(" ") is None


def test_combine_months_adds_rank_and_keeps_blank_rank_null(pac_bytes):
    june = pac.parse_pac_file(pac_bytes, "x")
    combined = pac.combine_months([june])

    by_code = combined.set_index("entity_code")
    assert by_code.loc["0001-01", "rank_in_month"] == 1  # 100% execution
    assert pd.isna(by_code.loc["0008-01", "pct_executed_calc"])
    assert pd.isna(by_code.loc["0008-01", "rank_in_month"])


def test_combine_months_rejects_a_month_without_20_localities(pac_bytes):
    june = pac.parse_pac_file(pac_bytes, "x")

    with pytest.raises(pac.PacValidationError, match="2025-06"):
        pac.combine_months([june.iloc[:19]])


def test_select_san_cristobal_and_cutoff(pac_bytes):
    may = pac.parse_pac_file(pac_bytes.replace(b"JUNIO", b"MAYO"), "x")
    june = pac.parse_pac_file(pac_bytes, "x")

    san_cristobal = pac.select_locality(pac.combine_months([june, may]))

    assert list(san_cristobal["month"]) == [5, 6]
    assert set(san_cristobal["entity_code"]) == {"0004-01"}
    assert pac.data_cutoff(san_cristobal) == "2025-06"


def test_select_monthly_resources_excludes_metadata():
    resources = [
        {"name": "PAC Junio 2025", "format": "CSV", "url": "a"},
        {"name": "Metadata Ranking PAC", "format": "CSV", "url": "b"},
        {"name": "Algo", "format": "PDF", "url": "c"},
    ]

    assert [r["url"] for r in pac.select_monthly_resources(resources)] == ["a"]
