"use client"

export { TraceSpanTree } from "./trace-span-tree"
export { ExecutionTimeline } from "./execution-timeline"
export { CostDisplay, CostSeverityBadge } from "./cost-badge"

import Link from "next/link"
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import { cn } from "@/lib/utils"
import { formatCost } from "@/lib/format"
import { TimeSeriesPoint } from "@/types"

export function MetricTile({
  label,
  value,
  sub,
  icon,
  href,
  trend,
}: {
  label: string
  value: React.ReactNode
  sub?: string
  icon?: React.ReactNode
  href?: string
  trend?: "up" | "down" | "neutral"
}) {
  const inner = (
    <div className="panel-lift rounded-lg p-4 h-full transition-colors hover:border-hairline-strong">
      <div className="flex items-center justify-between mb-2">
        <span className="caption-text">{label}</span>
        {icon}
      </div>
      <p className="text-headline font-display font-semibold text-ink tracking-tight">{value}</p>
      {sub && <p className="caption-text mt-1">{sub}</p>}
      {trend && (
        <p
          className={cn(
            "text-caption mt-1",
            trend === "up" ? "text-success" : trend === "down" ? "text-danger" : "text-ink-tertiary"
          )}
        >
          {trend === "up" ? "↑" : trend === "down" ? "↓" : "—"} vs prior period
        </p>
      )}
    </div>
  )
  if (href) return <Link href={href}>{inner}</Link>
  return inner
}

export function TimeSeriesChart({
  title,
  data,
  color = "#5e6ad2",
  id,
  unit = "",
  height = 260,
  bucket,
  compact = false,
}: {
  title?: string
  data: TimeSeriesPoint[]
  color?: string
  id: string
  unit?: string
  height?: number
  bucket?: string
  compact?: boolean
}) {
  const tickFormatter = (v: string) => {
    const s = String(v)
    if (bucket === "hour") {
      const d = new Date(s.includes("T") ? s : `${s}T00:00:00`)
      return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric" })
    }
    if (bucket === "week") return s.slice(5, 10)
    return s.slice(5, 10)
  }

  return (
    <div className={compact ? "panel-lift rounded-lg p-4 h-full" : "panel-lift rounded-lg p-5"}>
      {title && (
        <h3 className={compact ? "text-caption font-medium text-ink-muted mb-2" : "text-body-sm font-medium text-ink-muted mb-4"}>
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`grad-${id}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.35} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#23252a" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: "#8a8f98", fontSize: compact ? 10 : 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={tickFormatter}
            minTickGap={compact ? 24 : 32}
          />
          <YAxis tick={{ fill: "#8a8f98", fontSize: 11 }} axisLine={false} tickLine={false} width={48} />
          <Tooltip
            contentStyle={{
              background: "#0f1011",
              border: "1px solid #23252a",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            formatter={(v: number) => [unit === "$" && typeof v === "number" ? formatCost(v) : `${unit}${typeof v === "number" ? v.toLocaleString() : v}`, ""]}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            fill={`url(#grad-${id})`}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: color }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function HealthBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? "bg-success/15 text-success border-success/30" :
    score >= 60 ? "bg-warning/15 text-warning border-warning/30" :
    "bg-danger/15 text-danger border-danger/30"
  return (
    <span className={cn("text-caption font-medium px-2 py-0.5 rounded-pill border", color)}>
      {score.toFixed(0)}
    </span>
  )
}

export function SectionHeader({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow?: string
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
      <div>
        {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
        <h1 className="section-title">{title}</h1>
        {subtitle && <p className="body-text mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function EmptyMetric({ message }: { message: string }) {
  return (
    <div className="panel-lift rounded-lg p-8 text-center">
      <p className="text-body-sm text-ink-subtle">{message}</p>
      <p className="caption-text mt-1">Data appears when agents run in production</p>
    </div>
  )
}
