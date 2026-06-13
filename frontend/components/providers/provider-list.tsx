"use client"

import { memo, useMemo, useState } from "react"
import { ChevronDown, Loader2, Unplug, Zap } from "lucide-react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { providersService } from "@/services/api"
import { mergeProviderCatalog, staticProviderCatalog } from "@/lib/provider-catalog"
import { PROVIDER_BRANDS, sortProviders, type UiProviderId } from "@/lib/provider-brands"
import { friendlyErrorMessage } from "@/lib/friendly-error"
import { cn } from "@/lib/utils"
import type { ProviderCatalogItem } from "@/types"
import { ProviderAvatar } from "./provider-avatar"

const FALLBACK_CATALOG = staticProviderCatalog()

export function ProviderList() {
  const queryClient = useQueryClient()
  const [expanded, setExpanded] = useState<string | null>(null)
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<Record<string, string>>({})

  const { data, isFetching, isError } = useQuery({
    queryKey: ["providers"],
    queryFn: async () => mergeProviderCatalog(await providersService.list()),
    placeholderData: FALLBACK_CATALOG,
    retry: 0,
    staleTime: 30_000,
  })

  const providers = useMemo(() => sortProviders(data ?? FALLBACK_CATALOG), [data])

  async function handleConnect(providerId: string) {
    const key = apiKeys[providerId]?.trim()
    if (!key) return
    setBusy(providerId)
    setFeedback((f) => ({ ...f, [providerId]: "" }))
    try {
      const result = await providersService.connect(providerId, key)
      setFeedback((f) => ({
        ...f,
        [providerId]:
          result.status === "connected" ? "Connected" : result.last_error || "Connection failed",
      }))
      setApiKeys((k) => ({ ...k, [providerId]: "" }))
      await queryClient.invalidateQueries({ queryKey: ["providers"] })
    } catch (err) {
      setFeedback((f) => ({
        ...f,
        [providerId]: friendlyErrorMessage(err instanceof Error ? err.message : String(err)),
      }))
    } finally {
      setBusy(null)
    }
  }

  async function handleDisconnect(providerId: string) {
    setBusy(providerId)
    try {
      await providersService.disconnect(providerId)
      setFeedback((f) => ({ ...f, [providerId]: "Disconnected" }))
      await queryClient.invalidateQueries({ queryKey: ["providers"] })
    } finally {
      setBusy(null)
    }
  }

  async function handleTest(providerId: string) {
    setBusy(providerId)
    setFeedback((f) => ({ ...f, [providerId]: "" }))
    try {
      const result = await providersService.test(providerId)
      setFeedback((f) => ({
        ...f,
        [providerId]:
          result.status === "connected"
            ? `Verified${result.latency_ms ? ` · ${result.latency_ms}ms` : ""}`
            : result.message,
      }))
      await queryClient.invalidateQueries({ queryKey: ["providers"] })
    } catch (err) {
      setFeedback((f) => ({
        ...f,
        [providerId]: friendlyErrorMessage(err instanceof Error ? err.message : String(err)),
      }))
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="space-y-1.5">
      {isError && (
        <p className="text-[11px] text-ink-tertiary px-0.5 mb-2">Status unavailable — providers remain configurable.</p>
      )}

      {providers.map((p) => (
        <ProviderRow
          key={p.provider_id}
          provider={p}
          statusUnavailable={isError && !p.connected}
          open={expanded === p.provider_id}
          apiKey={apiKeys[p.provider_id] || ""}
          feedback={feedback[p.provider_id]}
          busy={busy === p.provider_id}
          onToggle={() => setExpanded((id) => (id === p.provider_id ? null : p.provider_id))}
          onKeyChange={(v) => setApiKeys((k) => ({ ...k, [p.provider_id]: v }))}
          onConnect={() => void handleConnect(p.provider_id)}
          onDisconnect={() => void handleDisconnect(p.provider_id)}
          onTest={() => void handleTest(p.provider_id)}
        />
      ))}

      {isFetching && !isError && (
        <p className="text-[11px] text-ink-tertiary px-0.5 pt-1">Refreshing status…</p>
      )}
    </div>
  )
}

const ProviderRow = memo(function ProviderRow({
  provider,
  statusUnavailable,
  open,
  apiKey,
  feedback,
  busy,
  onToggle,
  onKeyChange,
  onConnect,
  onDisconnect,
  onTest,
}: {
  provider: ProviderCatalogItem
  statusUnavailable: boolean
  open: boolean
  apiKey: string
  feedback?: string
  busy: boolean
  onToggle: () => void
  onKeyChange: (v: string) => void
  onConnect: () => void
  onDisconnect: () => void
  onTest: () => void
}) {
  const brand = PROVIDER_BRANDS[provider.provider_id as UiProviderId]
  const connected = provider.connected && provider.status === "connected"
  const name = brand?.name ?? provider.name

  return (
    <div
      className={cn(
        "rounded-lg border bg-surface-1 transition-all duration-200 ease-out",
        open
          ? "border-hairline-strong shadow-[0_0_0_1px_rgba(94,106,210,0.18)]"
          : "border-hairline hover:border-hairline-strong hover:shadow-[0_0_0_1px_rgba(94,106,210,0.12)]"
      )}
    >
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-3.5 px-3.5 py-3 text-left cursor-pointer group"
      >
        <ProviderAvatar providerId={provider.provider_id} name={name} />
        <span className="flex-1 min-w-0 text-body-sm font-medium text-ink truncate">{name}</span>
        <StatusPill connected={connected} statusUnavailable={statusUnavailable} />
        <ChevronDown
          className={cn(
            "w-4 h-4 text-ink-tertiary shrink-0 transition-transform duration-200",
            "group-hover:text-ink-subtle",
            open && "rotate-180"
          )}
        />
      </button>

      {open && (
        <ProviderRowDetails
          provider={provider}
          connected={connected}
          apiKey={apiKey}
          feedback={feedback}
          busy={busy}
          onKeyChange={onKeyChange}
          onConnect={onConnect}
          onDisconnect={onDisconnect}
          onTest={onTest}
        />
      )}
    </div>
  )
})

function StatusPill({
  connected,
  statusUnavailable,
}: {
  connected: boolean
  statusUnavailable: boolean
}) {
  if (connected) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-success/20 bg-success/10 px-2 py-0.5 text-[10px] font-medium tracking-wide text-success uppercase">
        <span className="h-1.5 w-1.5 rounded-full bg-success" />
        Connected
      </span>
    )
  }
  if (statusUnavailable) {
    return (
      <span className="text-[10px] font-medium tracking-wide text-ink-tertiary uppercase">
        Unavailable
      </span>
    )
  }
  return (
    <span className="inline-flex items-center rounded-full border border-hairline bg-surface-2/80 px-2 py-0.5 text-[10px] font-medium tracking-wide text-ink-tertiary uppercase">
      Not connected
    </span>
  )
}

