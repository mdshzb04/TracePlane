"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Bot, Activity, ClipboardCheck, Heart } from "lucide-react"
import { useTraces } from "@/hooks"
import { agentsService } from "@/services/api"
import { AppLayout } from "@/components/layout/app-layout"
import { AgentMetadataPanel } from "@/components/agents/agent-metadata-panel"
import { Card, StatusBadge, LoadingState, ErrorState, EmptyState, Table, TableHead, TableHeader, TableRow, TableCell } from "@/components/shared"
import { CostDisplay, HealthBadge } from "@/components/observability"
import { formatLatency } from "@/lib/format"
import { environmentSummary, formatRelativeTime, runtimeSummary } from "@/lib/agent-metadata"
import { AgentDetail, TraceSummary } from "@/types"

export default function AgentDetailPage() {
  const params = useParams()
  const agentId = params?.id as string
  const [agent, setAgent] = useState<AgentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("overview")

  const { data: traceData, isLoading: tracesLoading } = useTraces({ agent_id: agentId, page: 1, page_size: 10 })

  useEffect(() => {
    agentsService
      .detail(agentId)
      .then(setAgent)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load agent"))
      .finally(() => setLoading(false))
  }, [agentId])

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "traces", label: "Traces" },
  ]

  const traces = traceData?.traces ?? []

  return (
    <AppLayout>
      <div className="page-container max-w-6xl">
        <Link href="/agents" className="flex items-center gap-1 text-body-sm text-ink-subtle hover:text-ink mb-4">
          <ArrowLeft className="w-4 h-4" />
          Back to Agents
        </Link>

        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {agent && (
          <AgentDetailContent
            agent={agent}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            tabs={tabs}
            traces={traces}
            tracesLoading={tracesLoading}
          />
        )}
      </div>
    </AppLayout>
  )
}

function AgentDetailContent({
  agent,
  activeTab,
  onTabChange,
  tabs,
  traces,
  tracesLoading,
}: {
  agent: AgentDetail
  activeTab: string
  onTabChange: (tab: string) => void
  tabs: { id: string; label: string }[]
  traces: TraceSummary[]
  tracesLoading: boolean
}) {
  const runtimeLine = runtimeSummary(agent)
  const environmentLine = environmentSummary(agent)
  const lastSeen = formatRelativeTime(agent.last_seen_at)
  const hasTraffic = agent.health.total_executions > 0

  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-6 gap-4">
        <div className="flex items-center gap-4 min-w-0">
          <div className="w-12 h-12 rounded-lg bg-surface-2 border border-hairline flex items-center justify-center shrink-0">
            <Bot className="w-6 h-6 text-primary" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-headline font-display font-semibold text-ink tracking-tight">{agent.name}</h1>
            </div>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <StatusBadge status={agent.status} />
              {runtimeLine ? (
                <span className="text-caption text-ink-subtle">{runtimeLine}</span>
              ) : (
                <span className="text-caption text-ink-tertiary">No runtime profile yet</span>
              )}
              <HealthBadge score={agent.health.health_score} />
            </div>
          </div>
        </div>
        <div className="text-left sm:text-right text-caption text-ink-subtle space-y-1 shrink-0">
          {environmentLine && <p>{environmentLine}</p>}
          <p>
            {lastSeen ? (
              <>Last seen {lastSeen}</>
            ) : (
              <span className="text-ink-tertiary">No traces received yet</span>
            )}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <MetricCard
          icon={<Heart className="w-4 h-4 text-primary" />}
          label="Health"
          value={hasTraffic ? `${agent.health.health_score}` : "—"}
        />
        <MetricCard
          icon={<Activity className="w-4 h-4 text-success" />}
          label="Success rate"
          value={hasTraffic ? `${agent.health.success_rate.toFixed(1)}%` : "—"}
        />
        <MetricCard
          icon={<Activity className="w-4 h-4 text-warning" />}
          label="Avg latency"
          value={hasTraffic ? formatLatency(agent.health.avg_latency_ms) : "—"}
        />
        <MetricCard
          icon={<ClipboardCheck className="w-4 h-4 text-primary" />}
          label="Total cost"
          value={hasTraffic ? <CostDisplay value={agent.health.total_cost} /> : "—"}
        />
      </div>

      <div className="flex gap-1 mb-6 border-b border-hairline">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`px-4 py-2.5 text-body-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.id ? "text-ink border-primary" : "text-ink-subtle border-transparent hover:text-ink"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "overview" && <AgentMetadataPanel agent={agent} />}
      {activeTab === "traces" && <AgentTraces traces={traces} loading={tracesLoading} />}
    </>
  )
}

function MetricCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <Card className="panel-lift">
      <div className="flex items-center gap-2 text-ink-subtle mb-1">{icon}<span className="caption-text">{label}</span></div>
      <p className="text-body font-medium text-ink">{value}</p>
    </Card>
  )
}

function AgentTraces({ traces, loading }: { traces: TraceSummary[]; loading: boolean }) {
  if (loading) return <LoadingState />
  if (traces.length === 0) return <EmptyState message="No traces yet — instrument your agent with the SDK" />

  return (
    <Card className="p-0 overflow-hidden">
      <Table>
        <TableHead>
          <TableHeader>Status</TableHeader>
          <TableHeader>Model</TableHeader>
          <TableHeader>Latency</TableHeader>
          <TableHeader>Cost</TableHeader>
          <TableHeader>Started</TableHeader>
          <TableHeader></TableHeader>
        </TableHead>
        <tbody>
          {traces.map((trace) => (
            <TableRow key={trace.trace_id}>
              <TableCell><StatusBadge status={trace.status} /></TableCell>
              <TableCell className="font-mono text-caption">{trace.model || "—"}</TableCell>
              <TableCell>{trace.latency_ms != null ? formatLatency(trace.latency_ms) : "—"}</TableCell>
              <TableCell><CostDisplay value={trace.estimated_cost} /></TableCell>
              <TableCell>{new Date(trace.timestamp).toLocaleString()}</TableCell>
              <TableCell>
                <Link href={`/traces/${trace.trace_id}`} className="text-body-sm text-primary hover:underline">Open</Link>
              </TableCell>
            </TableRow>
          ))}
        </tbody>
      </Table>
    </Card>
  )
}
