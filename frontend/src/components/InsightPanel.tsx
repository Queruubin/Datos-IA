import { forwardRef, useEffect, useRef, type ReactNode } from 'react'
import type { ChatResponse } from '../api/types'
import { hasUnpublishedData } from '../lib/answerSummary'
import type { Selection } from '../lib/selection'
import { AnswerDetail } from './AnswerDetail'
import { EmptyState } from './EmptyState'
import { ErrorNotice } from './ErrorNotice'
import { LoadingIndicator } from './LoadingIndicator'
import { InfoIcon } from './icons'
import { VerdictPill } from './VerdictBadge'

interface InsightPanelProps {
  selection: Selection
  isLoading: boolean
  onAsk: (question: string) => void
  onRetry: (errorId: string) => void
}

/** Short status shown under the question, so the outcome reads at a glance (always icon/text, never color alone). */
function statusFor(response: ChatResponse): ReactNode {
  const unpublished = hasUnpublishedData(response)
  if (!response.comparison && !unpublished) return null
  return (
    <>
      {response.comparison && <VerdictPill verdict={response.comparison.verdict} />}
      {unpublished && (
        <span className="inline-flex items-center gap-1.5 rounded-full border border-wine-300 bg-wine-50 px-2.5 py-0.5 text-sm font-semibold text-wine-900">
          <InfoIcon />
          {response.status === 'answered' ? 'Respuesta parcial: falta un dato' : 'Dato no publicado'}
        </span>
      )}
    </>
  )
}

const Title = forwardRef<HTMLHeadingElement, { question: string; children?: ReactNode }>(function Title(
  { question, children },
  ref,
) {
  return (
    <header className="mb-8">
      <p className="eyebrow">Tu pregunta</p>
      <h2
        id="insight-title"
        ref={ref}
        tabIndex={-1}
        className="mt-2 font-display text-2xl leading-tight font-extrabold tracking-tight break-words text-ink focus:outline-none xl:text-[32px] xl:leading-[1.15]"
      >
        {question}
      </h2>
      {children && <div className="mt-3 flex flex-wrap items-center gap-2">{children}</div>}
    </header>
  )
})

/**
 * Desktop panel with everything about the selected answer: question, verdict, KPIs, charts,
 * text, gap and petition, evidence and usage. Empty state and loading skeleton too.
 */
export const InsightPanel = forwardRef<HTMLHeadingElement, InsightPanelProps>(function InsightPanel(
  { selection, isLoading, onAsk, onRetry },
  titleRef,
) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const key =
    selection.kind === 'message' ? selection.message.id : selection.kind === 'loading' ? 'loading' : 'empty'

  useEffect(() => {
    // A new selection starts at the top of the panel.
    scrollRef.current?.scrollTo?.({ top: 0 })
  }, [key])

  let content: ReactNode
  if (selection.kind === 'empty') {
    content = <EmptyState variant="panel" onAsk={onAsk} disabled={isLoading} />
  } else if (selection.kind === 'loading') {
    content = (
      <>
        <Title ref={titleRef} question={selection.question} />
        <LoadingIndicator />
      </>
    )
  } else if (selection.message.role === 'error') {
    const message = selection.message
    content = (
      <>
        <Title ref={titleRef} question={message.question} />
        <ErrorNotice message={message.message} onRetry={() => onRetry(message.id)} retryDisabled={isLoading} />
      </>
    )
  } else {
    const { id, question, response } = selection.message
    content = (
      <>
        <Title ref={titleRef} question={question}>
          {statusFor(response)}
        </Title>
        <AnswerDetail messageId={id} response={response} />
      </>
    )
  }

  return (
    <section
      aria-labelledby={selection.kind === 'empty' ? undefined : 'insight-title'}
      aria-label={selection.kind === 'empty' ? 'Panel de respuestas' : undefined}
      className="h-full min-h-0"
    >
      <div ref={scrollRef} className="h-full overflow-y-auto px-6 py-6 xl:px-10 xl:py-8">
        <div
          key={key}
          className="mx-auto max-w-4xl rounded-panel border border-sand-200 bg-white p-6 shadow-panel motion-safe:animate-panel-in xl:p-10"
        >
          {content}
        </div>
      </div>
    </section>
  )
})
