import { afterEach, describe, expect, it, vi } from 'vitest'
import { chatResponse, jsonResponse, mockFetch } from '../test/fixtures'
import { ApiError, API_BASE_URL, postChat, REQUEST_TIMEOUT_MS } from './client'
import { errorMessage } from './errors'

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('postChat', () => {
  it('posts the question as JSON and returns the parsed answer', async () => {
    const fetchMock = mockFetch()
    fetchMock.mockResolvedValue(jsonResponse(chatResponse()))

    const result = await postChat('¿Cuánto se ejecutó?')

    expect(result.status).toBe('answered')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe(`${API_BASE_URL}/api/chat`)
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({ question: '¿Cuánto se ejecutó?' })
  })

  it('raises an ApiError with the HTTP status and detail', async () => {
    mockFetch().mockResolvedValue(jsonResponse({ detail: 'Demasiadas preguntas' }, 429))

    await expect(postChat('hola')).rejects.toMatchObject({
      kind: 'http',
      status: 429,
      detail: 'Demasiadas preguntas',
    })
  })

  it('raises a network error when fetch fails', async () => {
    mockFetch().mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(postChat('hola')).rejects.toMatchObject({ kind: 'network' })
  })

  it('aborts after the timeout', async () => {
    vi.useFakeTimers()
    mockFetch().mockImplementation(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
        }),
    )

    const pending = expect(postChat('hola')).rejects.toMatchObject({ kind: 'timeout' })
    await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS)
    await pending
  })
})

describe('errorMessage', () => {
  it.each([
    [429, 'Espera un momento'],
    [502, 'El servicio está ocupado'],
    [503, 'no está configurado'],
    [422, 'entre 1 y 500 caracteres'],
    [500, 'error inesperado'],
  ])('maps HTTP %i to a friendly message', (status, expected) => {
    expect(errorMessage(new ApiError('http', { status }))).toContain(expected)
  })

  it('explains a network error as the server not running', () => {
    expect(errorMessage(new ApiError('network'))).toContain('No se pudo conectar con el servidor')
  })

  it('explains a timeout', () => {
    expect(errorMessage(new ApiError('timeout'))).toContain('tardó demasiado')
  })
})
