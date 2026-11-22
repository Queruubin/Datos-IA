import { useEffect, useRef } from 'react'
import { ChatInput } from '../components/ChatInput'
import { ExampleQuestions } from '../components/ExampleQuestions'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { MessageBubble } from '../components/MessageBubble'
import type { UseChat } from '../hooks/useChat'

interface ChatPageProps {
  chat: UseChat
}

export function ChatPage({ chat }: ChatPageProps) {
  const { messages, isLoading, send, retry } = chat
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' })
  }, [messages.length, isLoading])

  return (
    <div className="space-y-4">
      {messages.length === 0 && <ExampleQuestions onSelect={send} disabled={isLoading} />}

      <section aria-label="Conversación">
        <ol aria-label="Mensajes" aria-live="polite" aria-relevant="additions" className="space-y-4">
          {messages.map((message) => (
            <li key={message.id}>
              <MessageBubble message={message} onRetry={retry} retryDisabled={isLoading} />
            </li>
          ))}
        </ol>
        {isLoading && (
          <div className="mt-4">
            <LoadingIndicator />
          </div>
        )}
        <div ref={endRef} />
      </section>

      <div className="sticky bottom-0 -mx-4 border-t border-slate-200 bg-slate-50/95 px-4 pt-3 pb-4 backdrop-blur">
        <ChatInput onSend={send} isLoading={isLoading} />
      </div>
    </div>
  )
}
