"use client"

import { useEffect, useState } from "react"

const CHUNK_RECOVERY_KEY = "traceplane-chunk-recovery"

function isChunkError(message: string): boolean {
  const lower = message.toLowerCase()
  return (
    lower.includes("chunkloaderror") ||
    lower.includes("loading chunk") ||
    lower.includes("failed to fetch dynamically imported module")
  )
}

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const [reloading, setReloading] = useState(false)
  const chunkError = isChunkError(error.message || "")

  useEffect(() => {
    console.error(error)
  }, [error])

  useEffect(() => {
    if (process.env.NODE_ENV === "production" || !chunkError) return

    const attempts = Number(sessionStorage.getItem(CHUNK_RECOVERY_KEY) || "0")
    if (attempts < 2) {
      sessionStorage.setItem(CHUNK_RECOVERY_KEY, String(attempts + 1))
      setReloading(true)
      const url = new URL(window.location.href)
      url.searchParams.set("_cb", String(Date.now()))
      window.location.replace(url.toString())
    }
  }, [chunkError])

  useEffect(() => {
    if (!chunkError) sessionStorage.removeItem(CHUNK_RECOVERY_KEY)
  }, [chunkError])

  if (reloading) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
        <p className="text-body-sm text-ink-subtle">Reloading — stale dev cache detected…</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
      <div className="card p-8 max-w-md text-center">
        <h2 className="text-headline font-display text-ink mb-2">Something went wrong</h2>
        <p className="text-body-sm text-ink-subtle mb-6">
          {chunkError
            ? "A script failed to load (stale dev cache). Stop the dev server and run npm run dev:clean in frontend/."
            : error.message || "An unexpected error occurred."}
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <button
            type="button"
            onClick={() => {
              sessionStorage.removeItem(CHUNK_RECOVERY_KEY)
              window.location.reload()
            }}
            className="btn-primary"
          >
            Hard reload
          </button>
          {!chunkError && (
            <button type="button" onClick={reset} className="btn-secondary">
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
