import { describe, expect, it } from 'vitest'
import type { ChatMessage } from '../hooks/useChat'
import { chatResponse } from '../test/fixtures'
import { resolveSelection } from './selection'

const messages: ChatMessage[] = [
  { id: 'm1', role: 'user', text: 'Primera' },
  { id: 'm2', role: 'assistant', response: chatResponse(), question: 'Primera' },
  { id: 'm3', role: 'user', text: 'Segunda' },
  { id: 'm4', role: 'error', message: 'Falló', question: 'Segunda' },
]

describe('resolveSelection', () => {
  it('is empty before any question', () => {
    expect(resolveSelection([], null, null)).toEqual({ kind: 'empty' })
  })

  it('follows the latest answer or error when nothing is selected', () => {
    expect(resolveSelection(messages, null, null)).toMatchObject({ kind: 'message', message: { id: 'm4' } })
  })

  it('keeps an explicitly selected earlier answer', () => {
    expect(resolveSelection(messages, 'm2', null)).toMatchObject({ kind: 'message', message: { id: 'm2' } })
  })

  it('shows the pending question while loading unless an answer was picked', () => {
    expect(resolveSelection(messages, null, 'Tercera')).toEqual({ kind: 'loading', question: 'Tercera' })
    expect(resolveSelection(messages, 'm2', 'Tercera')).toMatchObject({ kind: 'message', message: { id: 'm2' } })
  })

  it('ignores user messages and ids that no longer exist', () => {
    expect(resolveSelection(messages, 'm1', null)).toMatchObject({ message: { id: 'm4' } })
    expect(resolveSelection(messages, 'gone', null)).toMatchObject({ message: { id: 'm4' } })
  })
})