const ProviderRowDetails = memo(function ProviderRowDetails({
  provider,
  connected,
  apiKey,
  feedback,
  busy,
  onKeyChange,
  onConnect,
  onDisconnect,
  onTest,
}: {
  provider: ProviderCatalogItem
  connected: boolean
  apiKey: string
  feedback?: string
  busy: boolean
  onKeyChange: (v: string) => void
  onConnect: () => void
  onDisconnect: () => void
  onTest: () => void
}) {
  return (
    <div className="px-3.5 pb-3 pt-0 border-t border-hairline/70">
      <div className="pt-3 space-y-2.5">
        {connected && provider.key_hint && (
          <p className="text-caption text-ink-tertiary font-mono">Key {provider.key_hint}</p>
        )}
        {!connected && (
          <input
            type="password"
            className="input w-full text-body-sm h-9"
            placeholder="Paste API key"
            value={apiKey}
            onChange={(e) => onKeyChange(e.target.value)}
            autoComplete="off"
          />
        )}
        <div className="flex flex-wrap items-center gap-2">
          {connected ? (
            <>
              <button
                type="button"
                className="btn-secondary text-caption h-8 inline-flex items-center gap-1.5 px-3"
                disabled={busy}
                onClick={onTest}
              >
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                Test connection
              </button>
              <button
                type="button"
                className="btn-secondary text-caption h-8 inline-flex items-center gap-1.5 px-3"
                disabled={busy}
                onClick={onDisconnect}
              >
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Unplug className="w-3.5 h-3.5" />}
                Disconnect
              </button>
            </>
          ) : (
            <button
              type="button"
              className="btn-primary text-body-sm h-8 px-4"
              disabled={busy || !apiKey.trim()}
              onClick={onConnect}
            >
              {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : "Connect"}
            </button>
          )}
        </div>
        {feedback && <p className="caption-text text-ink-subtle">{feedback}</p>}
        {provider.last_error && !feedback && (
          <p className="caption-text text-warning">{provider.last_error}</p>
        )}
      </div>
    </div>
  )
})
