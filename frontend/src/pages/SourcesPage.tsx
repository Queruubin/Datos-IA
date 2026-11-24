import { PageError, PageLoading, PageShell } from '../components/PageShell'
import { SourcesTable } from '../components/SourcesTable'
import { useSources } from '../hooks/useSources'

export function SourcesPage() {
  const { state, reload } = useSources()

  return (
    <PageShell
      titleId="sources-title"
      eyebrow="Transparencia"
      title="Fuentes de datos"
      description="Estos son los conjuntos de datos oficiales que usa el asistente. La fecha de corte indica hasta cuándo llegan los datos."
    >
      {state.status === 'loading' && <PageLoading label="Cargando fuentes…" />}
      {state.status === 'error' && <PageError message={state.message} onRetry={reload} />}
      {state.status === 'ready' && <SourcesTable sources={state.sources} />}
    </PageShell>
  )
}
