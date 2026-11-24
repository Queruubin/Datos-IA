import { describe, expect, it } from 'vitest'
import { formatCompact, formatCopCompact, formatFull } from './formatValue'

describe('formatCopCompact', () => {
  it.each([
    [25_500_000_000, '$25,5 mil M'],
    [1_200_000_000_000, '$1,2 billones'],
    [4_000_000, '$4 M'],
    [12_500, '$12,5 mil'],
    [950, '$950'],
    [-3_000_000, '-$3 M'],
  ])('%d → %s', (value, expected) => {
    expect(formatCopCompact(value)).toBe(expected)
  })
})

describe('formatCompact / formatFull', () => {
  it('formats each unit in es-CO', () => {
    expect(formatCompact(43.25, 'percent')).toBe('43,3 %')
    expect(formatCompact(1234, 'count')).toBe('1.234')
    expect(formatCompact(7.5, 'days')).toBe('7,5 días')
    expect(formatCompact(1, 'days')).toBe('1 día')
    expect(formatFull(25_500_000_000, 'COP')).toBe('$25.500.000.000 COP')
  })

  it('never adds a currency to an unknown unit', () => {
    expect(formatCompact(1_234_567, 'unknown')).toBe('1.234.567')
    expect(formatFull(1_234_567.25, 'unknown')).toBe('1.234.567,3')
  })

  it('shows missing values as "sin dato"', () => {
    expect(formatCompact(null, 'COP')).toBe('sin dato')
    expect(formatFull(Number.NaN, 'count')).toBe('sin dato')
  })
})
