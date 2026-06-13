"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { ArrowLeft, Clock, DollarSign, Hash, Cpu } from "lucide-react"
import { analyticsService } from "@/services/api"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, StatusBadge, LoadingState, ErrorState } from "@/components/shared"
import { TraceSpanTree, ExecutionTimeline, CostDisplay } from "@/components/observability"
import { formatLatency, formatTokens } from "@/lib/format"
import { TraceDetail, TraceEvent } from "@/types"

export default function TraceDetailPage() {
  const params = useParams()
  const id = params.id as string
  const [detail, setDetail] = useState<TraceDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<"spans" | "llm" | "tools" | "errors" | "all">("spans")

  useEffect(() => {
    analyticsService
      .traceDetail(id)
      .then(setDetail)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load trace"))
      .finally(() => setLoading(false))
  }, [id])

  const trace = detail?.trace
  const timelines = detail?.timelines

  const tabEvents: TraceEvent[] =
    tab === "llm" ? timelines?.llm_calls || []
    : tab === "tools" ? timelines?.tool_calls || []
    : tab === "errors" ? timelines?.errors || []
    : detail?.events || []

  const tabs = [
    { id: "spans" as const, label: "Span tree", count: detail?.spans?.length || 0 },
    { id: "llm" as const, label: "LLM calls", count: timelines?.llm_calls?.length || 0 },
    { id: "tools" as const, label: "Tool calls", count: timelines?.tool_calls?.length || 0 },
    { id: "errors" as const, label: "Errors", count: timelines?.errors?.length || 0 },
    { id: "all" as const, label: "All events", count: detail?.events?.length || 0 },
  ]

  return (
    <AppLayout>
      <div className="page-container max-w-5xl">
        <Link href="/traces" className="inline-flex items-center gap-2 text-body-sm text-ink-subtle hover:text-ink mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to Trace Explorer
        </Link>

        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {trace && detail && (
          <>
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-2">
                <StatusBadge status={trace.status} />
                <span className="mono-text text-ink-muted">{trace.execution_id}</span>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="section-title">{trace.agent_name || "Execution Trace"}</h1>
              </div>
              <p className="caption-text mt-1">Correlation ID: {detail.correlation_id}</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <Metric icon={<Clock className="w-4 h-4" />} label="Latency" value={formatLatency(trace.latency_ms)} />
              <Metric icon={<DollarSign className="w-4 h-4" />} label="Cost" value={<CostDisplay value={trace.estimated_cost} />} />
              <Metric icon={<Hash className="w-4 h-4" />} label="Tokens" value={formatTokens(trace.total_tokens)} />
              <Metric icon={<Cpu className="w-4 h-4" />} label="Model" value={trace.model || "—"} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <Card>
                <h3 className="text-body-sm font-medium text-ink-muted mb-3">Input</h3>
                <pre className="mono-text text-body-sm text-ink-subtle whitespace-pre-wrap break-words max-h-64 overflow-auto">
                  {detail.input || "No input recorded"}
                </pre>
              </Card>
              <Card>
                <h3 className="text-body-sm font-medium text-ink-muted mb-3">Output</h3>
                <pre className="mono-text text-body-sm text-ink-subtle whitespace-pre-wrap break-words max-h-64 overflow-auto">
                  {detail.output || trace.error || "No output recorded"}
                </pre>
              </Card>
            </div>

            <Card>
              <div className="flex flex-wrap gap-2 mb-4 border-b border-hairline pb-3">
                {tabs.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTab(t.id)}
                    className={`px-3 py-1.5 rounded-md text-body-sm transition-colors ${
                      tab === t.id ? "bg-primary text-on-primary" : "text-ink-muted hover:bg-surface-2"
                    }`}
                  >
                    {t.label} ({t.count})
                  </button>
                ))}
              </div>

              {tab === "spans" ? (
                <TraceSpanTree spans={detail.spans || []} />
              ) : tabEvents.length > 0 ? (
                <ExecutionTimeline events={tabEvents.map((e) => ({
                  id: e.id,
                  execution_id: trace.execution_id,
                  event_type: e.event_type,
                  event_data: e.event_data,
                  timestamp: e.timestamp,
                }))} />
              ) : (
                <p className="caption-text text-ink-tertiary py-6 text-center">No events in this timeline</p>
              )}
            </Card>
          </>
        )}
      </div>
    </AppLayout>
  )
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return (
    <Card className="panel-lift">
      <div className="flex items-center gap-2 text-ink-subtle mb-1">
        {icon}
        <span className="caption-text">{label}</span>
      </div>
      <p className="text-body-sm font-medium text-ink truncate">{value}</p>
    </Card>
  )
}
