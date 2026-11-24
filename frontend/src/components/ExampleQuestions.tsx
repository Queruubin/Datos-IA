import { QUICK_STARTS, type QuickStart } from '../lib/examples'
import { ArrowRightIcon } from './icons'

interface ExampleQuestionsProps {
  onSelect: (question: string) => void
  disabled?: boolean
  items?: QuickStart[]
  /** Heading id; the component is rendered in the welcome flow and in the empty chat. */
  headingId?: string
  heading?: string
  /** Grid columns from the sm breakpoint (the empty conversation pane on mobile uses 1-2). */
  columns?: 2 | 3
}

/** Quick-start cards: one tap sends a ready-made question. */
export function ExampleQuestions({
  onSelect,
  disabled,
  items = QUICK_STARTS,
  headingId = 'examples-title',
  heading = 'Empieza con un ejemplo',
  columns = 2,
}: ExampleQuestionsProps) {
  return (
    <section aria-labelledby={headingId}>
      <h3 id={headingId} className="text-sm font-semibold text-ink">
        {heading}
      </h3>
      <ul className={`mt-3 grid gap-2 sm:grid-cols-2 ${columns === 3 ? 'xl:grid-cols-3' : ''}`}>
        {items.map((item) => (
          <li key={item.question} className="flex">
            <button
              type="button"
              onClick={() => onSelect(item.question)}
              disabled={disabled}
              className="focus-ring group flex min-h-11 w-full flex-col items-start gap-1 rounded-card border border-sand-200 bg-white px-4 py-3 text-left transition hover:-translate-y-px hover:border-wine-300 hover:bg-wine-50 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
            >
              <span className="flex w-full items-center justify-between gap-2">
                <span className="eyebrow">{item.title}</span>
                <ArrowRightIcon className="h-4 w-4 shrink-0 text-wine-700 opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100" />
              </span>
              <span className="text-sm leading-snug font-medium text-ink">{item.question}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
