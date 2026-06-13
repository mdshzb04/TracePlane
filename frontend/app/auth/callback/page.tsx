"use client"

import { useEffect, useState } from "react"
import { setSession } from "@/lib/auth"
import { TraceplaneLogo } from "@/components/brand/traceplane-logo"

function parseHashTokens(): { access_token?: string; refresh_token?: string } {
  if (typeof window === "undefined") return {}
  const hash = window.location.hash.replace(/^#/, "")
  if (!hash) return {}
  const params = new URLSearchParams(hash)
  return {
    access_token: params.get("access_token") ?? undefined,
    refresh_token: params.get("refresh_token") ?? undefined,
  }
}

export default function AuthCallbackPage() {
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const { access_token, refresh_token } = parseHashTokens()
    if (access_token && refresh_token) {
      setSession({ access_token, refresh_token })
      window.history.replaceState(null, "", "/auth/callback")
      window.location.assign("/agents")
      return
    }
    setError("GitHub sign-in did not return session tokens. Try again from the login page.")
  }, [])

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center px-4">
      <div className="text-center max-w-sm">
        <div className="flex justify-center mb-6">
          <TraceplaneLogo href={null} height={32} priority />
        </div>
        {error ? (
          <>
            <p className="text-body text-danger mb-4">{error}</p>
            <a href="/login" className="btn-primary inline-block">
              Back to sign in
            </a>
          </>
        ) : (
          <p className="text-body text-ink-muted">Completing sign-in…</p>
        )}
      </div>
    </div>
  )
}
