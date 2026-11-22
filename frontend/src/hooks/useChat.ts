import { useCallback, useRef, useState } from 'react'
import { postChat } from '../api/client'
import { errorMessage } from '../api/errors'
import type { ChatResponse } from '../api/types'

export const MAX_QUESTION_LENGTH = 500

export type ChatMessage =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'assistant'; response: ChatResponse }
  | { id: string; role: 'error'; message: string; question: string }

let counter = 0
const nextId = () => `m${++counter}`

export interface UseChat {
  messages: ChatMessage[]
  isLoading: boolean
  /** Disclaimer from the latest API answer, if any. */
  disclaimer: string | null
  send: (question: string) => Promise<void>
  retry: (errorId: string) => Promise<void>
}

export function useChat(ask: typeof postChat = postChat): UseChat {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [disclaimer, setDisclaimer] = useState<string | null>(null)
  const inFlight = useRef(false)

  const request = useCallback(
    async (question: string) => {
      inFlight.current = true
      setIsLoading(true)
      try {
        const response = await ask(question)
        if (response.disclaimer) setDisclaimer(response.disclaimer)
        setMessages((current) => [...current, { id: nextId(), role: 'assistant', response }])
      } catch (error) {
        setMessages((current) => [
          ...current,
          { id: nextId(), role: 'error', message: errorMessage(error), question },
        ])
      } finally {
        inFlight.current = false
        setIsLoading(false)
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

  return { messages, isLoading, disclaimer, send, retry }
}
