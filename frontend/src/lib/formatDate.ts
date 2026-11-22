const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

/**
 * Formats a backend cut-off date in short Spanish.
 * Accepts 'YYYY-MM-DD' (→ '30 sep 2026'), 'YYYY-MM' (→ 'sep 2026') or an ISO datetime.
 * Returns null for missing or unparseable values.
 */
export function formatCutoff(value: string | null | undefined): string | null {
  if (!value) return null
  const match = /^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(value.trim())
  if (!match) return null
  const [, year, month, day] = match
  const monthIndex = Number(month) - 1
  if (monthIndex < 0 || monthIndex > 11) return null
  const monthName = MONTHS[monthIndex]
  return day ? `${Number(day)} ${monthName} ${year}` : `${monthName} ${year}`
}

/** 'corte: 30 sep 2026' or 'corte: no indicado'. */
export function cutoffLabel(value: string | null | undefined): string {
  return `corte: ${formatCutoff(value) ?? 'no indicado'}`
}

const numberFormatter = new Intl.NumberFormat('es-CO')

export function formatNumber(value: number): string {
  return numberFormatter.format(value)
}
