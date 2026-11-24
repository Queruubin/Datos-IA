import type { ChatResponse } from '../api/types'
import { orderedCharts } from '../lib/answerSummary'
import { usageLine } from '../lib/formatUsage'
import { suggestsPetition } from '../lib/petition'
import { AnswerText } from './AnswerText'
import { ChartCard } from './charts/ChartCard'
import { EvidenceCard } from './EvidenceCard'
import { GapCard } from './GapCard'
import { QuestionIcon } from './icons'
import { PartialGapCard } from './PartialGapCard'
import { VerdictBadge } from './VerdictBadge'

interface AnswerDetailProps {
  /** Message id: makes evidence anchors unique across the conversation. */
  messageId: string
  response: ChatResponse
}

/**
 * The full answer: KPIs and charts first (the numbers), then the text with its evidence links,
 * the contrast verdict, the gap and petition when data is missing, the evidence list and the
 * usage line. Rendered in the insight panel (desktop) and inline under the question (mobile).
 */
export function AnswerDetail({ messageId, response }: AnswerDetailProps) {
  const anchorFor = (evidenceId: string) => `ev-${messageId}-${evidenceId}`
  const evidence = response.evidence ?? []
  const charts = orderedCharts(response)
  // An answer with related data only: suggest asking for the missing data (full gaps use GapCard).
  const partialGap =
    response.status === 'answered' && suggestsPetition(response.partial_gap) ? response.partial_gap : null

  return (
    <div className="space-y-6">
      {response.status === 'needs_clarification' && (
        <p className="eyebrow flex items-center gap-1.5">
          <QuestionIcon />
          Necesito más detalles
        </p>
      )}

      {charts.length > 0 && (
        <div aria-label="Gráficos de la respuesta" role="group" className="space-y-6">
          {charts.map((chart, index) => (
            <div key={chart.id} className={index > 0 ? 'border-t border-sand-200 pt-6' : undefined}>
              <ChartCard chart={chart} anchorFor={anchorFor} />
            </div>
          ))}
        </div>
      )}

      <div className={charts.length > 0 ? 'border-t border-sand-200 pt-6' : undefined}>
        {charts.length > 0 && <h3 className="eyebrow mb-2">Respuesta</h3>}
        <AnswerText text={response.answer} evidenceIds={evidence.map((item) => item.id)} anchorFor={anchorFor} />
      </div>

      {response.comparison && <VerdictBadge comparison={response.comparison} />}
      {response.status === 'information_gap' && <GapCard gap={response.gap} />}
      {partialGap && <PartialGapCard gap={partialGap} />}

      {evidence.length > 0 && (
        <section aria-label="Evidencia" className="border-t border-sand-200 pt-5">
          <h3 className="eyebrow">
            Evidencia · {evidence.length} {evidence.length === 1 ? 'fuente' : 'fuentes'}
          </h3>
          <ul className="mt-1 divide-y divide-sand-200">
            {evidence.map((item) => (
              <li key={item.id}>
                <EvidenceCard evidence={item} anchorId={anchorFor(item.id)} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {response.usage && (
        <p
          className="text-xs text-ink-muted tabular-nums"
          title="Equivalente en el plan pagado de Gemini. Con el plan gratuito el costo real es $0."
        >
          {usageLine(response.usage)}
        </p>
      )}
    </div>
  )
}
