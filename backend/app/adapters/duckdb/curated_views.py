"""DuckDB equivalents of the analytic views defined by the curated load scripts
(`curated_data/*/sql/01_*.sql`), plus one helper view with the full meta context.

Privacy: `vw_pqrs_detalle` deliberately leaves out `pqrs.usuario_actual` (names of public
officials). The column stays in the `pqrs` table but no view or tool exposes it.
"""

CURATED_VIEWS: dict[str, str] = {
    # Carga_PMR_SC/sql/01_carga_pmr.sql (DISTINCT ON is supported by DuckDB).
    "vw_seguimiento_meta_ultimo_corte": """
        SELECT DISTINCT ON (id_meta, vigencia) *
        FROM seguimiento_meta
        ORDER BY id_meta, vigencia, fecha_corte DESC
    """,
    "vw_calidad_poai_pmr": """
        SELECT
            m.codigo_meta_extendida,
            m.codigo_indicador,
            p.vigencia,
            p.magnitud_programada AS magnitud_poai,
            s.magnitud_programada AS magnitud_pmr,
            s.magnitud_programada - p.magnitud_programada AS diferencia_magnitud,
            p.valor_poai AS valor_poai,
            s.presupuesto_programado AS presupuesto_pmr,
            s.presupuesto_programado - p.valor_poai AS diferencia_presupuesto,
            s.fecha_corte AS fecha_corte_pmr
        FROM meta_proyecto m
        JOIN poai p ON p.id_meta = m.id_meta
        JOIN vw_seguimiento_meta_ultimo_corte s
          ON s.id_meta = m.id_meta AND s.vigencia = p.vigencia
    """,
    # Carga_CRP_SC/sql/01_carga_crp.sql: one row per CRP + meta, summing the source lines.
    "vw_crp_meta_resumen": """
        SELECT
            c.id_crp,
            c.numero_crp,
            c.vigencia,
            m.id_meta,
            m.codigo_meta_extendida,
            COUNT(*) AS numero_lineas_asignacion,
            SUM(cm.valor_asignado_pp) AS valor_total_crp_meta,
            ANY_VALUE(cm.source) AS source
        FROM crp_meta cm
        JOIN crp c ON c.id_crp = cm.id_crp
        JOIN meta_proyecto m ON m.id_meta = cm.id_meta
        GROUP BY c.id_crp, c.numero_crp, c.vigencia, m.id_meta, m.codigo_meta_extendida
    """,
    # Carga_ODS_SC/sql/01_carga_ods.sql
    "vw_meta_ods_detalle": """
        SELECT
            m.id_meta,
            m.codigo_meta_extendida,
            m.descripcion_meta,
            o.codigo_ods,
            o.nombre_ods,
            o.esfera_ods,
            mo.codigo_meta_ods,
            mo.descripcion_meta_ods
        FROM meta_ods_relacion r
        JOIN meta_proyecto m ON m.id_meta = r.id_meta
        JOIN meta_ods mo ON mo.id_meta_ods = r.id_meta_ods
        JOIN ods o ON o.id_ods = mo.id_ods
    """,
    # Carga_PQRS_SC/sql/01_carga_pqrs.sql, WITHOUT usuario_actual.
    "vw_pqrs_detalle": """
        SELECT
            q.id_pqrs,
            q.radicado,
            q.numero_sdqs,
            q.vigencia,
            q.fecha_registro,
            q.fecha_radicacion,
            q.fecha_asignacion,
            tp.nombre_tipo_peticion,
            mr.nombre_medio AS medio_recepcion,
            st.nombre_subtema,
            q.tiempo_tramite,
            q.estado_orfeo,
            q.observacion_general,
            q.observacion_sac,
            q.dependencia_actual,
            q.ultima_dependencia,
            q.radicado_respuesta,
            q.fecha_respuesta,
            q.fecha_seguimiento,
            l.nombre_localidad,
            q.codigo_localidad_fuente
        FROM pqrs q
        JOIN localidad l ON l.id_localidad = q.id_localidad
        LEFT JOIN tipo_peticion tp ON tp.id_tipo_peticion = q.id_tipo_peticion
        LEFT JOIN medio_recepcion mr ON mr.id_medio_recepcion = q.id_medio_recepcion
        LEFT JOIN subtema_pqrs st ON st.id_subtema = q.id_subtema
    """,
    # Helper (not in the load scripts): meta -> proyecto -> programa -> objetivo, sector, entidad.
    "vw_meta_contexto": """
        SELECT
            m.id_meta,
            m.codigo_meta_extendida,
            m.codigo_indicador,
            m.indicador_producto,
            m.descripcion_meta,
            m.componente_proyecto,
            m.linea_inversion,
            m.concepto_gasto,
            m.componente_presupuestal,
            m.meta_total_2025_2028,
            m.tipo_anualizacion,
            p.codigo_proyecto,
            p.nombre_proyecto,
            pr.codigo_programa,
            pr.nombre_programa,
            o.codigo_objetivo,
            o.nombre_objetivo,
            s.nombre_sector,
            e.nombre_entidad
        FROM meta_proyecto m
        JOIN proyecto p ON p.id_proyecto = m.id_proyecto
        LEFT JOIN programa pr ON pr.id_programa = p.id_programa
        LEFT JOIN objetivo_estrategico o ON o.id_objetivo = pr.id_objetivo
        JOIN sector s ON s.id_sector = m.id_sector
        LEFT JOIN entidad e ON e.id_entidad = m.id_entidad
    """,
}
