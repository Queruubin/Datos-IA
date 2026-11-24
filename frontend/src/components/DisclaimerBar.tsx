import { useId, useState } from 'react'
import { FALLBACK_DISCLAIMER } from '../lib/disclaimer'
import { ChevronIcon, InfoIcon } from './icons'

interface DisclaimerBarProps {
  disclaimer?: string | null
}

/**
 * The disclaimer is always on screen, but as one line: the full text stays in the DOM (screen
 * readers read it all) and "Leer más" unfolds it visually.
 */
export function DisclaimerBar({ disclaimer }: DisclaimerBarProps) {
  const id = useId()
  const [open, setOpen] = useState(false)
  return (
    <div className="border-b border-amber-200/80 bg-amber-50 text-amber-950">
      <div className="flex items-start gap-2 px-4 py-1.5 lg:px-5">
        <InfoIcon className="mt-0.5 h-4 w-4 shrink-0" />
        <p role="note" id={id} className={`min-w-0 flex-1 text-xs leading-5 ${open ? '' : 'truncate xl:overflow-visible xl:whitespace-normal'}`}>
          {disclaimer || FALLBACK_DISCLAIMER}
        </p>
        <button
          type="button"
          aria-expanded={open}
          aria-controls={id}
          onClick={() => setOpen((value) => !value)}
          className="focus-ring -my-1 inline-flex xl:hidden min-h-7 shrink-0 items-center gap-0.5 rounded px-1 text-xs font-semibold underline-offset-2 hover:underline"
        >
          {open ? 'Leer menos' : 'Leer más'}
          <ChevronIcon className={`h-3.5 w-3.5 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
        </button>
      </div>
    </div>
  )
}
