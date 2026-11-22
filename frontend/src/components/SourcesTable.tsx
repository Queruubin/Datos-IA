import type { SourceMetadata } from '../api/types'
import { formatCutoff, formatNumber } from '../lib/formatDate'
import { formatUnit } from '../lib/formatUnit'
import { isSafeUrl } from '../lib/url'
import { ExternalIcon } from './icons'

interface SourcesTableProps {
  sources: SourceMetadata[]
}

export function SourcesTable({ sources }: SourcesTableProps) {
  if (sources.length === 0) {
    return <p className="text-slate-700">Todavía no hay fuentes cargadas.</p>
  }

  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {sources.map((source) => (
        <li key={`${source.source_id}-${source.table_name}`}>
          <article className="h-full rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="font-semibold break-words text-slate-900">{source.title}</h3>
            <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
              <dt className="text-slate-600">Fecha de corte</dt>
              <dd className="text-slate-900">{formatCutoff(source.data_cutoff) ?? 'No indicada'}</dd>
              <dt className="text-slate-600">Registros</dt>
              <dd className="text-slate-900 tabular-nums">{formatNumber(source.rows)}</dd>
              <dt className="text-slate-600">Unidad</dt>
              <dd className="break-words text-slate-900">{formatUnit(source.unit)}</dd>
            </dl>
            {isSafeUrl(source.portal_url) && (
              <a
                href={source.portal_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-flex items-center gap-1 rounded text-sm font-medium text-blue-800 underline underline-offset-2 hover:text-blue-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
              >
                Ver en Datos Abiertos
                <ExternalIcon />
                <span className="sr-only">(se abre en una pestaña nueva)</span>
              </a>
            )}
          </article>
        </li>
      ))}
    </ul>
  )
}
