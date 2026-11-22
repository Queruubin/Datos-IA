import { useCallback, useEffect, useState } from 'react'
import { getSources } from '../api/client'
import { errorMessage } from '../api/errors'
import type { SourceMetadata } from '../api/types'

type SourcesState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; sources: SourceMetadata[] }

export function useSources(load: typeof getSources = getSources) {
  const [state, setState] = useState<SourcesState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    load()
      .then((sources) => active && setState({ status: 'ready', sources }))
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
