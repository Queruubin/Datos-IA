"""Curated relational package of San Cristóbal (`curated_data/` at the repository root).

The team delivered seven load folders (POAI, PMR, Presupuestos Participativos, CRP, ODS, PQRS
and SECOP II contracts) with CSVs, a `manifest.json` with the expected results and, for the first
six, PostgreSQL load scripts. This module rebuilds the same tables in memory (pandas), applying
the transformations of those scripts:

- `meta_proyecto.id_sector` (sector depends on the meta, not on the project) and
  `meta_proyecto.id_entidad` (Carga_CRP_SC/sql/00_ajuste_entidad.sql).
- POAI 2025 correction of the swapped codes 22851/22852 and 24953/24954, and recomputation of
  `porcentaje_recursos_poai` (Carga_PMR_SC/sql/00_correccion_integracion_poai_2025.sql).
- PMR rows are linked to the meta by `codigo_indicador`.
- `crp_meta` keeps every source line (also the 4 repeated CRP-meta pairs); `crp_propuesta` keeps
  unique pairs.
- Contracts: the source has one row per contract-(project, meta, CRP) link and repeats the full
  contract value on every row. It is split into `contrato` (one row per contract) and
  `contrato_vinculo` (one row per link). Only whitelisted columns are read: `Contratista`
  (names of natural persons) is never loaded.

Surrogate ids (`id_*`) are generated in file order; natural keys are kept. Every count and total
of the manifests is checked and any mismatch raises `CuratedDataError` (nothing is written).
Pure functions: no database, no network.
"""

import hashlib
import json
import math
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

POAI_DIR = "Carga_Base_POAI_SC"
CRP_DIR = "Carga_CRP_SC"
ODS_DIR = "Carga_ODS_SC"
PMR_DIR = "Carga_PMR_SC"
PP_DIR = "Carga_PP_SC"
PQRS_DIR = "Carga_PQRS_SC"
CONTRACTS_DIR = "Carga_Contratos_SC"
DOMAIN_DIRS = (POAI_DIR, CRP_DIR, ODS_DIR, PMR_DIR, PP_DIR, PQRS_DIR, CONTRACTS_DIR)
CONTRACTS_FILE = "Consulta_agente_San_Cristobal_2025_2026.csv"

SAN_CRISTOBAL_ID = 4
CURATED = "curated"
PORTAL = "portal"
# PMR 2025 budget comes in millions with two decimals: up to $5.000 of rounding vs the POAI.
PMR_2025_ROUNDING_COP = 5000

# Order matters only for readability; every table is replaced at once.
MODEL_TABLES = (
    "localidad", "sector", "objetivo_estrategico", "programa", "proyecto", "entidad",
    "meta_proyecto", "poai", "seguimiento_meta", "propuesta_ciudadana", "seguimiento_propuesta",
    "crp", "crp_meta", "crp_propuesta", "ods", "meta_ods", "meta_ods_relacion",
    "tipo_peticion", "medio_recepcion", "subtema_pqrs", "pqrs", "contrato", "contrato_vinculo",
)

# Contracts file: source column -> table column. Explicit whitelists: any other column (above all
# `Contratista`, names of natural persons) is never read.
CONTRACT_COLUMNS = {
    "ID Contrato": "id_contrato",
    "Referencia del Contrato": "referencia_contrato",
    "Vigencia del contrato": "vigencia",
    "Fecha de Firma": "fecha_firma",
    "Objeto del Contrato": "objeto",
    "Valor del Contrato (COP)": "valor_contrato",
    "Estado Contrato": "estado_contrato",
    "Enlace público del proceso": "url_proceso",
    "Enlace público del contrato": "url_contrato",
    "Registro en Datos Abiertos": "url_datos_abiertos",
}
CONTRACT_LINK_COLUMNS = {
    "ID Contrato": "id_contrato",
    "Código Proyecto": "codigo_proyecto",
    "Vigencia del proyecto": "vigencia_proyecto",
    "Código Meta": "codigo_meta",
    "Número de CRP del vínculo": "numero_crp",
    "Vigencia presupuestal CRP": "vigencia_crp",
    "Estado vínculo proyecto": "estado_vinculo_proyecto",
    "Estado vínculo meta": "estado_vinculo_meta",
    "Motivo de verificación": "motivo_verificacion",
}
LINK_VERIFIED = "Verificado"
LINK_PENDING = "Pendiente de verificación"


class CuratedDataError(ValueError):
    """The curated package is missing files, has broken references or does not match its
    manifests. The message lists every problem found."""

    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = list(problems)
        super().__init__(
            "El paquete curado no supera la validación:\n- " + "\n- ".join(self.problems)
        )


@dataclass
class CuratedModel:
    tables: dict[str, pd.DataFrame]
    manifests: dict[str, dict]


@dataclass
class CrpSupplement:
    """CRP lines of the open-data portal for vigencias absent from the curated CRP load."""

    vigencias: list[int] = field(default_factory=list)
    crp: int = 0
    lines: int = 0
    proposals: int = 0
    value: float = 0.0
    issues: list[str] = field(default_factory=list)


# --- reading ---------------------------------------------------------------------------------
def read_csv(
    root: Path, domain: str, name: str, columns: Iterable[str] | None = None
) -> pd.DataFrame:
    """Read one curated CSV as text. Only empty cells are null (the package already turned
    the source 'NA' into empty cells); every other literal is kept. With `columns`, ONLY those
    columns are read (the others never reach memory)."""
    path = Path(root) / domain / "csv" / name
    if not path.exists():
        raise CuratedDataError([f"Falta el archivo {domain}/csv/{name}"])
    wanted = list(columns) if columns is not None else None
    try:
        frame = pd.read_csv(
            path, encoding="utf-8-sig", dtype=str, keep_default_na=False, na_values=[""],
            usecols=wanted,
        )
    except ValueError as error:  # a whitelisted column is missing
        raise CuratedDataError([f"{domain}/csv/{name}: {error}"]) from error
    return frame.apply(lambda column: column.str.strip())


