import { useId, useRef, useState } from 'react'
import type { Gap } from '../api/types'
import { BOGOTA_TE_ESCUCHA_URL, buildPetitionDraft } from '../lib/petition'
import { ExternalIcon, InfoIcon } from './icons'

interface PetitionCardProps {
  gap: Gap
}

type CopyState = 'idle' | 'copied' | 'failed'

const button =
  'focus-ring inline-flex min-h-11 items-center justify-center gap-1.5 rounded-full px-5 text-sm font-semibold transition-colors'

/**
 * Suggests filing a right-of-petition when the data is not published. The draft comes from a
 * fixed template (no LLM, no figures); nothing is sent automatically.
 */
export function PetitionCard({ gap }: PetitionCardProps) {
  const uid = useId()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(() => buildPetitionDraft(gap))
  const [copyState, setCopyState] = useState<CopyState>('idle')
  const textRef = useRef<HTMLTextAreaElement>(null)

  const copy = async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable')
      await navigator.clipboard.writeText(draft)
      setCopyState('copied')
    } catch {
      // Fallback: select the text so the person can copy it by hand.
      textRef.current?.focus()
      textRef.current?.select()
      setCopyState('failed')
    }
  }

  return (
    <section
      aria-labelledby={`${uid}-title`}
      className="rounded-card bg-wine-50 p-4 ring-1 ring-wine-200 sm:p-5"
    >
      <p className="eyebrow">Derecho de petición</p>
      <h3 id={`${uid}-title`} className="mt-1 font-display text-lg leading-snug font-bold text-ink">
        ¿Quieres pedir este dato a la Alcaldía?
      </h3>
      <p className="mt-1 text-sm leading-relaxed text-ink">
        Cualquier persona puede pedir información pública a la Alcaldía Local con un derecho de petición. Te
        preparamos un borrador que puedes editar.
      </p>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={`${uid}-panel`}
        onClick={() => setOpen((value) => !value)}
        className={`${button} mt-3 bg-wine-700 text-white hover:bg-wine-800`}
      >
        {open ? 'Ocultar borrador' : 'Ver borrador'}
      </button>

      {open && (
        <div id={`${uid}-panel`} className="mt-3 space-y-3">
          <label htmlFor={`${uid}-draft`} className="block text-sm font-medium text-ink">
            Borrador del derecho de petición (editable)
          </label>
          <textarea
            id={`${uid}-draft`}
            ref={textRef}
            value={draft}
            rows={14}
            onChange={(event) => {
              setDraft(event.target.value)
              setCopyState('idle')
            }}
            aria-describedby={`${uid}-help`}
            className="block w-full rounded-tile border border-sand-300 bg-white px-3 py-2 font-mono text-[13px] leading-relaxed text-ink focus:border-wine-700 focus:outline-2 focus:outline-offset-0 focus:outline-wine-700"
          />
          <p id={`${uid}-help`} className="text-xs text-ink-muted">
            Reemplaza lo que está entre corchetes con tus datos. No guardamos ni enviamos nada: tú decides si lo
            radicas.
          </p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button type="button" onClick={copy} className={`${button} border border-wine-700 bg-white text-wine-800 hover:bg-wine-100`}>
              Copiar borrador
            </button>
            <a
              href={BOGOTA_TE_ESCUCHA_URL}
              target="_blank"
              rel="noopener noreferrer"
              className={`${button} bg-wine-700 text-white hover:bg-wine-800`}
            >
              Radicar en Bogotá Te Escucha
              <ExternalIcon />
              <span className="sr-only">(se abre en una pestaña nueva)</span>
            </a>
          </div>
          <p role="status" className="text-sm text-ink">
            {copyState === 'copied' && 'Borrador copiado. Pégalo en el formulario de Bogotá Te Escucha.'}
            {copyState === 'failed' && 'No se pudo copiar automáticamente: el texto quedó seleccionado para que lo copies.'}
          </p>
          <p className="flex items-start gap-1.5 text-xs leading-relaxed text-ink-muted">
            <InfoIcon className="mt-px h-3.5 w-3.5 shrink-0 text-wine-700" />
            Nada se envía automáticamente. Este asistente no es vocero de la Alcaldía; el borrador es una ayuda y
            puedes cambiarlo por completo.
          </p>
        </div>
      )}
    </section>
  )
}
