import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { DESKTOP_QUERY } from '../hooks/useMediaQuery'
import { WELCOME_DONE_KEY } from '../lib/storage'
import { chartSpec, chatResponse, evidence, jsonResponse, mockFetch } from '../test/fixtures'

/** Emulates a desktop (≥1024px) or narrow viewport for the CSS media query hook. */
function setViewport(desktop: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: desktop && query === DESKTOP_QUERY,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })),
  )
}

const ask = async (question: string) => {
  await userEvent.type(screen.getByLabelText('Escribe tu pregunta'), `${question}{Enter}`)
}

beforeEach(() => {
  window.location.hash = ''
  window.localStorage.clear()
  window.localStorage.setItem(WELCOME_DONE_KEY, '1')
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Chat workspace on desktop', () => {
  beforeEach(() => setViewport(true))

  it('starts with a welcome panel with quick starts and topics', () => {
    mockFetch()
    render(<App />)

    const empty = screen.getByRole('region', { name: 'Panel de respuestas' })
    expect(within(empty).getByRole('heading', { level: 2, name: '¿Qué quieres saber o hacer?' })).toBeInTheDocument()
    expect(within(empty).getByRole('heading', { name: 'Empieza con un ejemplo' })).toBeInTheDocument()
    expect(within(empty).getByText('Quejas y peticiones (PQRS)')).toBeInTheDocument()
  })

  it('shows the question with a skeleton while loading, then the answer in the panel', async () => {
    const fetchMock = mockFetch()
    let resolve: (value: Response) => void = () => {}
    fetchMock.mockReturnValue(new Promise<Response>((r) => (resolve = r)))
    render(<App />)

    await ask('¿Cuánto se ejecutó?')

    const loading = screen.getByRole('region', { name: '¿Cuánto se ejecutó?' })
    expect(within(loading).getByRole('status')).toHaveTextContent('Consultando fuentes oficiales…')
    expect(screen.getAllByRole('status')).toHaveLength(1)

    await act(async () => resolve(jsonResponse(chatResponse({ charts: [chartSpec()] }))))

    const answer = await screen.findByRole('region', { name: '¿Cuánto se ejecutó?' })
    await waitFor(() => expect(within(answer).queryByRole('status')).not.toBeInTheDocument())
    expect(within(answer).getByRole('region', { name: 'Inversión planeada 2026 por ODS (POAI)' })).toBeInTheDocument()
    expect(within(answer).getByRole('article', { name: evidence().title })).toBeInTheDocument()
    expect(within(answer).getByText(/Se ejecutó el 45 %/)).toBeInTheDocument()
  })

  it('keeps answers as previews in the conversation and opens the selected one in the panel', async () => {
    const fetchMock = mockFetch()
    fetchMock
      .mockResolvedValueOnce(jsonResponse(chatResponse({ answer: 'Primera respuesta (E1).' })))
      .mockResolvedValueOnce(
        jsonResponse(
          chatResponse({
            status: 'information_gap',
            answer: 'No encontré ese dato.',
            evidence: [],
            gap: { topic: 'seguridad', missing_data: 'Cámaras por barrio', kind: 'unpublished_data' },
          }),
        ),
      )
    render(<App />)

    await ask('Pregunta uno')
    await screen.findByRole('region', { name: 'Pregunta uno' })
    await ask('Pregunta dos')

    // The latest answer is auto-selected.
    const latest = await screen.findByRole('region', { name: 'Pregunta dos' })
    expect(within(latest).getByRole('region', { name: '¿Quieres pedir este dato a la Alcaldía?' })).toBeInTheDocument()

    const conversation = screen.getByRole('region', { name: 'Conversación' })
    const [first, second] = within(conversation).getAllByRole('button', { name: /^Respuesta:/ })
    expect(second).toHaveAttribute('aria-current', 'true')
    expect(second).toHaveTextContent('Dato no publicado')
    // Previews don't duplicate the full answer (no evidence cards or charts on the left).
    expect(within(conversation).queryByRole('article')).not.toBeInTheDocument()

    await userEvent.click(first)

    expect(first).toHaveAttribute('aria-current', 'true')
    const selected = screen.getByRole('region', { name: 'Pregunta uno' })
    expect(within(selected).getByText(/Primera respuesta/)).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Pregunta dos' })).not.toBeInTheDocument()

    // Arrow keys move between previews; the opened answer's title takes focus.
    await waitFor(() => expect(within(selected).getByRole('heading', { level: 2, name: 'Pregunta uno' })).toHaveFocus())
    first.focus()
    await userEvent.keyboard('{ArrowDown}')
    expect(second).toHaveFocus()
  })

  it('shows errors in the panel with a retry', async () => {
    const fetchMock = mockFetch()
    fetchMock
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(jsonResponse(chatResponse()))
    render(<App />)

    await ask('¿Y el presupuesto?')

    const failed = await screen.findByRole('region', { name: '¿Y el presupuesto?' })
    expect(within(failed).getByText(/No se pudo conectar con el servidor/)).toBeInTheDocument()
    await userEvent.click(within(failed).getByRole('button', { name: 'Intentar de nuevo' }))

    const answer = await screen.findByRole('region', { name: '¿Y el presupuesto?' })
    expect(await within(answer).findByText(/Se ejecutó el 45 %/)).toBeInTheDocument()
    expect(within(answer).queryByText(/No se pudo conectar/)).not.toBeInTheDocument()
  })
})

describe('Chat on narrow screens', () => {
  beforeEach(() => setViewport(false))

  it('renders the full answer inline under the question, without a side panel', async () => {
    mockFetch().mockResolvedValue(jsonResponse(chatResponse({ charts: [chartSpec()] })))
    render(<App />)

    await ask('¿Cuánto se ejecutó?')

    const conversation = screen.getByRole('region', { name: 'Conversación' })
    expect(await within(conversation).findByRole('region', { name: 'Inversión planeada 2026 por ODS (POAI)' })).toBeInTheDocument()
    expect(within(conversation).getByRole('article', { name: evidence().title })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Panel de respuestas' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Respuesta:/ })).not.toBeInTheDocument()
  })
})

describe('Disclaimer', () => {
  it('stays reachable on every page as a one-line note that unfolds', async () => {
    mockFetch().mockResolvedValue(jsonResponse([]))
    window.location.hash = '#/fuentes'
    render(<App />)

    const note = screen.getByRole('note')
    expect(note).toHaveTextContent('Este asistente no es vocero oficial de la Alcaldía')
    const toggle = screen.getByRole('button', { name: /Leer más/ })
    expect(toggle).toHaveAttribute('aria-controls', note.id)
    await userEvent.click(toggle)
    expect(screen.getByRole('button', { name: /Leer menos/ })).toHaveAttribute('aria-expanded', 'true')
  })
})
