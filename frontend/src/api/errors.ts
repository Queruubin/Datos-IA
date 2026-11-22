import { ApiError } from './client'

/** Friendly, plain-language Spanish message for any error coming from the API client. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.kind === 'timeout') {
      return 'La consulta tardó demasiado. Intenta de nuevo en un momento.'
    }
    if (error.kind === 'network') {
      return 'No se pudo conectar con el servidor. Verifica que el servicio esté en funcionamiento e intenta de nuevo.'
    }
    switch (error.status) {
      case 422:
        return 'La pregunta no es válida. Escribe entre 1 y 500 caracteres.'
      case 429:
        return 'Hiciste muchas preguntas en poco tiempo. Espera un momento e intenta de nuevo.'
      case 502:
        return 'El servicio está ocupado en este momento. Intenta de nuevo en unos segundos.'
      case 503:
        return 'El servicio de preguntas todavía no está configurado. Intenta más tarde.'
      default:
        return 'Ocurrió un error inesperado. Intenta de nuevo.'
    }
  }
  return 'Ocurrió un error inesperado. Intenta de nuevo.'
}
