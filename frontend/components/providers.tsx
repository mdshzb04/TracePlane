"use client"

import { useState } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { DevStyleRecovery } from "@/components/dev-style-recovery"
import { ThemeProvider } from "@/components/theme-provider"

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  })
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(makeQueryClient)
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <DevStyleRecovery />
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  )
}
