import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { EXAMPLE_QUESTIONS } from './lib/examples'
import { WELCOME_DONE_KEY } from './lib/storage'
import { chatResponse, DISCLAIMER, jsonResponse, mockFetch, source } from './test/fixtures'

beforeEach(() => {
  window.location.hash = ''
  window.localStorage.clear()
  // Most tests start in the chat: the welcome flow has its own tests below.
  window.localStorage.setItem(WELCOME_DONE_KEY, '1')
})

/** Quick-start cards are named by their title plus the question they send. */
const exampleButton = (index: number) =>
  screen.getByRole('button', { name: (name) => name.includes(EXAMPLE_QUESTIONS[index]) })

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Chat page', () => {
  it('shows the project name and the disclaimer before any question', () => {
    mockFetch()
    render(<App />)

    expect(
      screen.getByRole('heading', { level: 1, name: 'Verificador de información pública · San Cristóbal' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('note')).toHaveTextContent(DISCLAIMER)
  })

  it('sends an example question when clicked and renders the answer', async () => {
    const fetchMock = mockFetch()
    fetchMock.mockResolvedValue(jsonResponse(chatResponse()))
    render(<App />)

    await userEvent.click(exampleButton(0))

    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({ question: EXAMPLE_QUESTIONS[0] })
    expect(await screen.findByText(/Se ejecutó el 45 % del presupuesto/)).toBeInTheDocument()
    expect(screen.getByRole('article', { name: /Ranking mensual/ })).toBeInTheDocument()
    // Examples disappear once the conversation starts.
    expect(screen.queryByRole('button', { name: (name) => name.includes(EXAMPLE_QUESTIONS[0]) })).not.toBeInTheDocument()
  })

  it('limits the input to 500 characters and shows the counter', async () => {
    mockFetch()
    render(<App />)

    const input = screen.getByLabelText('Escribe tu pregunta')
    expect(input).toHaveAttribute('maxLength', '500')
    await userEvent.click(input)
    await userEvent.paste('a'.repeat(600))
    expect(input).toHaveValue('a'.repeat(500))
    expect(screen.getByText('500/500')).toBeInTheDocument()
  })

  it('sends with Enter and disables the input while loading', async () => {
    const fetchMock = mockFetch()
    let resolve: (value: Response) => void = () => {}
    fetchMock.mockReturnValue(new Promise<Response>((r) => (resolve = r)))
    render(<App />)

    const input = screen.getByLabelText('Escribe tu pregunta')
    await userEvent.type(input, '¿Cuánto se ejecutó?{Enter}')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(input).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Consultando…' })).toBeDisabled()
    expect(screen.getByRole('status')).toHaveTextContent('Consultando fuentes oficiales…')
    expect(screen.getByText('¿Cuánto se ejecutó?')).toBeInTheDocument()

    await act(async () => resolve(jsonResponse(chatResponse())))

    await waitFor(() => expect(input).not.toBeDisabled())
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('does not send empty questions', async () => {
    const fetchMock = mockFetch()
    render(<App />)

    await userEvent.type(screen.getByLabelText('Escribe tu pregunta'), '   {Enter}')

    expect(fetchMock).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'Enviar pregunta' })).toBeDisabled()
  })

  it.each([
    [429, 'Hiciste muchas preguntas en poco tiempo. Espera un momento e intenta de nuevo.'],
    [502, 'El servicio está ocupado en este momento. Intenta de nuevo en unos segundos.'],
    [503, 'El servicio de preguntas todavía no está configurado. Intenta más tarde.'],
  ])('shows a friendly message for HTTP %i', async (status, message) => {
    mockFetch().mockResolvedValue(jsonResponse({ detail: 'detalle del servidor' }, status))
    render(<App />)

    await userEvent.click(exampleButton(1))

    expect(await screen.findByText(message)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Intentar de nuevo' })).toBeInTheDocument()
  })

  it('explains a network failure and retries the same question', async () => {
    const fetchMock = mockFetch()
    fetchMock
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(jsonResponse(chatResponse()))
    render(<App />)

    await userEvent.click(exampleButton(2))
    expect(await screen.findByText(/No se pudo conectar con el servidor/)).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Intentar de nuevo' }))

    expect(await screen.findByText(/Se ejecutó el 45 % del presupuesto/)).toBeInTheDocument()
    expect(screen.queryByText(/No se pudo conectar con el servidor/)).not.toBeInTheDocument()
    expect(JSON.parse(fetchMock.mock.calls[1][1]?.body as string)).toEqual({ question: EXAMPLE_QUESTIONS[2] })
  })

  it('marks the message list as a polite live region', () => {
    mockFetch()
    render(<App />)

    expect(screen.getByRole('list', { name: 'Mensajes' })).toHaveAttribute('aria-live', 'polite')
  })
})

