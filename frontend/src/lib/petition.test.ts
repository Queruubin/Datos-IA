import { describe, expect, it } from 'vitest'
import { buildPetitionDraft, PETITION_PLACEHOLDERS, suggestsPetition } from './petition'

describe('buildPetitionDraft', () => {
  const gap = { topic: 'Seguridad', missing_data: 'Número de hurtos por barrio.' }
  const draft = buildPetitionDraft(gap)

  it('is addressed to the Alcaldía Local and invokes the right of petition', () => {
    expect(draft).toMatch(/^Señores\nAlcaldía Local de San Cristóbal/)
    expect(draft).toContain('artículo 23 de la Constitución Política')
    expect(draft).toContain('Ley 1755 de 2015')
    expect(draft).toContain('Asunto: Derecho de petición de información pública sobre seguridad')
  })

  it('requests the missing data and its publication as open data', () => {
    expect(draft).toContain('1. Que se me entregue la siguiente información: Número de hurtos por barrio.')
    expect(draft).toContain('se publique como datos abiertos')
  })

  it('leaves personal data as placeholders', () => {
    for (const placeholder of PETITION_PLACEHOLDERS) expect(draft).toContain(placeholder)
  })

  it('is deterministic and tolerates empty or messy fields', () => {
    expect(buildPetitionDraft(gap)).toBe(draft)
    const messy = buildPetitionDraft({ topic: '  ', missing_data: '  varias\n  líneas ' })
    expect(messy).toContain('sobre gestión pública local')
    expect(messy).toContain('información: varias líneas.')
  })
})

describe('suggestsPetition', () => {
  it('only for unpublished data (a missing kind means an older backend: unpublished)', () => {
    expect(suggestsPetition({ topic: 't', missing_data: 'm', kind: 'unpublished_data' })).toBe(true)
    expect(suggestsPetition({ topic: 't', missing_data: 'm' })).toBe(true)
    expect(suggestsPetition({ topic: 't', missing_data: 'm', kind: 'out_of_scope' })).toBe(false)
    expect(suggestsPetition({ topic: 't', missing_data: 'm', kind: 'unverified' })).toBe(false)
    expect(suggestsPetition(null)).toBe(false)
  })
})