def read_manifests(root: Path) -> dict[str, dict]:
    manifests = {}
    for domain in DOMAIN_DIRS:
        path = Path(root) / domain / "manifest.json"
        if not path.exists():
            raise CuratedDataError([f"Falta {domain}/manifest.json"])
        manifests[domain] = json.loads(path.read_text(encoding="utf-8-sig"))
    return manifests


def fingerprint(root: Path) -> str:
    """SHA-256 of every CSV and manifest of the package: changes when the team updates data."""
    digest = hashlib.sha256()
    root = Path(root)
    files = sorted(
        [*root.glob("*/csv/*.csv"), *root.glob("*/manifest.json")],
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


# --- building ----------------------------------------------------------------------------------
def load_curated_package(root: Path) -> CuratedModel:
    """Read, transform and validate the whole package. Raises `CuratedDataError`."""
    root = Path(root)
    manifests = read_manifests(root)
    problems: list[str] = []
    tables: dict[str, pd.DataFrame] = {}

    _build_poai(root, tables, problems)
    _apply_poai_2025_correction(root, tables, problems)
    _build_crp(root, tables, problems, before_pp=True)
    _build_ods(root, tables, problems)
    _build_pmr(root, tables, problems)
    _build_pp(root, tables, problems)
    _build_crp(root, tables, problems, before_pp=False)
    _build_pqrs(root, tables, problems)
    _build_contracts(root, tables, problems)
    if problems:
        raise CuratedDataError(problems)

    model = CuratedModel(tables, manifests)
    problems = validate_against_manifests(model, root)
    if problems:
        raise CuratedDataError(problems)
    return model


def _ids(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    frame = frame.reset_index(drop=True)
    frame.insert(0, column, range(1, len(frame) + 1))
    return frame


def _lookup(
    values: pd.Series, mapping: dict, what: str, problems: list[str], nullable: bool = False
) -> pd.Series:
    """Map natural keys to surrogate ids, reporting keys that do not exist."""
    mapped = values.map(mapping)
    missing = values[mapped.isna() & (values.notna() if nullable else True)]
    if len(missing):
        problems.append(f"{what}: {len(missing)} referencias inexistentes "
                        f"({', '.join(sorted(set(map(str, missing)))[:10])})")
    return mapped.astype("Int64")


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="raise").astype("Float64")


def _int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="raise").astype("Int64")


def _bool(series: pd.Series) -> pd.Series:
    return series.map({"True": True, "False": False}, na_action="ignore").astype("boolean")


def _date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%Y-%m-%d", errors="raise").dt.date


def _timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, format="%Y-%m-%d %H:%M:%S", errors="raise")


def _build_poai(root: Path, tables: dict, problems: list[str]) -> None:
    localidad = read_csv(root, POAI_DIR, "localidad.csv")
    localidad["id_localidad"] = _int(localidad["id_localidad"])
    tables["localidad"] = localidad[["id_localidad", "nombre_localidad"]]

    sector = _ids(read_csv(root, POAI_DIR, "sector.csv"), "id_sector")
    tables["sector"] = sector

    objetivo = _ids(read_csv(root, POAI_DIR, "objetivo_estrategico.csv"), "id_objetivo")
    objetivo["codigo_objetivo"] = _int(objetivo["codigo_objetivo"])
    tables["objetivo_estrategico"] = objetivo
    objective_ids = dict(zip(objetivo["codigo_objetivo"], objetivo["id_objetivo"], strict=True))

    programa = _ids(read_csv(root, POAI_DIR, "programa.csv"), "id_programa")
    programa["codigo_objetivo"] = _int(programa["codigo_objetivo"])
    programa["codigo_programa"] = _int(programa["codigo_programa"])
    programa.insert(1, "id_objetivo", _lookup(
        programa["codigo_objetivo"], objective_ids, "programa → objetivo", problems
    ))
    program_ids = {
        (int(o), int(p)): i for o, p, i in zip(
            programa["codigo_objetivo"], programa["codigo_programa"], programa["id_programa"],
            strict=True,
        )
    }
    tables["programa"] = programa[["id_programa", "id_objetivo", "codigo_programa",
                                   "nombre_programa"]]

    proyecto = _ids(read_csv(root, POAI_DIR, "proyecto.csv"), "id_proyecto")
    proyecto["id_localidad"] = _int(proyecto["id_localidad"])
    keys = pd.Series(list(zip(
        _int(proyecto["codigo_objetivo"]).astype(int),
        _int(proyecto["codigo_programa"]).astype(int),
        strict=True,
    )))
    proyecto["id_programa"] = _lookup(keys, program_ids, "proyecto → programa", problems)
    tables["proyecto"] = proyecto[["id_proyecto", "codigo_proyecto", "id_localidad",
                                   "id_programa", "nombre_proyecto"]]
    project_ids = dict(zip(
        proyecto.loc[proyecto["id_localidad"] == SAN_CRISTOBAL_ID, "codigo_proyecto"],
        proyecto.loc[proyecto["id_localidad"] == SAN_CRISTOBAL_ID, "id_proyecto"],
        strict=True,
    ))
    sector_ids = dict(zip(sector["nombre_sector"], sector["id_sector"], strict=True))

    meta = _ids(read_csv(root, POAI_DIR, "meta_proyecto.csv"), "id_meta")
    meta.insert(2, "id_proyecto", _lookup(
        meta.pop("codigo_proyecto"), project_ids, "meta → proyecto", problems
    ))
    meta.insert(3, "id_sector", _lookup(
        meta.pop("nombre_sector"), sector_ids, "meta → sector", problems
    ))
    meta["meta_total_2025_2028"] = _num(meta["meta_total_2025_2028"])
    tables["meta_proyecto"] = meta

    meta_ids = dict(zip(meta["codigo_meta_extendida"], meta["id_meta"], strict=True))
    poai = _ids(read_csv(root, POAI_DIR, "poai.csv"), "id_poai")
    poai.insert(1, "id_meta", _lookup(
        poai.pop("codigo_meta_extendida"), meta_ids, "poai → meta", problems
    ))
    poai["vigencia"] = _int(poai["vigencia"])
    for column in ("recurso_indicativo", "porcentaje_plan_plurianual", "magnitud_programada",
                   "valor_poai", "porcentaje_recursos_poai"):
        poai[column] = _num(poai[column])
    poai["tiene_propuesta_pp"] = _bool(poai["tiene_propuesta_pp"])
    poai["fecha_corte"] = pd.to_datetime(poai["fecha_corte"], format="%Y-%m-%d").dt.date
    tables["poai"] = poai


