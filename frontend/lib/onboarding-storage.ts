const API_KEY_KEY = "traceplane_api_key"
const SDK_INSTALLED_KEY = "traceplane_sdk_installed"

export function getStoredApiKey(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem(API_KEY_KEY)
}

export function setStoredApiKey(key: string): void {
  localStorage.setItem(API_KEY_KEY, key)
}

export function clearStoredApiKey(): void {
  localStorage.removeItem(API_KEY_KEY)
}

export function markSdkInstalled(): void {
  localStorage.setItem(SDK_INSTALLED_KEY, "1")
}

export function isSdkInstalledMarked(): boolean {
  if (typeof window === "undefined") return false
  return localStorage.getItem(SDK_INSTALLED_KEY) === "1"
}

const SDK_SESSION_STEP = "tp_sdk_session_step"
const SDK_SESSION_TRACE = "tp_sdk_session_trace"

export function isSdkStepDoneThisSession(): boolean {
  if (typeof window === "undefined") return false
  return sessionStorage.getItem(SDK_SESSION_STEP) === "1"
}

export function markSdkStepDoneThisSession(): void {
  sessionStorage.setItem(SDK_SESSION_STEP, "1")
}

export function isTraceStepDoneThisSession(): boolean {
  if (typeof window === "undefined") return false
  return sessionStorage.getItem(SDK_SESSION_TRACE) === "1"
}

export function markTraceStepDoneThisSession(): void {
  sessionStorage.setItem(SDK_SESSION_TRACE, "1")
}
