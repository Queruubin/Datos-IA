import type { ChartSpec, ChatResponse } from '../api/types'
import { suggestsPetition } from './petition'

/** Charts are only shown next to a verified answer (the backend already enforces this). */
export function visibleCharts(response: ChatResponse): ChartSpec[] {
  return response.status === 'answered' ? (response.charts ?? []) : []
}

/** KPI tiles first (the headline numbers), then bars and lines, keeping the backend order. */
export function orderedCharts(response: ChatResponse): ChartSpec[] {
  const charts = visibleCharts(response)
  return [...charts.filter((chart) => chart.kind === 'kpis'), ...charts.filter((chart) => chart.kind !== 'kpis')]
}

/** True when the answer is (fully or partly) missing data that could be requested by petition. */
export function hasUnpublishedData(response: ChatResponse): boolean {
  // A gap without a kind comes from an older backend: treat it as unpublished data.
  if (response.status === 'information_gap') return (response.gap?.kind ?? 'unpublished_data') === 'unpublished_data'
  return response.status === 'answered' && suggestsPetition(response.partial_gap)
}

/** Answer text without evidence references, for one-glance previews: "(E1, E2)" → "". */
export function previewText(answer: string): string {
  return answer
    .replace(/\s*\((?:E\d+(?:\s*[,;y]\s*)?)+\)/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

const plural = (count: number, one: string, many: string) => `${count} ${count === 1 ? one : many}`

/** Small labels under an answer preview: "2 gráficas", "2 fuentes", "Dato no publicado"… */
export function answerChips(response: ChatResponse): string[] {
  const chips: string[] = []
  const charts = visibleCharts(response).length
  const sources = (response.evidence ?? []).length
  if (charts > 0) chips.push(plural(charts, 'gráfica', 'gráficas'))
  if (sources > 0) chips.push(plural(sources, 'fuente', 'fuentes'))
  if (hasUnpublishedData(response)) chips.push('Dato no publicado')
  else if (response.status === 'information_gap') {
    chips.push(response.gap?.kind === 'out_of_scope' ? 'Fuera de alcance' : 'Sin verificar')
  }
  if (response.status === 'needs_clarification') chips.push('Necesito más detalles')
  return chips
}
