import type { ChatResponse } from '../api/types'
import type { ChatMessage } from '../hooks/useChat'
import { usageLine } from '../lib/formatUsage'
import { AnswerText } from './AnswerText'
import { EvidenceCard } from './EvidenceCard'
import { GapCard } from './GapCard'
import { AlertIcon, QuestionIcon } from './icons'
import { VerdictBadge } from './VerdictBadge'

interface MessageBubbleProps {
  message: ChatMessage
  onRetry?: (messageId: string) => void
  retryDisabled?: boolean
}

function AssistantContent({ messageId, response }: { messageId: string; response: ChatResponse }) {
  const anchorFor = (evidenceId: string) => `ev-${messageId}-${evidenceId}`
  const evidence = response.evidence ?? []

  return (
    <div className="space-y-3">
      {response.status === 'needs_clarification' && (
        <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-slate-600 uppercase">
          <QuestionIcon />
          Necesito más detalles
        </p>
      )}
      <AnswerText text={response.answer} evidenceIds={evidence.map((item) => item.id)} anchorFor={anchorFor} />
      {response.status === 'information_gap' && <GapCard gap={response.gap} />}
      {response.comparison && <VerdictBadge comparison={response.comparison} />}
      {evidence.length > 0 && (
        <section aria-label="Evidencia">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">
            Evidencia ({evidence.length} {evidence.length === 1 ? 'fuente' : 'fuentes'})
          </h3>
          <ul className="space-y-2">
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
          className="text-xs text-slate-500 tabular-nums"
          title="Equivalente en el plan pagado de Gemini. Con el plan gratuito el costo real es $0."
        >
          {usageLine(response.usage)}
        </p>
      )}
    </div>
  )
}

export function MessageBubble({ message, onRetry, retryDisabled }: MessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-blue-800 px-4 py-2 text-white">
          <p className="sr-only">Tu pregunta:</p>
          <p className="break-words whitespace-pre-line">{message.text}</p>
        </div>
      </div>
    )
  }

  if (message.role === 'error') {
    return (
      <div className="rounded-2xl rounded-bl-sm border border-red-300 bg-red-50 p-4 text-red-900">
        <p className="flex items-start gap-2">
          <AlertIcon className="mt-0.5 h-5 w-5 shrink-0" />
          <span>{message.message}</span>
        </p>
        {onRetry && (
          <button
            type="button"
            onClick={() => onRetry(message.id)}
            disabled={retryDisabled}
            className="mt-3 min-h-11 rounded-lg border border-red-800 bg-white px-4 py-2 text-sm font-semibold text-red-900 hover:bg-red-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            Intentar de nuevo
          </button>
        )}
      </div>
    )
  }

  const isClarification = message.response.status === 'needs_clarification'
  return (
    <div
      className={`rounded-2xl rounded-bl-sm border p-4 ${
        isClarification ? 'border-slate-300 bg-slate-100' : 'border-slate-200 bg-white shadow-sm'
      }`}
    >
      <p className="sr-only">Respuesta del asistente:</p>
      <AssistantContent messageId={message.id} response={message.response} />
    </div>
  )
}