def _apply_poai_2025_correction(root: Path, tables: dict, problems: list[str]) -> None:
    """00_correccion_integracion_poai_2025.sql: fixes only the integrated layer."""
    correction = read_csv(root, PMR_DIR, "correccion_integracion_poai_2025.csv")
    meta = tables["meta_proyecto"]
    meta_ids = dict(zip(meta["codigo_meta_extendida"], meta["id_meta"], strict=True))
    poai = tables["poai"]
    for row in correction.itertuples():
        id_meta = meta_ids.get(row.codigo_meta_pdl)
        target = (poai["id_meta"] == id_meta) & (poai["vigencia"] == 2025)
        if id_meta is None or target.sum() != 1:
            problems.append(f"Corrección POAI 2025: meta {row.codigo_meta_pdl} no encontrada")
            continue
        poai.loc[target, "magnitud_programada"] = float(row.magnitud_correcta_2025)
        poai.loc[target, "valor_poai"] = float(row.valor_correcto_2025)
    year = poai["vigencia"] == 2025
    total = poai.loc[year, "valor_poai"].sum()
    poai.loc[year, "porcentaje_recursos_poai"] = (
        poai.loc[year, "valor_poai"] / total if total else pd.NA
    )


def _build_crp(root: Path, tables: dict, problems: list[str], before_pp: bool) -> None:
    """Entidad must exist before the meta table is final; CRP relations need the proposals."""
    if before_pp:
        entidad = _ids(read_csv(root, CRP_DIR, "entidad.csv"), "id_entidad")
        tables["entidad"] = entidad
        entity_ids = dict(zip(entidad["nombre_entidad"], entidad["id_entidad"], strict=True))
        meta_entidad = read_csv(root, CRP_DIR, "meta_entidad.csv")
        mapping = dict(zip(
            meta_entidad["codigo_meta_extendida"],
            _lookup(meta_entidad["nombre_entidad"], entity_ids, "meta → entidad", problems),
            strict=True,
        ))
        meta = tables["meta_proyecto"]
        unknown = set(mapping) - set(meta["codigo_meta_extendida"])
        if unknown:
            problems.append(f"meta_entidad: metas inexistentes {sorted(unknown)}")
        meta["id_entidad"] = meta["codigo_meta_extendida"].map(mapping).astype("Int64")
        return

    crp = _ids(read_csv(root, CRP_DIR, "crp.csv"), "id_crp")
    crp["vigencia"] = _int(crp["vigencia"])
    crp["fecha_registro"] = _date(crp["fecha_registro"])
    crp["plazo"] = _int(crp["plazo"])
    crp["source"] = CURATED
    crp["source_file"] = f"{CRP_DIR}/csv/crp.csv"
    tables["crp"] = crp
    crp_ids = {
        (n, int(v)): i for n, v, i in zip(crp["numero_crp"], crp["vigencia"], crp["id_crp"],
                                          strict=True)
    }
    meta = tables["meta_proyecto"]
    meta_ids = dict(zip(meta["codigo_meta_extendida"], meta["id_meta"], strict=True))

    lines = read_csv(root, CRP_DIR, "crp_meta_detalle.csv")
    keys = pd.Series(list(zip(lines["numero_crp"], _int(lines["vigencia"]).astype(int),
                              strict=True)))
    crp_meta = pd.DataFrame({
        "id_crp": _lookup(keys, crp_ids, "crp_meta → crp", problems),
        "id_meta": _lookup(lines["codigo_meta_extendida"], meta_ids, "crp_meta → meta",
                           problems),
        "valor_asignado_pp": _num(lines["valor_asignado_pp"]),
        "linea_fuente": _int(lines["linea_fuente"]),
        "source": CURATED,
        "source_file": f"{CRP_DIR}/csv/crp_meta_detalle.csv",
    })
    tables["crp_meta"] = _ids(crp_meta, "id_crp_meta")

    proposal = tables["propuesta_ciudadana"]
    proposal_ids = dict(zip(proposal["codigo_propuesta"], proposal["id_propuesta"],
                            strict=True))
    relations = read_csv(root, CRP_DIR, "crp_propuesta.csv")
    keys = pd.Series(list(zip(relations["numero_crp"], _int(relations["vigencia"]).astype(int),
                              strict=True)))
    crp_propuesta = pd.DataFrame({
        "id_crp": _lookup(keys, crp_ids, "crp_propuesta → crp", problems),
        "id_propuesta": _lookup(relations["codigo_propuesta"], proposal_ids,
                                "crp_propuesta → propuesta", problems),
        "source": CURATED,
        "source_file": f"{CRP_DIR}/csv/crp_propuesta.csv",
    }).drop_duplicates(["id_crp", "id_propuesta"])
    tables["crp_propuesta"] = crp_propuesta.reset_index(drop=True)


