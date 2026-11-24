import type { ReactNode } from 'react'

interface StatTileProps {
  label: string
  value: ReactNode
  detail?: ReactNode
  /** 'lg' for headline numbers (insight panel KPIs), 'md' for dashboards. */
  size?: 'md' | 'lg'
}

/** One number with its label: the same tile in the insight panel and on the Consumo page. Lives in a <dl>. */
export function StatTile({ label, value, detail, size = 'md' }: StatTileProps) {
  return (
    // @container: the number scales with the tile's own width, so "$127,7 mil M" stays on one
    // line in narrow two-column grids on phones instead of breaking into "mil" / "M".
    <div className="@container min-w-0 rounded-tile bg-sand-100 px-4 py-3">
      <dt className="text-xs leading-snug font-medium text-ink-muted">{label}</dt>
      <dd
        className={`mt-1 font-display font-extrabold tracking-tight break-words text-ink tabular-nums ${
          size === 'lg'
            ? 'text-lg @[9.5rem]:text-xl @[11rem]:text-2xl @[14rem]:text-[28px] @[14rem]:leading-9'
            : 'text-base @[8.5rem]:text-lg @[11rem]:text-xl'
        }`}
      >
        {value}
      </dd>
      {detail && <dd className="mt-0.5 text-xs break-words text-ink-muted tabular-nums">{detail}</dd>}
    </div>
  )
}
