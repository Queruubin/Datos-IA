// Mirrors the FastAPI contract in backend/app/api/main.py and backend/app/domain.

export type AnswerStatus = 'answered' | 'information_gap' | 'needs_clarification'

export type Verdict = 'coherent' | 'difference_detected' | 'not_comparable'

export interface Evidence {
  id: string
  source_id: string
  title: string
  data_cutoff: string | null
  portal_url: string
  locator: string
  summary: string
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
}

export interface SourceMetadata {
  source_id: string
  title: string
  table_name: string
  portal_url: string
  resource_urls: string[]
  data_cutoff: string | null
  rows: number
  unit: string | null
  ingested_at: string
}
