import { useEffect, useState } from 'react'
import { DisclaimerBar } from './components/DisclaimerBar'
import { Header, type Page } from './components/Header'
import { WelcomeFlow } from './components/WelcomeFlow'
import { useChat } from './hooks/useChat'
import { readFlag, WELCOME_DONE_KEY, writeFlag } from './lib/storage'
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
  const [welcomeOpen, setWelcomeOpen] = useState(() => !readFlag(WELCOME_DONE_KEY))
  const [welcomeStep, setWelcomeStep] = useState(0)
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

  const showWelcome = page === 'chat' && welcomeOpen
  // The chat workspace fills the viewport on desktop (each pane scrolls on its own).
  const workspace = page === 'chat' && !showWelcome

  const finishWelcome = () => {
    writeFlag(WELCOME_DONE_KEY, true)
    setWelcomeOpen(false)
    if (window.scrollY > 0) window.scrollTo(0, 0)
    document.getElementById('main')?.focus({ preventScroll: true })
  }

  const openWelcome = () => {
    setWelcomeStep(0)
    setWelcomeOpen(true)
    if (page !== 'chat') window.location.hash = '#/'
  }

  const askFromWelcome = (question: string) => {
    finishWelcome()
    void chat.send(question)
  }

  return (
    <div className={`flex min-h-dvh flex-col ${workspace ? 'lg:h-dvh lg:overflow-hidden' : ''}`}>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-40 focus:rounded focus:bg-white focus:px-3 focus:py-2 focus:outline-2 focus:outline-wine-700"
        onClick={(event) => {
          event.preventDefault()
          document.getElementById('main')?.focus()
        }}
      >
        Ir al contenido
      </a>
      <Header page={page} onShowWelcome={openWelcome} />
      <DisclaimerBar disclaimer={chat.disclaimer} />
      <main id="main" tabIndex={-1} className="flex min-h-0 flex-1 flex-col focus:outline-none">
        {showWelcome && (
          <WelcomeFlow
            step={welcomeStep}
            onStepChange={setWelcomeStep}
            onFinish={finishWelcome}
            onAsk={askFromWelcome}
            isLoading={chat.isLoading}
          />
        )}
        {workspace && (
          <div className="flex flex-1 flex-col lg:min-h-0">
            <ChatPage chat={chat} />
          </div>
        )}
        {page === 'sources' && <SourcesPage />}
        {page === 'usage' && <UsagePage />}
      </main>
    </div>
  )
}
