import { PROVIDER_BRANDS, UI_PROVIDER_IDS } from "@/lib/provider-brands"
import type { ProviderCatalogItem } from "@/types"

/** Static catalog — renders instantly before the API responds. */
export function staticProviderCatalog(): ProviderCatalogItem[] {
  return UI_PROVIDER_IDS.map((id) => ({
    provider_id: id,
    name: PROVIDER_BRANDS[id].name,
    description: "",
    connected: false,
    status: null,
    key_hint: null,
    last_validated_at: null,
    last_error: null,
  }))
}

/** Merge API connection status into the static list (preserves order). */
export function mergeProviderCatalog(remote: ProviderCatalogItem[]): ProviderCatalogItem[] {
  const byId = new Map(remote.map((p) => [p.provider_id, p]))
  return staticProviderCatalog().map((base) => byId.get(base.provider_id) ?? base)
}
