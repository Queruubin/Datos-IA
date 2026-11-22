import { describe, expect, it } from 'vitest'
import { cutoffLabel, formatCutoff } from './formatDate'

describe('formatCutoff', () => {
  it('formats a full date in short Spanish', () => {
    expect(formatCutoff('2026-09-30')).toBe('30 sep 2026')
    expect(formatCutoff('2025-01-05')).toBe('5 ene 2025')
  })

  it('formats a year-month cut-off', () => {
    expect(formatCutoff('2025-06')).toBe('jun 2025')
  })

  it('accepts ISO datetimes', () => {
    expect(formatCutoff('2026-12-01T10:00:00')).toBe('1 dic 2026')
  })

  it('returns null for missing or invalid values', () => {
    expect(formatCutoff(null)).toBeNull()
    expect(formatCutoff('')).toBeNull()
    expect(formatCutoff('pronto')).toBeNull()
    expect(formatCutoff('2025-13')).toBeNull()
  })
})

describe('cutoffLabel', () => {
  it('prefixes the formatted date', () => {
    expect(cutoffLabel('2026-09-30')).toBe('corte: 30 sep 2026')
  })

  it('says when the cut-off is unknown', () => {
    expect(cutoffLabel(null)).toBe('corte: no indicado')
  })
})
