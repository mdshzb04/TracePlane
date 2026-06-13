"use client"

import { useEffect, useState } from "react"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, PageHeader, LoadingState, ErrorState } from "@/components/shared"
import { CostDisplay } from "@/components/observability"
import { analyticsService } from "@/services/api"
import type { ToolAnalyticsResponse } from "@/types"

export default function ToolAnalyticsPage() {
  const [data, setData] = useState<ToolAnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    analyticsService.tools()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false))
  }, [])

  return (
    <AppLayout>
      <div className="page-container">
        <PageHeader
          title="Tool Analytics"
          subtitle="Invocation volume, latency, failures, and cost impact per tool"
        />
        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {data && (
          <>
            <div className="grid grid-cols-2 gap-3 mb-6 max-w-md">
              <Card><p className="caption-text">Total invocations</p><p className="text-body font-semibold">{data.total_invocations}</p></Card>
              <Card><p className="caption-text">Total failures</p><p className="text-body font-semibold text-danger">{data.total_failures}</p></Card>
            </div>
            <Card className="p-0 overflow-hidden">
              <table className="w-full text-body-sm">
                <thead className="border-b border-hairline bg-surface-2">
                  <tr className="text-left text-caption text-ink-muted">
                    <th className="p-3">Tool</th>
                    <th className="p-3">Calls</th>
                    <th className="p-3">Success</th>
                    <th className="p-3">Failures</th>
                    <th className="p-3">Avg latency</th>
                    <th className="p-3">P95</th>
                    <th className="p-3">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tools.map((t) => (
                    <tr key={t.tool_name} className="border-b border-hairline last:border-0 hover:bg-surface-2/50">
                      <td className="p-3 font-mono text-ink">{t.tool_name}</td>
                      <td className="p-3">{t.invocation_count}</td>
                      <td className="p-3 text-success">{t.success_rate.toFixed(1)}%</td>
                      <td className="p-3">{t.failure_count}</td>
                      <td className="p-3">{t.avg_latency_ms.toFixed(0)}ms</td>
                      <td className="p-3">{t.p95_latency_ms.toFixed(0)}ms</td>
                      <td className="p-3"><CostDisplay value={t.total_cost} /></td>
                    </tr>
                  ))}
                  {data.tools.length === 0 && (
                    <tr><td colSpan={7} className="p-8 text-center text-ink-subtle">No tool events yet — instrument tool calls via SDK</td></tr>
                  )}
                </tbody>
              </table>
            </Card>
          </>
        )}
      </div>
    </AppLayout>
  )
}
