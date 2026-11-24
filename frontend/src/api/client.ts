import type { ChatResponse, SourceMetadata, UsageReport } from './types'

export const API_BASE_URL: string = (
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
).replace(/\/+$/, '')

export const REQUEST_TIMEOUT_MS = 60_000

export type ApiErrorKind = 'http' | 'network' | 'timeout'

/** Error raised by the API client. `status` is set only for HTTP errors. */
export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status?: number
  readonly detail?: string

  constructor(kind: ApiErrorKind, options: { status?: number; detail?: string } = {}) {
    super(options.detail ?? kind)
    this.name = 'ApiError'
    this.kind = kind
    this.status = options.status
    this.detail = options.detail
  }
}

async function readDetail(response: Response): Promise<string | undefined> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'detail' in body) {
      const { detail } = body as { detail: unknown }
      return typeof detail === 'string' ? detail : undefined
    }
  } catch {
    // Body is not JSON; fall through.
  }
  return undefined
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = REQUEST_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal })
  } catch (error) {
    if (controller.signal.aborted) throw new ApiError('timeout')
    throw new ApiError('network', { detail: error instanceof Error ? error.message : undefined })
  } finally {
    clearTimeout(timer)
  }
  if (!response.ok) {
    throw new ApiError('http', { status: response.status, detail: await readDetail(response) })
  }
  return (await response.json()) as T
}

export function postChat(question: string): Promise<ChatResponse> {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
}

export function getSources(): Promise<SourceMetadata[]> {
  return request<SourceMetadata[]>('/api/sources')
}

export function getUsage(): Promise<UsageReport> {
  return request<UsageReport>('/api/usage')
}
