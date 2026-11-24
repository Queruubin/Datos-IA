import { ExampleQuestions } from './ExampleQuestions'
import { ChartIcon, DocIcon, SparkIcon } from './icons'

interface EmptyStateProps {
  onAsk: (question: string) => void
  disabled?: boolean
  /** 'panel' = desktop insight panel (roomier, 3 columns); 'inline' = single column. */
  variant?: 'panel' | 'inline'
}

/** Topics the data covers (orientation only, not buttons). */
const TOPICS = ['Presupuesto e inversión', 'Metas del plan de desarrollo', 'Presupuestos participativos', 'Quejas y peticiones (PQRS)', 'Contratos']

const PROMISES = [
  { icon: <ChartIcon className="h-4 w-4 shrink-0" />, text: 'Cifras con gráficos' },
  { icon: <DocIcon className="h-4 w-4 shrink-0" />, text: 'Fuente y fecha de corte' },
  { icon: <SparkIcon className="h-4 w-4 shrink-0" />, text: 'Derecho de petición si falta un dato' },
]

/** First screen of the chat: what the assistant does, ready-made questions and topics. */
export function EmptyState({ onAsk, disabled, variant = 'inline' }: EmptyStateProps) {
  const isPanel = variant === 'panel'
  return (
    <div className={isPanel ? 'space-y-8' : 'space-y-6'}>
      <div>
        <p className="eyebrow">Pregunta, comprende y actúa</p>
        <h2
          className={`mt-2 font-display leading-[1.1] font-extrabold tracking-tight text-ink ${
            isPanel ? 'text-4xl xl:text-5xl' : 'text-[28px]'
          }`}
        >
          ¿Qué quieres saber <span className="text-wine-700">o hacer?</span>
        </h2>
        <p className={`mt-3 max-w-xl leading-relaxed text-ink-muted ${isPanel ? 'text-base' : 'text-sm'}`}>
          Las respuestas se basan en datos oficiales publicados, muestran gráficos hechos con esos datos y siempre
          citan la fuente.
        </p>
        <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm font-medium text-ink">
          {PROMISES.map((item) => (
            <li key={item.text} className="flex items-center gap-1.5">
              <span className="text-wine-700">{item.icon}</span>
              {item.text}
            </li>
          ))}
        </ul>
      </div>

      <ExampleQuestions onSelect={onAsk} disabled={disabled} columns={isPanel ? 3 : 2} />

      <section aria-labelledby={`topics-${variant}`}>
        <h3 id={`topics-${variant}`} className="text-sm font-semibold text-ink">
          Puedes preguntar sobre
        </h3>
        <ul className="mt-2 flex flex-wrap gap-2">
          {TOPICS.map((topic) => (
            <li
              key={topic}
              className="rounded-full border border-sand-300 bg-sand-50 px-3 py-1 text-xs font-medium text-ink-muted"
            >
              {topic}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
