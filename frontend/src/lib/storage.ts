/** localStorage can be missing or throw (private mode, blocked site data): never let it break the UI. */
export function readFlag(key: string): boolean {
  try {
    return window.localStorage.getItem(key) === '1'
  } catch {
    return false
  }
}

export function writeFlag(key: string, value: boolean): void {
  try {
    if (value) window.localStorage.setItem(key, '1')
    else window.localStorage.removeItem(key)
  } catch {
    // Not persisted: the welcome flow will simply show again next time.
  }
}

export const WELCOME_DONE_KEY = 'sc-verificador:welcome-done'
