import type { KeyboardEvent } from 'react'

/** Arrow keys move between answer previews (Tab still works as usual). */
export function moveBetweenPreviews(event: KeyboardEvent<HTMLButtonElement>) {
  if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return
  const all = Array.from(document.querySelectorAll<HTMLButtonElement>('[data-answer-preview]'))
  const index = all.indexOf(event.currentTarget)
  const next = all[index + (event.key === 'ArrowDown' ? 1 : -1)]
  if (next) {
    event.preventDefault()
    next.focus()
  }
}
