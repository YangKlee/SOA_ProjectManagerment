export const SESSION_TOKEN_KEY = 'graduation-project.auth.access.v1'

export function clearSessionToken(): boolean {
  try { sessionStorage.removeItem(SESSION_TOKEN_KEY); return true }
  catch {
    try { sessionStorage.setItem(SESSION_TOKEN_KEY, ''); return true }
    catch { return false }
  }
}
export function readSessionToken(): { token: string | null; unavailable: boolean } {
  try {
    const value = sessionStorage.getItem(SESSION_TOKEN_KEY)
    if (value === null) return { token: null, unavailable: false }
    if (!value.trim() || value.length > 16384) {
      clearSessionToken()
      return { token: null, unavailable: false }
    }
    return { token: value.trim(), unavailable: false }
  } catch { return { token: null, unavailable: true } }
}
export function saveSessionToken(token: string): boolean {
  try { sessionStorage.setItem(SESSION_TOKEN_KEY, token); return true }
  catch { clearSessionToken(); return false }
}
