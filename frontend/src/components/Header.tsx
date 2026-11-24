import { FALLBACK_DISCLAIMER } from '../lib/disclaimer'
import { InfoIcon } from './icons'

export type Page = 'chat' | 'sources' | 'usage'

interface HeaderProps {
  page: Page
  disclaimer?: string | null
}

const LINKS: { page: Page; href: string; label: string }[] = [
  { page: 'chat', href: '#/', label: 'Chat' },
  { page: 'sources', href: '#/fuentes', label: 'Fuentes' },
  { page: 'usage', href: '#/consumo', label: 'Consumo' },
]

export function Header({ page, disclaimer }: HeaderProps) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto max-w-3xl px-4 pt-4">
        <p className="text-sm font-medium text-blue-800">Datos abiertos · Bogotá</p>
        <h1 className="text-xl font-bold text-slate-900 sm:text-2xl">
          Verificador de información pública · San Cristóbal
        </h1>
        <p
          role="note"
          className="mt-3 flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950"
        >
          <InfoIcon className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{disclaimer || FALLBACK_DISCLAIMER}</span>
        </p>
        <nav aria-label="Secciones" className="mt-3">
          <ul className="flex gap-1">
            {LINKS.map((link) => {
              const current = link.page === page
              return (
                <li key={link.page}>
                  <a
                    href={link.href}
                    aria-current={current ? 'page' : undefined}
                    className={`inline-flex min-h-11 items-center border-b-2 px-3 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 ${
                      current
                        ? 'border-blue-800 text-blue-900'
                        : 'border-transparent text-slate-700 hover:text-slate-900'
                    }`}
                  >
                    {link.label}
                  </a>
                </li>
              )
            })}
          </ul>
        </nav>
      </div>
    </header>
  )
}
