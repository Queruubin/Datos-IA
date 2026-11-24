import { AlertIcon } from './icons'

interface ErrorNoticeProps {
  message: string
  onRetry?: () => void
  retryDisabled?: boolean
}

/** Friendly error with an optional retry (chat answers, Fuentes and Consumo). */
export function ErrorNotice({ message, onRetry, retryDisabled }: ErrorNoticeProps) {
  return (
    <div className="rounded-card border border-red-200 bg-red-50 p-4 text-red-900">
      <p className="flex items-start gap-2 text-sm leading-relaxed">
        <AlertIcon className="mt-0.5 h-5 w-5 shrink-0" />
        <span>{message}</span>
      </p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          disabled={retryDisabled}
          className="mt-3 inline-flex min-h-11 items-center rounded-full border border-red-800 bg-white px-5 text-sm font-semibold text-red-900 transition-colors hover:bg-red-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Intentar de nuevo
        </button>
      )}
    </div>
  )
}
