"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Copy } from "lucide-react"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, PageHeader, LoadingState, ErrorState } from "@/components/shared"
import { CostDisplay } from "@/components/observability"
import { apiKeysService } from "@/services/api"
import { setStoredApiKey } from "@/lib/onboarding-storage"
import { ApiKey } from "@/types"

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newKeyName, setNewKeyName] = useState("Default")
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  async function loadKeys() {
    setLoading(true)
    setError(null)
    try {
      setKeys(await apiKeysService.list())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load API keys")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadKeys()
  }, [])

  async function handleCreate() {
    setCreating(true)
    setCreatedKey(null)
    try {
      const result = await apiKeysService.create(newKeyName.trim() || "Default")
      setCreatedKey(result.key)
      setStoredApiKey(result.key)
      await loadKeys()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create API key")
    } finally {
      setCreating(false)
    }
  }

  async function handleRevoke(id: string) {
    if (!confirm("Revoke this API key? SDK clients using it will stop working.")) return
    await apiKeysService.revoke(id)
    await loadKeys()
  }

  async function handleRotate(id: string) {
    const result = await apiKeysService.rotate(id)
    setCreatedKey(result.key)
    setStoredApiKey(result.key)
    await loadKeys()
  }

  return (
    <AppLayout>
      <div className="page-container max-w-3xl">
        <PageHeader
          title="API Keys"
          subtitle="Workspace keys for SDK telemetry ingestion"
        />

        <p className="text-body-sm text-ink-subtle mb-6">
          <Link href="/sdk" className="text-primary hover:underline">SDK integration</Link>
          {" · "}
          Set <code className="mono-text text-caption">TRACEPLANE_API_KEY</code> in your application environment.
        </p>

        {error && <ErrorState message={error} />}

        <Card className="mb-6">
          <h3 className="text-body-sm font-medium text-ink-muted mb-4">Create API key</h3>
          <p className="text-body-sm text-ink-subtle mb-4">
            Agents are auto-discovered when your SDK sends telemetry. No manual registration required.
          </p>
          <div className="flex flex-wrap gap-2 mb-4">
            <input className="input flex-1 min-w-[180px]" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} placeholder="Key name" />
            <button type="button" onClick={handleCreate} disabled={creating} className="btn-primary">
              {creating ? "Creating…" : "Create key"}
            </button>
          </div>
          {createdKey && (
            <div className="flex items-center gap-2 rounded-md border border-hairline bg-surface-2 px-3 py-2">
              <code className="mono-text text-caption text-ink-subtle flex-1 break-all">{createdKey}</code>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(createdKey)
                  setCopiedId("new")
                  setTimeout(() => setCopiedId(null), 2000)
                }}
                className="btn-secondary text-caption flex items-center gap-1.5 shrink-0 py-1 px-2"
              >
                <Copy className="w-3.5 h-3.5" />
                {copiedId === "new" ? "Copied" : "Copy"}
              </button>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-body-sm font-medium text-ink-muted mb-4">Workspace keys</h3>
          {loading && <LoadingState />}
          {!loading && keys.length === 0 && (
            <p className="text-body-sm text-ink-subtle">No API keys yet. Create one to start sending telemetry.</p>
          )}
          {!loading && keys.length > 0 && (
            <div className="space-y-3">
              {keys.map((key) => (
                <div key={key.id} className="flex items-center justify-between py-3 border-b border-hairline last:border-0 gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-body-sm text-ink">{key.name}</p>
                      <span className="caption-text">{key.is_active ? "active" : "revoked"}</span>
                    </div>
                    <p className="caption-text mt-1">
                      {key.key_prefix}… · {key.request_count.toLocaleString()} requests · <CostDisplay value={key.total_cost} />
                    </p>
                    {key.last_used_at && (
                      <p className="caption-text text-ink-tertiary">Last used {new Date(key.last_used_at).toLocaleString()}</p>
                    )}
                    {!key.last_used_at && key.is_active && (
                      <p className="caption-text text-ink-tertiary">Never used</p>
                    )}
                  </div>
                  {key.is_active && (
                    <div className="flex gap-2 shrink-0">
                      <button type="button" onClick={() => handleRotate(key.id)} className="btn-secondary text-caption">Rotate</button>
                      <button type="button" onClick={() => handleRevoke(key.id)} className="btn-secondary text-caption">Revoke</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </AppLayout>
  )
}
