import { PageError, PageLoading, PageShell } from '../components/PageShell'
import { UsageReportView } from '../components/UsageReportView'
import { useUsage } from '../hooks/useUsage'

export function UsagePage() {
  const { state, reload } = useUsage()

  return (
    <PageShell
      titleId="usage-title"
      eyebrow="Transparencia del asistente"
      title="Consumo del modelo de lenguaje"
      description="Tokens usados por el asistente para responder y su costo equivalente con los precios publicados de Gemini."
    >
      {state.status === 'loading' && <PageLoading label="Cargando consumo…" />}
      {state.status === 'error' && <PageError message={state.message} onRetry={reload} />}
      {state.status === 'ready' && <UsageReportView report={state.report} />}
    </PageShell>
  )
}
