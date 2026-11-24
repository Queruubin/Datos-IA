import type { QuestionUsage } from '../api/types'

const integer = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })
const twoDecimals = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
// Tiny costs (fractions of a cent) keep two significant digits so they never show as 0.
const tiny = new Intl.NumberFormat('es-CO', { maximumSignificantDigits: 2 })

export function formatTokens(value: number): string {
  return integer.format(value)
}

/** '0,0021' for tiny amounts, '12,50' from one dollar up. */
export function formatUsd(value: number): string {
  if (value === 0) return '0'
  return Math.abs(value) < 1 ? tiny.format(value) : twoDecimals.format(value)
}

/** '0,35' for less than one peso, '8' or '12.345' from one peso up. */
export function formatCop(value: number): string {
  if (value === 0) return '0'
  return Math.abs(value) < 1 ? tiny.format(value) : integer.format(value)
}

/** '≈ 3.240 tokens · USD 0,0021 · COP 8'. Unknown costs are left out, never shown as 0. */
export function usageLine(usage: QuestionUsage): string {
  const parts = [`≈ ${formatTokens(usage.total_tokens)} tokens`]
  if (usage.cost_usd !== null) parts.push(`USD ${formatUsd(usage.cost_usd)}`)
  if (usage.cost_usd !== null && usage.cost_cop !== null) parts.push(`COP ${formatCop(usage.cost_cop)}`)
  return parts.join(' · ')
}

/** Always two decimals: '3.461,92', '0,30'. */
export function formatDecimal(value: number): string {
  return twoDecimals.format(value)
}
