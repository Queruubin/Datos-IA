import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { ChatResponse, Verdict } from '../api/types'
import { chatResponse, evidence } from '../test/fixtures'
import { MessageBubble } from './MessageBubble'

const renderAnswer = (response: ChatResponse) =>
  render(<MessageBubble message={{ id: 'm1', role: 'assistant', response }} />)

describe('MessageBubble — answered', () => {
  it('renders the answer with evidence cards and a safe external link', () => {
    renderAnswer(chatResponse())

    const card = screen.getByRole('article', { name: /Ranking mensual de recursos ejecutados de PAC/ })
    expect(within(card).getByText('corte: 30 sep 2026')).toBeInTheDocument()
    expect(within(card).getByText('Ejecución acumulada de 45 % a junio de 2025.')).toBeInTheDocument()
    expect(within(card).getByText('pac_execution · año 2025')).toBeInTheDocument()

    const link = within(card).getByRole('link', { name: /Ver fuente en Datos Abiertos/ })
    expect(link).toHaveAttribute('href', 'https://datosabiertos.bogota.gov.co/dataset/pac')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('links inline references to their evidence card', () => {
    renderAnswer(chatResponse())

    const reference = screen.getByRole('link', { name: 'Ver evidencia E1' })
    const card = screen.getByRole('article')
    expect(reference).toHaveAttribute('href', `#${card.id}`)
  })

  it('does not link references without matching evidence', () => {
    renderAnswer(chatResponse({ answer: 'Ver (E1) y (E9).' }))

    expect(screen.getByRole('link', { name: 'Ver evidencia E1' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Ver evidencia E9' })).not.toBeInTheDocument()
  })

  it('does not render unsafe portal URLs as links', () => {
    renderAnswer(chatResponse({ evidence: [evidence({ portal_url: 'javascript:alert(1)' })] }))

    expect(screen.queryByRole('link', { name: /Ver fuente/ })).not.toBeInTheDocument()
  })
})

describe('MessageBubble — comparison verdict', () => {
  it.each<[Verdict, string]>([
    ['coherent', 'Coherente'],
    ['difference_detected', 'Diferencia detectada'],
    ['not_comparable', 'No comparable'],
  ])('shows the %s verdict as text', (verdict, label) => {
    renderAnswer(chatResponse({ comparison: { verdict, rule: 'Regla de contraste de prueba.' } }))

    const section = screen.getByRole('region', { name: 'Resultado del contraste entre fuentes' })
    expect(within(section).getByText(label)).toBeInTheDocument()
    expect(within(section).getByText('¿Cómo se hizo la comparación?')).toBeInTheDocument()
    expect(within(section).getByText('Regla de contraste de prueba.')).toBeInTheDocument()
  })

  it('hides the verdict when there is no comparison', () => {
    renderAnswer(chatResponse())

    expect(screen.queryByRole('region', { name: 'Resultado del contraste entre fuentes' })).not.toBeInTheDocument()
  })
})

describe('MessageBubble — other statuses', () => {
  it('renders the information gap card', () => {
    renderAnswer(
      chatResponse({
        status: 'information_gap',
        answer: 'No encontré ese dato en las fuentes.',
        evidence: [],
        gap: { topic: 'seguridad', missing_data: 'Número de cámaras instaladas por barrio' },
      }),
    )

    const card = screen.getByRole('region', { name: 'Este dato no está publicado' })
    expect(within(card).getByText('seguridad')).toBeInTheDocument()
    expect(within(card).getByText('Número de cámaras instaladas por barrio')).toBeInTheDocument()
    expect(within(card).getByText(/para que la Alcaldía Local sepa qué información/)).toBeInTheDocument()
  })

  it('renders a clarification request in a neutral style', () => {
    renderAnswer(
      chatResponse({ status: 'needs_clarification', answer: '¿De qué año quieres saber?', evidence: [] }),
    )

    expect(screen.getByText('Necesito más detalles')).toBeInTheDocument()
    expect(screen.getByText('¿De qué año quieres saber?')).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Este dato no está publicado' })).not.toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Evidencia' })).not.toBeInTheDocument()
  })

  it('renders an error with a retry button', async () => {
    const onRetry = vi.fn()
    render(
      <MessageBubble
        message={{ id: 'e1', role: 'error', message: 'El servicio está ocupado.', question: 'hola' }}
        onRetry={onRetry}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Intentar de nuevo' }))
    expect(onRetry).toHaveBeenCalledWith('e1')
  })
})
