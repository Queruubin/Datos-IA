import { useCallback, useRef, useState } from 'react'
import { postChat } from '../api/client'
import { errorMessage } from '../api/errors'
import type { ChatResponse } from '../api/types'
import { resolveSelection, type Selection } from '../lib/selection'

export const MAX_QUESTION_LENGTH = 500

export type ChatMessage =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'assistant'; response: ChatResponse; question: string }
  | { id: string; role: 'error'; message: string; question: string }

let counter = 0
const nextId = () => `m${++counter}`

export interface UseChat {
  messages: ChatMessage[]
  isLoading: boolean
  /** Question being answered right now (null when idle). */
  pendingQuestion: string | null
  /** Disclaimer from the latest API answer, if any. */
  disclaimer: string | null
  /** What the insight panel shows: an answer or error, the pending question, or nothing yet. */
  selection: Selection
  /** Opens an answer or error in the panel; null follows the latest one (or the pending question). */
  select: (messageId: string | null) => void
  send: (question: string) => Promise<void>
  retry: (errorId: string) => Promise<void>
}

export function useChat(ask: typeof postChat = postChat): UseChat {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null)
  const [disclaimer, setDisclaimer] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const inFlight = useRef(false)

  const request = useCallback(
    async (question: string) => {
      inFlight.current = true
      setPendingQuestion(question)
      // Follow the new question: the panel shows its loading state, then its answer.
      setSelectedId(null)
      const id = nextId()
      try {
        const response = await ask(question)
        if (response.disclaimer) setDisclaimer(response.disclaimer)
        setMessages((current) => [...current, { id, role: 'assistant', response, question }])
      } catch (error) {
        setMessages((current) => [...current, { id, role: 'error', message: errorMessage(error), question }])
      } finally {
        // The newest answer is auto-selected.
        setSelectedId(id)
        inFlight.current = false
        setPendingQuestion(null)
      }
    },
    [ask],
  )

  const send = useCallback(
    async (raw: string) => {
      const question = raw.trim().slice(0, MAX_QUESTION_LENGTH)
      if (!question || inFlight.current) return
      setMessages((current) => [...current, { id: nextId(), role: 'user', text: question }])
      await request(question)
    },
    [request],
  )

  const retry = useCallback(
    async (errorId: string) => {
      if (inFlight.current) return
      const failed = messages.find((message) => message.id === errorId)
      if (!failed || failed.role !== 'error') return
      setMessages((current) => current.filter((message) => message.id !== errorId))
      await request(failed.question)
    },
    [messages, request],
  )

  const isLoading = pendingQuestion !== null
  const selection = resolveSelection(messages, selectedId, pendingQuestion)

  return { messages, isLoading, pendingQuestion, disclaimer, selection, select: setSelectedId, send, retry }
}
