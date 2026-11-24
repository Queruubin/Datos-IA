import type { Evidence } from '../api/types'
import { cutoffLabel } from '../lib/formatDate'
import { isSafeUrl } from '../lib/url'
import { ExternalIcon } from './icons'

interface EvidenceCardProps {
  evidence: Evidence
  /** DOM id so inline references like "(E1)" can link to this card. */
  anchorId: string
}

export function EvidenceCard({ evidence, anchorId }: EvidenceCardProps) {
  return (
    <article
      id={anchorId}
      tabIndex={-1}
      aria-labelledby={`${anchorId}-title`}
      className="scroll-mt-24 rounded-lg border border-slate-200 bg-white p-3 shadow-sm focus:outline-none target:ring-2 target:ring-blue-700"
    >
      <div className="flex items-start gap-2">
        <span className="shrink-0 rounded bg-blue-800 px-1.5 py-0.5 text-xs font-bold text-white">
          {evidence.id}
        </span>
        <h4 id={`${anchorId}-title`} className="min-w-0 flex-1 text-sm font-semibold break-words text-slate-900">
          {evidence.title}
        </h4>
      </div>
      <p className="mt-1 text-xs font-medium text-slate-600">{cutoffLabel(evidence.data_cutoff)}</p>
      <p className="mt-2 text-sm break-words text-slate-800">{evidence.summary}</p>
      <p className="mt-2 text-xs break-words text-slate-600">
        <span className="font-medium">Ubicación del dato:</span> {evidence.locator}
      </p>
      {!isSafeUrl(evidence.portal_url) && evidence.origin_note && (
        <p className="mt-1 text-xs break-words text-slate-600">
          <span className="font-medium">Origen:</span> {evidence.origin_note}
        </p>
      )}
      {isSafeUrl(evidence.portal_url) && (
        <a
          href={evidence.portal_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-flex items-center gap-1 rounded text-sm font-medium text-blue-800 underline underline-offset-2 hover:text-blue-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
        >
          Ver fuente en Datos Abiertos
          <ExternalIcon />
          <span className="sr-only">(se abre en una pestaña nueva)</span>
        </a>
      )}
    </article>
  )
}
