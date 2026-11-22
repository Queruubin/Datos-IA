export function LoadingIndicator() {
  return (
    <div role="status" className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <span
        aria-hidden="true"
        className="mt-0.5 h-5 w-5 shrink-0 rounded-full border-2 border-blue-200 border-t-blue-800 motion-safe:animate-spin"
      />
      <div>
        <p className="font-medium text-slate-900">Consultando fuentes oficiales…</p>
        <p className="text-sm text-slate-600">Esto puede tardar entre 2 y 15 segundos.</p>
      </div>
    </div>
  )
}
