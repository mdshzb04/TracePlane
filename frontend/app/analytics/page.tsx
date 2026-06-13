"use client"

import { useMemo, useState } from "react"
import { Activity, Bot, CheckCircle, Clock, DollarSign, Zap } from "lucide-react"
import { useObservabilityDashboard } from "@/hooks"
import { AppLayout } from "@/components/layout/app-layout"
import { MetricSkeletonGrid, ChartSkeletonGrid } from "@/components/shared/skeletons"
import { MetricTile, SectionHeader, TimeSeriesChart } from "@/components/observability"
import { DateRangeSelector } from "@/components/analytics/date-range-selector"
import { BreakdownChart } from "@/components/analytics/breakdown-chart"
import { RecentTracesTable } from "@/components/analytics/recent-traces-table"
import { formatCost } from "@/lib/format"
import { friendlyErrorMessage } from "@/lib/friendly-error"
import { DateRange, presetRange, toQueryParams } from "@/lib/analytics-range"

const CHART_HEIGHT = 300

export default function AnalyticsPage() {
  const [range, setRange] = useState<DateRange>(() => presetRange("7d"))
  const queryParams = useMemo(() => toQueryParams(range), [range])
  const { data, isLoading, isFetching, error, refetch } = useObservabilityDashboard(queryParams)
  const loading = isLoading && !data
  const errorMessage = error instanceof Error ? error.message : error ? String(error) : null

  const bucket = data?.bucket ?? "day"
  const ts = data?.timeseries
  const kpis = data?.kpis
  const breakdowns = data?.breakdowns
  const recentTraces = data?.tables.recent_executions ?? []
  const hasSeries = Boolean(ts?.requests?.length)

  return (
    <AppLayout>
      <div className="page-container max-w-[1600px]">
        <SectionHeader
          eyebrow="Observability"
          title="Analytics"
          subtitle="Production metrics and trends from live execution telemetry"
          action={<DateRangeSelector range={range} onChange={setRange} />}
        />

        {data?.degraded && (
          <div className="mb-4 rounded-lg border border-warning/30 bg-warning/10 px-4 py-2 text-body-sm text-ink-muted">
            Some analytics data may be incomplete for this time range.
          </div>
        )}

        {loading && (
          <>
            <MetricSkeletonGrid count={6} />
            <ChartSkeletonGrid count={4} />
          </>
        )}

        {errorMessage && !data && (
          <div className="panel-lift rounded-lg p-8 text-center">
            <p className="text-body-sm text-ink-muted">{friendlyErrorMessage(errorMessage)}</p>
            <button type="button" className="btn-secondary mt-4" onClick={() => void refetch()}>
              Retry
            </button>
          </div>
        )}

        {kpis && (
          <div className={isFetching ? "opacity-70 transition-opacity" : ""}>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
              <MetricTile
                label="Total Requests"
                value={kpis.total_requests.toLocaleString()}
                icon={<Activity className="w-4 h-4 text-primary" />}
              />
              <MetricTile
                label="Total Cost"
                value={formatCost(kpis.total_cost)}
                icon={<DollarSign className="w-4 h-4 text-success" />}
              />
              <MetricTile
                label="Total Tokens"
                value={kpis.total_tokens.toLocaleString()}
                icon={<Zap className="w-4 h-4 text-primary" />}
              />
              <MetricTile
                label="Success Rate"
                value={`${kpis.success_rate.toFixed(1)}%`}
                icon={<CheckCircle className="w-4 h-4 text-success" />}
              />
              <MetricTile
                label="Avg Latency"
                value={`${kpis.avg_latency_ms.toFixed(0)}ms`}
                icon={<Clock className="w-4 h-4 text-ink-subtle" />}
              />
              <MetricTile
                label="Active Agents"
                value={kpis.active_agents}
                icon={<Bot className="w-4 h-4 text-primary" />}
                href="/agents"
              />
            </div>

            {ts && hasSeries && breakdowns && (
              <>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-8">
                  <TimeSeriesChart
                    title="Requests Over Time"
                    data={ts.requests}
                    color="#5e6ad2"
                    id="req"
                    height={CHART_HEIGHT}
                    bucket={bucket}
                  />
                  <TimeSeriesChart
                    title="Cost Over Time"
                    data={ts.cost}
                    color="#27a644"
                    id="cost"
                    unit="$"
                    height={CHART_HEIGHT}
                    bucket={bucket}
                  />
                  <TimeSeriesChart
                    title="Token Usage Over Time"
                    data={ts.tokens}
                    color="#828fff"
                    id="tok"
                    height={CHART_HEIGHT}
                    bucket={bucket}
                  />
                  <TimeSeriesChart
                    title="Failure Rate Over Time"
                    data={ts.failure_rate}
                    color="#e67e22"
                    id="fail"
                    unit="%"
                    height={CHART_HEIGHT}
                    bucket={bucket}
                  />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
                  {breakdowns.top_providers.length > 0 && (
                    <BreakdownChart
                      title="Top Providers"
                      data={breakdowns.top_providers}
                      labelKey="provider"
                      valueKey="request_count"
                      color="#5e6ad2"
                    />
                  )}
                  {breakdowns.top_models.length > 0 && (
                    <BreakdownChart
                      title="Top Models"
                      data={breakdowns.top_models}
                      labelKey="model"
                      valueKey="request_count"
                      color="#828fff"
                    />
                  )}
                  {breakdowns.top_agents.length > 0 && (
                    <BreakdownChart
                      title="Top Agents"
                      data={breakdowns.top_agents}
                      labelKey="agent_name"
                      valueKey="request_count"
                      color="#7a7fad"
                    />
                  )}
                </div>

                {recentTraces.length > 0 && (
                  <RecentTracesTable rows={recentTraces} />
                )}
              </>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