def _build_ods(root: Path, tables: dict, problems: list[str]) -> None:
    ods = _ids(read_csv(root, ODS_DIR, "ods.csv"), "id_ods")
    tables["ods"] = ods
    ods_ids = dict(zip(ods["codigo_ods"], ods["id_ods"], strict=True))
    meta_ods = _ids(read_csv(root, ODS_DIR, "meta_ods.csv"), "id_meta_ods")
    meta_ods.insert(1, "id_ods", _lookup(meta_ods.pop("codigo_ods"), ods_ids,
                                         "meta_ods → ods", problems))
    tables["meta_ods"] = meta_ods
    goal_ids = dict(zip(meta_ods["codigo_meta_ods"], meta_ods["id_meta_ods"], strict=True))

    meta = tables["meta_proyecto"]
    meta_ids = dict(zip(meta["codigo_meta_extendida"], meta["id_meta"], strict=True))
    relations = read_csv(root, ODS_DIR, "meta_ods_relacion.csv")
    tables["meta_ods_relacion"] = pd.DataFrame({
        "id_meta": _lookup(relations["codigo_meta_extendida"], meta_ids,
                           "meta_ods_relacion → meta", problems),
        "id_meta_ods": _lookup(relations["codigo_meta_ods"], goal_ids,
                               "meta_ods_relacion → meta_ods", problems),
    }).drop_duplicates()
    # The ODS file also names the sector: it must match the sector already linked to the meta.
    sectors = tables["sector"].set_index("id_sector")["nombre_sector"]
    meta_sector = dict(zip(meta["codigo_meta_extendida"], meta["id_sector"].map(sectors),
                           strict=True))
    mismatched = [
        code for code, sector in zip(relations["codigo_meta_extendida"],
                                     relations["sector_relacionado"], strict=True)
        if meta_sector.get(code) != sector
    ]
    if mismatched:
        problems.append(f"ODS: sector distinto al de la meta en {sorted(mismatched)[:10]}")


def _build_pmr(root: Path, tables: dict, problems: list[str]) -> None:
    meta = tables["meta_proyecto"]
    indicator_ids = dict(zip(meta["codigo_indicador"], meta["id_meta"], strict=True))
    pmr = _ids(read_csv(root, PMR_DIR, "seguimiento_meta_pmr.csv"), "id_seguimiento_meta")
    pmr.insert(1, "id_meta", _lookup(pmr.pop("codigo_indicador"), indicator_ids,
                                     "seguimiento_meta → meta (codigo_indicador)", problems))
    pmr["vigencia"] = _int(pmr["vigencia"])
    pmr["fecha_corte"] = _date(pmr["fecha_corte"])
    for column in ("magnitud_programada", "magnitud_contratada", "magnitud_entregada",
                   "presupuesto_programado", "compromisos", "giros"):
        pmr[column] = _num(pmr[column])
    duplicated = pmr.duplicated(["id_meta", "vigencia", "fecha_corte"]).sum()
    if duplicated:
        problems.append(f"seguimiento_meta: {duplicated} filas repetidas por meta/vigencia/corte")
    tables["seguimiento_meta"] = pmr


def _build_pp(root: Path, tables: dict, problems: list[str]) -> None:
    meta = tables["meta_proyecto"]
    meta_ids = dict(zip(meta["codigo_meta_extendida"], meta["id_meta"], strict=True))
    proposal = _ids(read_csv(root, PP_DIR, "propuesta_ciudadana.csv"), "id_propuesta")
    proposal.insert(2, "id_meta", _lookup(proposal.pop("codigo_meta_extendida"), meta_ids,
                                          "propuesta → meta", problems))
    canonical = set(read_csv(root, PP_DIR, "normalizacion_metodologia.csv")["valor_canonico"])
    unexpected = set(proposal["metodologia"].dropna()) - canonical
    if unexpected:
        problems.append(f"Metodología sin normalizar: {sorted(unexpected)}")
    tables["propuesta_ciudadana"] = proposal
    proposal_ids = dict(zip(proposal["codigo_propuesta"], proposal["id_propuesta"],
                            strict=True))

    follow_up = _ids(read_csv(root, PP_DIR, "seguimiento_propuesta.csv"), "id_seguimiento")
    follow_up.insert(1, "id_propuesta", _lookup(follow_up.pop("codigo_propuesta"), proposal_ids,
                                                "seguimiento → propuesta", problems))
    follow_up["vigencia_ejecucion"] = _int(follow_up["vigencia_ejecucion"])
    follow_up["fecha_corte"] = _date(follow_up["fecha_corte"])
    follow_up["se_ejecuta_con_recursos"] = _bool(follow_up["se_ejecuta_con_recursos"])
    follow_up["poblacion_beneficiada"] = _int(follow_up["poblacion_beneficiada"])
    tables["seguimiento_propuesta"] = follow_up


def _build_pqrs(root: Path, tables: dict, problems: list[str]) -> None:
    catalogs = {
        "tipo_peticion": ("tipo_peticion.csv", "id_tipo_peticion", "nombre_tipo_peticion"),
        "medio_recepcion": ("medio_recepcion.csv", "id_medio_recepcion", "nombre_medio"),
        "subtema_pqrs": ("subtema_pqrs.csv", "id_subtema", "nombre_subtema"),
    }
    ids = {}
    for table, (file, id_column, name_column) in catalogs.items():
        catalog = _ids(read_csv(root, PQRS_DIR, file), id_column)
        tables[table] = catalog
        ids[table] = dict(zip(catalog[name_column], catalog[id_column], strict=True))

    raw = read_csv(root, PQRS_DIR, "pqrs_san_cristobal_normalizado.csv")
    pqrs = _ids(raw.drop(columns=["tipo_peticion", "medio_recepcion", "subtema"]), "id_pqrs")
    pqrs.insert(4, "id_tipo_peticion", _lookup(
        raw["tipo_peticion"], ids["tipo_peticion"], "pqrs → tipo_peticion", problems,
        nullable=True,
    ))
    pqrs.insert(5, "id_medio_recepcion", _lookup(
        raw["medio_recepcion"], ids["medio_recepcion"], "pqrs → medio_recepcion", problems,
        nullable=True,
    ))
    pqrs.insert(6, "id_subtema", _lookup(
        raw["subtema"], ids["subtema_pqrs"], "pqrs → subtema", problems, nullable=True,
    ))
    pqrs["id_localidad"] = _int(pqrs["id_localidad"])
    pqrs["vigencia"] = _int(pqrs["vigencia"])
    pqrs["tiempo_tramite"] = _num(pqrs["tiempo_tramite"])
    for column in ("fecha_registro", "fecha_radicacion", "fecha_asignacion", "fecha_respuesta",
                   "fecha_seguimiento"):
        pqrs[column] = _timestamp(pqrs[column])
    localities = set(tables["localidad"]["id_localidad"])
    if not set(pqrs["id_localidad"]) <= localities:
        problems.append("pqrs: localidad canónica no encontrada")
    tables["pqrs"] = pqrs


