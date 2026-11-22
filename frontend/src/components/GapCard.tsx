import type { Gap } from '../api/types'
import { InfoIcon } from './icons'

interface GapCardProps {
  gap?: Gap | null
}

export function GapCard({ gap }: GapCardProps) {
  return (
    <section
      aria-label="Este dato no está publicado"
      className="rounded-lg border-2 border-dashed border-slate-400 bg-slate-50 p-3"
    >
      <h4 className="flex items-center gap-1.5 text-sm font-semibold text-slate-900">
        <InfoIcon />
        <span>Este dato no está publicado</span>
      </h4>
      {gap && (
        <dl className="mt-2 space-y-1 text-sm break-words">
          <div>
            <dt className="inline font-medium text-slate-700">Tema: </dt>
            <dd className="inline text-slate-900">{gap.topic}</dd>
          </div>
          <div>
            <dt className="inline font-medium text-slate-700">Dato que haría falta: </dt>
            <dd className="inline text-slate-900">{gap.missing_data}</dd>
          </div>
        </dl>
      )}
      <p className="mt-2 text-xs text-slate-600">
        Este vacío queda registrado, sin datos personales, para que la Alcaldía Local sepa qué información hace
        falta publicar.
      </p>
    </section>
  )
}
