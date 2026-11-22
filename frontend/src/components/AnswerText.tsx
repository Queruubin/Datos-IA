import type { MouseEvent, ReactNode } from 'react'

interface AnswerTextProps {
  text: string
  /** Evidence ids present in this answer (e.g. ["E1", "E2"]). */
  evidenceIds: string[]
  /** Builds the DOM id of the evidence card for a given evidence id. */
  anchorFor: (evidenceId: string) => string
}

const REFERENCE = /\b(E\d+)\b/g

function focusCard(event: MouseEvent<HTMLAnchorElement>, anchorId: string) {
  const card = document.getElementById(anchorId)
  if (!card) return
  // Avoid touching the URL hash, which is used for page navigation.
  event.preventDefault()
  card.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  card.focus({ preventScroll: true })
}

/** Renders the answer text, turning references like "(E1)" into links to their evidence card. */
export function AnswerText({ text, evidenceIds, anchorFor }: AnswerTextProps) {
  const known = new Set(evidenceIds)
  const parts: ReactNode[] = []
  let cursor = 0
  for (const match of text.matchAll(REFERENCE)) {
    const id = match[1]
    if (!known.has(id) || match.index === undefined) continue
    if (match.index > cursor) parts.push(text.slice(cursor, match.index))
    const anchorId = anchorFor(id)
    parts.push(
      <a
        key={`${id}-${match.index}`}
        href={`#${anchorId}`}
        onClick={(event) => focusCard(event, anchorId)}
        aria-label={`Ver evidencia ${id}`}
        className="mx-0.5 inline-block rounded bg-blue-100 px-1 text-xs font-bold text-blue-900 no-underline ring-1 ring-blue-300 hover:bg-blue-200 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-700"
      >
        {id}
      </a>,
    )
    cursor = match.index + id.length
  }
  if (cursor < text.length) parts.push(text.slice(cursor))
  return <p className="text-base break-words whitespace-pre-line text-slate-900">{parts}</p>
}
