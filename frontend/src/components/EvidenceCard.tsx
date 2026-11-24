import type { Evidence } from '../api/types'
import { cutoffLabel } from '../lib/formatDate'
import { isSafeUrl } from '../lib/url'
import { ChevronIcon, ExternalIcon } from './icons'

interface EvidenceCardProps {
  evidence: Evidence
  /** DOM id so inline references like "(E1)" can link to this card. */
  anchorId: string
}

/**
 * Compact evidence row: id, source, cut-off and summary at a glance; where the figure sits in the
 * source (and its origin when it is not on the open-data portal) behind a disclosure.
 */
export function EvidenceCard({ evidence, anchorId }: EvidenceCardProps) {
  const portal = isSafeUrl(evidence.portal_url) ? evidence.portal_url : null
  return (
    <article
      id={anchorId}
      tabIndex={-1}
      aria-labelledby={`${anchorId}-title`}
      className="scroll-mt-6 rounded-tile py-3 transition-shadow focus:outline-none focus:ring-2 focus:ring-wine-700 focus:ring-offset-4"
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5 grid h-6 min-w-7 shrink-0 place-items-center rounded-md bg-wine-700 px-1.5 text-xs font-bold text-white tabular-nums">
          {evidence.id}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <h4 id={`${anchorId}-title`} className="text-sm font-semibold break-words text-ink">
              {evidence.title}
            </h4>
            <p className="text-xs font-medium whitespace-nowrap text-ink-muted">{cutoffLabel(evidence.data_cutoff)}</p>
          </div>
          <p className="mt-1 text-sm leading-relaxed text-ink-muted [overflow-wrap:anywhere]">{evidence.summary}</p>
          <div className="mt-1 flex flex-wrap items-center gap-x-4">
            <details className="group text-xs">
              <summary className="focus-ring inline-flex min-h-8 cursor-pointer list-none items-center gap-1 rounded font-semibold text-wine-700 hover:text-wine-900 [&::-webkit-details-marker]:hidden">
                {portal ? 'Ubicación del dato' : 'Origen y ubicación'}
                <ChevronIcon className="h-3.5 w-3.5 shrink-0 transition-transform group-open:rotate-180" />
              </summary>
              <div className="mt-1 space-y-1 border-l-2 border-sand-200 pl-3 text-ink-muted">
                <p className="[overflow-wrap:anywhere]">
                  <span className="font-medium text-ink">Ubicación del dato:</span> {evidence.locator}
                </p>
                {!portal && evidence.origin_note && (
                  <p className="[overflow-wrap:anywhere]">
                    <span className="font-medium text-ink">Origen:</span> {evidence.origin_note}
                  </p>
                )}
              </div>
            </details>
            {portal && (
              <a
                href={portal}
                target="_blank"
                rel="noopener noreferrer"
                className="focus-ring inline-flex min-h-8 items-center gap-1 rounded text-xs font-semibold text-wine-700 underline-offset-2 hover:text-wine-900 hover:underline"
              >
                Ver fuente en Datos Abiertos
                <ExternalIcon className="h-3.5 w-3.5 shrink-0" />
                <span className="sr-only">(se abre en una pestaña nueva)</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}
