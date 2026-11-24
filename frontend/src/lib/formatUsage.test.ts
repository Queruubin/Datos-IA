import { describe, expect, it } from 'vitest'
import { questionUsage } from '../test/fixtures'
import { formatCop, formatDecimal, formatTokens, formatUsd, usageLine } from './formatUsage'

describe('usage formatting', () => {
  it('formats the per-answer line in es-CO', () => {
    expect(usageLine(questionUsage())).toBe('≈ 3.240 tokens · USD 0,0021 · COP 8')
  })

  it('keeps tiny costs visible instead of rounding them to zero', () => {
    expect(formatUsd(0.000034)).toBe('0,000034')
    expect(formatCop(0.35)).toBe('0,35')
    expect(formatUsd(12.5)).toBe('12,50')
    expect(formatCop(12345.6)).toBe('12.346')
  })

  it('formats tokens and two-decimal values', () => {
    expect(formatTokens(1234567)).toBe('1.234.567')
    expect(formatDecimal(0.3)).toBe('0,30')
    expect(formatDecimal(3461.92)).toBe('3.461,92')
  })

  it('leaves out unknown costs instead of showing 0', () => {
    expect(usageLine(questionUsage({ cost_usd: null, cost_cop: null }))).toBe('≈ 3.240 tokens')
    expect(usageLine(questionUsage({ cost_cop: null }))).toBe('≈ 3.240 tokens · USD 0,0021')
  })
})
