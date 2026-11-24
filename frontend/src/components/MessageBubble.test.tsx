import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { ChatResponse, Verdict } from '../api/types'
import { chatResponse, evidence, questionUsage } from '../test/fixtures'
import { MessageBubble } from './MessageBubble'

const renderAnswer = (response: ChatResponse) =>
  render(<MessageBubble message={{ id: 'm1', role: 'assistant', response, question: '¿Pregunta de prueba?' }} />)

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

  it('shows the origin of evidence that has no open-data portal link', () => {
    renderAnswer(
      chatResponse({
        evidence: [evidence({ portal_url: null, origin_note: 'Archivo POAI entregado por la Alcaldía Local.' })],
      }),
    )

    expect(screen.queryByRole('link', { name: /Ver fuente/ })).not.toBeInTheDocument()
    expect(screen.getByText('Archivo POAI entregado por la Alcaldía Local.')).toBeInTheDocument()
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

  it('suggests a right-of-petition draft for unpublished data', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    renderAnswer(
      chatResponse({
        status: 'information_gap',
        answer: 'No encontré ese dato.',
        evidence: [],
        gap: { topic: 'seguridad', missing_data: 'Cámaras instaladas por barrio', kind: 'unpublished_data' },
      }),
    )

    const card = screen.getByRole('region', { name: '¿Quieres pedir este dato a la Alcaldía?' })
    await userEvent.click(within(card).getByRole('button', { name: 'Ver borrador' }))

    const draft = within(card).getByLabelText('Borrador del derecho de petición (editable)')
    expect((draft as HTMLTextAreaElement).value).toContain('Cámaras instaladas por barrio')
    expect((draft as HTMLTextAreaElement).value).toContain('[Nombre completo]')
    await userEvent.type(draft, ' Gracias.')

    await userEvent.click(within(card).getByRole('button', { name: 'Copiar borrador' }))
    expect(writeText).toHaveBeenCalledWith(expect.stringMatching(/Gracias\.$/))
    expect(within(card).getByRole('status')).toHaveTextContent('Borrador copiado')

    const file = within(card).getByRole('link', { name: /Radicar en Bogotá Te Escucha/ })
    expect(file).toHaveAttribute('href', 'https://bogota.gov.co/sdqs/')
    expect(file).toHaveAttribute('target', '_blank')
    expect(file).toHaveAttribute('rel', 'noopener noreferrer')
    expect(within(card).getByText(/Nada se envía automáticamente/)).toBeInTheDocument()
  })

  it('suggests a petition after a partial answer, keeping the answer and its evidence', async () => {
    renderAnswer(
      chatResponse({
        partial_gap: { topic: 'vías', missing_data: 'Número de huecos tapados en 2025', kind: 'unpublished_data' },
      }),
    )

    expect(screen.getByRole('article', { name: /Ranking mensual de recursos ejecutados de PAC/ })).toBeInTheDocument()
    const note = screen.getByRole('region', { name: 'La respuesta no está completa' })
    expect(note).toHaveTextContent('La respuesta no incluye: Número de huecos tapados en 2025')
    expect(screen.queryByRole('region', { name: 'Este dato no está publicado' })).not.toBeInTheDocument()

    const card = screen.getByRole('region', { name: '¿Quieres pedir este dato a la Alcaldía?' })
    await userEvent.click(within(card).getByRole('button', { name: 'Ver borrador' }))
    const draft = within(card).getByLabelText('Borrador del derecho de petición (editable)')
    expect((draft as HTMLTextAreaElement).value).toContain('Número de huecos tapados en 2025')
    expect(within(card).getByRole('link', { name: /Radicar en Bogotá Te Escucha/ })).toHaveAttribute(
      'href',
      'https://bogota.gov.co/sdqs/',
    )
  })

  it.each([
    ['a complete answer', null],
    ['an out-of-scope partial gap', { topic: 'funcionarios', missing_data: 'nombre', kind: 'out_of_scope' as const }],
  ])('does not suggest a petition for %s', (_label, partial_gap) => {
    renderAnswer(chatResponse({ partial_gap }))

    expect(screen.queryByRole('region', { name: 'La respuesta no está completa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('region', { name: '¿Quieres pedir este dato a la Alcaldía?' })).not.toBeInTheDocument()
  })

  it('selects the draft when the clipboard is not available', async () => {
    Object.defineProperty(navigator, 'clipboard', { value: undefined, configurable: true })
    renderAnswer(
      chatResponse({
        status: 'information_gap',
        evidence: [],
        gap: { topic: 'vías', missing_data: 'huecos por barrio' },
      }),
    )

    await userEvent.click(screen.getByRole('button', { name: 'Ver borrador' }))
    await userEvent.click(screen.getByRole('button', { name: 'Copiar borrador' }))

    expect(screen.getByRole('status')).toHaveTextContent('el texto quedó seleccionado')
    expect(screen.getByLabelText('Borrador del derecho de petición (editable)')).toHaveFocus()
  })

  it.each([
    ['out_of_scope', 'Esta pregunta está fuera de lo que puedo responder'],
    ['unverified', 'No pude verificar la respuesta'],
  ] as const)('does not suggest a petition for %s gaps', (kind, title) => {
    renderAnswer(
      chatResponse({
        status: 'information_gap',
        answer: 'No puedo responder eso.',
        evidence: [],
        gap: { topic: 'funcionarios', missing_data: 'nombre del alcalde', kind },
      }),
    )

    expect(screen.getByRole('region', { name: title })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: '¿Quieres pedir este dato a la Alcaldía?' })).not.toBeInTheDocument()
    expect(screen.queryByText('nombre del alcalde')).not.toBeInTheDocument()
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

describe('MessageBubble — usage line', () => {
  it('shows tokens and paid-plan equivalent cost under the answer', () => {
    renderAnswer(chatResponse({ usage: questionUsage() }))

    const line = screen.getByText('≈ 3.240 tokens · USD 0,0021 · COP 8')
    expect(line).toHaveAttribute('title', expect.stringContaining('el costo real es $0'))
  })

  it('shows only tokens when the cost is unknown', () => {
    renderAnswer(chatResponse({ usage: questionUsage({ cost_usd: null, cost_cop: null }) }))

    expect(screen.getByText('≈ 3.240 tokens')).toBeInTheDocument()
    expect(screen.queryByText(/USD/)).not.toBeInTheDocument()
  })

  it('shows nothing when the backend sends no usage', () => {
    renderAnswer(chatResponse())

    expect(screen.queryByText(/tokens/)).not.toBeInTheDocument()
  })
})
