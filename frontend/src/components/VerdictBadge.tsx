import type { ReactNode } from 'react'
import type { Comparison, Verdict } from '../api/types'
import { AlertIcon, CheckIcon, MinusIcon } from './icons'

interface VerdictStyle {
  label: string
  className: string
  icon: ReactNode
  note: string
}

const VERDICTS: Record<Verdict, VerdictStyle> = {
  coherent: {
    label: 'Coherente',
    className: 'border-green-700 bg-green-50 text-green-900',
    icon: <CheckIcon />,
    note: 'Las fuentes comparadas coinciden según la regla aplicada.',
  },
  difference_detected: {
    label: 'Diferencia detectada',
    className: 'border-amber-600 bg-amber-50 text-amber-900',
    icon: <AlertIcon />,
    note: 'Las fuentes no coinciden por completo. Una diferencia no implica una irregularidad: puede deberse, por ejemplo, a fechas de corte distintas o a datos que aún no se han publicado.',
  },
  not_comparable: {
    label: 'No comparable',
    className: 'border-slate-500 bg-slate-100 text-slate-800',
    icon: <MinusIcon />,
    note: 'Las fuentes no tienen datos suficientes para hacer la comparación.',
  },
}

interface VerdictBadgeProps {
  comparison: Comparison
}

/** Verdict as icon + text (never color alone). */
export function VerdictPill({ verdict: key }: { verdict: Verdict }) {
  const verdict = VERDICTS[key] ?? VERDICTS.not_comparable
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-sm font-semibold ${verdict.className}`}
    >
      {verdict.icon}
      {verdict.label}
    </span>
  )
}

export function VerdictBadge({ comparison }: VerdictBadgeProps) {
  const verdict = VERDICTS[comparison.verdict] ?? VERDICTS.not_comparable
  return (
    <section
      aria-label="Resultado del contraste entre fuentes"
      className="rounded-card border border-sand-200 bg-sand-50 p-4"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <p className="eyebrow">Contraste entre fuentes</p>
        <VerdictPill verdict={comparison.verdict} />
      </div>
      <p className="mt-2 text-sm leading-relaxed text-ink-muted">{verdict.note}</p>
      {comparison.rule && (
        <details className="mt-2 text-sm">
          <summary className="focus-ring cursor-pointer rounded font-semibold text-wine-700 hover:text-wine-900">
            ¿Cómo se hizo la comparación?
          </summary>
          <p className="mt-2 text-ink-muted">{comparison.rule}</p>
        </details>
      )}
    </section>
  )
}
