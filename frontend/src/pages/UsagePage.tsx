import { UsageReportView } from '../components/UsageReportView'
import { useUsage } from '../hooks/useUsage'

export function UsagePage() {
  const { state, reload } = useUsage()

  return (
    <section aria-labelledby="usage-title" className="space-y-4 pb-8">
      <div>
        <h2 id="usage-title" className="text-lg font-semibold text-slate-900">
          Consumo del modelo de lenguaje
        </h2>
        <p className="mt-1 text-sm text-slate-700">
          Tokens usados por el asistente para responder y su costo equivalente con los precios publicados de Gemini.
        </p>
      </div>

      {state.status === 'loading' && (
        <p role="status" className="text-slate-700">
          Cargando consumo…
        </p>
      )}

      {state.status === 'error' && (
        <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-900">
          <p>{state.message}</p>
          <button
            type="button"
            onClick={reload}
            className="mt-3 min-h-11 rounded-lg border border-red-800 bg-white px-4 py-2 text-sm font-semibold hover:bg-red-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-800"
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      {state.status === 'ready' && <UsageReportView report={state.report} />}
    </section>
  )
}
