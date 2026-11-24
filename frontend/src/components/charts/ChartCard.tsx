import { useId, useState, type MouseEvent } from 'react'
import type { ChartSpec } from '../../api/types'
import { formatCutoff } from '../../lib/formatDate'
import { formatFull, UNIT_LABELS } from '../../lib/formatValue'
import { focusElement } from '../../lib/motion'
import { ChevronIcon, InfoIcon } from '../icons'
import { BarChart } from './BarChart'
import { KpiTiles } from './KpiTiles'
import { LineChart } from './LineChart'

interface ChartCardProps {
  chart: ChartSpec
  /** Builds the DOM id of the evidence card for an evidence id. */
  anchorFor: (evidenceId: string) => string
}

const KIND_NAMES: Record<ChartSpec['kind'], string> = {
  bars: 'Gráfico de barras',
  grouped_bars: 'Gráfico de barras agrupadas',
  line: 'Gráfico de líneas',
  kpis: 'Indicadores',
}

function DataTable({ chart, id }: { chart: ChartSpec; id: string }) {
  const firstHeader = chart.kind === 'line' ? 'Mes' : 'Categoría'
  return (
    <div id={id} className="mt-2 overflow-x-auto rounded-tile border border-sand-200">
      <table className="w-full text-left text-xs">
        <caption className="sr-only">Datos de: {chart.title}</caption>
        <thead className="bg-sand-100 text-ink">
          <tr>
            <th scope="col" className="px-3 py-2 font-semibold">
              {firstHeader}
            </th>
            {chart.series.map((series) => (
              <th key={series.name} scope="col" className="px-3 py-2 text-right font-semibold">
                {series.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {chart.categories.map((category, row) => (
            <tr key={`${category}-${row}`} className="border-t border-sand-200">
              <th scope="row" className="px-3 py-2 font-normal break-words text-ink">
                {category}
              </th>
              {chart.series.map((series) => (
                <td key={series.name} className="px-3 py-2 text-right whitespace-nowrap text-ink tabular-nums">
                  {formatFull(series.values[row] ?? null, chart.unit)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * One chart built by backend code. Shows title, unit, cut-off and links to the evidence that
 * backs it, plus a "Ver datos" table (the accessible twin of the graphic). Flat: it sits on the
 * answer surface, separated by hairlines, never as a card inside a card.
 */
export function ChartCard({ chart, anchorFor }: ChartCardProps) {
  const uid = useId()
  const titleId = `${uid}-title`
  const tableId = `${uid}-table`
  const [showTable, setShowTable] = useState(false)
  const cutoff = formatCutoff(chart.data_cutoff)
  const isKpis = chart.kind === 'kpis'
  const ids = chart.evidence_ids.length > 0 ? chart.evidence_ids : [chart.evidence_id]

  const goTo = (event: MouseEvent<HTMLAnchorElement>, evidenceId: string) => {
    if (focusElement(anchorFor(evidenceId))) event.preventDefault()
  }

  return (
    <section aria-labelledby={titleId} className="@container">
      <h3 id={titleId} className="font-display text-base leading-snug font-bold text-ink sm:text-lg">
        {chart.title}
      </h3>
      <p className="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-ink-muted">
        {!isKpis && <span>Unidad: {UNIT_LABELS[chart.unit]}</span>}
        {!isKpis && <span aria-hidden="true">·</span>}
        <span>{cutoff ? `Corte: ${cutoff}` : 'Corte no indicado'}</span>
        <span aria-hidden="true">·</span>
        <span>Fuente:</span>
        {ids.map((id) => (
          <a
            key={id}
            href={`#${anchorFor(id)}`}
            onClick={(event) => goTo(event, id)}
            aria-label={`Ver evidencia ${id} de este gráfico`}
            className="focus-ring rounded-md bg-wine-50 px-1.5 py-0.5 font-bold text-wine-800 ring-1 ring-wine-200 transition-colors hover:bg-wine-100"
          >
            {id}
          </a>
        ))}
      </p>

      <div className="mt-4">
        {isKpis ? (
          <KpiTiles chart={chart} />
        ) : (
          <div
            role="img"
            aria-label={`${KIND_NAMES[chart.kind]}: ${chart.title}. ${chart.categories.length} categorías. Usa “Ver datos” para leer los valores.`}
          >
            {chart.kind === 'line' ? <LineChart chart={chart} /> : <BarChart chart={chart} />}
          </div>
        )}
      </div>

      {chart.note && (
        <p className="mt-3 flex items-start gap-1.5 text-xs leading-relaxed text-ink-muted">
          <InfoIcon className="mt-px h-3.5 w-3.5 shrink-0 text-wine-700" />
          <span>{chart.note}</span>
        </p>
      )}

      {!isKpis && (
        <>
          <button
            type="button"
            aria-expanded={showTable}
            aria-controls={tableId}
            onClick={() => setShowTable((open) => !open)}
            className="focus-ring -ml-2 mt-1 inline-flex min-h-11 items-center gap-1 rounded-full px-2 text-sm font-semibold text-wine-700 transition-colors hover:text-wine-900"
          >
            {showTable ? 'Ocultar datos' : 'Ver datos'}
            <ChevronIcon className={`h-4 w-4 shrink-0 transition-transform ${showTable ? 'rotate-180' : ''}`} />
          </button>
          {showTable && <DataTable chart={chart} id={tableId} />}
        </>
      )}
    </section>
  )
}
