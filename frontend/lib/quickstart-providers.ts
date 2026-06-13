import type { SdkProvider } from "@/lib/sdk-provider-snippets"
import { PROVIDER_META } from "@/lib/sdk-provider-snippets"
import type { UiProviderId } from "@/lib/provider-brands"

export type QuickstartProviderId = UiProviderId

export const PROVIDER_MODELS: Record<QuickstartProviderId, string[]> = {
  openai: ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
  anthropic: ["claude-3-5-haiku-latest", "claude-sonnet-4-20250514"],
  google: ["gemini-2.0-flash", "gemini-2.5-pro"],
  deepseek: ["deepseek-chat", "deepseek-reasoner"],
  xai: ["grok-2-1212", "grok-2"],
  openrouter: ["google/gemini-2.0-flash-001", "anthropic/claude-3.5-sonnet", "openai/gpt-4o-mini"],
  cohere: ["command-r-plus-08-2024", "command-r7b-12-2024"],
  perplexity: ["sonar", "sonar-pro"],
  mistral: ["mistral-small-latest", "mistral-large-latest"],
  minimax: ["abab6.5-chat", "abab6.5s-chat"],
  cerebras: ["llama-3.3-70b", "llama3.1-8b"],
  deepinfra: ["meta-llama/Meta-Llama-3.1-8B-Instruct", "Qwen/Qwen2.5-72B-Instruct"],
  fireworks: [
    "accounts/fireworks/models/llama-v3p1-8b-instruct",
    "accounts/fireworks/models/llama-v3p1-70b-instruct",
  ],
}

export const DEFAULT_PROMPT = "Reply with exactly one word: Traceplane"
export const DEFAULT_AGENT_NAME = "sdk-agent"

export function providerIdFor(name: SdkProvider): QuickstartProviderId {
  return PROVIDER_META[name].providerId as QuickstartProviderId
}

export function defaultModelFor(providerId: QuickstartProviderId): string {
  const models = PROVIDER_MODELS[providerId]
  if (models?.length) return models[0]
  for (const meta of Object.values(PROVIDER_META)) {
    if (meta.providerId === providerId) return meta.model
  }
  return PROVIDER_MODELS.openai[0]
}
