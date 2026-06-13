"use client"

import Link from "next/link"
import { Key, Code2, UserCircle, Plug } from "lucide-react"
import { AppLayout } from "@/components/layout/app-layout"
import { Card, PageHeader } from "@/components/shared"

const links = [
  { href: "/settings/account", label: "Account", icon: UserCircle, desc: "GitHub sign-in and profile" },
  { href: "/settings/providers", label: "AI Providers", icon: Plug, desc: "Connect and validate provider API keys" },
  { href: "/settings/api-keys", label: "API Keys", icon: Key, desc: "Manage workspace ingestion keys" },
  { href: "/sdk", label: "SDK", icon: Code2, desc: "Connect provider, copy snippet, send test request" },
]

export default function SettingsPage() {
  return (
    <AppLayout>
      <div className="page-container max-w-2xl">
        <PageHeader title="Settings" subtitle="Workspace configuration and documentation" />
        <div className="space-y-3">
          {links.map((item) => (
            <Link key={item.href} href={item.href}>
              <Card className="panel-lift flex items-center gap-4 hover:border-hairline-strong transition-colors">
                <item.icon className="w-5 h-5 text-primary shrink-0" />
                <div>
                  <p className="text-body-sm font-medium text-ink">{item.label}</p>
                  <p className="caption-text">{item.desc}</p>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </AppLayout>
  )
}
