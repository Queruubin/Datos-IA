import type { ChartUnit } from '../api/types'

const integer = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })
const oneDecimal = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 })

// Colombian long scale: "mil millones" = 10^9, "billón" = 10^12.
const COP_STEPS: [number, string][] = [
  [1e12, ' billones'],
  [1e9, ' mil M'],
  [1e6, ' M'],
  [1e3, ' mil'],
]

/** '$25,5 mil M' for 25.500.000.000. Used for labels; the full value goes in tooltips/tables. */
export function formatCopCompact(value: number): string {
  const sign = value < 0 ? '-' : ''
  const absolute = Math.abs(value)
  for (const [step, suffix] of COP_STEPS) {
    if (absolute >= step) return `${sign}$${oneDecimal.format(absolute / step)}${suffix}`
  }
  return `${sign}$${integer.format(absolute)}`
}

/** '$25.500.000.000' (pesos, no decimals). */
export function formatCopFull(value: number): string {
  const sign = value < 0 ? '-' : ''
  return `${sign}$${integer.format(Math.abs(value))}`
}

/** Short label for a chart value in its unit. */
export function formatCompact(value: number | null, unit: ChartUnit): string {
  if (value === null || !Number.isFinite(value)) return 'sin dato'
  switch (unit) {
    case 'COP':
      return formatCopCompact(value)
    case 'percent':
      return `${oneDecimal.format(value)} %`
    case 'days':
      return `${oneDecimal.format(value)} ${value === 1 ? 'día' : 'días'}`
    case 'count':
      return integer.format(value)
    default:
      // Unknown currency: never add a symbol or a scale word.
      return oneDecimal.format(value)
  }
}

/** Full value for tooltips and data tables. */
export function formatFull(value: number | null, unit: ChartUnit): string {
  if (value === null || !Number.isFinite(value)) return 'sin dato'
  if (unit === 'COP') return `${formatCopFull(value)} COP`
  if (unit === 'unknown') return oneDecimal.format(value)
  return formatCompact(value, unit)
}

export const UNIT_LABELS: Record<ChartUnit, string> = {
  COP: 'Pesos colombianos (COP)',
  percent: 'Porcentaje',
  count: 'Cantidad',
  days: 'Días calendario',
  unknown: 'Unidad no documentada por la fuente',
}
