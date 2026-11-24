import { answerChips, previewText } from '../lib/answerSummary'
import { moveBetweenPreviews } from '../lib/keyboard'
import type { AnswerMessage } from '../lib/selection'
import { AlertIcon, ArrowRightIcon, SparkIcon } from './icons'

interface MessagePreviewProps {
  message: AnswerMessage
  selected: boolean
  onSelect: (messageId: string) => void
}

/**
 * Concise assistant message in the conversation pane: the first lines of the answer and small
 * chips. Clicking it opens the full answer in the insight panel.
 */
export function MessagePreview({ message, selected, onSelect }: MessagePreviewProps) {
  const isError = message.role === 'error'
  const text = isError ? message.message : previewText(message.response.answer)
  const chips = isError ? [] : answerChips(message.response)

  return (
    <button
      type="button"
      data-answer-preview=""
      aria-current={selected ? 'true' : undefined}
      onClick={() => onSelect(message.id)}
      onKeyDown={moveBetweenPreviews}
      className={`focus-ring group relative flex w-full gap-3 rounded-card border p-3 text-left transition-colors ${
        selected
          ? 'border-wine-300 bg-wine-50'
          : 'border-transparent hover:border-sand-200 hover:bg-sand-50'
      }`}
    >
      <span
        aria-hidden="true"
        className={`mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full ${
          isError ? 'bg-red-100 text-red-800' : selected ? 'bg-wine-700 text-white' : 'bg-wine-100 text-wine-800'
        }`}
      >
        {isError ? <AlertIcon className="h-4 w-4 shrink-0" /> : <SparkIcon className="h-4 w-4 shrink-0" />}
      </span>
      <span className="min-w-0 flex-1">
        <span className="sr-only">{isError ? 'Error: ' : 'Respuesta: '}</span>
        <span className={`line-clamp-2 text-sm leading-snug ${isError ? 'text-red-900' : 'text-ink'}`}>{text}</span>
        {chips.length > 0 && (
          <span className="mt-2 flex flex-wrap gap-1.5">
            {chips.map((chip) => (
              <span
                key={chip}
                className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                  chip === 'Dato no publicado' ? 'bg-wine-100 text-wine-900' : 'bg-sand-100 text-ink-muted'
                }`}
              >
                {chip}
              </span>
            ))}
          </span>
        )}
        <span className="sr-only"> (ver en el panel)</span>
      </span>
      <ArrowRightIcon
        className={`mt-1 h-4 w-4 shrink-0 transition-opacity ${
          selected ? 'text-wine-700 opacity-100' : 'text-ink-muted opacity-0 group-hover:opacity-100'
        }`}
      />
    </button>
  )
}
