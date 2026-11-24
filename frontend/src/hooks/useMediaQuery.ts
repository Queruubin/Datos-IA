import { useCallback, useSyncExternalStore } from 'react'

/** Desktop workspace (conversation + insight panel); below it the answer renders inline. */
export const DESKTOP_QUERY = '(min-width: 1024px)'

function getMatcher(query: string): MediaQueryList | null {
  try {
    return typeof window.matchMedia === 'function' ? window.matchMedia(query) : null
  } catch {
    return null
  }
}

/** Live result of a CSS media query (false where matchMedia is unavailable, e.g. tests). */
export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const matcher = getMatcher(query)
      if (!matcher) return () => {}
      matcher.addEventListener?.('change', onChange)
      return () => matcher.removeEventListener?.('change', onChange)
    },
    [query],
  )
  return useSyncExternalStore(
    subscribe,
    () => getMatcher(query)?.matches ?? false,
    () => false,
  )
}
