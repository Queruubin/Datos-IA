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

export function VerdictBadge({ comparison }: VerdictBadgeProps) {
  const verdict = VERDICTS[comparison.verdict] ?? VERDICTS.not_comparable
  return (
    <section
      aria-label="Resultado del contraste entre fuentes"
      className="rounded-lg border border-slate-200 bg-white p-3"
    >
      <p className="text-xs font-semibold tracking-wide text-slate-600 uppercase">Contraste entre fuentes</p>
      <p className="mt-1">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-sm font-semibold ${verdict.className}`}
        >
          {verdict.icon}
          {verdict.label}
        </span>
      </p>
      <p className="mt-2 text-sm text-slate-700">{verdict.note}</p>
      {comparison.rule && (
        <details className="mt-2 text-sm">
          <summary className="cursor-pointer rounded font-medium text-blue-800 underline underline-offset-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700">
            ¿Cómo se hizo la comparación?
          </summary>
          <p className="mt-2 text-slate-700">{comparison.rule}</p>
        </details>
      )}
    </section>
  )
}
