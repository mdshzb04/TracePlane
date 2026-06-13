"use client"

import Link from "next/link"
import { ExecutionTableRow } from "@/types"
import { CostDisplay } from "@/components/observability"
import { StatusBadge } from "@/components/shared"
import { formatLatency, formatTokens } from "@/lib/format"

export function RecentTracesTable({ rows }: { rows: ExecutionTableRow[] }) {
  return (
    <div className="panel-lift rounded-lg overflow-hidden">
      <div className="px-5 py-4 border-b border-hairline">
        <h3 className="text-body font-medium text-ink">Recent Traces</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-body-sm">
          <thead>
            <tr className="border-b border-hairline bg-surface-2/40 text-caption text-ink-tertiary">
              <th className="px-4 py-3 font-medium">Trace ID</th>
              <th className="px-4 py-3 font-medium">Agent</th>
              <th className="px-4 py-3 font-medium">Provider</th>
              <th className="px-4 py-3 font-medium">Model</th>
              <th className="px-4 py-3 font-medium text-right">Tokens</th>
              <th className="px-4 py-3 font-medium text-right">Cost</th>
              <th className="px-4 py-3 font-medium text-right">Latency</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.trace_id}
                className="border-b border-hairline/60 last:border-0 hover:bg-surface-2/30 transition-colors"
              >
                <td className="px-4 py-3">
                  <Link
                    href={`/traces/${row.trace_id}`}
                    className="font-mono text-caption text-primary hover:underline"
                  >
                    {row.trace_id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink truncate max-w-[140px]">{row.agent_name}</td>
                <td className="px-4 py-3 text-ink-subtle capitalize">{row.provider || "—"}</td>
                <td className="px-4 py-3 text-ink-subtle font-mono text-caption truncate max-w-[160px]">
                  {row.model || "—"}
                </td>
                <td className="px-4 py-3 text-right text-ink-muted tabular-nums">
                  {formatTokens(row.total_tokens)}
                </td>
                <td className="px-4 py-3 text-right">
                  <CostDisplay value={row.estimated_cost} />
                </td>
                <td className="px-4 py-3 text-right text-ink-muted tabular-nums">
                  {row.latency_ms != null ? formatLatency(row.latency_ms) : "—"}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={row.status} />
                </td>
                <td className="px-4 py-3 text-right text-ink-tertiary text-caption whitespace-nowrap tabular-nums">
                  {row.started_at
                    ? new Date(row.started_at).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
