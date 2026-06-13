"use client"

import { Suspense } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Activity, Bot, Coins, Zap, AlertTriangle, ArrowRight, Clock, TrendingUp } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { AppLayout } from "@/components/layout/app-layout"
import { StatusBadge } from "@/components/shared"
import { MetricSkeletonGrid } from "@/components/shared/skeletons"
import { MetricTile, SectionHeader, CostDisplay } from "@/components/observability"
import { analyticsService } from "@/services/api"
import { friendlyErrorMessage } from "@/lib/friendly-error"
import { formatLatency, formatTokens } from "@/lib/format"

export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardFallback />}>
      <DashboardContent />
    </Suspense>
  )
}

function DashboardFallback() {
  return (
    <AppLayout>
      <div className="page-container max-w-[1600px]">
        <MetricSkeletonGrid count={6} />
      </div>
    </AppLayout>
  )
}

function DashboardContent() {
  const searchParams = useSearchParams()
  const testSuccess = searchParams.get("test") === "success"
  const testTraceId = searchParams.get("trace")

  const live = useQuery({
    queryKey: ["dashboard", "live"],
    queryFn: () => analyticsService.live(),
    refetchInterval: 30_000,
    refetchOnMount: "always",
  })

  const loading = live.isLoading && !live.data
  const errorMessage = live.error instanceof Error ? live.error.message : live.error ? String(live.error) : null
  const data = live.data

  return (
    <AppLayout>
      <div className="page-container max-w-[1600px]">
        <SectionHeader
          eyebrow="Overview"
          title="Dashboard"
          subtitle="Live metrics from SDK telemetry — updates automatically as your app sends traces"
          action={
            <Link href="/analytics" className="btn-secondary text-body-sm inline-flex items-center gap-1.5">
              Full analytics <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          }
        />

        {testSuccess && (
          <div className="mb-4 rounded-lg border border-success/30 bg-success/5 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
            <p className="text-body-sm text-ink">Test trace ingested successfully.</p>
            {testTraceId && (
              <Link href={`/traces/${testTraceId}`} className="btn-secondary text-body-sm shrink-0">
                View trace
              </Link>
            )}
          </div>
        )}

        {loading && <MetricSkeletonGrid count={12} />}
        {errorMessage && !data && (
          <div className="panel-lift rounded-lg p-8 text-center">
            <p className="text-body-sm text-ink-muted">{friendlyErrorMessage(errorMessage)}</p>
            <button type="button" className="btn-secondary mt-4" onClick={() => void live.refetch()}>
              Retry
            </button>
          </div>
        )}

        {data && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-3">
              <MetricTile label="Requests today" value={data.executions_today} icon={<Activity className="w-4 h-4 text-primary" />} />
              <MetricTile label="Success rate" value={`${data.success_rate.toFixed(1)}%`} icon={<TrendingUp className="w-4 h-4 text-success" />} />
              <MetricTile label="Error rate" value={`${data.error_rate.toFixed(1)}%`} icon={<AlertTriangle className="w-4 h-4 text-warning" />} />
              <MetricTile label="Avg latency" value={formatLatency(data.avg_latency_ms)} icon={<Clock className="w-4 h-4 text-primary" />} />
              <MetricTile label="Cost today" value={<CostDisplay value={data.cost_today} />} icon={<Coins className="w-4 h-4 text-success" />} />
              <MetricTile label="Active agents" value={data.active_agents} href="/agents" icon={<Bot className="w-4 h-4 text-primary" />} />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 gap-3 mb-6">
              <MetricTile label="Prompt tokens" value={formatTokens(data.input_tokens_today)} icon={<Zap className="w-4 h-4 text-primary" />} />
              <MetricTile label="Completion tokens" value={formatTokens(data.output_tokens_today)} icon={<Zap className="w-4 h-4 text-success" />} />
              <MetricTile label="Total tokens" value={formatTokens(data.tokens_today)} icon={<Zap className="w-4 h-4 text-primary" />} />
            </div>

            {(data.top_providers.length > 0 || data.top_models.length > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                {data.top_providers.length > 0 && (
                  <BreakdownCard title="Top providers" rows={data.top_providers.map((p) => ({ label: p.provider, count: p.request_count }))} />
                )}
                {data.top_models.length > 0 && (
                  <BreakdownCard title="Top models" rows={data.top_models.map((m) => ({ label: m.model, count: m.request_count }))} />
                )}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <TraceFeed title="Recent traces" rows={data.recent_executions} empty="No traces yet. Integrate the SDK to start tracing." />
              <TraceFeed title="Running" rows={data.running_executions} empty="No in-flight requests." />
              <TraceFeed title="Recent failures" rows={data.failed_executions} empty="No failures." highlightFailed />
            </div>

            {!data.recent_executions.length && !data.running_executions.length && !data.failed_executions.length && (
              <div className="panel-lift rounded-lg p-8 mt-4 text-center">
                <p className="text-body text-ink-muted mb-2">No telemetry yet</p>
                <p className="text-body-sm text-ink-subtle mb-4">
                  Connect a provider, copy the SDK snippet, and deploy your app. Metrics populate automatically from production traffic.
                </p>
                <div className="flex flex-wrap justify-center gap-3">
                  <Link href="/settings/providers" className="btn-secondary">Connect provider</Link>
                  <Link href="/sdk" className="btn-primary">Copy SDK snippet</Link>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  )
}

function BreakdownCard({ title, rows }: { title: string; rows: { label: string; count: number }[] }) {
  return (
    <div className="panel-lift rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-hairline">
        <h3 className="text-body-sm font-medium text-ink">{title}</h3>
      </div>
      <ul className="divide-y divide-hairline">
        {rows.map((row) => (
          <li key={row.label} className="flex items-center justify-between px-4 py-2.5 text-body-sm">
            <span className="text-ink truncate mr-2">{row.label}</span>
            <span className="text-ink-subtle shrink-0">{row.count.toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function TraceFeed({
  title,
  rows,
  empty,
  highlightFailed,
}: {
  title: string
  rows: { execution_id: string; agent_name?: string | null; status: string; model?: string | null; latency_ms?: number | null; estimated_cost?: number; started_at: string }[]
  empty: string
  highlightFailed?: boolean
}) {
  return (
    <div className="panel-lift rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-hairline flex items-center gap-2">
        {highlightFailed && <AlertTriangle className="w-4 h-4 text-warning" />}
        <h3 className="text-body-sm font-medium text-ink">{title}</h3>
      </div>
      {rows.length === 0 ? (
        <p className="px-4 py-8 text-body-sm text-ink-subtle text-center">{empty}</p>
      ) : (
        <ul className="divide-y divide-hairline">
          {rows.slice(0, 8).map((row) => (
            <li key={row.execution_id}>
              <Link
                href={`/traces/${row.execution_id}`}
                className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-surface-2/50 transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-body-sm text-ink truncate">{row.agent_name || "Unknown agent"}</p>
                  <p className="caption-text text-ink-tertiary truncate">{row.model || "—"}</p>
                </div>
                <div className="text-right shrink-0">
                  <StatusBadge status={row.status} />
                  <p className="caption-text text-ink-tertiary mt-0.5">
                    {row.latency_ms != null ? formatLatency(row.latency_ms) : "—"} · <CostDisplay value={row.estimated_cost ?? 0} />
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
