import { useCallback, useEffect, useState } from 'react'
import { getUsage } from '../api/client'
import { errorMessage } from '../api/errors'
import type { UsageReport } from '../api/types'

type UsageState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; report: UsageReport }

export function useUsage(load: typeof getUsage = getUsage) {
  const [state, setState] = useState<UsageState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    load()
      .then((report) => active && setState({ status: 'ready', report }))
      .catch((error: unknown) => active && setState({ status: 'error', message: errorMessage(error) }))
    return () => {
      active = false
    }
  }, [load, attempt])

  const reload = useCallback(() => {
    setState({ status: 'loading' })
    setAttempt((value) => value + 1)
  }, [])

  return { state, reload }
}
