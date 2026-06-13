"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft, Github, Mail } from "lucide-react"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, ErrorState, LoadingState, PageHeader } from "@/components/shared"
import { authService } from "@/services/api"
import type { User } from "@/types"

export default function AccountSettingsPage() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    authService
      .me()
      .then(setUser)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load account"))
      .finally(() => setLoading(false))
  }, [])

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

        <PageHeader title="Account" subtitle="GitHub sign-in and profile" />

        {loading && <LoadingState />}
        {error && !loading && <ErrorState message={error} />}
        {!loading && user && (
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
                {!user.has_github && (
                  <span className="text-body-sm text-ink-tertiary">No GitHub account linked</span>
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
        )}
      </div>
    </AppLayout>
  )
}
