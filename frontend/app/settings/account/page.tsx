"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft, Github, KeyRound, Mail } from "lucide-react"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, ErrorState, LoadingState, PageHeader } from "@/components/shared"
import { authService } from "@/services/api"
import type { User } from "@/types"

export default function AccountSettingsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [password, setPassword] = useState("")
  const [currentPassword, setCurrentPassword] = useState("")
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    authService
      .me()
      .then(setUser)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load account"))
      .finally(() => setLoading(false))
  }, [])

  async function handleSetPassword(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    if (password.length < 8) {
      setError("Password must be at least 8 characters")
      return
    }
    setSaving(true)
    try {
      const updated = await authService.setPassword({
        password,
        ...(user?.has_password ? { current_password: currentPassword } : {}),
      })
      setUser(updated)
      setPassword("")
      setCurrentPassword("")
      setSuccess(user?.has_password ? "Password updated." : "Password set. You can now sign in with email.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update password")
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppLayout>
      <div className="page-container max-w-2xl">
        <Link
          href="/settings"
          className="inline-flex items-center gap-1.5 text-body-sm text-ink-muted hover:text-ink mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Settings
        </Link>

        <PageHeader title="Account" subtitle="Authentication methods and profile" />

        {loading && <LoadingState />}
        {error && !loading && <ErrorState message={error} />}
        {!loading && user && (
          <div className="space-y-4">
            <Card className="panel-lift p-5 space-y-4">
              <div className="flex items-start gap-4">
                {user.avatar_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={user.avatar_url}
                    alt=""
                    className="w-12 h-12 rounded-full border border-hairline"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-surface-3 border border-hairline flex items-center justify-center">
                    <Mail className="w-5 h-5 text-ink-muted" />
                  </div>
                )}
                <div>
                  <p className="text-body font-medium text-ink">{user.full_name || user.email}</p>
                  <p className="text-body-sm text-ink-subtle">{user.email}</p>
                  <p className="caption-text mt-1 capitalize">Primary provider: {user.provider}</p>
                </div>
              </div>

              <div className="border-t border-hairline pt-4 space-y-3">
                <p className="text-body-sm font-medium text-ink">Connected sign-in methods</p>
                <div className="flex flex-wrap gap-2">
                  {user.has_github && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-2 border border-hairline text-body-sm text-ink-muted">
                      <Github className="w-3.5 h-3.5" />
                      GitHub
                    </span>
                  )}
                  {user.has_password && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-surface-2 border border-hairline text-body-sm text-ink-muted">
                      <Mail className="w-3.5 h-3.5" />
                      Email & password
                    </span>
                  )}
                  {!user.has_github && !user.has_password && (
                    <span className="text-body-sm text-ink-tertiary">No methods connected</span>
                  )}
                </div>
                {!user.has_github && (
                  <a href={authService.githubLoginUrl()} className="btn-secondary text-body-sm inline-flex items-center gap-2">
                    <Github className="w-4 h-4" />
                    Link GitHub account
                  </a>
                )}
              </div>
            </Card>

            <Card className="panel-lift p-5">
              <div className="flex items-center gap-2 mb-4">
                <KeyRound className="w-4 h-4 text-primary" />
                <h2 className="text-body font-medium text-ink">
                  {user.has_password ? "Change password" : "Set a password"}
                </h2>
              </div>
              <p className="text-body-sm text-ink-subtle mb-4">
                {user.has_password
                  ? "Update your email sign-in password."
                  : "Add email/password sign-in alongside GitHub."}
              </p>
              {success && (
                <div className="bg-success/20 text-success text-body-sm rounded-md p-3 mb-4">{success}</div>
              )}
              <form onSubmit={handleSetPassword} className="space-y-4">
                {user.has_password && (
                  <div>
                    <label htmlFor="currentPassword" className="block text-body-sm text-ink-muted mb-1.5">
                      Current password
                    </label>
                    <input
                      id="currentPassword"
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="input w-full"
                      autoComplete="current-password"
                      required
                    />
                  </div>
                )}
                <div>
                  <label htmlFor="newPassword" className="block text-body-sm text-ink-muted mb-1.5">
                    {user.has_password ? "New password" : "Password"}
                  </label>
                  <input
                    id="newPassword"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input w-full"
                    placeholder="At least 8 characters"
                    autoComplete="new-password"
                    minLength={8}
                    required
                  />
                </div>
                <button type="submit" disabled={saving} className="btn-primary">
                  {saving ? "Saving…" : user.has_password ? "Update password" : "Set password"}
                </button>
              </form>
            </Card>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
