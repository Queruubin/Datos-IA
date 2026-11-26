"""A miniature curated package (same folders, CSV columns and manifests as `curated_data/`) and
the portal commitments frame used for the CRP supplement. Hand-written values; the manifests
state what the loader must obtain, so they are an independent check."""

import csv
import json
from pathlib import Path

import pandas as pd

# Name that must never leave the database through a tool (pqrs.usuario_actual).
OFFICIAL_NAME = "FUNCIONARIA SECRETA UNO"


def _write(root: Path, domain: str, name: str, header: list[str], rows: list[list]) -> None:
    folder = root / domain / "csv"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _manifest(root: Path, domain: str, content: dict) -> None:
    (root / domain).mkdir(parents=True, exist_ok=True)
    (root / domain / "manifest.json").write_text(
        json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_mini_package(root: Path) -> Path:
    root = Path(root)
    poai = "Carga_Base_POAI_SC"
    _write(root, poai, "localidad.csv", ["id_localidad", "nombre_localidad"],
           [[4, "San Cristóbal"]])
    _write(root, poai, "sector.csv", ["nombre_sector"],
           [["CULTURA, RECREACIÓN Y DEPORTE"], ["AMBIENTE"], ["MOVILIDAD"]])
    _write(root, poai, "objetivo_estrategico.csv", ["codigo_objetivo", "nombre_objetivo"],
           [[1, "Objetivo uno"], [2, "Objetivo dos"]])
    _write(root, poai, "programa.csv", ["codigo_objetivo", "codigo_programa", "nombre_programa"],
           [[1, 1, "Programa uno"], [2, 5, "Programa cinco"]])
    _write(root, poai, "proyecto.csv",
           ["codigo_proyecto", "id_localidad", "codigo_objetivo", "codigo_programa",
            "nombre_proyecto"],
           [[2251, 4, 1, 1, "Cultura viva"], [2502, 4, 2, 5, "Ambiente sano"]])
    meta_header = [
        "codigo_meta_extendida", "codigo_proyecto", "nombre_sector", "codigo_indicador",
        "indicador_producto", "descripcion_meta", "componente_proyecto", "linea_inversion",
        "concepto_gasto", "componente_presupuestal", "meta_total_2025_2028", "tipo_anualizacion",
    ]
    _write(root, poai, "meta_proyecto.csv", meta_header, [
        [22511, 2251, "CULTURA, RECREACIÓN Y DEPORTE", 56, "Proyectos culturales financiados",
         "Financiar 120 proyectos culturales", "SOSTENIBILIDAD", "Cultura", "Gasto", "PP", 120,
         "Suma"],
        [22512, 2251, "CULTURA, RECREACIÓN Y DEPORTE", 57, "Festivales realizados",
         "Realizar 10 festivales", "EVENTOS", "Cultura", "Gasto", "PP", 10, "Suma"],
        [25021, 2502, "AMBIENTE", 60, "Árboles plantados", "Plantar 500 árboles", "VERDE",
         "Ambiente", "Gasto", "PP", 500, "Suma"],
        # Same project, other sector: the sector depends on the meta.
        [25022, 2502, "MOVILIDAD", 61, "Kilómetros de malla vial",
         "Intervenir 2 km de malla vial", "VIAS", "Movilidad", "Gasto", "", 2, "Suma"],
    ])
    poai_header = [
        "codigo_meta_extendida", "vigencia", "recurso_indicativo", "porcentaje_plan_plurianual",
        "magnitud_programada", "valor_poai", "porcentaje_recursos_poai", "tiene_propuesta_pp",
        "fecha_corte",
    ]
    _write(root, poai, "poai.csv", poai_header, [
        # 2025 codes 22511/22512 are swapped in the source; the PMR correction fixes them.
        [22511, 2025, "", "", 5, 2000, 0.2, "", ""],
        [22512, 2025, "", "", 30, 1000, 0.1, "", ""],
        [25021, 2025, "", "", 100, 3000, 0.3, "", ""],
        [25022, 2025, "", "", 1, 4000, 0.4, "", ""],
        [22511, 2026, 1500, 0.1, 40, 1500, 0.125, "True", ""],
        [22512, 2026, 2500, 0.1, 6, 2500, 0.208, "True", ""],
        [25021, 2026, 3500, 0.1, 200, 3500, 0.292, "True", ""],
        [25022, 2026, 4500, 0.1, 2, 4500, 0.375, "False", ""],
    ])
    _manifest(root, poai, {
        "conteos": {"localidad": 1, "sector": 3, "objetivo_estrategico": 2, "programa": 2,
                    "proyecto": 2, "meta_proyecto": 4, "poai_2025": 4, "poai_2026": 4},
        "totales_poai": {"2025": 10000, "2026": 12000},
    })

    pmr = "Carga_PMR_SC"
    _write(root, pmr, "correccion_integracion_poai_2025.csv",
           ["codigo_meta_pdl", "motivo", "magnitud_correcta_2025", "valor_correcto_2025"],
           [[22511, "Cruce de descripciones", 30, 1000],
            [22512, "Cruce de descripciones", 5, 2000]])
    pmr_header = [
        "codigo_indicador", "vigencia", "fecha_corte", "magnitud_programada",
        "magnitud_contratada", "magnitud_entregada", "presupuesto_programado", "compromisos",
        "giros",
    ]
    rows_2025 = [
        [56, 30, 30, 30, 1000, 900, ""],
        [57, 5, 5, 5, 2000, 2000, ""],
        [60, 100, 100, 80, 3000, 2500, ""],
        [61, 1, 1, 1, 4000, 4000, ""],
    ]
    march = [
        [56, 40, 10, 0, 1500, 500, 100],
        [57, 6, 0, 0, 2500, 0, 0],
        [60, 200, 50, 10, 3500, 1000, 200],
        [61, 2, 0, 0, 4500, 0, 0],
    ]
    june = [
        [56, 40, 20, 5, 1500, 800, 400],
        [57, 6, 0, 0, 2500, 0, 0],
        [60, 150, 50, 20, 3500, 1000, 600],  # POAI says 200: one magnitude difference
        [61, 2, 1, 0, 4500, 2000, 100],
    ]
    pmr_rows = []
    for cut in ("2026-03-31", "2026-06-30"):
        pmr_rows += [[r[0], 2025, cut, *r[1:]] for r in rows_2025]
    pmr_rows += [[r[0], 2026, "2026-03-31", *r[1:]] for r in march]
    pmr_rows += [[r[0], 2026, "2026-06-30", *r[1:]] for r in june]
    _write(root, pmr, "seguimiento_meta_pmr.csv", pmr_header, pmr_rows)
    _manifest(root, pmr, {
        "carga": {"metas_por_corte": 4, "cortes": ["2026-03-31", "2026-06-30"],
                  "vigencias": [2025, 2026], "registros_seguimiento_meta": 16},
        "cambios_marzo_junio_2026": {"magnitud_contratada": 2, "magnitud_entregada": 2,
                                     "compromisos": 2, "giros": 3},
        "calidad_poai_pmr_2026": {"diferencias_presupuesto": 0, "diferencias_magnitud": 1},
    })

    pp = "Carga_PP_SC"
    _write(root, pp, "normalizacion_metodologia.csv", ["valor_fuente", "valor_canonico"], [
        ["D. General", "Diálogo General"], ["Diálogo General", "Diálogo General"],
        ["Diálogo Diferencial", "Diálogo Diferencial"], ["Idea Lo Local", "Idea Lo Local"],
        ["Transforma lo Local", "Transforma lo Local"],
    ])
    _write(root, pp, "propuesta_ciudadana.csv",
           ["codigo_propuesta", "codigo_meta_extendida", "nombre_propuesta", "metodologia",
            "tipo_acuerdo"], [
               [101, 22511, "Festival de rock", "Diálogo General", "acuerdo"],
               [102, 22511, "Escuela de teatro", "Idea Lo Local", "acuerdo"],
               [103, 25021, "Huerta comunitaria", "Diálogo Diferencial", "acuerdo"],
               [104, 25021, "Sendero ecológico", "Transforma lo Local", "acuerdo"],
               [105, 22512, "Mural barrial", "Diálogo General", "acuerdo"],
               [106, 25021, "Reciclaje barrial", "Diálogo General", "acuerdo"],
           ])
    follow_header = [
        "codigo_propuesta", "vigencia_ejecucion", "fecha_corte", "se_ejecuta_con_recursos",
        "estado_propuesta", "poblacion_beneficiada", "clasificacion_poblacional",
        "avance_gestion", "dificultades",
    ]
    states = {  # code: (vigencia, march state, october state, march text, october text)
        101: (2025, "En ejecución", "Materializada", "contrato firmado", "evento realizado"),
        102: (2025, "En ejecución", "En ejecución", "contrato firmado", "clases iniciadas"),
        103: (2025, "Contratada", "Contratada", "contratada", "contratada"),
        104: (2025, "No ejecutada", "No ejecutada", "sin recursos", "sin recursos"),
        105: (2026, "En formulación", "En formulación", "mesas", "mesas"),
        106: (2025, "En ejecución", "En ejecución", "en curso", "en curso"),
    }
    follow_rows = []
    for code, (year, before, after, text_before, text_after) in states.items():
        follow_rows.append([code, year, "2026-03-31", "True", before, 100, "", text_before, ""])
        follow_rows.append([code, year, "2026-10-01", "True", after, 100, "", text_after, ""])
    _write(root, pp, "seguimiento_propuesta.csv", follow_header, follow_rows)
    _manifest(root, pp, {
        "propuestas": 6, "seguimientos": 12, "cortes": {"2026-03-31": 6, "2026-10-01": 6},
        "cambios_estado": 1, "cambios_avance": 2,
    })

    crp = "Carga_CRP_SC"
    _write(root, crp, "entidad.csv", ["nombre_entidad"],
           [["Secretaría de Cultura"], ["Secretaría de Ambiente"]])
    _write(root, crp, "meta_entidad.csv", ["codigo_meta_extendida", "nombre_entidad"], [
        [22511, "Secretaría de Cultura"], [22512, "Secretaría de Cultura"],
        [25021, "Secretaría de Ambiente"],
    ])
    _write(root, crp, "crp.csv", [
        "numero_crp", "vigencia", "fecha_registro", "numero_compromiso", "tipo_compromiso",
        "plazo", "objeto", "codigo_modalidad", "modalidad_seleccion",
        "tipo_documento_beneficiario",
    ], [
        [900, 2025, "2025-07-15", "679 2025", "CONVENIO", 169, "Objeto", 10, "DIRECTA", "NIT"],
        [901, 2025, "2025-08-01", "700 2025", "CONTRATO", 120, "Objeto", 2, "MENOR", "NIT"],
    ])
    _write(root, crp, "crp_meta_detalle.csv",
           ["linea_fuente", "numero_crp", "vigencia", "codigo_meta_extendida",
            "valor_asignado_pp"],
           # CRP 900 + meta 22511 appears twice with different values: both lines are kept.
           [[1, 900, 2025, 22511, 600], [2, 900, 2025, 22511, 400], [3, 901, 2025, 25021, 2000]])
    _write(root, crp, "crp_propuesta.csv", ["numero_crp", "vigencia", "codigo_propuesta"],
           [[900, 2025, 101], [900, 2025, 102], [901, 2025, 103]])
    _manifest(root, crp, {
        "conteos": {"filas_fuente_crp": 3, "crp": 2, "crp_meta_lineas": 3,
                    "crp_meta_pares_distintos": 2, "crp_propuesta_relaciones": 3,
                    "propuestas_financiadas_distintas": 3, "entidades": 2,
                    "metas_con_entidad": 3, "crp_meta_pares_repetidos": 1},
        "valor_total_crp_pp": 3000,
        "integridad": {"propuestas_referenciadas_no_encontradas": 0,
                       "propuestas_con_meta_incoherente": 0},
    })

    ods = "Carga_ODS_SC"
    _write(root, ods, "ods.csv", ["codigo_ods", "nombre_ods", "esfera_ods"], [
        [8, "Trabajo decente y crecimiento económico", "Prosperidad"],
        [11, "Ciudades y Comunidades Sostenibles", "Prosperidad"],
    ])
    _write(root, ods, "meta_ods.csv", ["codigo_meta_ods", "codigo_ods", "descripcion_meta_ods"],
           [["8.3", 8, "Promover empleo"], ["11.7", 11, "Espacios públicos"]])
    _write(root, ods, "meta_ods_relacion.csv",
           ["codigo_meta_extendida", "codigo_meta_ods", "codigo_ods", "sector_relacionado"], [
               [22511, "8.3", 8, "CULTURA, RECREACIÓN Y DEPORTE"],
               [22512, "8.3", 8, "CULTURA, RECREACIÓN Y DEPORTE"],
               [25021, "11.7", 11, "AMBIENTE"],
               [25022, "11.7", 11, "MOVILIDAD"],
           ])
    _manifest(root, ods, {
        "conteos": {"registros_san_cristobal": 4, "ods": 2, "meta_ods": 2, "meta_ods_relacion": 4},
        "integridad": {"metas_proyecto_unicas": 4, "metas_proyecto_con_match": 4,
                       "sectores_coincidentes_con_modelo": 4},
    })

    pqrs = "Carga_PQRS_SC"
    _write(root, pqrs, "tipo_peticion.csv", ["nombre_tipo_peticion"], [["DERECHO DE PETICION"]])
    _write(root, pqrs, "medio_recepcion.csv", ["nombre_medio"], [["Correo"]])
    _write(root, pqrs, "subtema_pqrs.csv", ["nombre_subtema"],
           [["MALLA VIAL"], ["PARQUES"], ["'; DROP TABLE pqrs; --"]])
    answered = "Se otorga informacion al Peticionario. Se Evidencia Acuse de Recibido"
    pqrs_header = [
        "radicado", "numero_sdqs", "id_localidad", "tipo_peticion", "medio_recepcion", "subtema",
        "fecha_registro", "fecha_radicacion", "fecha_asignacion", "vigencia", "tiempo_tramite",
        "estado_orfeo", "observacion_general", "observacion_sac", "usuario_actual",
        "dependencia_actual", "ultima_dependencia", "radicado_respuesta", "fecha_respuesta",
        "fecha_seguimiento", "codigo_localidad_fuente",
    ]
    _write(root, pqrs, "pqrs_san_cristobal_normalizado.csv", pqrs_header, [
        [1001, "s1", 4, "DERECHO DE PETICION", "Correo", "MALLA VIAL", "2025-01-01 08:00:00",
         "2025-01-01 08:00:00", "2025-01-02 00:00:00", 2025, "15.0", "TRAMITE CERRADO",
         answered, "", OFFICIAL_NAME, "ARCHIVO DE DOCUMENTOS", "Area de Gestion", "R1",
         "2025-01-11 08:00:00", "2025-01-20 08:00:00", 545],
        [1002, "s2", 4, "", "Correo", "MALLA VIAL", "2025-02-01 08:00:00",
         "2025-02-01 08:00:00", "2025-02-02 00:00:00", 2025, "", "RADICADO EN GESTION",
         "Sin respuesta al peticionario", "No hay respuesta al peticionario 6 de 15 dias",
         "FUNCIONARIO SECRETO DOS", "Area de Gestion de Desarrollo Local", "", "", "", "", ""],
        [1003, "s3", 4, "DERECHO DE PETICION", "Correo", "PARQUES", "2025-03-01 08:00:00",
         "2025-03-01 08:00:00", "2025-03-02 00:00:00", 2025, "15.0", "TRAMITE CERRADO",
         answered, "", OFFICIAL_NAME, "ARCHIVO DE DOCUMENTOS", "Area de Gestion", "R3",
         "2025-03-21 08:00:00", "2025-03-25 08:00:00", 460],
        # Vigencia 2024 but registered in 2025: kept as the source says.
        [1004, "s4", 4, "DERECHO DE PETICION", "Correo", "MALLA VIAL", "2025-01-02 08:00:00",
         "2025-01-02 08:00:00", "2025-01-03 00:00:00", 2024, "15.0", "TRAMITE CERRADO",
         answered, "", OFFICIAL_NAME, "ARCHIVO DE DOCUMENTOS", "Area de Gestion", "R4",
         "2025-01-07 08:00:00", "2025-01-08 08:00:00", 545],
        [1005, "s5", 4, "DERECHO DE PETICION", "Correo", "'; DROP TABLE pqrs; --",
         "2025-04-01 08:00:00", "2025-04-01 08:00:00", "2025-04-02 00:00:00", 2025, "15.0",
         "TRAMITE CERRADO", answered, "", OFFICIAL_NAME, "ARCHIVO DE DOCUMENTOS",
         "Area de Gestion", "R5", "2025-04-02 08:00:00", "2025-04-03 08:00:00", 545],
    ])
    _manifest(root, pqrs, {
        "registros": {"total_fuente": 10, "san_cristobal": 5, "radicados_unicos": 5},
        "catalogos": {"tipo_peticion": 1, "medio_recepcion": 1, "subtema_pqrs": 3},
        "nulos_normalizados": {
            "tipo_peticion": 1, "tiempo_tramite": 1, "observacion_general": 0,
            "observacion_sac": 4, "ultima_dependencia": 1, "radicado_respuesta": 1,
            "fecha_respuesta": 1, "fecha_seguimiento": 1, "codigo_localidad_fuente": 1,
        },
        "calidad": {"vigencia_vs_anio_fecha_registro": 1},
        "periodo": {"primera_fecha_registro": "2025-01-01 08:00:00",
                    "ultima_fecha_registro": "2025-04-01 08:00:00"},
    })

    _write_contracts(root)
    return root


# Natural person in the contracts file: must never reach a table nor a tool.
CONTRACTOR_NAME = "PERSONA NATURAL FICTICIA"

CONTRACT_HEADER = [
    "ID Contrato", "Referencia del Contrato", "Vigencia del contrato", "Fecha de Firma",
    "Objeto del Contrato", "Contratista", "Valor del Contrato (COP)", "Estado Contrato",
    "Código Proyecto", "Nombre del Proyecto", "Vigencia del proyecto", "Código Meta", "Meta",
    "ID Meta", "Número de CRP del vínculo", "Vigencia presupuestal CRP",
    "CRP registrados del contrato", "Estado vínculo proyecto", "Estado vínculo meta",
    "Motivo de verificación", "Enlace público del proceso", "Enlace público del contrato",
    "Registro en Datos Abiertos",
]
V, P = "Verificado", "Pendiente de verificación"


def _contract_row(number: int, year: int, signed: str, objeto: str, value: int, status: str,
                  project: str, meta: str, crp: str, project_link: str, meta_link: str,
                  reason: str = "") -> list:
    return [
        f"CO1.PCCNTR.{number}", f"FDLSC-CPS-{number:03d}-{year}", year, signed, objeto,
        CONTRACTOR_NAME, value, status, project, f"Proyecto {project}" if project else "",
        year if project else "", meta, f"Meta {meta}" if meta else "",
        f"M-{year}-{meta}" if meta else "", crp, year if crp else "", crp, project_link,
        meta_link, reason, f"https://community.secop.gov.co/proceso/{number}",
        f"https://community.secop.gov.co/contrato/{number}",
        f"https://www.datos.gov.co/resource/jbjy-vk9h.json?id_contrato=CO1.PCCNTR.{number}",
    ]


def _write_contracts(root: Path) -> None:
    """Five contracts, eight link rows. Contract 1 has three links (its value 1000 repeats on
    each row); contract 3 has only a pending link; contract 5 is worth 0; 'cedido' comes in
    lower case as in the real file."""
    signed = "2025-02-01 10:00:00.123000"
    rows = [
        _contract_row(1, 2025, signed, "Prestar servicios de apoyo a la gestión cultural", 1000,
                      "En ejecución", "2251", "22511", "10", V, V),
        _contract_row(1, 2025, signed, "Prestar servicios de apoyo a la gestión cultural", 1000,
                      "En ejecución", "2251", "22512", "11", V, V),
        _contract_row(1, 2025, signed, "Prestar servicios de apoyo a la gestión cultural", 1000,
                      "En ejecución", "2502", "", "", V, P,
                      "La evidencia identifica el proyecto. Falta soporte de la meta específica."),
        _contract_row(2, 2026, "2026-03-10 09:00:00", "Suministro de árboles para arborización",
                      500, "cedido", "2502", "25021", "20", V, V),
        _contract_row(3, 2025, "2025-01-15 08:00:00", "Mantenimiento de la malla vial local",
                      300, "Cerrado", "", "", "", P, P, "Pendiente de acceso al certificado"),
        _contract_row(4, 2026, "2026-05-20 11:30:00", "Festival de rock al parque local", 2000,
                      "Modificado", "2251", "", "", V, P),
        _contract_row(4, 2026, "2026-05-20 11:30:00", "Festival de rock al parque local", 2000,
                      "Modificado", "", "", "", P, P, "Sin CRP verificable"),
        _contract_row(5, 2025, "2025-06-30 16:00:00", "Adición sin valor al convenio vial", 0,
                      "Aprobado", "2502", "25022", "30", V, V),
    ]
    _write(root, "Carga_Contratos_SC", "Consulta_agente_San_Cristobal_2025_2026.csv",
           CONTRACT_HEADER, rows)
    _manifest(root, "Carga_Contratos_SC", {
        "conteos": {"vinculos": 8, "contratos": 5, "contratos_con_varios_vinculos": 2,
                    "vinculos_proyecto_verificados": 6, "vinculos_meta_verificados": 4,
                    "contratos_valor_cero": 1},
        "valor_total_contratos": 3800,  # summing the rows would give 7800
    })


def portal_commitments_frame() -> pd.DataFrame:
    """Rows shaped like the portal table `f3_pp_commitments` (after the F3 parser)."""
    base = {
        "no_localidad": 4, "fecha_registro": pd.Timestamp("2026-08-11"),
        "no_compromiso": "628 2026", "compromiso": "CONVENIO INTERADMINISTRATIVO",
        "plazo": 142, "objeto": "AUNAR ESFUERZOS", "modalidad_seleccion": 10,
        "descripcion_mod_selec": "CONTRATACIÓN DIRECTA", "tipo_doc_bp_beneficiario": "NIT",
        "sector": "CULTURA",
    }
    rows = [
        # 2025 is already in the curated load: ignored.
        {**base, "vigencia_ejecucion": 2025, "cod_meta_proyecto_extendida": 22511,
         "no_crp": 900, "valor_crp_asignado_presupuestos_participativos": 600.0,
         "codigo_propuestas_financiadas_crp": "101;102"},
        {**base, "vigencia_ejecucion": 2026, "cod_meta_proyecto_extendida": 22512,
         "no_crp": 950, "valor_crp_asignado_presupuestos_participativos": 700.0,
         "codigo_propuestas_financiadas_crp": "105; 999"},  # 999 does not exist
        {**base, "vigencia_ejecucion": 2026, "cod_meta_proyecto_extendida": 99999,
         "no_crp": 951, "valor_crp_asignado_presupuestos_participativos": 50.0,
         "codigo_propuestas_financiadas_crp": "105"},  # meta does not exist
        {**base, "vigencia_ejecucion": 2026, "no_localidad": 7,
         "cod_meta_proyecto_extendida": 22512, "no_crp": 960,
         "valor_crp_asignado_presupuestos_participativos": 9999.0,
         "codigo_propuestas_financiadas_crp": "105"},  # another locality
    ]
    return pd.DataFrame(rows)
