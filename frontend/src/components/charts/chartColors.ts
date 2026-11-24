/**
 * Series colors (validated with the dataviz palette script against a white surface).
 * - One series: brand wine.
 * - Ordered stages (planned → committed → paid, or cut-off 1 → 2): one-hue ordinal wine ramp.
 * - Line chart (programmed vs executed): categorical blue + wine.
 * Text never uses these colors; identity comes from the swatch beside the text.
 */
export const SINGLE_SERIES = '#8e2332'
const ORDINAL_3 = ['#e3a3ad', '#b83246', '#5e1621']
const ORDINAL_2 = ['#e3a3ad', '#5e1621']
export const LINE_SERIES = ['#2a78d6', '#8e2332']

export function groupedColors(count: number): string[] {
  if (count <= 1) return [SINGLE_SERIES]
  if (count === 2) return ORDINAL_2
  return ORDINAL_3.slice(0, count)
}
