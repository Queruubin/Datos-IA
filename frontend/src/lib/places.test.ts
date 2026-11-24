import { describe, expect, it } from 'vitest'
import { PLACES } from './places'

describe('PLACES', () => {
  it('every photo has a complete Wikimedia Commons attribution', () => {
    expect(PLACES).toHaveLength(4)
    for (const place of PLACES) {
      expect(place.imageUrl).toMatch(/^https:\/\/thumb\.wikimedia\.org\/wikipedia\/commons\/thumb\//)
      expect(place.fileUrl).toMatch(/^https:\/\/commons\.wikimedia\.org\/wiki\/File:/)
      expect(place.authorUrl).toMatch(/^https:\/\/commons\.wikimedia\.org\/wiki\/User:/)
      expect(place.author).not.toBe('')
      expect(place.license).toMatch(/^CC BY-SA [34]\.0$/)
      expect(place.licenseUrl).toMatch(/^https:\/\/creativecommons\.org\/licenses\/by-sa\/[34]\.0$/)
    }
  })
})
