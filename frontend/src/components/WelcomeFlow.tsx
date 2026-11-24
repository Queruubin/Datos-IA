import { useEffect, useRef } from 'react'
import { PLACES } from '../lib/places'
import { ChatInput } from './ChatInput'
import { ExampleQuestions } from './ExampleQuestions'
import { ArrowRightIcon } from './icons'
import { PlacePhoto } from './PlaceScene'

export const WELCOME_STEPS = 3

interface WelcomeFlowProps {
  step: number
  onStepChange: (step: number) => void
  /** Closes the flow (Saltar, or after asking). */
  onFinish: () => void
  /** Sends a question to the chat and closes the flow. */
  onAsk: (question: string) => void
  isLoading?: boolean
}

const FEATURES = [
  { title: 'Pregunta', text: 'Escribe con tus palabras, como le preguntarías a una vecina o a un vecino.' },
  { title: 'Comprende', text: 'Recibes cifras con gráficos, la fecha de corte y la fuente de cada dato.' },
  { title: 'Actúa', text: 'Si un dato no está publicado, te ayudamos a pedirlo con un derecho de petición.' },
]

const EYEBROWS = ['San Cristóbal · Bogotá', 'Cómo funciona', 'Tu consulta']

const primary =
  'focus-ring group inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-wine-700 px-7 text-base font-semibold text-white transition-colors hover:bg-wine-800'

/** Three-step introduction shown on the first visit (it can be reopened from the header). */
export function WelcomeFlow({ step, onStepChange, onFinish, onAsk, isLoading = false }: WelcomeFlowProps) {
  const headingRef = useRef<HTMLHeadingElement>(null)
  const firstRender = useRef(true)

  useEffect(() => {
    // Move focus to the new step's heading (not on the first render: don't steal focus on load).
    if (firstRender.current) {
      firstRender.current = false
      return
    }
    headingRef.current?.focus()
  }, [step])

  const heading = (text: string) => (
    <h2
      ref={headingRef}
      tabIndex={-1}
      className="mt-3 font-display text-[34px] leading-[1.05] font-extrabold tracking-tight text-ink focus:outline-none sm:text-5xl"
    >
      {text}
    </h2>
  )

  const next = (label: string) => (
    <button type="button" onClick={() => onStepChange(step + 1)} className={`${primary} mt-7`}>
      {label}
      <ArrowRightIcon className="h-5 w-5 shrink-0 transition-transform group-hover:translate-x-0.5" />
    </button>
  )

  return (
    <section
      aria-label="Introducción"
      className="mx-auto grid w-full max-w-6xl gap-5 px-4 py-4 sm:py-6 lg:flex-1 lg:grid-cols-[1.05fr_1fr] lg:gap-12 lg:px-8 lg:py-8"
    >
      <PlacePhoto
        place={PLACES[step] ?? PLACES[0]}
        className="h-48 sm:h-72 lg:order-none lg:h-auto lg:min-h-[480px]"
      />

      <div className="flex flex-col lg:py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <ol aria-label="Pasos de la introducción" className="flex items-center">
              {Array.from({ length: WELCOME_STEPS }, (_, index) => (
                <li key={index}>
                  <button
                    type="button"
                    onClick={() => onStepChange(index)}
                    aria-current={index === step ? 'step' : undefined}
                    aria-label={`Paso ${index + 1} de ${WELCOME_STEPS}`}
                    className="focus-ring grid h-11 w-10 place-items-center rounded-full"
                  >
                    <span
                      aria-hidden="true"
                      className={`block h-1.5 rounded-full transition-all duration-300 ${
                        index === step ? 'w-8 bg-wine-700' : index < step ? 'w-4 bg-wine-300' : 'w-4 bg-sand-300'
                      }`}
                    />
                  </button>
                </li>
              ))}
            </ol>
            <p aria-hidden="true" className="text-xs font-semibold text-ink-muted tabular-nums">
              {step + 1} / {WELCOME_STEPS}
            </p>
          </div>
          <button
            type="button"
            onClick={onFinish}
            className="focus-ring min-h-11 rounded-full px-4 text-sm font-semibold text-ink-muted transition-colors hover:bg-sand-100 hover:text-ink"
          >
            Saltar
          </button>
        </div>

        <div key={step} className="flex flex-1 flex-col justify-center py-4 motion-safe:animate-panel-in lg:py-8">
          <p className="eyebrow">{EYEBROWS[step]}</p>

          {step === 0 && (
            <>
              {heading('Hola. ¿Exploramos la localidad?')}
              <p className="mt-5 max-w-lg text-base leading-relaxed text-ink-muted sm:text-lg">
                Consulta en lenguaje sencillo cómo se invierten los recursos de la Alcaldía Local de San Cristóbal:
                metas del plan, presupuestos participativos y peticiones ciudadanas, siempre con su fuente.
              </p>
              <div>{next('Comenzar')}</div>
            </>
          )}

          {step === 1 && (
            <>
              {heading('Pregunta, comprende y actúa.')}
              <ul className="mt-6 space-y-2.5">
                {FEATURES.map((feature, index) => (
                  <li key={feature.title} className="flex gap-4 rounded-card border border-sand-200 bg-white px-4 py-3">
                    <span
                      aria-hidden="true"
                      className="grid h-9 w-9 shrink-0 place-items-center rounded-tile bg-wine-700 font-display text-sm font-extrabold text-white"
                    >
                      {index + 1}
                    </span>
                    <div>
                      <h3 className="font-display font-bold text-ink">{feature.title}</h3>
                      <p className="mt-0.5 text-sm leading-relaxed text-ink-muted">{feature.text}</p>
                    </div>
                  </li>
                ))}
              </ul>
              <div>{next('Continuar')}</div>
            </>
          )}

          {step === 2 && (
            <div className="space-y-6">
              {heading('¿Qué quieres saber o hacer?')}
              <ChatInput onSend={onAsk} isLoading={isLoading} inputId="welcome-question" rows={2} />
              <ExampleQuestions onSelect={onAsk} disabled={isLoading} headingId="welcome-examples" />
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
