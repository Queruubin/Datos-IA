import type { ChartSpec } from '../../api/types'
import { formatCompact, formatFull } from '../../lib/formatValue'
import { StatTile } from '../StatTile'
import { VerdictPill } from '../VerdictBadge'

interface KpiTilesProps {
  chart: ChartSpec
}

/** Stat tiles: the number is the chart. The full value is shown under compact COP amounts. */
export function KpiTiles({ chart }: KpiTilesProps) {
  return (
    <dl className="grid grid-cols-2 gap-2 @xl:grid-cols-3">
      {chart.verdict && (
        <div className="col-span-full flex flex-wrap items-center gap-x-3 gap-y-1">
          <dt className="text-xs text-ink-muted">Resultado del contraste (calculado por código)</dt>
          <dd>
            <VerdictPill verdict={chart.verdict} />
          </dd>
        </div>
      )}
      {chart.kpis.map((kpi) => (
        <StatTile
          key={kpi.label}
          size="lg"
          label={kpi.label}
          value={formatCompact(kpi.value, kpi.unit)}
          detail={kpi.unit === 'COP' && kpi.value !== null ? formatFull(kpi.value, kpi.unit) : undefined}
        />
      ))}
    </dl>
  )
}