describe('Welcome flow', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('walks through the three steps on the first visit and asks from the last one', async () => {
    const fetchMock = mockFetch()
    fetchMock.mockResolvedValue(jsonResponse(chatResponse()))
    render(<App />)

    expect(screen.getByRole('heading', { level: 2, name: 'Hola. ¿Exploramos la localidad?' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Paso 1 de 3' })).toHaveAttribute('aria-current', 'step')
    expect(screen.getByText('Páramo de Cruz Verde')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Comenzar' }))
    const second = screen.getByRole('heading', { level: 2, name: 'Pregunta, comprende y actúa.' })
    expect(second).toHaveFocus()
    expect(screen.getByRole('heading', { level: 3, name: 'Actúa' })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Continuar' }))
    expect(screen.getByRole('heading', { level: 2, name: '¿Qué quieres saber o hacer?' })).toBeInTheDocument()

    await userEvent.click(exampleButton(0))

    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string)).toEqual({ question: EXAMPLE_QUESTIONS[0] })
    expect(await screen.findByText(/Se ejecutó el 45 % del presupuesto/)).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Introducción' })).not.toBeInTheDocument()
    expect(window.localStorage.getItem(WELCOME_DONE_KEY)).toBe('1')
  })

  it('can be skipped, is remembered and can be reopened from the header', async () => {
    mockFetch()
    const { unmount } = render(<App />)

    await userEvent.click(screen.getByRole('button', { name: 'Saltar' }))
    expect(screen.queryByRole('region', { name: 'Introducción' })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Escribe tu pregunta')).toBeInTheDocument()
    unmount()

    render(<App />)
    expect(screen.queryByRole('region', { name: 'Introducción' })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Ver introducción' }))
    expect(screen.getByRole('region', { name: 'Introducción' })).toBeInTheDocument()
  })

  it('still works when localStorage throws', async () => {
    mockFetch()
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    render(<App />)

    await userEvent.click(screen.getByRole('button', { name: 'Saltar' }))
    expect(screen.getByLabelText('Escribe tu pregunta')).toBeInTheDocument()
  })

  it('credits the background photo with author, license and Wikimedia Commons links', () => {
    mockFetch()
    render(<App />)

    expect(screen.getByRole('link', { name: 'Felipe Restrepo Acosta' })).toHaveAttribute(
      'href',
      'https://commons.wikimedia.org/wiki/User:Pedro_Felipe',
    )
    expect(screen.getByRole('link', { name: 'CC BY-SA 3.0' })).toHaveAttribute(
      'href',
      'https://creativecommons.org/licenses/by-sa/3.0',
    )
    expect(screen.getByRole('link', { name: 'Wikimedia Commons' })).toHaveAttribute('rel', 'noopener noreferrer')
  })
})

describe('Sources page', () => {
  it('lists sources with cut-off date, rows and a plain-Spanish unit', async () => {
    mockFetch().mockResolvedValue(
      jsonResponse([
        source(),
        source({ source_id: 'pqrs', table_name: 'pqrs', title: 'PQRS', unit: 'pesos', data_cutoff: null }),
        source({
          source_id: 'pac',
          table_name: 'pac',
          title: 'PAC',
          unit: 'unknown (likely millions of COP)',
          data_cutoff: '2026-09-30',
        }),
      ]),
    )
    window.location.hash = '#/fuentes'
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Ranking mensual de recursos ejecutados de PAC' })).toBeInTheDocument()
    expect(screen.getByText('jun 2025')).toBeInTheDocument()
    expect(screen.getAllByText('1.234')).toHaveLength(3)
    expect(screen.getByText('No aplica')).toBeInTheDocument()
    expect(screen.getByText('pesos')).toBeInTheDocument()
    expect(
      screen.getByText('No documentada por la fuente (probablemente millones de pesos)'),
    ).toBeInTheDocument()
    expect(screen.queryByText(/unknown/)).not.toBeInTheDocument()
    expect(screen.getByText('No indicada')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /Ver en Datos Abiertos/ })[0]).toHaveAttribute(
      'rel',
      'noopener noreferrer',
    )
    expect(screen.getByRole('link', { name: 'Fuentes' })).toHaveAttribute('aria-current', 'page')
  })

  it('shows the origin of curated sources that are not on the open-data portal', async () => {
    mockFetch().mockResolvedValue(
      jsonResponse([
        source({
          source_id: 'POAI',
          table_name: 'poai',
          title: 'POAI San Cristóbal 2025–2026',
          portal_url: null,
          unit: 'COP (pesos colombianos)',
          data_cutoff: null,
          origin_note: 'Archivo POAI entregado por la Alcaldía Local, consolidado por el equipo.',
        }),
      ]),
    )
    window.location.hash = '#/fuentes'
    render(<App />)

    expect(await screen.findByRole('heading', { name: 'POAI San Cristóbal 2025–2026' })).toBeInTheDocument()
    expect(screen.getByText(/Archivo POAI entregado por la Alcaldía Local/)).toBeInTheDocument()
    expect(screen.getByText('No publicada en el portal de Datos Abiertos.')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Ver en Datos Abiertos/ })).not.toBeInTheDocument()
    expect(screen.getByText('COP (pesos colombianos)')).toBeInTheDocument()
  })

  it('shows an error with retry when the backend is down', async () => {
    const fetchMock = mockFetch()
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch')).mockResolvedValueOnce(jsonResponse([source()]))
    window.location.hash = '#/fuentes'
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar con el servidor')
    await userEvent.click(screen.getByRole('button', { name: 'Intentar de nuevo' }))
    expect(await screen.findByText('No aplica')).toBeInTheDocument()
  })
})
