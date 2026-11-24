interface LoadingIndicatorProps {
  /** 'full' adds the KPI and chart placeholders (insight panel and inline answers). */
  variant?: 'compact' | 'full'
}

function Status() {
  return (
    <div role="status" className="flex items-center gap-3">
      <span
        aria-hidden="true"
        className="h-5 w-5 shrink-0 rounded-full border-2 border-wine-200 border-t-wine-700 motion-safe:animate-spin"
      />
      <div>
        <p className="text-sm font-semibold text-ink">Consultando fuentes oficiales…</p>
        <p className="text-xs text-ink-muted">Esto puede tardar entre 5 y 30 segundos.</p>
      </div>
    </div>
  )
}

/** Waiting state for an answer: status text plus a skeleton of what is coming (numbers, chart). */
export function LoadingIndicator({ variant = 'full' }: LoadingIndicatorProps) {
  if (variant === 'compact') return <Status />
  return (
    <div className="space-y-6">
      <Status />
      <div aria-hidden="true" className="space-y-6">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          {[0, 1, 2].map((index) => (
            <div key={index} className={`rounded-tile bg-sand-100 px-4 py-3 ${index === 2 ? 'hidden sm:block' : ''}`}>
              <div className="skeleton h-3 w-16 rounded" />
              <div className="skeleton mt-3 h-7 w-24 rounded-md" />
            </div>
          ))}
        </div>
        <div className="space-y-3">
          <div className="skeleton h-4 w-1/2 rounded" />
          {[88, 70, 52, 34].map((width) => (
            <div key={width} className="flex items-center gap-3">
              <div className="skeleton h-3 w-20 shrink-0 rounded" />
              <div className="skeleton h-3 rounded-r" style={{ width: `${width}%` }} />
            </div>
          ))}
        </div>
        <div className="space-y-2">
          <div className="skeleton h-3 w-full rounded" />
          <div className="skeleton h-3 w-11/12 rounded" />
          <div className="skeleton h-3 w-3/5 rounded" />
        </div>
      </div>
    </div>
  )
}
