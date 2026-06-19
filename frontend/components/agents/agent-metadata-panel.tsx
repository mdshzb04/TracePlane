"use client"

import { useState } from "react"
import { Check, Copy, HelpCircle } from "lucide-react"
import { Badge, Card } from "@/components/shared"
import { InfoTooltip } from "@/components/ui/tooltip"
import { CostDisplay } from "@/components/observability"
import { ProviderAvatar } from "@/components/providers/provider-avatar"
import {
  environmentSummary,
  formatAbsoluteTime,
  formatEnvironmentLabel,
  formatFrameworkLabel,
  formatProviderLabel,
  formatRelativeTime,
  formatSourceLabel,
  isAutoDiscoveryDescription,
  isDefaultEnvironment,
  isMeaningfulOwner,
  isMeaningfulText,
  truncateId,
} from "@/lib/agent-metadata"
import { formatLatency } from "@/lib/format"
import { PROVIDER_BRANDS, type UiProviderId } from "@/lib/provider-brands"
import { cn } from "@/lib/utils"
import type { AgentDetail } from "@/types"

type MetadataField = {
  label: string
  hint?: string
  value: React.ReactNode
  mono?: boolean
}

function MetadataRow({ label, hint, value, mono }: MetadataField) {
  return (
    <div className="grid grid-cols-[minmax(0,9rem)_1fr] sm:grid-cols-[minmax(0,10rem)_1fr] gap-x-3 gap-y-1 py-2.5 border-b border-hairline last:border-b-0">
      <dt className="flex items-start gap-1 text-caption text-ink-subtle pt-0.5">
        <span>{label}</span>
        {hint && (
          <InfoTooltip content={hint}>
            <button
              type="button"
              className="text-ink-tertiary hover:text-ink-subtle transition-colors"
              aria-label={`About ${label}`}
            >
              <HelpCircle className="w-3.5 h-3.5" strokeWidth={1.75} />
            </button>
          </InfoTooltip>
        )}
      </dt>
      <dd className={cn("text-body-sm text-ink min-w-0 break-words", mono && "font-mono text-caption")}>
        {value}
      </dd>
    </div>
  )
}

function TimestampValue({ iso, emptyLabel = "Not reported" }: { iso: string | null; emptyLabel?: string }) {
  const relative = formatRelativeTime(iso)
  const absolute = formatAbsoluteTime(iso)
  if (!relative || !absolute) {
    return <span className="text-ink-tertiary">{emptyLabel}</span>
  }
  return (
    <InfoTooltip content={absolute}>
      <time dateTime={iso!} className="cursor-default border-b border-dotted border-ink-tertiary/50">
        {relative}
      </time>
    </InfoTooltip>
  )
}

function MissingValue({ label = "Not reported" }: { label?: string }) {
  return <span className="text-ink-tertiary">{label}</span>
}

function MetadataSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="px-4 py-4 sm:px-5">
      <h4 className="text-caption font-medium uppercase tracking-wide text-ink-subtle mb-1">{title}</h4>
      <dl>{children}</dl>
    </section>
  )
}

function RuntimeBadges({ agent }: { agent: AgentDetail }) {
  const badges: React.ReactNode[] = []

  if (isMeaningfulText(agent.framework)) {
    badges.push(
      <Badge key="framework" variant="primary">
        {formatFrameworkLabel(agent.framework)}
      </Badge>
    )
  }
  if (isMeaningfulText(agent.provider)) {
    const providerId = agent.provider.toLowerCase()
    const brand = PROVIDER_BRANDS[providerId as UiProviderId]
    badges.push(
      <span
        key="provider"
        className="inline-flex items-center gap-1.5 rounded-pill border border-hairline bg-surface-2 px-2 py-0.5 text-caption font-medium text-ink"
      >
        {brand && <ProviderAvatar providerId={providerId} name={brand.name} size={16} />}
        {formatProviderLabel(agent.provider)}
      </span>
    )
  }
  if (isMeaningfulText(agent.environment) && !isDefaultEnvironment(agent)) {
    badges.push(
      <Badge key="environment" variant="default">
        {formatEnvironmentLabel(agent.environment)}
      </Badge>
    )
  }
  if (isMeaningfulText(agent.model)) {
    badges.push(
      <span
        key="model"
        className="inline-flex items-center rounded-pill border border-hairline bg-surface-2 px-2 py-0.5 font-mono text-caption text-ink-muted"
      >
        {agent.model}
      </span>
    )
  }

  if (badges.length === 0) {
    return <p className="text-caption text-ink-tertiary">Runtime profile will appear after the first SDK trace.</p>
  }

  return <div className="flex flex-wrap items-center gap-2">{badges}</div>
}

