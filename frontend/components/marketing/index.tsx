"use client"

import Link from "next/link"
import {
  Bot,
  Activity,
  Search,
  GitBranch,
  LineChart,
} from "lucide-react"
import { ProviderShowcase } from "./provider-showcase"
import { MarketingDashboardPreview } from "./dashboard-preview"
import { MarketingNav } from "./marketing-nav"
import { MarketingWorkflow } from "./workflow"
import { MarketingFooter } from "./marketing-footer"
import { HeroProviderOrbit } from "./hero-provider-orbit"

export { ProviderShowcase, MarketingNav, MarketingWorkflow, MarketingFooter }

export function MarketingHero() {
  return (
    <section className="max-w-[1200px] mx-auto px-5 sm:px-6 lg:px-8 pt-12 pb-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-14 items-center">
        <div>
          <h1 className="text-[36px] sm:text-[42px] lg:text-[48px] font-semibold text-ink tracking-tight leading-[1.08]">
            Control plane for{" "}
            <span className="text-primary">AI agents</span>
          </h1>
          <p className="text-[15px] sm:text-[16px] text-ink-muted mt-5 max-w-md leading-relaxed">
            Monitor traces, costs, and failures across every model provider — one SDK,
            full visibility in production.
          </p>
          <div className="flex flex-wrap items-center gap-3 mt-8">
            <Link
              href="/login"
              className="inline-flex items-center rounded-lg bg-primary px-4 py-2.5 text-[14px] font-medium text-on-primary shadow-[0_4px_20px_-4px_rgb(var(--tp-primary)/0.55)] hover:bg-primary-hover transition-all duration-200"
            >
              Try for free →
            </Link>
            <a href="#dashboard" className="text-[14px] font-medium text-ink-subtle hover:text-ink transition-colors">
              See the dashboard
            </a>
          </div>
        </div>
        <HeroProviderOrbit />
      </div>

      <div id="dashboard" className="mt-12 lg:mt-16 scroll-mt-24">
        <MarketingDashboardPreview />
      </div>
    </section>
  )
}

const capabilities = [
  {
    icon: GitBranch,
    title: "Trace Explorer",
    desc: "Search and inspect execution traces with event timelines for every agent run.",
    glow: "feature-card--purple",
    iconHover: "group-hover:text-violet-400",
  },
  {
    icon: LineChart,
    title: "Cost & Usage",
    desc: "Token usage, cost by model, latency percentiles, and anomaly detection.",
    glow: "feature-card--emerald",
    iconHover: "group-hover:text-emerald-400",
  },
  {
    icon: Bot,
    title: "Agents",
    desc: "Agents auto-discover when you instrument with the SDK — health and metadata.",
    glow: "feature-card--pink-purple",
    iconHover: "group-hover:text-fuchsia-400",
  },
  {
    icon: Activity,
    title: "Trace Monitoring",
    desc: "Success rates, latency, and failure trends per agent across your fleet.",
    glow: "feature-card--blue",
    iconHover: "group-hover:text-blue-400",
  },
  {
    icon: Search,
    title: "Alerts",
    desc: "Threshold monitoring for failure rate, latency, cost, and errors.",
    glow: "feature-card--amber",
    iconHover: "group-hover:text-amber-400",
  },
]

export function FeatureGrid() {
  return (
    <section id="observability" className="max-w-[1200px] mx-auto px-5 sm:px-6 lg:px-8 py-16 scroll-mt-24">
      <h2 className="text-[22px] sm:text-[26px] font-semibold text-ink tracking-tight mb-2">
        Observability built for AI agents
      </h2>
      <p className="text-[14px] text-ink-muted max-w-2xl mb-10">
        Connect your agents and every metric flows from real telemetry — not demo data.
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        {capabilities.map((f) => (
          <div
            key={f.title}
            className={`group feature-card ${f.glow} aspect-square rounded-xl border border-hairline bg-surface-1 p-4 flex flex-col cursor-default`}
          >
            <div className="relative z-[1] feature-card-icon w-8 h-8 rounded-lg bg-surface-2 border border-hairline flex items-center justify-center mb-3 shrink-0 transition-all duration-[250ms] ease">
              <f.icon className={`w-4 h-4 text-ink-muted transition-colors duration-[250ms] ease ${f.iconHover}`} />
            </div>
            <h3 className="relative z-[1] text-[13px] font-semibold text-ink mb-1.5 leading-tight">{f.title}</h3>
            <p className="relative z-[1] text-[11px] sm:text-[12px] text-ink-subtle leading-snug line-clamp-4">{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