def _build_contracts(root: Path, tables: dict, problems: list[str]) -> None:
    """SECOP II contracts: `contrato` (one row per contract) + `contrato_vinculo` (one row per
    contract-project-meta-CRP link). The CRP numbers of this file are kept as an attribute: they
    are NOT joined with the `crp` table (which only has participatory-budget CRPs)."""
    raw = read_csv(root, CONTRACTS_DIR, CONTRACTS_FILE,
                   columns={**CONTRACT_COLUMNS, **CONTRACT_LINK_COLUMNS})
    contract_rows = raw[list(CONTRACT_COLUMNS)].rename(columns=CONTRACT_COLUMNS)
    # Contract-level fields are repeated on every link row: they must never disagree.
    varying = [
        column for column in contract_rows.columns if column != "id_contrato"
        and (contract_rows.groupby("id_contrato")[column].nunique(dropna=False) > 1).any()
    ]
    if varying:
        problems.append(f"contratos: datos del contrato distintos entre sus vínculos {varying}")
    contrato = contract_rows.drop_duplicates("id_contrato").reset_index(drop=True)
    contrato["vigencia"] = _int(contrato["vigencia"])
    contrato["fecha_firma"] = pd.to_datetime(
        contrato["fecha_firma"], format="ISO8601", errors="raise"
    ).dt.date
    contrato["valor_contrato"] = _num(contrato["valor_contrato"])
    contrato["estado_contrato"] = contrato["estado_contrato"].map(
        lambda value: value[:1].upper() + value[1:], na_action="ignore"
    )
    tables["contrato"] = contrato

    links = _ids(raw[list(CONTRACT_LINK_COLUMNS)].rename(columns=CONTRACT_LINK_COLUMNS),
                 "id_vinculo")
    links["vigencia_proyecto"] = _int(links["vigencia_proyecto"])
    links["vigencia_crp"] = _int(links["vigencia_crp"])
    statuses = {LINK_VERIFIED, LINK_PENDING}
    for level, code in (("proyecto", "codigo_proyecto"), ("meta", "codigo_meta")):
        status = links[f"estado_vinculo_{level}"]
        unexpected = set(status.dropna()) - statuses
        if unexpected or status.isna().any():
            problems.append(f"contratos: estado de vínculo con {level} inesperado "
                            f"{sorted(unexpected) or ['vacío']}")
        unverifiable = int(((status == LINK_VERIFIED) & links[code].isna()).sum())
        if unverifiable:
            problems.append(f"contratos: {unverifiable} vínculos con {level} verificado sin código")

    proyecto = tables["proyecto"]
    local = proyecto[proyecto["id_localidad"] == SAN_CRISTOBAL_ID]
    unknown = set(links["codigo_proyecto"].dropna()) - set(local["codigo_proyecto"])
    if unknown:
        problems.append(f"contratos → proyecto: códigos inexistentes {sorted(unknown)[:10]}")
    meta = tables["meta_proyecto"]
    project_codes = dict(zip(proyecto["id_proyecto"], proyecto["codigo_proyecto"], strict=True))
    meta_project = dict(zip(meta["codigo_meta_extendida"], meta["id_proyecto"].map(project_codes),
                            strict=True))
    unknown = set(links["codigo_meta"].dropna()) - set(meta_project)
    if unknown:
        problems.append(f"contratos → meta: códigos inexistentes {sorted(unknown)[:10]}")
    with_meta = links.dropna(subset=["codigo_meta"])
    mismatched = with_meta[with_meta["codigo_meta"].map(meta_project)
                           != with_meta["codigo_proyecto"]]
    if len(mismatched):
        problems.append(f"contratos: {len(mismatched)} vínculos con una meta de otro proyecto")
    tables["contrato_vinculo"] = links


