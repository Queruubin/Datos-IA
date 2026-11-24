import type { Gap, GapKind } from '../api/types'
import { InfoIcon } from './icons'
import { PetitionCard } from './PetitionCard'

interface GapCardProps {
  gap?: Gap | null
}

const COPY: Record<GapKind, { title: string; note: string | null }> = {
  unpublished_data: {
    title: 'Este dato no está publicado',
    note: 'Este vacío queda registrado, sin datos personales, para que la Alcaldía Local sepa qué información hace falta publicar.',
  },
  out_of_scope: {
    title: 'Esta pregunta está fuera de lo que puedo responder',
    note: 'Solo respondo sobre la gestión pública de San Cristóbal con datos publicados. No doy nombres de personas ni opiniones.',
  },
  unverified: {
    title: 'No pude verificar la respuesta',
    note: 'Prueba reformulando la pregunta o consulta las fuentes en la sección Fuentes.',
  },
}

export function GapCard({ gap }: GapCardProps) {
  const kind: GapKind = gap?.kind ?? 'unpublished_data'
  const copy = COPY[kind] ?? COPY.unpublished_data

  return (
    <div className="space-y-3">
      <section
        aria-label={copy.title}
        className="rounded-card border border-dashed border-sand-300 bg-sand-50 p-4"
      >
        <h3 className="flex items-center gap-2 font-display text-base font-bold text-ink">
          <InfoIcon className="h-5 w-5 shrink-0 text-wine-700" />
          <span>{copy.title}</span>
        </h3>
        {gap && kind !== 'unverified' && (
          <dl className="mt-2 space-y-1 text-sm break-words">
            <div>
              <dt className="inline font-medium text-ink-muted">Tema: </dt>
              <dd className="inline text-ink">{gap.topic}</dd>
            </div>
            {kind === 'unpublished_data' && (
              <div>
                <dt className="inline font-medium text-ink-muted">Dato que haría falta: </dt>
                <dd className="inline text-ink">{gap.missing_data}</dd>
              </div>
            )}
          </dl>
        )}
        {copy.note && <p className="mt-2 text-xs leading-relaxed text-ink-muted">{copy.note}</p>}
      </section>
      {gap && kind === 'unpublished_data' && <PetitionCard gap={gap} />}
    </div>
  )
}
