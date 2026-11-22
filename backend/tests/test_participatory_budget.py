import pytest

from app.ingestion import participatory_budget as pp
from tests.conftest import build_ods, pp_progress_frame


def test_reads_only_the_first_sheet_and_normalizes_columns():
    raw = build_ods({"Datos": pp_progress_frame(), "Hoja vacia 1": pp_progress_frame().iloc[:0]})

    frame = pp.read_first_sheet(raw)

    assert len(frame) == 4
    assert list(frame.columns) == [
        "vigencia_ejecucion", "codigo_propuestas", "no_localidad", "sector",
        "pct_de_avance_propuesta",
    ]


def test_filters_locality_4():
    frame = pp.parse_participatory_file(build_ods({"Datos": pp_progress_frame()}))

    assert len(frame) == 3
    assert set(frame["no_localidad"]) == {4}


def test_sector_spelling_variants_are_merged():
    frame = pp.parse_participatory_file(build_ods({"Datos": pp_progress_frame()}))

    assert frame["sector"].value_counts().to_dict() == {
        "CULTURA, RECREACION Y DEPORTE": 2,
        "MUJERES": 1,
    }


def test_cutoff_is_read_from_the_url():
    assert pp.cutoff_from_url("https://x/avance_30-09-2026.ods") == "2026-09-30"
    assert pp.cutoff_from_url("https://x/avance.ods") is None


def test_pick_resource_skips_metadata_urls():
    resources = [
        {"url": "https://x/avance_propuestas_priorizadas_metadata.ods"},
        {"url": "https://x/AVANCE_PROPUESTAS_PRIORIZADAS_30-09-2026.ods"},
    ]

    assert pp.pick_resource(resources, pp.PROGRESS_KEYWORD) is resources[1]
    with pytest.raises(LookupError):
        pp.pick_resource(resources, pp.COMMITMENTS_KEYWORD)
