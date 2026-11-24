import { useRef } from 'react'
import { ConversationPane } from '../components/ConversationPane'
import { InsightPanel } from '../components/InsightPanel'
import type { UseChat } from '../hooks/useChat'
import { DESKTOP_QUERY, useMediaQuery } from '../hooks/useMediaQuery'

interface ChatPageProps {
  chat: UseChat
}

/**
 * Desktop (≥1024px): conversation on the left, insight panel with the selected answer on the
 * right. Below that, a single column with every answer in full under its question.
 */
export function ChatPage({ chat }: ChatPageProps) {
  const { messages, isLoading, selection, select, send, retry } = chat
  const isDesktop = useMediaQuery(DESKTOP_QUERY)
  const panelTitleRef = useRef<HTMLHeadingElement>(null)

  if (!isDesktop) {
    return <ConversationPane layout="stacked" messages={messages} isLoading={isLoading} onSend={send} onRetry={retry} />
  }

  const selectedId = selection.kind === 'message' ? selection.message.id : null

  const openInPanel = (messageId: string | null) => {
    select(messageId)
    // Keyboard and screen-reader users land on the answer they just opened.
    requestAnimationFrame(() => panelTitleRef.current?.focus({ preventScroll: true }))
  }

  return (
    <div className="grid min-h-0 flex-1 grid-cols-[minmax(340px,40fr)_60fr] grid-rows-[minmax(0,1fr)]">
      <ConversationPane
        layout="split"
        messages={messages}
        isLoading={isLoading}
        selectedId={selectedId}
        onSelect={openInPanel}
        onSend={send}
        onRetry={retry}
      />
      <InsightPanel ref={panelTitleRef} selection={selection} isLoading={isLoading} onAsk={send} onRetry={retry} />
    </div>
  )
}
