import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { API_BASE_URL } from '../api/client'
import { jsonResponse, mockFetch, usageReport } from '../test/fixtures'

beforeEach(() => {
  window.location.hash = '#/consumo'
})

afterEach(() => {
  vi.unstubAllGlobals()
})

const tileValue = (label: string) => screen.getByText(label).nextElementSibling

describe('Usage page', () => {
  it('shows KPIs, the free-tier note, models, days, rate and prices', async () => {
    const fetchMock = mockFetch()
    fetchMock.mockResolvedValue(jsonResponse(usageReport()))
    render(<App />)

    expect(await screen.findByText('Costo equivalente USD')).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][0]).toBe(`${API_BASE_URL}/api/usage`)
    expect(screen.getByRole('link', { name: 'Consumo' })).toHaveAttribute('aria-current', 'page')
    expect(
      screen.getByText(
        'Con el plan gratuito de Gemini el costo real es $0; estas cifras son el equivalente en el plan pagado.',
      ),
    ).toBeInTheDocument()

    expect(tileValue('Preguntas')).toHaveTextContent('12')
    expect(tileValue('Tokens totales')).toHaveTextContent('38.880')
    expect(tileValue('Costo equivalente USD')).toHaveTextContent('USD 0,025')
    expect(tileValue('Costo equivalente COP')).toHaveTextContent('COP 98')
    expect(tileValue('Costo promedio por pregunta')).toHaveTextContent('USD 0,0021')

    const [models, prices] = screen.getAllByRole('table')
    expect(within(models).getByRole('row', { name: /gemini-3\.5-flash-lite/ })).toHaveTextContent('30')
    expect(within(models).getByRole('row', { name: /gemini-x/ })).toHaveTextContent('Sin precio')
    expect(screen.getByText(/6 llamadas usaron un modelo sin precio conocido/)).toBeInTheDocument()

    expect(screen.getByText('22 nov 2026')).toBeInTheDocument()
    expect(screen.getByText(/3\.461,92 COP por USD/)).toBeInTheDocument()
    expect(screen.getByText(/vigente desde el 21 nov 2026/)).toBeInTheDocument()
    expect(screen.getByText(/TRM oficial publicada en datos\.gov\.co/)).toBeInTheDocument()
    expect(within(prices).getByText('Desde el 1 ene 2027')).toBeInTheDocument()
    expect(within(prices).getAllByText('0,30')).toHaveLength(1)
    expect(screen.getByRole('link', { name: /tabla oficial de precios/ })).toHaveAttribute(
      'href',
      'https://aistudio.google.com/docs/pricing',
    )
  })

  it('shows an empty state but still explains prices', async () => {
    const report = usageReport()
    mockFetch().mockResolvedValue(
      jsonResponse({
        ...report,
        all_time: { ...report.all_time, questions: 0, calls: 0, total_tokens: 0 },
        by_model: [],
        by_day: [],
        exchange_rate: { value: null, valid_from: null, source: 'unavailable' },
      }),
    )
    render(<App />)

    expect(await screen.findByText(/Todavía no hay preguntas registradas/)).toBeInTheDocument()
    expect(screen.queryByText('Costo equivalente USD')).not.toBeInTheDocument()
    expect(screen.getByText(/Tasa de cambio: no disponible/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Precios usados' })).toBeInTheDocument()
  })

  it('shows an error with retry when the backend is down', async () => {
    const fetchMock = mockFetch()
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch')).mockResolvedValueOnce(jsonResponse(usageReport()))
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar con el servidor')
    await userEvent.click(screen.getByRole('button', { name: 'Intentar de nuevo' }))
    expect(await screen.findByText('Costo equivalente USD')).toBeInTheDocument()
  })
})
