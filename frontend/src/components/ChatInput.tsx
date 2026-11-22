import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { MAX_QUESTION_LENGTH } from '../hooks/useChat'

interface ChatInputProps {
  onSend: (question: string) => void
  isLoading: boolean
  maxLength?: number
}

export function ChatInput({ onSend, isLoading, maxLength = MAX_QUESTION_LENGTH }: ChatInputProps) {
  const [value, setValue] = useState('')
  const canSend = !isLoading && value.trim().length > 0

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
    <form onSubmit={handleSubmit} className="space-y-2">
      <label htmlFor="question" className="block text-sm font-medium text-slate-800">
        Escribe tu pregunta
      </label>
      <textarea
        id="question"
        name="question"
        rows={2}
        value={value}
        maxLength={maxLength}
        disabled={isLoading}
        onChange={(event) => setValue(event.target.value.slice(0, maxLength))}
        onKeyDown={handleKeyDown}
        aria-describedby="question-help question-count"
        placeholder="Por ejemplo: ¿Cuánto se ejecutó del presupuesto en 2025?"
        className="block w-full resize-none rounded-lg border border-slate-400 bg-white px-3 py-2 text-base text-slate-900 placeholder:text-slate-500 focus:border-blue-700 focus:outline-2 focus:outline-offset-0 focus:outline-blue-700 disabled:bg-slate-100 disabled:text-slate-500"
      />
      <div className="flex items-center justify-between gap-3">
        <p id="question-help" className="text-xs text-slate-600">
          Enter para enviar · Shift + Enter para nueva línea
        </p>
        <p id="question-count" className="shrink-0 text-xs text-slate-600 tabular-nums">
          {value.length}/{maxLength}
          <span className="sr-only"> caracteres</span>
        </p>
      </div>
      <button
        type="submit"
        disabled={!canSend}
        className="min-h-11 w-full rounded-lg bg-blue-800 px-4 py-2 font-semibold text-white hover:bg-blue-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400 sm:w-auto"
      >
        {isLoading ? 'Consultando…' : 'Enviar pregunta'}
      </button>
    </form>
  )
}
