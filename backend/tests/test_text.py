from app.ingestion.text import normalize_column, normalize_label, strip_accents


def test_strip_accents():
    assert strip_accents("San Cristóbal, AÑO, Bolívar") == "San Cristobal, ANO, Bolivar"


def test_normalize_column():
    assert normalize_column("% de avance  propuesta") == "pct_de_avance_propuesta"
    assert normalize_column("Vigencia Ejecución") == "vigencia_ejecucion"
    assert normalize_column(" No_Localidad ") == "no_localidad"


def test_normalize_label_merges_spelling_variants():
    assert normalize_label("Cultura, recreación y deporte") == "CULTURA, RECREACION Y DEPORTE"
    assert normalize_label(" CULTURA,  RECREACIÓN Y DEPORTE ") == "CULTURA, RECREACION Y DEPORTE"
