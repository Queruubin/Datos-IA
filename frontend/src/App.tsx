import { useEffect, useState } from 'react'
import { Header, type Page } from './components/Header'
import { useChat } from './hooks/useChat'
import { ChatPage } from './pages/ChatPage'
import { SourcesPage } from './pages/SourcesPage'
import { UsagePage } from './pages/UsagePage'

function pageFromHash(hash: string): Page {
  if (hash.startsWith('#/fuentes')) return 'sources'
  if (hash.startsWith('#/consumo')) return 'usage'
  return 'chat'
}

const TITLES: Record<Page, string> = {
  chat: 'Verificador de información pública · San Cristóbal',
  sources: 'Fuentes · Verificador de información pública · San Cristóbal',
  usage: 'Consumo · Verificador de información pública · San Cristóbal',
}

export default function App() {
  const [page, setPage] = useState<Page>(() => pageFromHash(window.location.hash))
  // Chat state lives here so the conversation survives switching pages.
  const chat = useChat()

  useEffect(() => {
    const onHashChange = () => setPage(pageFromHash(window.location.hash))
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  useEffect(() => {
    document.title = TITLES[page]
  }, [page])

  return (
    <div className="min-h-dvh">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-10 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:outline-2 focus:outline-blue-700"
        onClick={(event) => {
          event.preventDefault()
          document.getElementById('main')?.focus()
        }}
      >
        Ir al contenido
      </a>
      <Header page={page} disclaimer={chat.disclaimer} />
      <main id="main" tabIndex={-1} className="mx-auto max-w-3xl px-4 pt-4 focus:outline-none">
        {page === 'chat' && <ChatPage chat={chat} />}
        {page === 'sources' && <SourcesPage />}
        {page === 'usage' && <UsagePage />}
      </main>
    </div>
  )
}
