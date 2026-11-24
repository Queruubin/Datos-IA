import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../hooks/useChat'
import { moveBetweenPreviews } from '../lib/keyboard'
import { scrollBehavior } from '../lib/motion'
import { ChatInput } from './ChatInput'
import { EmptyState } from './EmptyState'
import { LoadingIndicator } from './LoadingIndicator'
import { MessageBubble, UserBubble } from './MessageBubble'
import { MessagePreview } from './MessagePreview'
import { SparkIcon } from './icons'

interface ConversationPaneProps {
  messages: ChatMessage[]
  isLoading: boolean
  /**
   * 'split' (desktop): answers are short previews that open in the insight panel.
   * 'stacked' (mobile/tablet): every answer renders in full under its question.
   */
  layout: 'split' | 'stacked'
  /** Id of the answer shown in the panel ('pending' while following the question in progress). */
  selectedId?: string | null
  onSelect?: (messageId: string | null) => void
  onSend: (question: string) => void
  onRetry: (errorId: string) => void
}

function questionCount(messages: ChatMessage[]): string {
  const count = messages.filter((message) => message.role === 'user').length
  return `${count} ${count === 1 ? 'pregunta' : 'preguntas'}`
}

export function ConversationPane({
  messages,
  isLoading,
  layout,
  selectedId = null,
  onSelect = () => {},
  onSend,
  onRetry,
}: ConversationPaneProps) {
  const endRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef(new Map<string, HTMLLIElement>())
  const split = layout === 'split'
  const last = messages.at(-1)

  useEffect(() => {
    // Stacked: show a new answer from its top (its numbers first), not from the end of its evidence.
    if (!split && last && last.role !== 'user') {
      itemRefs.current.get(last.id)?.scrollIntoView?.({ behavior: scrollBehavior(), block: 'start' })
      return
    }
    endRef.current?.scrollIntoView?.({ behavior: scrollBehavior(), block: 'end' })
  }, [split, last, isLoading])

  const list = (
    <ol aria-label="Mensajes" aria-live="polite" aria-relevant="additions" className={split ? 'space-y-3' : 'space-y-4'}>
      {messages.map((message) => (
        <li
          key={message.id}
          ref={(element) => {
            if (element) itemRefs.current.set(message.id, element)
            else itemRefs.current.delete(message.id)
          }}
          className="scroll-mt-4"
        >
          {message.role === 'user' ? (
            <UserBubble text={message.text} />
          ) : split ? (
            <MessagePreview message={message} selected={message.id === selectedId} onSelect={onSelect} />
          ) : (
            <MessageBubble message={message} onRetry={onRetry} retryDisabled={isLoading} />
          )}
        </li>
      ))}
    </ol>
  )

  if (split) {
    return (
      <section aria-label="Conversación" className="flex h-full min-h-0 flex-col border-r border-sand-200 bg-white">
        <div className="flex items-center justify-between border-b border-sand-200 px-5 py-3">
          <h2 className="text-sm font-semibold text-ink">Conversación</h2>
          {messages.length > 0 && (
            <p className="text-xs text-ink-muted tabular-nums">{questionCount(messages)}</p>
          )}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center px-6 text-center">
              <span
                aria-hidden="true"
                className="grid h-12 w-12 place-items-center rounded-card bg-wine-50 text-wine-700 ring-1 ring-wine-200"
              >
                <SparkIcon className="h-6 w-6 shrink-0" />
              </span>
              <p className="mt-4 font-display text-base font-bold text-ink">Tu conversación empieza aquí</p>
              <p className="mt-1 max-w-xs text-sm leading-relaxed text-ink-muted">
                Escribe abajo o elige un ejemplo. Cada respuesta se abre a la derecha con sus cifras, gráficos y
                fuentes.
              </p>
            </div>
          )}
          {list}
          {isLoading && (
            <button
              type="button"
              data-answer-preview=""
              aria-current={selectedId === null ? 'true' : undefined}
              onClick={() => onSelect(null)}
              onKeyDown={moveBetweenPreviews}
              className={`focus-ring mt-3 flex w-full items-center gap-3 rounded-card border p-3 text-left text-sm ${
                selectedId === null ? 'border-wine-300 bg-wine-50' : 'border-transparent hover:bg-sand-50'
              }`}
            >
              <span aria-hidden="true" className="flex h-7 w-7 shrink-0 items-center justify-center gap-0.5">
                {[0, 1, 2].map((dot) => (
                  <span
                    key={dot}
                    className="h-1.5 w-1.5 rounded-full bg-wine-700 motion-safe:animate-pulse"
                    style={{ animationDelay: `${dot * 160}ms` }}
                  />
                ))}
              </span>
              <span className="text-ink-muted">Buscando en las fuentes…</span>
            </button>
          )}
          <div ref={endRef} />
        </div>
        <div className="border-t border-sand-200 bg-white px-4 pt-3 pb-3">
          <ChatInput onSend={onSend} isLoading={isLoading} />
        </div>
      </section>
    )
  }

  return (
    <section aria-label="Conversación" className="flex flex-1 flex-col">
      <div className="flex-1 space-y-4 px-4 pt-5 pb-4">
        {messages.length === 0 && <EmptyState onAsk={onSend} disabled={isLoading} />}
        {list}
        {isLoading && (
          <div className="rounded-card border border-sand-200 bg-white p-4">
            <LoadingIndicator />
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="sticky bottom-0 z-10 border-t border-sand-200 bg-canvas/95 px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur">
        <ChatInput onSend={onSend} isLoading={isLoading} />
      </div>
    </section>
  )
}
