import type { ChartSpec } from '../../api/types'
import { formatCompact, formatFull } from '../../lib/formatValue'
import { groupedColors, SINGLE_SERIES } from './chartColors'
import { Legend } from './Legend'

interface BarChartProps {
  chart: ChartSpec
}

/** Longest bar uses 78% of the track so the value label always fits at its tip. */
const MAX_BAR_SHARE = 78

function barWidth(value: number | null, max: number): string {
  if (value === null || value <= 0 || max <= 0) return '0%'
  return `${Math.max((value / max) * MAX_BAR_SHARE, 0.8)}%`
}

/**
 * Horizontal bars (one series) or grouped bars (2-3 series per category). In a wide container
 * the label sits in its own column; in a narrow one it goes on its own line so long names
 * wrap instead of being clipped.
 */
export function BarChart({ chart }: BarChartProps) {
  const grouped = chart.series.length > 1
  const colors = grouped ? groupedColors(chart.series.length) : [SINGLE_SERIES]
  const max = Math.max(0, ...chart.series.flatMap((series) => series.values.map((value) => value ?? 0)))

  return (
    <div className="space-y-4">
      {grouped && <Legend names={chart.series.map((series) => series.name)} colors={colors} />}
      <ul className="space-y-3 @lg:space-y-2.5">
        {chart.categories.map((category, row) => (
          <li
            key={`${category}-${row}`}
            className="@lg:grid @lg:grid-cols-[minmax(0,13rem)_1fr] @lg:items-center @lg:gap-4"
          >
            <p className="text-xs leading-snug font-medium break-words text-ink @lg:text-right @lg:text-[13px]">
              {category}
            </p>
            <div className="mt-1 space-y-0.5 @lg:mt-0">
              {chart.series.map((series, index) => {
                const value = series.values[row] ?? null
                const full = formatFull(value, chart.unit)
                return (
                  <div key={series.name} className="group relative flex items-center gap-2">
                    <span
                      className="block h-3 shrink-0 rounded-r-[4px] transition-opacity group-hover:opacity-80"
                      style={{ width: barWidth(value, max), backgroundColor: colors[index] }}
                    />
                    <span className="text-xs font-semibold whitespace-nowrap text-ink tabular-nums">
                      {formatCompact(value, chart.unit)}
                    </span>
                    <span
                      role="presentation"
                      className="pointer-events-none absolute top-1/2 right-0 z-10 hidden -translate-y-1/2 rounded-md bg-ink px-2 py-1 text-xs whitespace-nowrap text-white shadow group-hover:block"
                    >
                      {grouped ? `${series.name}: ${full}` : full}
                    </span>
                  </div>
                )
              })}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
