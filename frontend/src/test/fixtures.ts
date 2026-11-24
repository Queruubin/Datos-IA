import { vi } from 'vitest'
import type {
  ChartSpec,
  ChatResponse,
  Evidence,
  ModelPrice,
  QuestionUsage,
  SourceMetadata,
  UsageReport,
  UsageTotals,
} from '../api/types'

export const DISCLAIMER =
  'Este asistente no es vocero oficial de la Alcaldía. Las respuestas se basan en datos públicos con la fecha de corte indicada.'

export const evidence = (overrides: Partial<Evidence> = {}): Evidence => ({
  id: 'E1',
  source_id: 'pac_fdl',
  title: 'Ranking mensual de recursos ejecutados de PAC',
  data_cutoff: '2026-09-30',
  portal_url: 'https://datosabiertos.bogota.gov.co/dataset/pac',
  locator: 'pac_execution · año 2025',
  summary: 'Ejecución acumulada de 45 % a junio de 2025.',
  ...overrides,
})

export const chatResponse = (overrides: Partial<ChatResponse> = {}): ChatResponse => ({
  answer: 'Se ejecutó el 45 % del presupuesto (E1).',
  status: 'answered',
  evidence: [evidence()],
  comparison: null,
  gap: null,
  disclaimer: DISCLAIMER,
  ...overrides,
})

export const source = (overrides: Partial<SourceMetadata> = {}): SourceMetadata => ({
  source_id: 'pac_fdl',
  title: 'Ranking mensual de recursos ejecutados de PAC',
  table_name: 'pac_execution',
  portal_url: 'https://datosabiertos.bogota.gov.co/dataset/pac',
  resource_urls: [],
  data_cutoff: '2025-06',
  rows: 1234,
  unit: null,
  ingested_at: '2026-11-22T10:00:00',
  origin_note: null,
  ...overrides,
})

export const questionUsage = (overrides: Partial<QuestionUsage> = {}): QuestionUsage => ({
  input_tokens: 2900,
  output_tokens: 240,
  thinking_tokens: 100,
  total_tokens: 3240,
  calls: 3,
  models: ['gemini-3.5-flash-lite'],
  cost_usd: 0.0021,
  cost_cop: 8.2,
  unpriced_models: [],
  ...overrides,
})

const totals = (overrides: Partial<UsageTotals> = {}): UsageTotals => ({
  questions: 12,
  calls: 36,
  input_tokens: 30000,
  output_tokens: 6000,
  thinking_tokens: 2880,
  total_tokens: 38880,
  cost_usd: 0.0252,
  cost_cop: 98.4,
  unpriced_calls: 0,
  ...overrides,
})

const price = (overrides: Partial<ModelPrice>): ModelPrice => ({
  model: 'gemini-3.5-flash-lite',
  input_usd_per_million: 0.3,
  output_usd_per_million: 2.5,
  valid_from: null,
  valid_until: null,
  note: null,
  ...overrides,
})

export const usageReport = (overrides: Partial<UsageReport> = {}): UsageReport => ({
  note: 'Con el plan gratuito de Gemini el costo real es $0.',
  all_time: totals({ unpriced_calls: 6 }),
  today: totals({ questions: 2, calls: 6, total_tokens: 6480, cost_usd: 0.0042, cost_cop: 16.4 }),
  avg_tokens_per_question: 3240,
  avg_cost_usd_per_question: 0.0021,
  avg_cost_cop_per_question: 8.2,
  by_model: [
    { model: 'gemini-3.5-flash-lite', ...totals({ calls: 30 }) },
    { model: 'gemini-x', ...totals({ calls: 6, cost_usd: null, cost_cop: null, unpriced_calls: 6 }) },
  ],
  by_day: [
    { day: '2026-11-22', ...totals({ questions: 10, total_tokens: 32400 }) },
    { day: '2026-11-23', ...totals({ questions: 1, total_tokens: 3240 }) },
  ],
  exchange_rate: { value: 3461.92, valid_from: '2026-11-21', source: 'datos.gov.co' },
  pricing: {
    source_url: 'https://aistudio.google.com/docs/pricing',
    read_on: '2026-11-23',
    tier: 'Standard (plan pagado)',
    unit: 'USD por 1 millón de tokens',
    prices: [
      price({}),
      price({ model: 'gemini-3.8-flash', input_usd_per_million: 0.75, output_usd_per_million: 3.75, valid_until: '2027-01-01' }),
      price({ model: 'gemini-3.8-flash', input_usd_per_million: 1.5, output_usd_per_million: 7.5, valid_from: '2027-01-01' }),
    ],
  },
  ...overrides,
})

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Replaces global fetch with a mock; no network is ever used in tests. */
export function mockFetch() {
  const fetchMock = vi.fn<typeof fetch>()
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

export const chartSpec = (overrides: Partial<ChartSpec> = {}): ChartSpec => ({
  id: 'C1',
  kind: 'bars',
  title: 'Inversión planeada 2026 por ODS (POAI)',
  unit: 'COP',
  evidence_id: 'E1',
  evidence_ids: ['E1'],
  categories: ['ODS 11 · Ciudades sostenibles', 'ODS 8 · Trabajo decente'],
  series: [{ name: 'Planeado (POAI)', values: [25_500_000_000, 4_000_000] }],
  kpis: [],
  note: null,
  data_cutoff: '2026-06-30',
  verdict: null,
  ...overrides,
})
