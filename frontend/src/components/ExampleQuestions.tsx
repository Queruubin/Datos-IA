import { EXAMPLE_QUESTIONS } from '../lib/examples'

interface ExampleQuestionsProps {
  onSelect: (question: string) => void
  disabled?: boolean
  questions?: string[]
}

export function ExampleQuestions({ onSelect, disabled, questions = EXAMPLE_QUESTIONS }: ExampleQuestionsProps) {
  return (
    <section aria-labelledby="examples-title" className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 id="examples-title" className="text-lg font-semibold text-slate-900">
        Pregunta sobre la gestión de la Alcaldía Local
      </h2>
      <p className="mt-1 text-sm text-slate-700">
        Las respuestas se basan en datos oficiales publicados y siempre citan la fuente. Puedes empezar con un
        ejemplo:
      </p>
      <ul className="mt-3 space-y-2">
        {questions.map((question) => (
          <li key={question}>
            <button
              type="button"
              onClick={() => onSelect(question)}
              disabled={disabled}
              className="min-h-11 w-full rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-left text-sm font-medium text-blue-900 hover:bg-blue-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {question}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
