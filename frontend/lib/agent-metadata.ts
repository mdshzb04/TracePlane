import { PROVIDER_BRANDS, type UiProviderId } from "@/lib/provider-brands"
import type { AgentDetail } from "@/types"

const AUTO_DISCOVERED_DESC_RE = /^Auto-discovered via SDK \(.+\)$/
const PLACEHOLDER_OWNERS = new Set(["sdk", "unknown", "default"])

export function isAutoDiscoveryDescription(description: string | null | undefined): boolean {
  return Boolean(description && AUTO_DISCOVERED_DESC_RE.test(description))
}

export function isMeaningfulText(value: string | null | undefined): value is string {
  if (!value) return false
  const trimmed = value.trim()
  return trimmed.length > 0 && trimmed.toLowerCase() !== "unknown"
}

export function isMeaningfulOwner(owner: string | null | undefined): owner is string {
  if (!isMeaningfulText(owner)) return false
  return !PLACEHOLDER_OWNERS.has(owner.trim().toLowerCase())
}

export function isDefaultEnvironment(agent: Pick<AgentDetail, "environment" | "tags">): boolean {
  if (!agent.environment) return true
  if (agent.environment.toLowerCase() !== "production") return false
  return agent.tags.includes("auto-discovered")
}

export function formatFrameworkLabel(framework: string): string {
  const key = framework.trim().toLowerCase()
  const labels: Record<string, string> = {
    langgraph: "LangGraph",
    crewai: "CrewAI",
    "openai-agents": "OpenAI Agents",
    autogen: "AutoGen",
    pydanticai: "Pydantic AI",
    agno: "Agno",
    opentelemetry: "OpenTelemetry",
    custom: "Custom",
  }
  return labels[key] ?? framework
}

export function formatProviderLabel(provider: string): string {
  const key = provider.trim().toLowerCase() as UiProviderId
  return PROVIDER_BRANDS[key]?.name ?? provider
}

export function formatSourceLabel(source: string): string {
  const key = source.trim().toLowerCase()
  if (key === "sdk") return "SDK telemetry"
  if (key === "api") return "API"
  if (key === "manual") return "Manual"
  return source
}

export function formatEnvironmentLabel(environment: string): string {
  const key = environment.trim().toLowerCase()
  if (key === "production") return "Production"
  if (key === "staging") return "Staging"
  if (key === "development") return "Development"
  return environment
}

export function formatRelativeTime(iso: string | null | undefined): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null

  const diffSec = Math.round((Date.now() - date.getTime()) / 1000)
  if (diffSec < 45) return "just now"
  const diffMin = Math.round(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.round(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.round(diffHr / 24)
  if (diffDay < 30) return `${diffDay}d ago`
  return date.toLocaleDateString()
}

export function formatAbsoluteTime(iso: string | null | undefined): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date)
}

export function truncateId(id: string, head = 8, tail = 4): string {
  if (id.length <= head + tail + 1) return id
  return `${id.slice(0, head)}…${id.slice(-tail)}`
}

export function runtimeSummary(agent: AgentDetail): string | null {
  const parts: string[] = []
  if (isMeaningfulText(agent.framework)) parts.push(formatFrameworkLabel(agent.framework))
  if (isMeaningfulText(agent.model)) parts.push(agent.model)
  if (isMeaningfulText(agent.provider)) parts.push(formatProviderLabel(agent.provider))
  return parts.length > 0 ? parts.join(" · ") : null
}

export function environmentSummary(agent: AgentDetail): string | null {
  if (!isMeaningfulText(agent.environment) || isDefaultEnvironment(agent)) return null
  return formatEnvironmentLabel(agent.environment)
}
