/** Display metadata for supported UI providers. */
export const UI_PROVIDER_IDS = [
  "openai",
  "anthropic",
  "google",
  "deepseek",
  "xai",
  "openrouter",
  "cohere",
  "perplexity",
  "mistral",
  "minimax",
  "cerebras",
  "deepinfra",
  "fireworks",
] as const

export type UiProviderId = (typeof UI_PROVIDER_IDS)[number]

/** Exact logo file mapping — never fall back across providers. */
export const PROVIDER_LOGOS: Record<UiProviderId, string> = {
  openai: "/providers/openai.png?v=5",
  anthropic: "/providers/anthropic.png?v=5",
  google: "/providers/gemini.png?v=5",
  deepseek: "/providers/deepseek.png?v=5",
  xai: "/providers/grok.png?v=5",
  openrouter: "/providers/openrouter.png?v=5",
  cohere: "/providers/cohere.png?v=5",
  perplexity: "/providers/perplexity.png?v=5",
  mistral: "/providers/mistral.png?v=5",
  minimax: "/providers/minimax.png?v=5",
  cerebras: "/providers/cerebras.png?v=5",
  deepinfra: "/providers/deepinfra.png?v=5",
  fireworks: "/providers/fireworks.png?v=5",
}

export const PROVIDER_BRANDS: Record<UiProviderId, { name: string; logo: string }> = {
  openai: { name: "OpenAI", logo: PROVIDER_LOGOS.openai },
  anthropic: { name: "Anthropic", logo: PROVIDER_LOGOS.anthropic },
  google: { name: "Gemini", logo: PROVIDER_LOGOS.google },
  deepseek: { name: "DeepSeek", logo: PROVIDER_LOGOS.deepseek },
  xai: { name: "Grok", logo: PROVIDER_LOGOS.xai },
  openrouter: { name: "OpenRouter", logo: PROVIDER_LOGOS.openrouter },
  cohere: { name: "Cohere", logo: PROVIDER_LOGOS.cohere },
  perplexity: { name: "Perplexity", logo: PROVIDER_LOGOS.perplexity },
  mistral: { name: "Mistral", logo: PROVIDER_LOGOS.mistral },
  minimax: { name: "MiniMax", logo: PROVIDER_LOGOS.minimax },
  cerebras: { name: "Cerebras", logo: PROVIDER_LOGOS.cerebras },
  deepinfra: { name: "DeepInfra", logo: PROVIDER_LOGOS.deepinfra },
  fireworks: { name: "Fireworks", logo: PROVIDER_LOGOS.fireworks },
}

export function sdkProviderFromId(id: UiProviderId): string {
  const map: Record<UiProviderId, string> = {
    openai: "OpenAI",
    anthropic: "Claude",
    google: "Gemini",
    deepseek: "DeepSeek",
    xai: "Grok",
    openrouter: "OpenRouter",
    cohere: "Cohere",
    perplexity: "Perplexity",
    mistral: "Mistral",
    minimax: "MiniMax",
    cerebras: "Cerebras",
    deepinfra: "DeepInfra",
    fireworks: "Fireworks",
  }
  return map[id]
}

export function idFromSdkProvider(name: string): UiProviderId | null {
  for (const id of UI_PROVIDER_IDS) {
    if (sdkProviderFromId(id) === name || PROVIDER_BRANDS[id].name === name) return id
  }
  return null
}

/** Connected first, then catalog order. */
export function sortProviders(items: { provider_id: string; connected: boolean; status: string | null }[]) {
  const order = new Map(UI_PROVIDER_IDS.map((id, index) => [id, index]))
  return [...items].sort((a, b) => {
    const aConn = a.connected && a.status === "connected"
    const bConn = b.connected && b.status === "connected"
    if (aConn !== bConn) return aConn ? -1 : 1
    return (order.get(a.provider_id as UiProviderId) ?? 99) - (order.get(b.provider_id as UiProviderId) ?? 99)
  })
}
