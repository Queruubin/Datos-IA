import { describe, expect, it } from 'vitest'
import { chartSpec, chatResponse, evidence } from '../test/fixtures'
import { answerChips, orderedCharts, previewText } from './answerSummary'

describe('previewText', () => {
  it('drops evidence references and collapses whitespace', () => {
    expect(previewText('Se ejecutó el 45 % (E1).\n\nGiros: 20 % (E1, E2).')).toBe('Se ejecutó el 45 %. Giros: 20 %.')
  })
})

describe('answerChips', () => {
  it('counts charts and sources', () => {
    const response = chatResponse({
      charts: [chartSpec(), chartSpec({ id: 'C2' })],
      evidence: [evidence(), evidence({ id: 'E2' })],
    })
    expect(answerChips(response)).toEqual(['2 gráficas', '2 fuentes'])
  })

  it('flags unpublished data for full and partial gaps only', () => {
    const gap = { topic: 'vías', missing_data: 'huecos' }
    expect(answerChips(chatResponse({ status: 'information_gap', evidence: [], gap }))).toEqual(['Dato no publicado'])
    expect(answerChips(chatResponse({ partial_gap: { ...gap, kind: 'unpublished_data' } }))).toContain('Dato no publicado')
    expect(
      answerChips(chatResponse({ status: 'information_gap', evidence: [], gap: { ...gap, kind: 'out_of_scope' } })),
    ).toEqual(['Fuera de alcance'])
  })

  it('never counts charts on a gap', () => {
    const response = chatResponse({ status: 'information_gap', evidence: [], gap: null, charts: [chartSpec()] })
    expect(answerChips(response)).toEqual(['Dato no publicado'])
  })
})

describe('orderedCharts', () => {
  it('puts KPI tiles before bars and lines', () => {
    const response = chatResponse({ charts: [chartSpec({ id: 'bars' }), chartSpec({ id: 'kpis', kind: 'kpis' })] })
    expect(orderedCharts(response).map((chart) => chart.id)).toEqual(['kpis', 'bars'])
  })
})
