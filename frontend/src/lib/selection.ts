import type { ChatMessage } from '../hooks/useChat'

export type AnswerMessage = Extract<ChatMessage, { role: 'assistant' | 'error' }>

export type Selection =
  | { kind: 'empty' }
  | { kind: 'loading'; question: string }
  | { kind: 'message'; message: AnswerMessage }

const isAnswer = (message: ChatMessage): message is AnswerMessage => message.role !== 'user'

/**
 * Decides what the insight panel shows:
 * 1. the answer or error the person selected (if it still exists),
 * 2. otherwise the question being answered right now,
 * 3. otherwise the latest answer or error,
 * 4. otherwise nothing (empty state).
 */
export function resolveSelection(
  messages: ChatMessage[],
  selectedId: string | null,
  pendingQuestion: string | null,
): Selection {
  if (selectedId !== null) {
    const selected = messages.find((message) => message.id === selectedId)
    if (selected && isAnswer(selected)) return { kind: 'message', message: selected }
  }
  if (pendingQuestion !== null) return { kind: 'loading', question: pendingQuestion }
  const latest = messages.findLast(isAnswer)
  return latest ? { kind: 'message', message: latest } : { kind: 'empty' }
}
