/** Shared observability formatters — consistent precision across all surfaces. */

export type CostSeverity = "low" | "medium" | "high"

const COST_SEVERITY_THRESHOLDS = {
  medium: 0.01,
  high: 0.1,
} as const

/** Format USD cost without rounding small non-zero values to $0.00 */
export function formatCost(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—"
  const n = Number(value)
  if (n === 0) return "$0.000000"

  const abs = Math.abs(n)
  let decimals = 6
  if (abs >= 1) decimals = 4
  else if (abs >= 0.01) decimals = 4
  else {
    // Ensure sub-cent costs remain visible
    while (decimals <= 10) {
      const candidate = n.toFixed(decimals)
      if (parseFloat(candidate) !== 0) return `$${candidate}`
      decimals += 1
    }
    return `$${n.toExponential(4)}`
  }

  const rounded2 = Math.round(n * 100) / 100
  if (rounded2 === 0 && n !== 0) {
    return `$${n.toFixed(6)}`
  }
  return `$${n.toFixed(decimals)}`
}

/** Raw numeric cost for charts/API comparisons (6 decimal places). */
export function normalizeCost(value: number | null | undefined): number {
  if (value == null || Number.isNaN(Number(value))) return 0
  return Math.round(Number(value) * 1_000_000) / 1_000_000
}

export function formatTokens(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—"
  return Number(value).toLocaleString()
}

export function formatLatency(value: number | null | undefined): string {
  if (value == null || Number.isNaN(Number(value))) return "—"
  return `${Math.round(Number(value))}ms`
}

export function getCostSeverity(value: number | null | undefined): CostSeverity {
  if (value == null || Number.isNaN(Number(value)) || value <= 0) return "low"
  if (value >= COST_SEVERITY_THRESHOLDS.high) return "high"
  if (value >= COST_SEVERITY_THRESHOLDS.medium) return "medium"
  return "low"
}

export const COST_SEVERITY_STYLES: Record<CostSeverity, string> = {
  low: "bg-success/15 text-success border-success/30",
  medium: "bg-warning/15 text-warning border-warning/30",
  high: "bg-danger/15 text-danger border-danger/30",
}
