import type { Gap } from '../api/types'
import { InfoIcon } from './icons'
import { PetitionCard } from './PetitionCard'

interface PartialGapCardProps {
  gap: Gap
}

/**
 * Shown after an answer that only gives related data: names the data that is missing and
 * suggests the same right-of-petition draft as a full unpublished-data gap.
 */
export function PartialGapCard({ gap }: PartialGapCardProps) {
  return (
    <div className="space-y-3">
      <section
        aria-label="La respuesta no está completa"
        className="rounded-card border border-dashed border-sand-300 bg-sand-50 p-4"
      >
        <p className="flex items-start gap-2 text-sm break-words text-ink">
          <InfoIcon className="mt-0.5 h-4 w-4 shrink-0 text-wine-700" />
          <span>
            <span className="font-semibold">La respuesta no incluye: </span>
            {gap.missing_data}
          </span>
        </p>
        <p className="mt-2 pl-6 text-xs leading-relaxed text-ink-muted">
          Este vacío queda registrado, sin datos personales, para que la Alcaldía Local sepa qué información hace falta
          publicar.
        </p>
      </section>
      <PetitionCard gap={gap} />
    </div>
  )
}
