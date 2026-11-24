import type { ReactNode } from 'react'
import { ErrorNotice } from './ErrorNotice'

interface PageShellProps {
  titleId: string
  eyebrow: string
  title: string
  description: ReactNode
  children: ReactNode
}

/** Layout of the secondary pages (Fuentes, Consumo): title block and content on the warm canvas. */
export function PageShell({ titleId, eyebrow, title, description, children }: PageShellProps) {
  return (
    <section aria-labelledby={titleId} className="mx-auto w-full max-w-6xl space-y-6 px-4 py-6 pb-12 lg:px-8 lg:py-10">
      <div className="max-w-2xl">
        <p className="eyebrow">{eyebrow}</p>
        <h2 id={titleId} className="mt-2 font-display text-3xl leading-tight font-extrabold tracking-tight text-ink sm:text-4xl">
          {title}
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-ink-muted sm:text-base">{description}</p>
      </div>
      {children}
    </section>
  )
}

export function PageLoading({ label }: { label: string }) {
  return (
    <div role="status" className="grid gap-3 md:grid-cols-2">
      <p className="sr-only">{label}</p>
      {[0, 1, 2, 3].map((index) => (
        <div key={index} aria-hidden="true" className="rounded-card border border-sand-200 bg-white p-5">
          <div className="skeleton h-4 w-2/3 rounded" />
          <div className="skeleton mt-4 h-3 w-1/2 rounded" />
          <div className="skeleton mt-2 h-3 w-1/3 rounded" />
        </div>
      ))}
    </div>
  )
}

export function PageError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert">
      <ErrorNotice message={message} onRetry={onRetry} />
    </div>
  )
}
