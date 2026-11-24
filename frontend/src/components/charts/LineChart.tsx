import { useEffect, useRef, useState } from 'react'
import type { ChartSpec } from '../../api/types'
import { formatCompact, formatFull } from '../../lib/formatValue'
import { LINE_SERIES } from './chartColors'
import { Legend } from './Legend'

interface LineChartProps {
  chart: ChartSpec
}

const HEIGHT = 180
const PAD = { top: 12, right: 64, bottom: 26, left: 48 }

/** Tracks the rendered width so text keeps its real size (no viewBox scaling). */
function useWidth(fallback = 320) {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(fallback)
  useEffect(() => {
    const element = ref.current
    if (!element) return
    const update = () => setWidth(Math.max(element.clientWidth || fallback, 240))
    update()
    if (typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(update)
    observer.observe(element)
    return () => observer.disconnect()
  }, [fallback])
  return [ref, width] as const
}

function niceMax(value: number): number {
  if (value <= 0) return 1
  const power = 10 ** Math.floor(Math.log10(value))
  const step = [1, 2, 2.5, 5, 10].find((factor) => factor * power >= value) ?? 10
  return step * power
}

/** Monthly series (e.g. PAC programmed vs executed): 2px lines, one y axis, end labels. */
export function LineChart({ chart }: LineChartProps) {
  const [ref, width] = useWidth()
  const [hover, setHover] = useState<number | null>(null)
  const count = chart.categories.length
  const values = chart.series.flatMap((series) => series.values.map((value) => value ?? 0))
  const top = niceMax(Math.max(0, ...values))
  const plotWidth = width - PAD.left - PAD.right
  const plotHeight = HEIGHT - PAD.top - PAD.bottom
  const x = (index: number) => PAD.left + (count <= 1 ? plotWidth / 2 : (index / (count - 1)) * plotWidth)
  const y = (value: number) => PAD.top + plotHeight - (Math.max(value, 0) / top) * plotHeight
  const ticks = [0, top / 2, top]
  const labelIndexes = count <= 4 ? chart.categories.map((_, i) => i) : [0, Math.floor((count - 1) / 2), count - 1]

  const ends = chart.series.map((series) => {
    const last = series.values[count - 1]
    return last === null || last === undefined ? null : y(last)
  })
  const endsCollide = ends.length === 2 && ends[0] !== null && ends[1] !== null && Math.abs(ends[0] - ends[1]) < 14

  return (
    <div className="space-y-2">
      <Legend names={chart.series.map((series) => series.name)} colors={LINE_SERIES} shape="line" />
      <div ref={ref} className="relative w-full">
        <svg width={width} height={HEIGHT} className="block max-w-full overflow-visible" aria-hidden="true">
          {ticks.map((tick) => (
            <g key={tick}>
              <line x1={PAD.left} x2={width - PAD.right} y1={y(tick)} y2={y(tick)} stroke="#ece3df" strokeWidth={1} />
              <text x={PAD.left - 6} y={y(tick)} textAnchor="end" dominantBaseline="middle" className="fill-ink-muted text-[11px] tabular-nums">
                {formatCompact(tick, chart.unit)}
              </text>
            </g>
          ))}
          {labelIndexes.map((index) => (
            <text key={index} x={x(index)} y={HEIGHT - 8} textAnchor="middle" className="fill-ink-muted text-[11px]">
              {chart.categories[index]}
            </text>
          ))}
          {hover !== null && (
            <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={PAD.top + plotHeight} stroke="#c9b8b2" strokeWidth={1} />
          )}
          {chart.series.map((series, s) => {
            const points = series.values
              .map((value, index) => (value === null ? null : `${x(index)},${y(value)}`))
              .filter(Boolean)
              .join(' ')
            const last = series.values[count - 1]
            return (
              <g key={series.name}>
                <polyline points={points} fill="none" stroke={LINE_SERIES[s]} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
                {last !== null && last !== undefined && (
                  <>
                    <circle cx={x(count - 1)} cy={y(last)} r={4} fill={LINE_SERIES[s]} stroke="#fff" strokeWidth={2} />
                    {!endsCollide && (
                      <text x={x(count - 1) + 8} y={y(last)} dominantBaseline="middle" className="fill-ink text-[11px] font-semibold tabular-nums">
                        {formatCompact(last, chart.unit)}
                      </text>
                    )}
                  </>
                )}
                {hover !== null && series.values[hover] !== null && (
                  <circle cx={x(hover)} cy={y(series.values[hover] ?? 0)} r={4} fill={LINE_SERIES[s]} stroke="#fff" strokeWidth={2} />
                )}
              </g>
            )
          })}
          {chart.categories.map((category, index) => {
            const half = count <= 1 ? plotWidth / 2 : plotWidth / (count - 1) / 2
            return (
              <rect
                key={category}
                x={x(index) - half}
                y={PAD.top}
                width={half * 2}
                height={plotHeight}
                fill="transparent"
                onMouseEnter={() => setHover(index)}
                onMouseLeave={() => setHover(null)}
              />
            )
          })}
        </svg>
        {hover !== null && (
          <div
            role="presentation"
            className="pointer-events-none absolute top-0 z-10 -translate-x-1/2 rounded-md bg-ink px-2 py-1 text-xs whitespace-nowrap text-white shadow"
            style={{ left: Math.min(Math.max(x(hover), 70), width - 70) }}
          >
            <p className="font-semibold">{chart.categories[hover]}</p>
            {chart.series.map((series) => (
              <p key={series.name} className="tabular-nums">
                {series.name}: {formatFull(series.values[hover] ?? null, chart.unit)}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