# --- manifest validation -----------------------------------------------------------------------
def validate_against_manifests(model: CuratedModel, root: Path) -> list[str]:
    """Compare the built tables with every expected value of the six manifests."""
    t, m = model.tables, model.manifests
    problems: list[str] = []

    def check(label: str, actual: object, expected: object) -> None:
        if _differs(actual, expected):
            problems.append(f"{label}: se obtuvo {actual}, el manifiesto dice {expected}")

    # POAI
    counts = m[POAI_DIR]["conteos"]
    for table in ("localidad", "sector", "objetivo_estrategico", "programa", "proyecto",
                  "meta_proyecto"):
        check(f"POAI {table}", len(t[table]), counts[table])
    poai = t["poai"]
    for year, total in m[POAI_DIR]["totales_poai"].items():
        rows = poai[poai["vigencia"] == int(year)]
        check(f"POAI registros {year}", len(rows), counts[f"poai_{year}"])
        check(f"POAI total {year}", float(rows["valor_poai"].sum()), float(total))

    # PMR
    pmr = t["seguimiento_meta"]
    load = m[PMR_DIR]["carga"]
    check("PMR registros", len(pmr), load["registros_seguimiento_meta"])
    check("PMR cortes", sorted(str(d) for d in pmr["fecha_corte"].unique()),
          sorted(load["cortes"]))
    check("PMR vigencias", sorted(int(v) for v in pmr["vigencia"].unique()),
          sorted(load["vigencias"]))
    for cut, rows in pmr.groupby("fecha_corte"):
        for year, year_rows in rows.groupby("vigencia"):
            check(f"PMR metas corte {cut} vigencia {year}", len(year_rows),
                  load["metas_por_corte"])
    poai_2026 = float(poai.loc[poai["vigencia"] == 2026, "valor_poai"].sum())
    for cut, rows in pmr[pmr["vigencia"] == 2026].groupby("fecha_corte"):
        check(f"PMR 2026 presupuesto programado (corte {cut}) = POAI 2026",
              float(rows["presupuesto_programado"].sum()), poai_2026)
    changes = pmr_changes(pmr, 2026)
    for variable, expected in m[PMR_DIR]["cambios_marzo_junio_2026"].items():
        check(f"PMR cambios marzo→junio {variable}", changes.get(variable), expected)
    quality = poai_pmr_differences(t, 2026)
    check("Calidad POAI-PMR 2026 diferencias de presupuesto", quality["budget"],
          m[PMR_DIR]["calidad_poai_pmr_2026"]["diferencias_presupuesto"])
    check("Calidad POAI-PMR 2026 diferencias de magnitud", quality["magnitude"],
          m[PMR_DIR]["calidad_poai_pmr_2026"]["diferencias_magnitud"])
    # Note: 02_validar_pmr.sql expects 0 magnitude differences in 2025 after the correction,
    # but the delivered CSVs keep 3 (22852, 23163, 28052). It is not a manifest value, so it is
    # reported by the compare_poai_vs_pmr tool instead of failing the load.

    # PP
    pp = m[PP_DIR]
    follow_up = t["seguimiento_propuesta"]
    check("PP propuestas", len(t["propuesta_ciudadana"]), pp["propuestas"])
    check("PP seguimientos", len(follow_up), pp["seguimientos"])
    for cut, expected in pp["cortes"].items():
        check(f"PP seguimientos corte {cut}",
              int((follow_up["fecha_corte"].astype(str) == cut).sum()), expected)
    state, progress = pp_changes(follow_up)
    check("PP cambios de estado", state, pp["cambios_estado"])
    check("PP cambios de avance", progress, pp["cambios_avance"])

    # CRP (curated lines only)
    crp_counts = m[CRP_DIR]["conteos"]
    crp = t["crp"]
    lines = t["crp_meta"]
    relations = t["crp_propuesta"]
    check("CRP crp", len(crp), crp_counts["crp"])
    check("CRP filas fuente", len(lines), crp_counts["filas_fuente_crp"])
    check("CRP líneas crp_meta", len(lines), crp_counts["crp_meta_lineas"])
    pairs = lines.groupby(["id_crp", "id_meta"]).size()
    check("CRP pares crp-meta distintos", len(pairs), crp_counts["crp_meta_pares_distintos"])
    check("CRP pares repetidos", int((pairs > 1).sum()), crp_counts["crp_meta_pares_repetidos"])
    check("CRP relaciones crp-propuesta", len(relations), crp_counts["crp_propuesta_relaciones"])
    check("CRP propuestas financiadas", relations["id_propuesta"].nunique(),
          crp_counts["propuestas_financiadas_distintas"])
    check("CRP entidades", len(t["entidad"]), crp_counts["entidades"])
    check("CRP metas con entidad", int(t["meta_proyecto"]["id_entidad"].notna().sum()),
          crp_counts["metas_con_entidad"])
    check("CRP valor total", float(lines["valor_asignado_pp"].sum()),
          float(m[CRP_DIR]["valor_total_crp_pp"]))
    check("CRP propuestas con meta incoherente", crp_incoherent_relations(t),
          m[CRP_DIR]["integridad"]["propuestas_con_meta_incoherente"])

    # ODS
    ods = m[ODS_DIR]["conteos"]
    check("ODS ods", len(t["ods"]), ods["ods"])
    check("ODS meta_ods", len(t["meta_ods"]), ods["meta_ods"])
    check("ODS relaciones", len(t["meta_ods_relacion"]), ods["meta_ods_relacion"])
    check("ODS metas con relación", t["meta_ods_relacion"]["id_meta"].nunique(),
          m[ODS_DIR]["integridad"]["metas_proyecto_con_match"])

    # PQRS
    q = m[PQRS_DIR]
    pqrs = t["pqrs"]
    check("PQRS registros", len(pqrs), q["registros"]["san_cristobal"])
    check("PQRS radicados únicos", pqrs["radicado"].nunique(), q["registros"]["radicados_unicos"])
    for table, expected in q["catalogos"].items():
        check(f"PQRS catálogo {table}", len(t[table]), expected)
    null_columns = {"tipo_peticion": "id_tipo_peticion"}
    for column, expected in q["nulos_normalizados"].items():
        check(f"PQRS nulos {column}", int(pqrs[null_columns.get(column, column)].isna().sum()),
              expected)
    check("PQRS vigencia distinta al año de fecha_registro", pqrs_year_mismatches(pqrs),
          q["calidad"]["vigencia_vs_anio_fecha_registro"])
    check("PQRS primera fecha_registro", str(pqrs["fecha_registro"].min()),
          q["periodo"]["primera_fecha_registro"])
    check("PQRS última fecha_registro", str(pqrs["fecha_registro"].max()),
          q["periodo"]["ultima_fecha_registro"])

    # Contracts (the value is counted ONCE per contract)
    c = m[CONTRACTS_DIR]
    contracts, links = t["contrato"], t["contrato_vinculo"]
    check("Contratos vínculos", len(links), c["conteos"]["vinculos"])
    check("Contratos distintos", len(contracts), c["conteos"]["contratos"])
    check("Contratos con varios vínculos", int((links.groupby("id_contrato").size() > 1).sum()),
          c["conteos"]["contratos_con_varios_vinculos"])
    check("Contratos vínculos con proyecto verificado",
          int((links["estado_vinculo_proyecto"] == LINK_VERIFIED).sum()),
          c["conteos"]["vinculos_proyecto_verificados"])
    check("Contratos vínculos con meta verificada",
          int((links["estado_vinculo_meta"] == LINK_VERIFIED).sum()),
          c["conteos"]["vinculos_meta_verificados"])
    check("Contratos con valor 0", int((contracts["valor_contrato"] == 0).sum()),
          c["conteos"]["contratos_valor_cero"])
    check("Contratos valor total", float(contracts["valor_contrato"].sum()),
          float(c["valor_total_contratos"]))
    return problems


