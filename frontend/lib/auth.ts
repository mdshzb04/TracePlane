const SESSION_COOKIE = "has_session"
const CSRF_COOKIE = "tp_csrf_token"
const ACCESS_TOKEN_KEY = "tp_access_token"
const REFRESH_TOKEN_KEY = "tp_refresh_token"

export function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null
  const match = document.cookie.match(new RegExp(`(?:^|; )${CSRF_COOKIE}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null
  return sessionStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null
  return sessionStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setSession(tokens?: { access_token: string; refresh_token: string }) {
  if (typeof window === "undefined") return
  if (tokens?.access_token) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token)
    const maxAge = 7 * 24 * 60 * 60
    document.cookie = `${SESSION_COOKIE}=1; path=/; SameSite=Lax; max-age=${maxAge}`
  }
  if (tokens?.refresh_token) {
    sessionStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token)
  }
}

export function clearSession() {
  if (typeof window === "undefined") return
  document.cookie = `${SESSION_COOKIE}=; path=/; max-age=0`
  document.cookie = `${CSRF_COOKIE}=; path=/; max-age=0`
  sessionStorage.removeItem(ACCESS_TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function isAuthenticated(): boolean {
  if (typeof document === "undefined") return false
  return document.cookie.includes(`${SESSION_COOKIE}=1`)
}
