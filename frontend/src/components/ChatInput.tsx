import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { MAX_QUESTION_LENGTH } from '../hooks/useChat'
import { SendIcon } from './icons'

interface ChatInputProps {
  onSend: (question: string) => void
  isLoading: boolean
  maxLength?: number
  /** Unique field id (the welcome flow and the chat each render one). */
  inputId?: string
  rows?: number
}

export function ChatInput({
  onSend,
  isLoading,
  maxLength = MAX_QUESTION_LENGTH,
  inputId = 'question',
  rows = 1,
}: ChatInputProps) {
  const [value, setValue] = useState('')
  const canSend = !isLoading && value.trim().length > 0
  const nearLimit = value.length >= maxLength * 0.9

  const submit = () => {
    if (!canSend) return
    onSend(value.trim())
    setValue('')
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor={inputId} className="sr-only">
        Escribe tu pregunta
      </label>
      <div className="flex items-end gap-2 rounded-card border border-sand-300 bg-white p-1.5 pl-4 transition-colors focus-within:border-wine-700 focus-within:ring-2 focus-within:ring-wine-700/15 has-[:disabled]:bg-sand-50">
        <textarea
          id={inputId}
          name="question"
          rows={rows}
          value={value}
          maxLength={maxLength}
          disabled={isLoading}
          onChange={(event) => setValue(event.target.value.slice(0, maxLength))}
          onKeyDown={handleKeyDown}
          aria-describedby={`${inputId}-help ${inputId}-count`}
          placeholder="Pregunta sobre San Cristóbal…"
          className="max-h-40 min-h-11 flex-1 resize-none self-center bg-transparent py-2.5 text-base leading-6 text-ink [field-sizing:content] placeholder:text-ink-muted focus:outline-none disabled:text-ink-muted"
        />
        <button
          type="submit"
          disabled={!canSend}
          className="focus-ring grid h-11 w-11 shrink-0 place-items-center rounded-tile bg-wine-700 text-white transition-colors hover:bg-wine-800 disabled:cursor-not-allowed disabled:bg-sand-300 disabled:text-ink-muted"
        >
          {isLoading ? (
            <span
              aria-hidden="true"
              className="h-4 w-4 rounded-full border-2 border-white/40 border-t-white motion-safe:animate-spin"
            />
          ) : (
            <SendIcon />
          )}
          <span className="sr-only">{isLoading ? 'Consultando…' : 'Enviar pregunta'}</span>
        </button>
      </div>
      <div className="mt-1.5 flex items-center justify-between gap-3 px-1 text-[11px] text-ink-muted">
        <p id={`${inputId}-help`} className="hidden sm:block">
          Enter para enviar · Shift + Enter para nueva línea
        </p>
        <p id={`${inputId}-count`} className={`ml-auto tabular-nums ${nearLimit ? 'font-semibold text-wine-800' : ''}`}>
          {value.length}/{maxLength}
          <span className="sr-only"> caracteres</span>
        </p>
      </div>
    </form>
  )
}