def _differs(actual: object, expected: object) -> bool:
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            return not math.isclose(float(actual), float(expected), abs_tol=0.5)
        except (TypeError, ValueError):
            return True
    return actual != expected


# --- shared deterministic calculations (also used by the agent tools) ------------------------
PMR_CHANGE_COLUMNS = ("magnitud_contratada", "magnitud_entregada", "compromisos", "giros")


def pmr_changes(pmr: pd.DataFrame, year: int) -> dict[str, int]:
    """Metas whose value changed between the first and the last PMR cut-off (null-safe)."""
    rows = pmr[pmr["vigencia"] == year]
    cuts = sorted(rows["fecha_corte"].unique())
    if len(cuts) < 2:
        return {}
    first = rows[rows["fecha_corte"] == cuts[0]].set_index("id_meta")
    last = rows[rows["fecha_corte"] == cuts[-1]].set_index("id_meta")
    both = first.index.intersection(last.index)
    return {
        column: int(_distinct(first.loc[both, column], last.loc[both, column]).sum())
        for column in PMR_CHANGE_COLUMNS
    }


def pp_changes(follow_up: pd.DataFrame) -> tuple[int, int]:
    """(state changes, progress-text changes) between the first and the last PP cut-off."""
    cuts = sorted(follow_up["fecha_corte"].unique())
    if len(cuts) < 2:
        return 0, 0
    first = follow_up[follow_up["fecha_corte"] == cuts[0]].set_index("id_propuesta")
    last = follow_up[follow_up["fecha_corte"] == cuts[-1]].set_index("id_propuesta")
    both = first.index.intersection(last.index)
    state = _distinct(first.loc[both, "estado_propuesta"], last.loc[both, "estado_propuesta"])
    text = _distinct(first.loc[both, "avance_gestion"], last.loc[both, "avance_gestion"])
    return int(state.sum()), int(text.sum())


def _distinct(left: pd.Series, right: pd.Series) -> pd.Series:
    """SQL `IS DISTINCT FROM`: two nulls are equal, a null and a value differ."""
    both_null = left.isna() & right.isna()
    one_null = left.isna() ^ right.isna()
    different = (left != right).fillna(False).astype(bool)
    return (one_null | (different & ~both_null)).astype(bool)


def poai_pmr_differences(tables: dict[str, pd.DataFrame], year: int) -> dict[str, int]:
    """Counts of budget and magnitude differences between POAI and the latest PMR cut-off."""
    comparison = poai_pmr_comparison(tables["poai"], tables["seguimiento_meta"], year)
    return {
        "budget": int(comparison["budget_differs"].sum()),
        "magnitude": int(comparison["magnitude_differs"].sum()),
    }


def poai_pmr_comparison(poai: pd.DataFrame, pmr: pd.DataFrame, year: int) -> pd.DataFrame:
    """One row per meta present in both sources for `year` (PMR at its latest cut-off)."""
    latest = latest_cut(pmr)
    planned = poai[poai["vigencia"] == year][["id_meta", "magnitud_programada", "valor_poai"]]
    reported = latest[latest["vigencia"] == year][
        ["id_meta", "magnitud_programada", "presupuesto_programado", "fecha_corte"]
    ]
    merged = planned.merge(reported, on="id_meta", suffixes=("_poai", "_pmr"))
    merged["diferencia_presupuesto"] = merged["presupuesto_programado"] - merged["valor_poai"]
    merged["diferencia_magnitud"] = (
        merged["magnitud_programada_pmr"] - merged["magnitud_programada_poai"]
    )
    tolerance = PMR_2025_ROUNDING_COP if year == 2025 else 0.5
    merged["budget_differs"] = (
        merged["diferencia_presupuesto"].abs().fillna(float("inf")) > tolerance
    ).astype(bool)
    merged["magnitude_differs"] = (
        merged["diferencia_magnitud"].abs().fillna(float("inf")) > 1e-9
    ).astype(bool)
    return merged


def latest_cut(pmr: pd.DataFrame) -> pd.DataFrame:
    """Same as `vw_seguimiento_meta_ultimo_corte`: the latest cut-off per meta and vigencia."""
    ordered = pmr.sort_values(["id_meta", "vigencia", "fecha_corte"])
    return ordered.drop_duplicates(["id_meta", "vigencia"], keep="last").reset_index(drop=True)


def crp_incoherent_relations(tables: dict[str, pd.DataFrame]) -> int:
    """CRP-proposal relations whose proposal meta is not among the metas of that CRP."""
    relations = tables["crp_propuesta"].merge(
        tables["propuesta_ciudadana"][["id_propuesta", "id_meta"]], on="id_propuesta"
    )
    metas = tables["crp_meta"][["id_crp", "id_meta"]].drop_duplicates()
    matched = relations.merge(metas, on=["id_crp", "id_meta"], how="left", indicator=True)
    return int((matched["_merge"] == "left_only").sum())


def pqrs_year_mismatches(pqrs: pd.DataFrame) -> int:
    years = pqrs["fecha_registro"].dt.year
    return int(((pqrs["vigencia"] != years) & pqrs["vigencia"].notna() & years.notna()).sum())


# --- CRP 2026 supplement from the portal -------------------------------------------------------
PROPOSAL_CODE = re.compile(r"\d+")


