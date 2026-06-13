"use client"

import { AppLayout } from "@/components/layout/app-layout"
import { PageHeader } from "@/components/shared"
import { ProviderList } from "@/components/providers/provider-list"

export default function ProvidersSettingsPage() {
  return (
    <AppLayout>
      <div className="page-container max-w-xl">
        <PageHeader
          title="Providers"
          subtitle="Connect LLM providers for SDK telemetry and observability"
        />
        <ProviderList />
      </div>
    </AppLayout>
  )
}
