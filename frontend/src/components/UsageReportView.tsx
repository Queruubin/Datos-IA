import type { ExchangeRate, ModelPrice, UsageReport } from '../api/types'
import { formatCutoff } from '../lib/formatDate'
import { formatCop, formatDecimal, formatTokens, formatUsd } from '../lib/formatUsage'
import { isSafeUrl } from '../lib/url'
import { AlertIcon, ExternalIcon, InfoIcon } from './icons'

interface UsageReportViewProps {
  report: UsageReport
}

const NOT_AVAILABLE = 'No disponible'

const usd = (value: number | null) => (value === null ? NOT_AVAILABLE : `USD ${formatUsd(value)}`)
const cop = (value: number | null) => (value === null ? NOT_AVAILABLE : `COP ${formatCop(value)}`)

function Tile({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <dt className="text-xs font-medium text-slate-600">{label}</dt>
      <dd className="mt-1 text-lg font-semibold break-words text-slate-900 tabular-nums">{value}</dd>
      {detail && <dd className="text-xs text-slate-600 tabular-nums">{detail}</dd>}
    </div>
  )
}

function rateSourceLabel(rate: ExchangeRate): string {
  switch (rate.source) {
    case 'datos.gov.co':
      return 'TRM oficial publicada en datos.gov.co'
    case 'fallback_setting':
      return 'valor de respaldo configurado en el servidor (no se pudo consultar la TRM oficial)'
    default:
      return 'no disponible'
  }
}

function ExchangeRateInfo({ rate }: { rate: ExchangeRate }) {
  if (rate.value === null) {
    return (
      <p className="text-sm text-slate-700">
        Tasa de cambio: no disponible. No se pudo consultar la TRM oficial, así que los costos en pesos no se
        muestran.
      </p>
    )
  }
  const since = formatCutoff(rate.valid_from)
  return (
    <p className="text-sm text-slate-700">
      Tasa de cambio usada: <span className="font-semibold tabular-nums">{formatDecimal(rate.value)} COP por USD</span>
      {since && <> · vigente desde el {since}</>} · fuente: {rateSourceLabel(rate)}.
    </p>
  )
}

function validity(price: ModelPrice): string {
  if (price.valid_from && price.valid_until) {
    return `Del ${formatCutoff(price.valid_from)} al ${formatCutoff(price.valid_until)} (sin incluir)`
  }
  if (price.valid_from) return `Desde el ${formatCutoff(price.valid_from)}`
  if (price.valid_until) return `Antes del ${formatCutoff(price.valid_until)}`
  return 'Vigente'
}

