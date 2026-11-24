// Mirrors the FastAPI contract in backend/app/api/main.py and backend/app/domain.

export type AnswerStatus = 'answered' | 'information_gap' | 'needs_clarification'

export type Verdict = 'coherent' | 'difference_detected' | 'not_comparable'

export interface Evidence {
  id: string
  source_id: string
  title: string
  data_cutoff: string | null
  /** Null when the data does not come from the open-data portal (see origin_note). */
  portal_url: string | null
  locator: string
  summary: string
  origin_note?: string | null
}

/** Free-form dict on the backend; `verdict` and `rule` are the stable keys. */
export interface Comparison {
  verdict: Verdict
  rule: string
  evidence_ids?: string[]
  [key: string]: unknown
}

export interface Gap {
  topic: string
  missing_data: string
}

export interface ChatResponse {
  answer: string
  status: AnswerStatus
  evidence: Evidence[]
  comparison?: Comparison | null
  gap?: Gap | null
  disclaimer: string
  /** Tokens and paid-plan equivalent cost of this answer (absent on older backends). */
  usage?: QuestionUsage | null
}

export interface QuestionUsage {
  input_tokens: number
  /** Visible answer tokens. */
  output_tokens: number
  /** Reasoning tokens (billed as output). */
  thinking_tokens: number
  total_tokens: number
  calls: number
  models: string[]
  /** null when a model has no known price. */
  cost_usd: number | null
  /** null when there is no USD cost or no USD→COP rate. */
  cost_cop: number | null
  unpriced_models?: string[]
}

export interface UsageTotals {
  questions: number
  calls: number
  input_tokens: number
  output_tokens: number
  thinking_tokens: number
  total_tokens: number
  cost_usd: number | null
  cost_cop: number | null
  /** Calls whose model has no known price (left out of the cost). */
  unpriced_calls: number
}

export interface ModelUsage extends UsageTotals {
  model: string
}

export interface DayUsage extends UsageTotals {
  /** 'YYYY-MM-DD' in Bogotá time. */
  day: string
}

export type RateSource = 'datos.gov.co' | 'fallback_setting' | 'unavailable'

export interface ExchangeRate {
  value: number | null
  valid_from: string | null
  source: RateSource | string
}

export interface ModelPrice {
  model: string
  input_usd_per_million: number
  output_usd_per_million: number
  valid_from: string | null
  valid_until: string | null
  note: string | null
}

export interface UsageReport {
  note: string
  all_time: UsageTotals
  today: UsageTotals
  avg_tokens_per_question: number | null
  avg_cost_usd_per_question: number | null
  avg_cost_cop_per_question: number | null
  by_model: ModelUsage[]
  by_day: DayUsage[]
  exchange_rate: ExchangeRate
  pricing: {
    source_url: string
    read_on: string
    tier: string
    unit: string
    prices: ModelPrice[]
  }
}

export interface SourceMetadata {
  source_id: string
  title: string
  table_name: string
  /** Null for curated files that are not published on the open-data portal. */
  portal_url: string | null
  resource_urls: string[]
  data_cutoff: string | null
  rows: number
  unit: string | null
  ingested_at: string
  /** Where the data comes from (e.g. file delivered by the Alcaldía Local). */
  origin_note?: string | null
}
