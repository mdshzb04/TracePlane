/** Canonical production API base for external SDK clients. */
export const TRACEPLANE_PRODUCTION_BASE_URL = "https://traceplane.shazeb.site/api/v1"

const LOCAL_DEV_BASE_URL = "http://127.0.0.1:8000/api/v1"

/** Base URL shown in SDK snippets and copy-to-clipboard env blocks. */
export function getTraceplaneSdkBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_TRACEPLANE_BASE_URL?.trim()
  if (fromEnv) return fromEnv.replace(/\/$/, "")

  if (typeof window !== "undefined") {
    const { hostname, origin } = window.location
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return LOCAL_DEV_BASE_URL
    }
    return `${origin}/api/v1`
  }

  return TRACEPLANE_PRODUCTION_BASE_URL
}

export function buildTraceplaneEnvBlock(apiKey = "aoh_your_api_key", providerKeyEnv?: string): string {
  const lines = [
    `TRACEPLANE_API_KEY=${apiKey}`,
    `TRACEPLANE_BASE_URL=${getTraceplaneSdkBaseUrl()}`,
  ]
  if (providerKeyEnv) lines.push(`${providerKeyEnv}=...`)
  return lines.join("\n")
}
