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
