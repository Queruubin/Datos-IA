import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import type { ChatResponse } from '../../api/types'
import { chartSpec, chatResponse, evidence } from '../../test/fixtures'
import { MessageBubble } from '../MessageBubble'
import { ChartCard } from './ChartCard'

const anchorFor = (id: string) => `ev-m1-${id}`

describe('ChartCard', () => {
  it('shows title, unit, cut-off and compact COP labels', () => {
    render(<ChartCard chart={chartSpec()} anchorFor={anchorFor} />)

    const card = screen.getByRole('region', { name: 'Inversión planeada 2026 por ODS (POAI)' })
    expect(within(card).getByText('Unidad: Pesos colombianos (COP)')).toBeInTheDocument()
    expect(within(card).getByText('Corte: 30 jun 2026')).toBeInTheDocument()
    expect(within(card).getByRole('img', { name: /Gráfico de barras: Inversión planeada/ })).toBeInTheDocument()
    expect(within(card).getByText('$25,5 mil M')).toBeInTheDocument()
    expect(within(card).getByText('$4 M')).toBeInTheDocument()
  })

  it('links the evidence badges to their evidence cards', () => {
    render(<ChartCard chart={chartSpec({ evidence_ids: ['E2', 'E1'], evidence_id: 'E2' })} anchorFor={anchorFor} />)

    expect(screen.getByRole('link', { name: 'Ver evidencia E2 de este gráfico' })).toHaveAttribute('href', '#ev-m1-E2')
    expect(screen.getByRole('link', { name: 'Ver evidencia E1 de este gráfico' })).toHaveAttribute('href', '#ev-m1-E1')
  })

  it('toggles a data table with full values', async () => {
    render(<ChartCard chart={chartSpec()} anchorFor={anchorFor} />)

    const toggle = screen.getByRole('button', { name: 'Ver datos' })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(toggle)

    const table = screen.getByRole('table', { name: /Datos de: Inversión planeada/ })
    expect(within(table).getByRole('columnheader', { name: 'Planeado (POAI)' })).toBeInTheDocument()
    expect(within(table).getByText('$25.500.000.000 COP')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ocultar datos' })).toHaveAttribute('aria-expanded', 'true')
  })

  it('renders grouped bars with a legend', () => {
    render(
      <ChartCard
        chart={chartSpec({
          kind: 'grouped_bars',
          series: [
            { name: 'Planeado (POAI)', values: [10, 20] },
            { name: 'Compromisos (PMR)', values: [5, 8] },
            { name: 'Giros (PMR)', values: [1, null] },
          ],
        })}
        anchorFor={anchorFor}
      />,
    )

    const legend = screen.getByRole('list', { name: 'Leyenda' })
    expect(within(legend).getAllByRole('listitem')).toHaveLength(3)
    expect(screen.getAllByText('sin dato').length).toBeGreaterThan(0)
  })

  it('renders a monthly line chart without a currency for an unknown unit', async () => {
    render(
      <ChartCard
        chart={chartSpec({
          kind: 'line',
          title: 'PAC: programado vs ejecutado por mes',
          unit: 'unknown',
          categories: ['ene 2025', 'feb 2025'],
          series: [
            { name: 'Programado', values: [200, 300] },
            { name: 'Ejecutado', values: [150, 150] },
          ],
          note: 'La fuente no documenta la unidad monetaria del PAC.',
        })}
        anchorFor={anchorFor}
      />,
    )

    expect(screen.getByText('Unidad: Unidad no documentada por la fuente')).toBeInTheDocument()
    expect(screen.getByText('La fuente no documenta la unidad monetaria del PAC.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Ver datos' }))
    expect(screen.getByRole('columnheader', { name: 'Mes' })).toBeInTheDocument()
    expect(screen.queryByText(/\$/)).not.toBeInTheDocument()
  })

  it('renders KPI tiles with the code-computed verdict and no data toggle', () => {
    render(
      <ChartCard
        chart={chartSpec({
          kind: 'kpis',
          unit: 'count',
          title: 'Contraste POAI vs PMR 2026',
          categories: [],
          series: [],
          kpis: [
            { label: 'Metas comparadas', value: 104, unit: 'count' },
            { label: 'Comprometido', value: 43.2, unit: 'percent' },
            { label: 'Compromisos', value: 3_800_000_000, unit: 'COP' },
          ],
          verdict: 'difference_detected',
        })}
        anchorFor={anchorFor}
      />,
    )

    expect(screen.getByText('104')).toBeInTheDocument()
    expect(screen.getByText('43,2 %')).toBeInTheDocument()
    expect(screen.getByText('$3,8 mil M')).toBeInTheDocument()
    expect(screen.getByText('$3.800.000.000 COP')).toBeInTheDocument()
    expect(screen.getByText('Diferencia detectada')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Ver datos' })).not.toBeInTheDocument()
  })
})

describe('MessageBubble — charts', () => {
  const renderAnswer = (response: ChatResponse) =>
    render(<MessageBubble message={{ id: 'm1', role: 'assistant', response, question: '¿Pregunta de prueba?' }} />)

  it('shows charts above the answer text, linked to the evidence card', () => {
    renderAnswer(chatResponse({ charts: [chartSpec()] }))

    const chart = screen.getByRole('region', { name: 'Inversión planeada 2026 por ODS (POAI)' })
    const text = screen.getByText(/Se ejecutó el 45 %/)
    expect(chart.compareDocumentPosition(text) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByRole('link', { name: 'Ver evidencia E1 de este gráfico' })).toHaveAttribute(
      'href',
      `#${screen.getByRole('article', { name: evidence().title }).id}`,
    )
  })

  it('never shows charts for gaps even if some arrive', () => {
    renderAnswer(
      chatResponse({
        status: 'information_gap',
        evidence: [],
        gap: { topic: 'vías', missing_data: 'huecos' },
        charts: [chartSpec()],
      }),
    )

    expect(screen.queryByRole('group', { name: 'Gráficos de la respuesta' })).not.toBeInTheDocument()
  })

  it('works with older backends that send no charts', () => {
    renderAnswer(chatResponse())

    expect(screen.queryByRole('group', { name: 'Gráficos de la respuesta' })).not.toBeInTheDocument()
  })
})
