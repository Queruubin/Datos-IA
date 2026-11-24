import type { SourceMetadata } from '../api/types'
import { formatCutoff, formatNumber } from '../lib/formatDate'
import { formatUnit } from '../lib/formatUnit'
import { isSafeUrl } from '../lib/url'
import { DocIcon, ExternalIcon } from './icons'

interface SourcesTableProps {
  sources: SourceMetadata[]
}

export function SourcesTable({ sources }: SourcesTableProps) {
  if (sources.length === 0) {
    return <p className="text-ink-muted">Todavía no hay fuentes cargadas.</p>
  }

  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {sources.map((source) => (
        <li key={`${source.source_id}-${source.table_name}`} className="min-w-0">
          <article className="flex h-full flex-col rounded-card border border-sand-200 bg-white p-5 transition-colors hover:border-sand-300">
            <div className="flex items-start gap-3">
              <span
                aria-hidden="true"
                className="grid h-9 w-9 shrink-0 place-items-center rounded-tile bg-wine-50 text-wine-700"
              >
                <DocIcon className="h-4 w-4 shrink-0" />
              </span>
              <h3 className="min-w-0 pt-1.5 font-display leading-snug font-bold break-words text-ink">{source.title}</h3>
            </div>
            <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
              <dt className="text-ink-muted">Fecha de corte</dt>
              <dd className="font-medium text-ink">{formatCutoff(source.data_cutoff) ?? 'No indicada'}</dd>
              <dt className="text-ink-muted">Registros</dt>
              <dd className="font-medium text-ink tabular-nums">{formatNumber(source.rows)}</dd>
              <dt className="text-ink-muted">Unidad</dt>
              <dd className="min-w-0 font-medium text-ink [overflow-wrap:anywhere]">{formatUnit(source.unit)}</dd>
            </dl>
            {source.origin_note && (
              <p className="mt-3 text-sm leading-relaxed text-ink-muted [overflow-wrap:anywhere]">
                <span className="font-medium text-ink">Origen:</span> {source.origin_note}
              </p>
            )}
            <div className="mt-auto pt-4">
              {isSafeUrl(source.portal_url) ? (
                <a
                  href={source.portal_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="focus-ring inline-flex items-center gap-1 rounded text-sm font-semibold text-wine-700 underline-offset-2 hover:text-wine-900 hover:underline"
                >
                  Ver en Datos Abiertos
                  <ExternalIcon />
                  <span className="sr-only">(se abre en una pestaña nueva)</span>
                </a>
              ) : (
                <p className="text-sm text-ink-muted">No publicada en el portal de Datos Abiertos.</p>
              )}
            </div>
          </article>
        </li>
      ))}
    </ul>
  )
}
