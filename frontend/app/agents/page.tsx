"use client"

import { useState } from "react"
import Link from "next/link"
import { Search } from "lucide-react"
import { useAgents } from "@/hooks"
import type { Agent } from "@/types"
import { AppLayout } from "@/components/layout/app-layout"
import {
  PageHeader,
  Card,
  Table,
  TableHead,
  TableHeader,
  TableRow,
  TableCell,
  StatusBadge,
  LoadingState,
  ErrorState,
  Select,
} from "@/components/shared"

const statusOptions = [
  { value: "", label: "All Statuses" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "deprecated", label: "Deprecated" },
]

export default function AgentsPage() {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("")
  const [page, setPage] = useState(1)

  const { data, loading, error } = useAgents({ status, search, page, page_size: 20 })

  const agents = data?.items || []
  const totalPages = data?.total_pages || 1

  return (
    <AppLayout>
      <div className="page-container">
        <PageHeader
          title="Agents"
          subtitle="Auto-discovered agents from SDK telemetry — no manual registration"
        />

        <Card className="mb-6">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-subtle" />
              <input
                type="text"
                placeholder="Search agents..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                className="input w-full pl-9"
              />
            </div>
            <Select
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1) }}
              options={statusOptions}
              className="w-40"
            />
          </div>
        </Card>

        {loading && <LoadingState />}
        {error && <ErrorState message={error} />}
        {!loading && !error && agents.length === 0 && (
          <Card className="text-center py-12">
            <p className="text-body-sm text-ink-subtle mb-4">No auto-discovered agents yet.</p>
            <div className="flex justify-center gap-3">
              <Link href="/settings/api-keys" className="btn-primary text-body-sm">Create API Key</Link>
              <Link href="/sdk" className="btn-secondary text-body-sm">SDK onboarding</Link>
            </div>
          </Card>
        )}
        {!loading && !error && agents.length > 0 && (
          <>
            <Card className="p-0 overflow-hidden">
              <Table>
                <TableHead>
                  <TableHeader>Name</TableHeader>
                  <TableHeader>Framework</TableHeader>
                  <TableHeader>Model</TableHeader>
                  <TableHeader>Status</TableHeader>
                  <TableHeader>Tags</TableHeader>
                </TableHead>
                <tbody>
                  {agents.map((agent: Agent) => (
                    <TableRow key={agent.id}>
                      <TableCell>
                        <Link href={`/agents/${agent.id}`} className="text-ink hover:text-primary transition-colors">
                          {agent.name}
                        </Link>
                      </TableCell>
                      <TableCell>{agent.framework || "—"}</TableCell>
                      <TableCell>{agent.model || "—"}</TableCell>
                      <TableCell>
                        <StatusBadge status={agent.status} />
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {agent.tags?.map((tag) => (
                            <span key={tag} className="text-caption bg-surface-2 text-ink-subtle rounded-sm px-1.5 py-0.5">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </tbody>
              </Table>
            </Card>

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 mt-6">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="btn-secondary disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="text-body-sm text-ink-muted">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="btn-secondary disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  )
}
