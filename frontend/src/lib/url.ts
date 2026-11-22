/** Only http(s) links from the API are rendered as anchors. */
export function isSafeUrl(value: string | null | undefined): value is string {
  if (!value) return false
  try {
    const { protocol } = new URL(value)
    return protocol === 'https:' || protocol === 'http:'
  } catch {
    return false
  }
}
