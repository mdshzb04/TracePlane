"use client"

import { useState } from "react"
import Link from "next/link"
import { useTraces } from "@/hooks"
import { AppLayout } from "@/components/layout/app-layout"
import { CostDisplay } from "@/components/observability"
import { formatLatency } from "@/lib/format"
import {
  StatusBadge,
  LoadingState,
  ErrorState,
  PageHeader,
  Table,
  TableHead,
  TableHeader,
  TableRow,
  TableCell,
} from "@/components/shared"

export default function TracesPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useTraces({ page, page_size: 20 })
  const traces = data?.traces ?? []
  const total = data?.total ?? 0
  const loading = isLoading
  const errorMessage = error instanceof Error ? error.message : error ? String(error) : null
  const totalPages = Math.ceil(total / 20) || 1

  return (
    <AppLayout>
      <div className="page-container">
        <PageHeader
          title="Trace Explorer"
          subtitle="Execution traces with correlation and drill-down"
        />

        {loading && <LoadingState />}
        {errorMessage && <ErrorState message={errorMessage} />}
        {!loading && !errorMessage && (
          <>
            <Table>
              <TableHead>
                <TableHeader>Trace</TableHeader>
                <TableHeader>Agent</TableHeader>
                <TableHeader>Status</TableHeader>
                <TableHeader>Model</TableHeader>
                <TableHeader>Latency</TableHeader>
                <TableHeader>Cost</TableHeader>
                <TableHeader>Started</TableHeader>
              </TableHead>
              <tbody>
                {traces.map((t) => (
                  <TableRow key={t.trace_id}>
                    <TableCell>
                      <Link href={`/traces/${t.execution_id}`} className="text-primary hover:underline font-mono text-caption">
                        {t.trace_id.slice(0, 8)}…
                      </Link>
                    </TableCell>
                    <TableCell>{t.agent_name || t.agent_id?.slice(0, 8) || "—"}</TableCell>
                    <TableCell><StatusBadge status={t.status} /></TableCell>
                    <TableCell className="text-ink-subtle">{t.model || "—"}</TableCell>
                    <TableCell>{t.latency_ms != null ? formatLatency(t.latency_ms) : "—"}</TableCell>
                    <TableCell><CostDisplay value={t.estimated_cost} /></TableCell>
                    <TableCell className="text-ink-tertiary text-caption">
                      {t.timestamp ? new Date(t.timestamp).toLocaleString() : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </tbody>
            </Table>
            <div className="flex items-center justify-between mt-4">
              <p className="caption-text text-ink-tertiary">{total} traces</p>
              <div className="flex gap-2">
                <button className="btn-secondary text-caption" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
                <span className="caption-text text-ink-subtle self-center">Page {page} / {totalPages}</span>
                <button className="btn-secondary text-caption" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</button>
              </div>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  )
}
