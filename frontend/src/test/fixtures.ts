import { vi } from 'vitest'
import type { ChatResponse, Evidence, SourceMetadata } from '../api/types'

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
