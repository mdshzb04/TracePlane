"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Github } from "lucide-react"
import { authService } from "@/services/api"
import { clearSession } from "@/lib/auth"
import { TraceplaneIcon } from "@/components/brand/traceplane-icon"
import { PRODUCT_NAME } from "@/lib/brand"
import { useTheme } from "@/components/theme-provider"

const OAUTH_ERRORS: Record<string, string> = {
  access_denied: "GitHub sign-in was cancelled.",
  invalid_state: "Sign-in session expired. Please try again.",
  missing_code: "GitHub did not return an authorization code.",
  github_auth_failed: "GitHub sign-in failed. Check OAuth configuration and try again.",
}

function GitHubButton({
  onClick,
  disabled,
  label = "Continue with GitHub",
}: {
  onClick: () => void
  disabled?: boolean
  label?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="btn-primary w-full flex items-center justify-center gap-2.5 py-2.5 disabled:opacity-60"
    >
      <Github className="w-5 h-5" />
      {label}
    </button>
  )
}

export function LoginForm() {
  const searchParams = useSearchParams()
  const { theme } = useTheme()
  const [error, setError] = useState<string | null>(null)
  const [githubStatus, setGithubStatus] = useState<"loading" | "enabled" | "disabled" | "unreachable">("loading")

  useEffect(() => {
    clearSession()
    const oauthError = searchParams.get("error")
    if (oauthError) {
      setError(OAUTH_ERRORS[oauthError] ?? "Authentication failed. Please try again.")
    }
    void authService.githubOAuthStatus().then(setGithubStatus)
  }, [searchParams])

  function handleGitHub() {
    if (githubStatus === "unreachable") {
      setError("Cannot reach the API server. Start the backend on port 8000 and try again.")
      return
    }
    if (githubStatus !== "enabled") {
      setError("GitHub sign-in is not configured on this server. Contact your administrator.")
      return
    }
    setError(null)
    window.location.assign(authService.githubLoginUrl())
  }

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col" data-theme={theme}>
      <header className="h-14 border-b border-hairline px-4 sm:px-6 flex items-center bg-canvas">
        <Link href="/" className="inline-flex items-center gap-2 hover:opacity-90 transition-opacity">
          <TraceplaneIcon size={24} />
          <span className="text-[15px] font-semibold tracking-tight text-ink">{PRODUCT_NAME}</span>
        </Link>
      </header>

      <div className="flex-1 flex items-center justify-center px-4 py-10 sm:py-12">
        <div className="w-full max-w-sm">
          <p className="eyebrow mb-3 text-center">Control Plane</p>
          <h1 className="text-headline font-display font-semibold text-ink text-center tracking-tight">
            Welcome back
          </h1>
          <p className="text-body-sm text-ink-subtle text-center mt-2 mb-8">
            Sign in with your GitHub account to continue.
          </p>

          <div className="panel-lift rounded-lg p-5 sm:p-6">
            {error && (
              <div className="bg-danger/20 text-danger text-body-sm rounded-md p-3 mb-4">{error}</div>
            )}

            <GitHubButton onClick={handleGitHub} disabled={githubStatus !== "enabled"} />
            {githubStatus === "unreachable" && (
              <p className="text-caption text-ink-tertiary text-center mt-4">
                API server offline — run the backend on port 8000 to enable GitHub sign-in.
              </p>
            )}
            {githubStatus === "disabled" && (
              <p className="text-caption text-ink-tertiary text-center mt-4">
                GitHub OAuth is not configured on this server.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
