interface LegendProps {
  names: string[]
  colors: string[]
  shape?: 'square' | 'line'
}

export function Legend({ names, colors, shape = 'square' }: LegendProps) {
  return (
    <ul aria-label="Leyenda" className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-muted">
      {names.map((name, index) => (
        <li key={name} className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className={shape === 'line' ? 'h-0.5 w-4 rounded-full' : 'h-2.5 w-2.5 rounded-sm'}
            style={{ backgroundColor: colors[index] }}
          />
          {name}
        </li>
      ))}
    </ul>
  )
}