export function UsageReportView({ report }: UsageReportViewProps) {
  const { all_time: total, today } = report
  const maxDayTokens = Math.max(1, ...report.by_day.map((day) => day.total_tokens))
  const isEmpty = total.calls === 0

  return (
    <div className="space-y-6">
      <p
        role="note"
        className="flex items-start gap-2 rounded-lg border border-blue-300 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-950"
      >
        <InfoIcon className="mt-0.5 h-4 w-4 shrink-0" />
        <span>Con el plan gratuito de Gemini el costo real es $0; estas cifras son el equivalente en el plan pagado.</span>
      </p>

      {isEmpty ? (
        <p className="text-slate-700">Todavía no hay preguntas registradas. Las cifras aparecerán después de usar el chat.</p>
      ) : (
        <>
          <section aria-labelledby="usage-kpis">
            <h3 id="usage-kpis" className="sr-only">
              Resumen
            </h3>
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <Tile label="Preguntas" value={formatTokens(total.questions)} detail={`Hoy: ${formatTokens(today.questions)}`} />
              <Tile
                label="Tokens totales"
                value={formatTokens(total.total_tokens)}
                detail={`Hoy: ${formatTokens(today.total_tokens)}`}
              />
              <Tile label="Costo equivalente USD" value={usd(total.cost_usd)} />
              <Tile label="Costo equivalente COP" value={cop(total.cost_cop)} />
              <Tile
                label="Costo promedio por pregunta"
                value={usd(report.avg_cost_usd_per_question)}
                detail={
                  report.avg_cost_cop_per_question === null ? undefined : cop(report.avg_cost_cop_per_question)
                }
              />
              <Tile
                label="Tokens promedio por pregunta"
                value={report.avg_tokens_per_question === null ? NOT_AVAILABLE : formatTokens(report.avg_tokens_per_question)}
              />
            </dl>
            {total.unpriced_calls > 0 && (
              <p className="mt-3 flex items-start gap-2 text-sm text-amber-900">
                <AlertIcon className="mt-0.5 h-4 w-4 shrink-0" />
                <span>
                  {total.unpriced_calls === 1
                    ? '1 llamada usó un modelo sin precio conocido; no se incluye en el costo.'
                    : `${formatTokens(total.unpriced_calls)} llamadas usaron un modelo sin precio conocido; no se incluyen en el costo.`}
                </span>
              </p>
            )}
          </section>

          <section aria-labelledby="usage-models" className="space-y-2">
            <h3 id="usage-models" className="font-semibold text-slate-900">
              Por modelo
            </h3>
            <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100 text-xs text-slate-700">
                  <tr>
                    <th scope="col" className="px-3 py-2 font-semibold">
                      Modelo
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">
                      Llamadas
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">
                      Entrada
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">
                      Salida
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">
                      Razonamiento
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-semibold">
                      Costo
                    </th>
                  </tr>
                </thead>
                <tbody className="tabular-nums">
                  {report.by_model.map((row) => (
                    <tr key={row.model} className="border-t border-slate-200">
                      <th scope="row" className="px-3 py-2 font-medium break-all text-slate-900">
                        {row.model}
                      </th>
                      <td className="px-3 py-2 text-right">{formatTokens(row.calls)}</td>
                      <td className="px-3 py-2 text-right">{formatTokens(row.input_tokens)}</td>
                      <td className="px-3 py-2 text-right">{formatTokens(row.output_tokens)}</td>
                      <td className="px-3 py-2 text-right">{formatTokens(row.thinking_tokens)}</td>
                      <td className="px-3 py-2 text-right whitespace-nowrap">
                        {row.cost_usd === null ? 'Sin precio' : usd(row.cost_usd)}
                        {row.cost_cop !== null && (
                          <span className="block text-xs text-slate-600">{cop(row.cost_cop)}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section aria-labelledby="usage-days" className="space-y-2">
            <h3 id="usage-days" className="font-semibold text-slate-900">
              Últimos 30 días
            </h3>
            <ul className="space-y-2">
              {report.by_day.map((day) => (
                <li key={day.day} className="text-sm">
                  <div className="flex flex-wrap justify-between gap-x-3 text-slate-700">
                    <span className="font-medium text-slate-900">{formatCutoff(day.day) ?? day.day}</span>
                    <span className="tabular-nums">
                      {formatTokens(day.total_tokens)} tokens · {formatTokens(day.questions)}{' '}
                      {day.questions === 1 ? 'pregunta' : 'preguntas'} · {usd(day.cost_usd)}
                    </span>
                  </div>
                  <div className="mt-1 h-2 rounded bg-slate-200" aria-hidden="true">
                    <div
                      className="h-2 rounded bg-blue-700"
                      style={{ width: `${Math.max(2, (day.total_tokens / maxDayTokens) * 100)}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}

      <section aria-labelledby="usage-prices" className="space-y-2">
        <h3 id="usage-prices" className="font-semibold text-slate-900">
          Precios usados
        </h3>
        <ExchangeRateInfo rate={report.exchange_rate} />
        <p className="text-sm text-slate-700">
          Plan {report.pricing.tier}. {report.pricing.unit}. Consultados el {formatCutoff(report.pricing.read_on)}.
        </p>
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 text-xs text-slate-700">
              <tr>
                <th scope="col" className="px-3 py-2 font-semibold">
                  Modelo
                </th>
                <th scope="col" className="px-3 py-2 text-right font-semibold">
                  Entrada (USD)
                </th>
                <th scope="col" className="px-3 py-2 text-right font-semibold">
                  Salida (USD)
                </th>
                <th scope="col" className="px-3 py-2 font-semibold">
                  Vigencia
                </th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {report.pricing.prices.map((price) => (
                <tr key={`${price.model}-${price.valid_from ?? ''}`} className="border-t border-slate-200">
                  <th scope="row" className="px-3 py-2 font-medium break-all text-slate-900">
                    {price.model}
                  </th>
                  <td className="px-3 py-2 text-right">{formatDecimal(price.input_usd_per_million)}</td>
                  <td className="px-3 py-2 text-right">{formatDecimal(price.output_usd_per_million)}</td>
                  <td className="px-3 py-2">{validity(price)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {isSafeUrl(report.pricing.source_url) && (
          <a
            href={report.pricing.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded text-sm font-medium text-blue-800 underline underline-offset-2 hover:text-blue-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
          >
            Ver la tabla oficial de precios de Gemini
            <ExternalIcon />
            <span className="sr-only">(se abre en una pestaña nueva)</span>
          </a>
        )}
      </section>
    </div>
  )
}
