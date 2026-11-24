import type { ChatMessage } from '../hooks/useChat'
import { AnswerDetail } from './AnswerDetail'
import { ErrorNotice } from './ErrorNotice'

interface MessageBubbleProps {
  message: ChatMessage
  onRetry?: (messageId: string) => void
  retryDisabled?: boolean
}

/** User question as a wine bubble. */
export function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[85%] rounded-card rounded-br-md bg-wine-700 px-4 py-2.5 text-[15px] leading-snug text-white">
        <p className="sr-only">Tu pregunta:</p>
        <p className="break-words whitespace-pre-line">{text}</p>
      </div>
    </div>
  )
}

/** One message rendered in full (single-column layout: the answer goes inline under its question). */
export function MessageBubble({ message, onRetry, retryDisabled }: MessageBubbleProps) {
  if (message.role === 'user') return <UserBubble text={message.text} />

  if (message.role === 'error') {
    return (
      <ErrorNotice
        message={message.message}
        onRetry={onRetry ? () => onRetry(message.id) : undefined}
        retryDisabled={retryDisabled}
      />
    )
  }

  return (
    <div className="rounded-card border border-sand-200 bg-white p-4 sm:p-5">
      <p className="sr-only">Respuesta del asistente:</p>
      <AnswerDetail messageId={message.id} response={message.response} />
    </div>
  )
}
