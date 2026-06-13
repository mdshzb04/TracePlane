import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback } from "react"
import {
  agentsService,
  analyticsService,
} from "@/services/api"
import { Agent, OverviewStats, PaginatedResponse } from "@/types"

export function useAgents(params?: { status?: string; search?: string; page?: number; page_size?: number }) {
  const query = useQuery({
    queryKey: ["agents", params],
    queryFn: () => agentsService.list(params),
    placeholderData: (prev) => prev,
  })

  const refresh = useCallback(() => {
    void query.refetch()
  }, [query])

  return {
    data: query.data ?? null,
    loading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : query.error ? String(query.error) : null,
    refresh,
  }
}

export function useAgent(id: string | null) {
  const query = useQuery({
    queryKey: ["agent", id],
    queryFn: () => agentsService.get(id!),
    enabled: Boolean(id),
  })

  const refresh = useCallback(() => {
    void query.refetch()
  }, [query])

  return {
    data: query.data ?? null,
    loading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : query.error ? String(query.error) : null,
    refresh,
  }
}

export function useAnalyticsOverview() {
  const query = useQuery({
    queryKey: ["analytics", "overview"],
    queryFn: () => analyticsService.overview(),
  })

  return {
    data: query.data ?? null,
    loading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : query.error ? String(query.error) : null,
  }
}

export function useObservabilityDashboard(params: Record<string, string>) {
  const query = useQuery({
    queryKey: ["analytics", "observability", params],
    queryFn: () => analyticsService.observability(params),
    placeholderData: (prev) => prev,
    refetchOnMount: "always",
  })

  return query
}

export function useTraces(params: {
  page: number
  page_size?: number
  agent_id?: string
  model?: string
  status?: string
  search?: string
}) {
  const query = useQuery({
    queryKey: ["traces", params],
    queryFn: () => analyticsService.traces(params),
    placeholderData: (prev) => prev,
  })

  return query
}

export { useQueryClient }