function CopyableId({ id }: { id: string }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(id)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <span className="inline-flex items-center gap-2 min-w-0">
      <InfoTooltip content={id}>
        <code className="font-mono text-caption text-ink-muted truncate">{truncateId(id)}</code>
      </InfoTooltip>
      <button
        type="button"
        onClick={() => void copy()}
        className="shrink-0 text-ink-subtle hover:text-ink transition-colors"
        aria-label="Copy agent ID"
      >
        {copied ? <Check className="w-3.5 h-3.5 text-success" /> : <Copy className="w-3.5 h-3.5" />}
      </button>
    </span>
  )
}

function buildIdentityFields(agent: AgentDetail): MetadataField[] {
  const fields: MetadataField[] = [
    {
      label: "Agent ID",
      hint: "Stable identifier for this agent in your workspace.",
      value: <CopyableId id={agent.id} />,
    },
  ]

  if (isMeaningfulText(agent.external_name) && agent.external_name !== agent.name) {
    fields.push({
      label: "SDK name",
      hint: "Name reported by the SDK on ingest — used to match traces to this agent.",
      value: agent.external_name,
      mono: true,
    })
  }

  if (isMeaningfulText(agent.description) && !isAutoDiscoveryDescription(agent.description)) {
    fields.push({
      label: "Description",
      value: agent.description,
    })
  }

  if (isMeaningfulOwner(agent.owner)) {
    fields.push({
      label: "Owner",
      hint: "Team or owner string sent with agent metadata from the SDK.",
      value: agent.owner,
    })
  }

  if (isMeaningfulText(agent.source)) {
    fields.push({
      label: "Registration",
      hint: "How this agent record was created in Traceplane.",
      value: <Badge variant="default">{formatSourceLabel(agent.source)}</Badge>,
    })
  }

  return fields
}

function buildRuntimeFields(agent: AgentDetail): MetadataField[] {
  return [
    {
      label: "Model",
      hint: "Primary model observed in recent traces.",
      value: isMeaningfulText(agent.model) ? (
        <span className="font-mono text-caption">{agent.model}</span>
      ) : (
        <MissingValue />
      ),
    },
    {
      label: "Framework",
      hint: "Agent framework inferred from SDK metadata or span events.",
      value: isMeaningfulText(agent.framework) ? (
        formatFrameworkLabel(agent.framework)
      ) : (
        <MissingValue />
      ),
    },
    {
      label: "Provider",
      hint: "LLM provider inferred from model or explicit SDK metadata.",
      value: isMeaningfulText(agent.provider) ? (
        formatProviderLabel(agent.provider)
      ) : (
        <MissingValue />
      ),
    },
    {
      label: "Environment",
      hint: "Deployment environment reported by the SDK (e.g. production, staging).",
      value:
        isMeaningfulText(agent.environment) && !isDefaultEnvironment(agent) ? (
          formatEnvironmentLabel(agent.environment)
        ) : (
          <MissingValue label="Not reported" />
        ),
    },
  ]
}

function buildActivityFields(agent: AgentDetail): MetadataField[] {
  return [
    {
      label: "Last seen",
      hint: "Most recent trace received from this agent.",
      value: <TimestampValue iso={agent.last_seen_at} emptyLabel="No traces yet" />,
    },
    {
      label: "Discovered",
      hint: "When this agent was first registered in your workspace.",
      value: <TimestampValue iso={agent.created_at} />,
    },
    {
      label: "Updated",
      hint: "When agent metadata was last refreshed from telemetry.",
      value: <TimestampValue iso={agent.updated_at} />,
    },
  ]
}

