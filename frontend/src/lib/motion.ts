export function prefersReducedMotion(): boolean {
  try {
    return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
  } catch {
    return false
  }
}

/** 'smooth' unless the person asked the system to reduce motion. */
export function scrollBehavior(): ScrollBehavior {
  return prefersReducedMotion() ? 'auto' : 'smooth'
}

/** Scrolls an evidence card into view and focuses it without touching the URL hash (used for pages). */
export function focusElement(id: string): boolean {
  const element = document.getElementById(id)
  if (!element) return false
  element.scrollIntoView?.({ behavior: scrollBehavior(), block: 'center' })
  element.focus({ preventScroll: true })
  return true
}
