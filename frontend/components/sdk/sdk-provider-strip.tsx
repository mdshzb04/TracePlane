"use client"

import { useState } from "react"
import { UI_PROVIDER_IDS, PROVIDER_BRANDS, sdkProviderFromId } from "@/lib/provider-brands"
import { ProviderAvatar } from "@/components/providers/provider-avatar"
import { cn } from "@/lib/utils"
import type { SdkProvider } from "@/lib/sdk-provider-snippets"

type ProviderRow = {
  provider_id: string
  status?: string | null
}

type SdkProviderStripProps = {
  providers: ProviderRow[]
  selectedId?: string | null
  onSelect?: (providerId: string, sdkName: SdkProvider) => void
}

export function SdkProviderStrip({ providers, selectedId, onSelect }: SdkProviderStripProps) {
  const [activeId, setActiveId] = useState<string | null>(null)

  const connectedIds = new Set(
    providers.filter((p) => p.status === "connected").map((p) => p.provider_id)
  )
  const testedIds = new Set(
    providers.filter((p) => p.status === "tested").map((p) => p.provider_id)
  )

  function handleClick(id: (typeof UI_PROVIDER_IDS)[number]) {
    setActiveId(id)
    const sdkName = sdkProviderFromId(id) as SdkProvider
    onSelect?.(id, sdkName)
  }

  const statusId = activeId ?? selectedId
  const statusName = statusId ? PROVIDER_BRANDS[statusId as keyof typeof PROVIDER_BRANDS]?.name : null
  const isConnected = statusId ? connectedIds.has(statusId) : false
  const needsReconnect = statusId ? testedIds.has(statusId) : false

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {UI_PROVIDER_IDS.map((id) => {
          const connected = connectedIds.has(id)
          const isActive = activeId === id || selectedId === id
          return (
            <button
              key={id}
              type="button"
              onClick={() => handleClick(id)}
              title={PROVIDER_BRANDS[id].name}
              className={cn(
                "rounded-full transition-all duration-150 hover:ring-2 hover:ring-primary/30 hover:scale-105",
                isActive && "ring-2 ring-primary/50"
              )}
            >
              <ProviderAvatar providerId={id} name={PROVIDER_BRANDS[id].name} size={30} />
              <span className="sr-only">
                {PROVIDER_BRANDS[id].name} — {connected ? "Connected" : "Not Connected"}
              </span>
            </button>
          )
        })}
      </div>
      {statusName && (
        <p className="text-caption text-ink-subtle transition-opacity duration-150">
          <span className="text-ink-muted">{statusName}</span>
          <span className="mx-1.5 text-ink-tertiary">·</span>
          <span className={isConnected ? "text-success" : needsReconnect ? "text-ink-muted" : "text-ink-tertiary"}>
            {isConnected ? "Connected" : needsReconnect ? "Reconnect required" : "Not Connected"}
          </span>
        </p>
      )}
    </div>
  )
}
