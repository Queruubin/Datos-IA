import type { MouseEvent, ReactNode } from 'react'
import { focusElement } from '../lib/motion'

interface AnswerTextProps {
  text: string
  /** Evidence ids present in this answer (e.g. ["E1", "E2"]). */
  evidenceIds: string[]
  /** Builds the DOM id of the evidence card for a given evidence id. */
  anchorFor: (evidenceId: string) => string
}

const REFERENCE = /\b(E\d+)\b/g

function focusCard(event: MouseEvent<HTMLAnchorElement>, anchorId: string) {
  // Avoid touching the URL hash, which is used for page navigation.
  if (focusElement(anchorId)) event.preventDefault()
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
        className="mx-0.5 inline-block rounded bg-wine-50 px-1 text-xs font-bold text-wine-800 no-underline ring-1 ring-wine-200 hover:bg-wine-100 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-wine-700"
      >
        {id}
      </a>,
    )
    cursor = match.index + id.length
  }
  if (cursor < text.length) parts.push(text.slice(cursor))
  return <p className="text-base leading-relaxed break-words whitespace-pre-line text-ink">{parts}</p>
}