function TelemetrySummary({ agent }: { agent: AgentDetail }) {
  const { health } = agent
  const hasTraffic = health.total_executions > 0

  const items = [
    {
      label: "Executions",
      hint: "Total traced runs for this agent.",
      value: hasTraffic ? health.total_executions.toLocaleString() : "—",
    },
    {
      label: "Success rate",
      hint: "Share of executions that completed successfully.",
      value: hasTraffic ? `${health.success_rate.toFixed(1)}%` : "—",
    },
    {
      label: "Error rate",
      hint: "Share of executions that failed.",
      value: hasTraffic ? `${health.error_rate.toFixed(1)}%` : "—",
    },
    {
      label: "Avg latency",
      hint: "Mean end-to-end latency across executions.",
      value: hasTraffic ? formatLatency(health.avg_latency_ms) : "—",
    },
    {
      label: "Total cost",
      hint: "Estimated spend across all executions.",
      value: hasTraffic ? <CostDisplay value={health.total_cost} /> : "—",
    },
  ]

  return (
    <div className="border-t border-hairline px-4 py-4 sm:px-5">
      <div className="flex items-center gap-1 mb-3">
        <h4 className="text-caption font-medium uppercase tracking-wide text-ink-subtle">Telemetry</h4>
        <InfoTooltip content="Aggregated from real execution data — not placeholders.">
          <button type="button" className="text-ink-tertiary hover:text-ink-subtle" aria-label="About telemetry">
            <HelpCircle className="w-3.5 h-3.5" strokeWidth={1.75} />
          </button>
        </InfoTooltip>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-md border border-hairline bg-surface-2/40 px-3 py-2.5">
            <div className="flex items-center gap-1 text-caption text-ink-subtle mb-1">
              <span>{item.label}</span>
              <InfoTooltip content={item.hint}>
                <button type="button" className="text-ink-tertiary hover:text-ink-subtle" aria-label={item.label}>
                  <HelpCircle className="w-3 h-3" strokeWidth={1.75} />
                </button>
              </InfoTooltip>
            </div>
            <p className="text-body-sm font-medium text-ink">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export function AgentMetadataPanel({ agent }: { agent: AgentDetail }) {
  const identityFields = buildIdentityFields(agent)
  const runtimeFields = buildRuntimeFields(agent)
  const activityFields = buildActivityFields(agent)
  const meaningfulTags = agent.tags.filter((tag) => tag !== "auto-discovered")

  return (
    <Card className="panel-lift overflow-hidden p-0">
      <div className="border-b border-hairline px-4 py-4 sm:px-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="text-body-sm font-medium text-ink">Agent metadata</h3>
            <p className="text-caption text-ink-subtle mt-1 max-w-prose">
              Identity, runtime, and activity derived from SDK telemetry — empty fields are omitted or marked as not
              reported.
            </p>
          </div>
          <RuntimeBadges agent={agent} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 lg:divide-x divide-hairline">
        <MetadataSection title="Identity & registration">
          {identityFields.map((field) => (
            <MetadataRow key={field.label} {...field} />
          ))}
        </MetadataSection>

        <div className="border-t lg:border-t-0 border-hairline">
          <MetadataSection title="Runtime">
            {runtimeFields.map((field) => (
              <MetadataRow key={field.label} {...field} />
            ))}
          </MetadataSection>
          <MetadataSection title="Activity">
            {activityFields.map((field) => (
              <MetadataRow key={field.label} {...field} />
            ))}
          </MetadataSection>
        </div>
      </div>

      <TelemetrySummary agent={agent} />

      <div className="border-t border-hairline px-4 py-4 sm:px-5">
        <div className="flex items-center gap-1 mb-2">
          <h4 className="text-caption font-medium uppercase tracking-wide text-ink-subtle">Tags</h4>
          <InfoTooltip content="Custom labels sent with agent metadata from the SDK.">
            <button type="button" className="text-ink-tertiary hover:text-ink-subtle" aria-label="About tags">
              <HelpCircle className="w-3.5 h-3.5" strokeWidth={1.75} />
            </button>
          </InfoTooltip>
        </div>
        {meaningfulTags.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {meaningfulTags.map((tag) => (
              <Badge key={tag} variant="default">
                {tag}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-body-sm text-ink-tertiary">No custom tags reported by the SDK.</p>
        )}
        {agent.tags.includes("auto-discovered") && (
          <p className="text-caption text-ink-tertiary mt-2">
            This agent was auto-discovered from your first trace.
          </p>
        )}
      </div>
    </Card>
  )
}
