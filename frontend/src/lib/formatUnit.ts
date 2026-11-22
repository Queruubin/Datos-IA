/** The backend stores units as technical notes; citizens get a plain-Spanish label. */
export function formatUnit(unit: string | null): string {
  if (unit === null) return 'No aplica'
  if (unit.toLowerCase().startsWith('unknown')) {
    return 'No documentada por la fuente (probablemente millones de pesos)'
  }
  return unit
}