def add_portal_crp_supplement(
    model: CuratedModel, portal: pd.DataFrame, source_file: str
) -> CrpSupplement:
    """Append to the curated CRP tables the portal CRP lines (`f3_pp_commitments`) of the
    vigencias the curated load does not have. Rows are tagged `source="portal"`.

    Lines or proposals that reference a meta/proposal absent from the curated model are NOT
    loaded: they are listed in `issues` (nothing is invented)."""
    t = model.tables
    result = CrpSupplement()
    curated_years = set(t["crp"]["vigencia"].astype(int))
    portal = portal.copy()
    portal["vigencia_ejecucion"] = pd.to_numeric(portal["vigencia_ejecucion"], errors="coerce")
    if "no_localidad" in portal.columns:
        portal = portal[pd.to_numeric(portal["no_localidad"], errors="coerce")
                        == SAN_CRISTOBAL_ID]
    rows = portal[portal["vigencia_ejecucion"].notna()
                  & ~portal["vigencia_ejecucion"].isin(curated_years)].copy()
    if rows.empty:
        return result
    rows["vigencia_ejecucion"] = rows["vigencia_ejecucion"].astype(int)
    rows["numero_crp"] = rows["no_crp"].map(_code)
    rows["codigo_meta"] = rows["cod_meta_proyecto_extendida"].map(_code)
    result.vigencias = sorted(set(rows["vigencia_ejecucion"]))

    meta_ids = dict(zip(t["meta_proyecto"]["codigo_meta_extendida"],
                        t["meta_proyecto"]["id_meta"], strict=True))
    proposals = t["propuesta_ciudadana"]
    proposal_ids = dict(zip(proposals["codigo_propuesta"], proposals["id_propuesta"],
                            strict=True))
    proposal_meta = dict(zip(proposals["id_propuesta"], proposals["id_meta"], strict=True))

    # crp: one row per CRP number + vigencia, contractual fields from its first line.
    next_crp = int(t["crp"]["id_crp"].max()) + 1
    new_crp, crp_ids = [], {}
    for (number, year), group in rows.groupby(["numero_crp", "vigencia_ejecucion"], sort=True):
        first = group.iloc[0]
        for column in ("fecha_registro", "no_compromiso", "compromiso", "objeto"):
            if group[column].astype(str).nunique() > 1:
                result.issues.append(
                    f"CRP {number}/{year}: '{column}' varía entre líneas; se usa la primera"
                )
        crp_ids[(number, year)] = next_crp
        new_crp.append({
            "id_crp": next_crp, "numero_crp": number, "vigencia": year,
            "fecha_registro": pd.to_datetime(first["fecha_registro"]).date()
            if pd.notna(first["fecha_registro"]) else None,
            "numero_compromiso": _text(first["no_compromiso"]),
            "tipo_compromiso": _text(first["compromiso"]),
            "plazo": int(_code(first["plazo"])) if _code(first["plazo"]) else None,
            "objeto": _text(first["objeto"]),
            "codigo_modalidad": _code(first["modalidad_seleccion"]) or None,
            "modalidad_seleccion": _text(first["descripcion_mod_selec"]),
            "tipo_documento_beneficiario": _text(first["tipo_doc_bp_beneficiario"]),
            "source": PORTAL, "source_file": source_file,
        })
        next_crp += 1

    next_line = int(t["crp_meta"]["id_crp_meta"].max()) + 1
    new_lines, new_relations, seen = [], [], set()
    for position, row in enumerate(rows.itertuples(), start=1):
        id_crp = crp_ids[(row.numero_crp, row.vigencia_ejecucion)]
        id_meta = meta_ids.get(row.codigo_meta)
        if id_meta is None:
            result.issues.append(
                f"CRP {row.numero_crp}/{row.vigencia_ejecucion}: la meta {row.codigo_meta} "
                "no existe en meta_proyecto; la línea no se cargó"
            )
            continue
        new_lines.append({
            "id_crp_meta": next_line, "id_crp": id_crp, "id_meta": id_meta,
            "valor_asignado_pp": float(row.valor_crp_asignado_presupuestos_participativos),
            "linea_fuente": position, "source": PORTAL, "source_file": source_file,
        })
        next_line += 1
        for code in PROPOSAL_CODE.findall(str(row.codigo_propuestas_financiadas_crp or "")):
            id_proposal = proposal_ids.get(code)
            if id_proposal is None:
                result.issues.append(
                    f"CRP {row.numero_crp}/{row.vigencia_ejecucion}: la propuesta {code} no "
                    "existe en propuesta_ciudadana; la relación no se cargó"
                )
                continue
            if proposal_meta[id_proposal] != id_meta:
                result.issues.append(
                    f"CRP {row.numero_crp}/{row.vigencia_ejecucion}: la propuesta {code} "
                    f"pertenece a otra meta distinta de {row.codigo_meta}"
                )
            if (id_crp, id_proposal) not in seen:
                seen.add((id_crp, id_proposal))
                new_relations.append({"id_crp": id_crp, "id_propuesta": id_proposal,
                                      "source": PORTAL, "source_file": source_file})

    loaded_crp = {line["id_crp"] for line in new_lines}
    new_crp = [crp for crp in new_crp if crp["id_crp"] in loaded_crp]
    # Build every frame first: the model is only changed when all of them are valid.
    frames = {
        "crp": _append(t["crp"], new_crp),
        "crp_meta": _append(t["crp_meta"], new_lines),
        "crp_propuesta": _append(t["crp_propuesta"], new_relations),
    }
    t.update(frames)
    result.crp = len(new_crp)
    result.lines = len(new_lines)
    result.proposals = len({r["id_propuesta"] for r in new_relations})
    result.value = float(sum(line["valor_asignado_pp"] for line in new_lines))
    return result


def _append(frame: pd.DataFrame, rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return frame
    extra = pd.DataFrame(rows, columns=frame.columns).astype(frame.dtypes.to_dict())
    return pd.concat([frame, extra], ignore_index=True)


def _code(value: object) -> str:
    """Portal numbers arrive as int/float ('2605.0'): keep the digits as text."""
    if value is None or (isinstance(value, float) and math.isnan(value)) or value is pd.NA:
        return ""
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") else text


def _text(value: object) -> str | None:
    if value is None or value is pd.NA or (isinstance(value, float) and math.isnan(value)):
        return None
    return str(value).strip() or None
