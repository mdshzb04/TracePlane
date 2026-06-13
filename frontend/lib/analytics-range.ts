export type DateRangePreset = "24h" | "7d" | "30d" | "90d" | "custom"

export interface DateRange {
  preset: DateRangePreset
  start: Date
  end: Date
}

export function presetRange(preset: Exclude<DateRangePreset, "custom">): DateRange {
  const end = new Date()
  const start = new Date(end)
  if (preset === "24h") start.setHours(start.getHours() - 24)
  else if (preset === "7d") start.setDate(start.getDate() - 7)
  else if (preset === "30d") start.setDate(start.getDate() - 30)
  else start.setDate(start.getDate() - 90)
  return { preset, start, end }
}

export function toQueryParams(range: DateRange): { start_date: string; end_date: string } {
  return {
    start_date: range.start.toISOString(),
    end_date: range.end.toISOString(),
  }
}

export function formatBucketTick(value: string, bucket: string): string {
  const s = String(value)
  if (bucket === "hour") {
    const d = new Date(s.includes("T") ? s : `${s}T00:00:00`)
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric" })
  }
  if (bucket === "week") return s.slice(5, 10)
  return s.slice(5, 10)
}

export function presetLabel(preset: DateRangePreset): string {
  const labels: Record<DateRangePreset, string> = {
    "24h": "24h",
    "7d": "7d",
    "30d": "30d",
    "90d": "90d",
    custom: "Custom",
  }
  return labels[preset]
}
