import { SourcesTable } from '../components/SourcesTable'
import { useSources } from '../hooks/useSources'

export function SourcesPage() {
  const { state, reload } = useSources()

  return (
    <section aria-labelledby="sources-title" className="space-y-4 pb-8">
      <div>
        <h2 id="sources-title" className="text-lg font-semibold text-slate-900">
          Fuentes de datos
        </h2>
        <p className="mt-1 text-sm text-slate-700">
          Estos son los conjuntos de datos oficiales que usa el asistente. La fecha de corte indica hasta cuándo
          llegan los datos.
        </p>
      </div>

      {state.status === 'loading' && (
        <p role="status" className="text-slate-700">
          Cargando fuentes…
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

      {state.status === 'ready' && <SourcesTable sources={state.sources} />}
    </section>
  )
}
