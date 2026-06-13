"use client"

import { cn } from "@/lib/utils"
import { formatCost, getCostSeverity, COST_SEVERITY_STYLES } from "@/lib/format"

export function CostDisplay({ value, className }: { value: number | null | undefined; className?: string }) {
  return <span className={cn("font-mono tabular-nums", className)}>{formatCost(value)}</span>
}

export function CostSeverityBadge({ value }: { value: number | null | undefined }) {
  const severity = getCostSeverity(value)
  return (
    <span className={cn("text-caption font-medium px-2 py-0.5 rounded-pill border capitalize", COST_SEVERITY_STYLES[severity])}>
      {severity}
    </span>
  )
}
