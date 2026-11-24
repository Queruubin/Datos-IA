import json
from pathlib import Path

import pytest

from app.config import REPO_ROOT
from app.ingestion import curated
from tests.curated_fixture import OFFICIAL_NAME, portal_commitments_frame, write_mini_package


@pytest.fixture
def package(tmp_path):
    return write_mini_package(tmp_path / "curated_data")


@pytest.fixture
def model(package):
    return curated.load_curated_package(package)


def test_builds_every_table_of_the_physical_model(model):
    assert set(model.tables) == set(curated.MODEL_TABLES)
    meta = model.tables["meta_proyecto"].set_index("codigo_meta_extendida")
    sectors = model.tables["sector"].set_index("id_sector")["nombre_sector"]
    # Natural keys kept, surrogate ids generated.
    assert list(meta.index) == ["22511", "22512", "25021", "25022"]
    assert list(meta["id_meta"]) == [1, 2, 3, 4]
    # The sector depends on the meta: project 2502 has two sectors.
    assert sectors[meta.at["25021", "id_sector"]] == "AMBIENTE"
    assert sectors[meta.at["25022", "id_sector"]] == "MOVILIDAD"
    # Entidad is nullable: never invented for metas without one.
    assert meta["id_entidad"].isna().tolist() == [False, False, False, True]


def test_poai_2025_swapped_codes_are_corrected(model):
    poai = model.tables["poai"].merge(model.tables["meta_proyecto"], on="id_meta")
    year = poai[poai["vigencia"] == 2025].set_index("codigo_meta_extendida")

    assert year.at["22511", "valor_poai"] == 1000
    assert year.at["22511", "magnitud_programada"] == 30
    assert year.at["22512", "valor_poai"] == 2000
    assert year["porcentaje_recursos_poai"].sum() == pytest.approx(1.0)
    assert year.at["22511", "porcentaje_recursos_poai"] == pytest.approx(0.1)


def test_crp_lines_keep_repeated_pairs_and_relations_are_unique(model):
    lines = model.tables["crp_meta"]
    assert len(lines) == 3
    assert lines.groupby(["id_crp", "id_meta"]).size().max() == 2
    assert set(lines["source"]) == {"curated"}
    assert not model.tables["crp_propuesta"].duplicated(["id_crp", "id_propuesta"]).any()


def test_pqrs_keeps_usuario_actual_in_the_table_only(model):
    pqrs = model.tables["pqrs"]
    assert OFFICIAL_NAME in set(pqrs["usuario_actual"])  # loaded, never exposed by tools
    assert pqrs["id_tipo_peticion"].isna().sum() == 1


def test_manifest_mismatch_lists_every_problem(package):
    path = package / "Carga_CRP_SC" / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["conteos"]["crp_meta_lineas"] = 2
    manifest["valor_total_crp_pp"] = 1
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(curated.CuratedDataError) as error:
        curated.load_curated_package(package)

    assert "CRP líneas crp_meta: se obtuvo 3, el manifiesto dice 2" in error.value.problems
    assert any(p.startswith("CRP valor total") for p in error.value.problems)


def test_pmr_budget_must_equal_poai(package):
    path = package / "Carga_PMR_SC" / "csv" / "seguimiento_meta_pmr.csv"
    text = path.read_text(encoding="utf-8-sig")
    path.write_text(text.replace("57,2026,2026-06-30,6,0,0,2500", "57,2026,2026-06-30,6,0,0,2600"),
                    encoding="utf-8-sig")

    with pytest.raises(curated.CuratedDataError) as error:
        curated.load_curated_package(package)

    assert any("= POAI 2026" in problem for problem in error.value.problems)


def test_broken_reference_and_missing_file_fail(package):
    path = package / "Carga_PP_SC" / "csv" / "propuesta_ciudadana.csv"
    path.write_text(path.read_text(encoding="utf-8-sig").replace("106,25021", "106,77777"),
                    encoding="utf-8-sig")
    with pytest.raises(curated.CuratedDataError, match="propuesta → meta"):
        curated.load_curated_package(package)

    (package / "Carga_ODS_SC" / "csv" / "ods.csv").unlink()
    with pytest.raises(curated.CuratedDataError, match="Falta el archivo"):
        curated.load_curated_package(package)


def test_portal_supplement_maps_lines_and_reports_unknown_references(model):
    result = curated.add_portal_crp_supplement(
        model, portal_commitments_frame(), "compromisos_30-09-2026.ods"
    )

    assert result.vigencias == [2026]
    assert (result.crp, result.lines, result.proposals, result.value) == (1, 1, 1, 700.0)
    assert any("propuesta 999 no existe" in issue for issue in result.issues)
    assert any("meta 99999 no existe" in issue for issue in result.issues)

    crp = model.tables["crp"]
    added = crp[crp["source"] == "portal"].iloc[0]
    assert (added["numero_crp"], added["vigencia"]) == ("950", 2026)
    assert added["numero_compromiso"] == "628 2026"
    assert added["tipo_compromiso"] == "CONVENIO INTERADMINISTRATIVO"
    assert added["codigo_modalidad"] == "10"
    assert added["source_file"] == "compromisos_30-09-2026.ods"
    lines = model.tables["crp_meta"]
    portal_line = lines[lines["source"] == "portal"].iloc[0]
    assert portal_line["valor_asignado_pp"] == 700.0
    assert portal_line["id_crp"] == added["id_crp"]
    relations = model.tables["crp_propuesta"]
    assert len(relations[relations["source"] == "portal"]) == 1
    # The curated 2025 lines are untouched (the portal 2025 row is ignored).
    assert len(lines[lines["source"] == "curated"]) == 3


def test_supplement_is_empty_when_curated_already_has_the_year(model):
    portal = portal_commitments_frame()
    portal = portal[portal["vigencia_ejecucion"] == 2025]

    result = curated.add_portal_crp_supplement(model, portal, "x.ods")

    assert result.lines == 0 and result.vigencias == []
    assert len(model.tables["crp_meta"]) == 3


def test_fingerprint_changes_with_the_data(package):
    before = curated.fingerprint(package)
    path = package / "Carga_ODS_SC" / "csv" / "ods.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    assert curated.fingerprint(package) != before


REAL_PACKAGE = REPO_ROOT / "curated_data"


@pytest.mark.skipif(not Path(REAL_PACKAGE / "Carga_PQRS_SC").exists(),
                    reason="curated_data not present")
def test_real_package_matches_its_manifests():
    model = curated.load_curated_package(REAL_PACKAGE)

    t = model.tables
    assert len(t["meta_proyecto"]) == 83
    assert len(t["seguimiento_meta"]) == 332
    assert len(t["pqrs"]) == 4026
    assert len(t["crp_meta"]) == 66
    poai = t["poai"]
    assert poai.loc[poai["vigencia"] == 2025, "valor_poai"].sum() == 130_871_828_000
    assert poai.loc[poai["vigencia"] == 2026, "valor_poai"].sum() == 127_690_480_000
    assert curated.poai_pmr_differences(t, 2026) == {"budget": 0, "magnitude": 6}
