"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Github, LogIn, UserPlus } from "lucide-react"
import { authService } from "@/services/api"
import { clearSession } from "@/lib/auth"
import { getEmailValidationError } from "@/lib/validation"
import { TraceplaneIcon } from "@/components/brand/traceplane-icon"
import { PRODUCT_NAME } from "@/lib/brand"
import { useTheme } from "@/components/theme-provider"

type AuthMode = "signin" | "signup"

const OAUTH_ERRORS: Record<string, string> = {
  access_denied: "GitHub sign-in was cancelled.",
  invalid_state: "Sign-in session expired. Please try again.",
  missing_code: "GitHub did not return an authorization code.",
  github_auth_failed: "GitHub sign-in failed. Check OAuth configuration and try again.",
}

function AuthDivider({ label }: { label: string }) {
  return (
    <div className="relative py-1">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-hairline" />
      </div>
      <div className="relative flex justify-center">
        <span className="bg-surface-1 px-3 text-caption text-ink-tertiary">{label}</span>
      </div>
    </div>
  )
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
  const [mode, setMode] = useState<AuthMode>("signin")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showEmail, setShowEmail] = useState(false)
  const [githubStatus, setGithubStatus] = useState<"loading" | "enabled" | "disabled" | "unreachable">("loading")

  useEffect(() => {
    clearSession()
    const oauthError = searchParams.get("error")
    if (oauthError) {
      setError(OAUTH_ERRORS[oauthError] ?? "Authentication failed. Please try again.")
    }
    void authService.githubOAuthStatus().then(setGithubStatus)
  }, [searchParams])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    const emailError = getEmailValidationError(email)
    if (emailError) {
      setError(emailError)
      return
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters")
      return
    }

    setLoading(true)
    try {
      const normalizedEmail = email.trim().toLowerCase()
      if (mode === "signup") {
        await authService.register({
          email: normalizedEmail,
          password,
          full_name: fullName.trim() || undefined,
        })
        await authService.login({ email: normalizedEmail, password })
      } else {
        await authService.login({ email: normalizedEmail, password })
      }
      window.location.assign("/agents")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed")
    } finally {
      setLoading(false)
    }
  }

  function handleGitHub() {
    if (githubStatus === "unreachable") {
      setError("Cannot reach the API server. Start the backend on port 8000 and try again.")
      return
    }
    if (githubStatus !== "enabled") {
      setError("GitHub sign-in is not configured on this server. Use email or contact your administrator.")
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
            {showEmail ? (mode === "signin" ? "Sign in with email" : "Create account") : "Welcome back"}
          </h1>
          <p className="text-body-sm text-ink-subtle text-center mt-2 mb-8">
            {showEmail
              ? mode === "signin"
                ? "Use your email and password, or continue with GitHub"
                : "Register with email, or continue with GitHub"
              : "Sign in with GitHub or continue with email"}
          </p>

          <div className="panel-lift rounded-lg p-5 sm:p-6">
            {error && (
              <div className="bg-danger/20 text-danger text-body-sm rounded-md p-3 mb-4">{error}</div>
            )}

            {!showEmail ? (
              <div className="space-y-4">
                <GitHubButton onClick={handleGitHub} disabled={githubStatus !== "enabled"} />
                {githubStatus === "unreachable" && (
                  <p className="text-caption text-ink-tertiary text-center">
                    API server offline — run the backend on port 8000 to enable GitHub sign-in.
                  </p>
                )}
                {githubStatus === "disabled" && (
                  <p className="text-caption text-ink-tertiary text-center">
                    GitHub OAuth is not configured on this server.
                  </p>
                )}

                <AuthDivider label="or continue with email" />

                <button
                  type="button"
                  onClick={() => { setShowEmail(true); setMode("signin"); setError(null) }}
                  className="btn-secondary w-full"
                >
                  Sign in with Email
                </button>
                <button
                  type="button"
                  onClick={() => { setShowEmail(true); setMode("signup"); setError(null) }}
                  className="w-full text-body-sm text-ink-muted hover:text-ink transition-colors py-1"
                >
                  Create account with Email
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <button
                  type="button"
                  onClick={() => { setShowEmail(false); setError(null) }}
                  className="text-body-sm text-ink-muted hover:text-ink transition-colors"
                >
                  ← Back to sign-in options
                </button>

                <div className="flex gap-2 p-1 bg-surface-2 rounded-md">
                  <button
                    type="button"
                    onClick={() => { setMode("signin"); setError(null) }}
                    className={`flex-1 py-2 text-body-sm rounded-sm transition-colors ${
                      mode === "signin" ? "bg-primary text-on-primary" : "text-ink-muted hover:text-ink"
                    }`}
                  >
                    Sign in
                  </button>
                  <button
                    type="button"
                    onClick={() => { setMode("signup"); setError(null) }}
                    className={`flex-1 py-2 text-body-sm rounded-sm transition-colors ${
                      mode === "signup" ? "bg-primary text-on-primary" : "text-ink-muted hover:text-ink"
                    }`}
                  >
                    Create account
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  {mode === "signup" && (
                    <div>
                      <label htmlFor="fullName" className="block text-body-sm text-ink-muted mb-1.5">
                        Full name <span className="text-ink-tertiary">(optional)</span>
                      </label>
                      <input
                        id="fullName"
                        type="text"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="input w-full"
                        placeholder="Your name"
                        autoComplete="name"
                      />
                    </div>
                  )}
                  <div>
                    <label htmlFor="email" className="block text-body-sm text-ink-muted mb-1.5">Email</label>
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="input w-full"
                      placeholder="you@gmail.com"
                      autoComplete="email"
                      required
                    />
                    <p className="text-caption text-ink-tertiary mt-1.5">
                      Allowed: @gmail.com or @company.com
                    </p>
                  </div>
                  <div>
                    <label htmlFor="password" className="block text-body-sm text-ink-muted mb-1.5">Password</label>
                    <input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="input w-full"
                      placeholder="At least 8 characters"
                      autoComplete={mode === "signup" ? "new-password" : "current-password"}
                      minLength={8}
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {mode === "signin" ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
                    {loading
                      ? mode === "signin" ? "Signing in..." : "Creating account..."
                      : mode === "signin" ? "Sign in" : "Create account"}
                  </button>
                </form>

                <AuthDivider label="or" />
                <GitHubButton onClick={handleGitHub} disabled={githubStatus !== "enabled"} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
