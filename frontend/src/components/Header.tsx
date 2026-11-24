import { SparkIcon } from './icons'

export type Page = 'chat' | 'sources' | 'usage'

interface HeaderProps {
  page: Page
  /** Reopens the welcome flow. */
  onShowWelcome?: () => void
}

const LINKS: { page: Page; href: string; label: string }[] = [
  { page: 'chat', href: '#/', label: 'Chat' },
  { page: 'sources', href: '#/fuentes', label: 'Fuentes' },
  { page: 'usage', href: '#/consumo', label: 'Consumo' },
]

/** One compact row: logo, product name (from sm), section tabs and the introduction link. */
export function Header({ page, onShowWelcome }: HeaderProps) {
  return (
    <header className="relative z-30 border-b border-sand-200 bg-white">
      <div className="flex h-14 items-center gap-2 px-4 sm:gap-3 lg:px-5">
        <a href="#/" className="focus-ring flex min-w-0 items-center gap-2.5 rounded-tile" aria-label="Ir al chat">
          <span
            aria-hidden="true"
            className="grid h-9 w-9 shrink-0 place-items-center rounded-tile bg-linear-135 from-wine-700 to-wine-900 font-display text-sm font-extrabold tracking-tight text-white"
          >
            SC
          </span>
        </a>
        <h1 aria-label="Verificador de información pública · San Cristóbal" className="min-w-0 leading-tight max-sm:sr-only">
          <span className="block truncate text-[15px] font-bold text-ink">
            Verificador<span className="max-lg:hidden"> de información pública</span>
          </span>
          <span className="block truncate text-xs font-medium text-ink-muted">
            San Cristóbal
          </span>
        </h1>

        <nav aria-label="Secciones" className="ml-auto">
          <ul className="flex items-center gap-0.5 rounded-full bg-sand-100 p-1">
            {LINKS.map((link) => {
              const current = link.page === page
              return (
                <li key={link.page}>
                  <a
                    href={link.href}
                    aria-current={current ? 'page' : undefined}
                    className={`focus-ring inline-flex min-h-9 items-center rounded-full px-3 text-[13px] font-semibold transition-colors sm:px-4 sm:text-sm ${
                      current ? 'bg-white text-wine-800 shadow-sm ring-1 ring-sand-200' : 'text-ink-muted hover:text-ink'
                    }`}
                  >
                    {link.label}
                  </a>
                </li>
              )
            })}
          </ul>
        </nav>

        {onShowWelcome && (
          <button
            type="button"
            aria-label="Ver introducción"
            onClick={onShowWelcome}
            className="focus-ring inline-flex h-11 min-w-11 shrink-0 items-center justify-center gap-1.5 rounded-full px-2 text-sm font-semibold text-wine-700 transition-colors hover:bg-wine-50 sm:px-3"
          >
            <SparkIcon className="h-5 w-5 shrink-0 sm:h-4 sm:w-4" />
            <span className="hidden sm:inline">Introducción</span>
          </button>
        )}
      </div>
    </header>
  )
}
