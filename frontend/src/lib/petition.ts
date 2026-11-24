import type { Gap } from '../api/types'

/** Official channel of the District to file petitions (redirects to Bogotá Te Escucha). */
export const BOGOTA_TE_ESCUCHA_URL = 'https://bogota.gov.co/sdqs/'

/** Placeholders the citizen fills in. Personal data is never prefilled. */
export const PETITION_PLACEHOLDERS = [
  '[Nombre completo]',
  '[Documento de identidad]',
  '[Correo o dirección para respuesta]',
] as const

const MAX_FIELD = 300

function clean(text: string | null | undefined, fallback: string): string {
  const value = (text ?? '').replace(/\s+/g, ' ').trim().slice(0, MAX_FIELD)
  return value || fallback
}

/** True when the gap is public data that is not published (the only case to suggest a petition). */
export function suggestsPetition(gap: Gap | null | undefined): gap is Gap {
  return !!gap && (gap.kind ?? 'unpublished_data') === 'unpublished_data'
}

/**
 * Deterministic right-of-petition draft (no LLM, no figures). It only uses the topic and the
 * missing data reported for the gap; the citizen completes the placeholders and files it.
 */
export function buildPetitionDraft(gap: Pick<Gap, 'topic' | 'missing_data'>): string {
  const topic = clean(gap.topic, 'gestión pública local').toLowerCase()
  const missing = clean(gap.missing_data, 'la información sobre este tema').replace(/[.;\s]+$/, '')
  const [name, id, contact] = PETITION_PLACEHOLDERS
  return [
    'Señores',
    'Alcaldía Local de San Cristóbal',
    'Bogotá D.C.',
    '',
    `Asunto: Derecho de petición de información pública sobre ${topic}`,
    '',
    `Yo, ${name}, identificado(a) con ${id}, en ejercicio del derecho fundamental de petición ` +
      'consagrado en el artículo 23 de la Constitución Política y regulado por la Ley 1755 de 2015, ' +
      'respetuosamente solicito:',
    '',
    `1. Que se me entregue la siguiente información: ${missing}.`,
    '2. Que esta información se publique como datos abiertos en el portal de Datos Abiertos de ' +
      'Bogotá, con su fecha de corte y su fuente, para que cualquier persona pueda consultarla.',
    '',
    `Recibiré la respuesta en: ${contact}.`,
    '',
    'Atentamente,',
    '',
    name,
    id,
  ].join('\n')
}
