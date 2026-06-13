import type { QueryClient } from "@tanstack/react-query"

/** Bust cached metrics after a real trace is ingested from Quick Start / test request. */
export function invalidateTelemetryCaches(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
    queryClient.invalidateQueries({ queryKey: ["analytics"] }),
    queryClient.invalidateQueries({ queryKey: ["agents"] }),
    queryClient.invalidateQueries({ queryKey: ["traces"] }),
    queryClient.invalidateQueries({ queryKey: ["agent"] }),
  ])
}
