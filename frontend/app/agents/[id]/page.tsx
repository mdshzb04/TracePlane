"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Bot, Activity, ClipboardCheck, Heart } from "lucide-react"
import { useTraces } from "@/hooks"
import { agentsService } from "@/services/api"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, StatusBadge, LoadingState, ErrorState, EmptyState, Table, TableHead, TableHeader, TableRow, TableCell } from "@/components/shared"
import { CostDisplay, HealthBadge } from "@/components/observability"
import { formatLatency } from "@/lib/format"
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
          <>
            <div className="flex items-start justify-between mb-6 gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-surface-2 border border-hairline flex items-center justify-center">
                  <Bot className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h1 className="text-headline font-display font-semibold text-ink tracking-tight">{agent.name}</h1>
                  </div>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    <StatusBadge status={agent.status} />
                    <span className="text-caption text-ink-subtle">{agent.framework || "custom"} · {agent.model || "—"}</span>
                    <HealthBadge score={agent.health.health_score} />
                  </div>
                </div>
              </div>
              <div className="text-right text-caption text-ink-subtle space-y-2">
                <p>{agent.environment || "production"} · {agent.provider || "—"}</p>
                <p>Last seen {agent.last_seen_at ? new Date(agent.last_seen_at).toLocaleString() : "—"}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <MetricCard icon={<Heart className="w-4 h-4 text-primary" />} label="Health" value={`${agent.health.health_score}`} />
              <MetricCard icon={<Activity className="w-4 h-4 text-success" />} label="Success rate" value={`${agent.health.success_rate}%`} />
              <MetricCard icon={<Activity className="w-4 h-4 text-warning" />} label="Avg latency" value={`${agent.health.avg_latency_ms}ms`} />
              <MetricCard icon={<ClipboardCheck className="w-4 h-4 text-primary" />} label="Total cost" value={<CostDisplay value={agent.health.total_cost} />} />
            </div>

            <div className="flex gap-1 mb-6 border-b border-hairline">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2.5 text-body-sm font-medium transition-colors border-b-2 -mb-px ${
                    activeTab === tab.id ? "text-ink border-primary" : "text-ink-subtle border-transparent hover:text-ink"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === "overview" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card>
                  <h3 className="text-body-sm font-medium text-ink-muted mb-3">Agent metadata</h3>
                  <dl className="space-y-2 text-body-sm">
                    <div className="flex justify-between gap-4"><dt className="text-ink-subtle">Owner</dt><dd className="text-ink">{agent.owner}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-ink-subtle">Source</dt><dd className="text-ink">{agent.source}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-ink-subtle">Framework</dt><dd className="text-ink">{agent.framework || "—"}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-ink-subtle">Provider</dt><dd className="text-ink">{agent.provider || "—"}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-ink-subtle">Total requests</dt><dd className="text-ink">{agent.health.total_executions}</dd></div>
                  </dl>
                </Card>
                <Card>
                  <h3 className="text-body-sm font-medium text-ink-muted mb-3">Tags</h3>
                  {agent.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {agent.tags.map((tag) => (
                        <span key={tag} className="text-caption bg-surface-2 text-ink-subtle rounded-sm px-2 py-1">{tag}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-body-sm text-ink-subtle">No tags reported by SDK</p>
                  )}
                </Card>
              </div>
            )}

            {activeTab === "traces" && <AgentTraces traces={traces} loading={tracesLoading} />}
          </>
        )}
      </div>
    </AppLayout>
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
