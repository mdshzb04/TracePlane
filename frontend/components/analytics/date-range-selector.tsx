"use client"

import { cn } from "@/lib/utils"
import { DateRange, DateRangePreset, presetLabel } from "@/lib/analytics-range"

const PRESETS: DateRangePreset[] = ["24h", "7d", "30d", "90d"]

export function DateRangeSelector({
  range,
  onChange,
}: {
  range: DateRange
  onChange: (range: DateRange) => void
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="inline-flex rounded-lg border border-hairline bg-surface-1 p-0.5">
        {PRESETS.map((preset) => (
          <button
            key={preset}
            type="button"
            onClick={() => {
              const end = new Date()
              const start = new Date(end)
              if (preset === "24h") start.setHours(start.getHours() - 24)
              else if (preset === "7d") start.setDate(start.getDate() - 7)
              else if (preset === "30d") start.setDate(start.getDate() - 30)
              else start.setDate(start.getDate() - 90)
              onChange({ preset, start, end })
            }}
            className={cn(
              "px-3 py-1.5 text-caption font-medium rounded-md transition-colors",
              range.preset === preset
                ? "bg-primary text-on-primary"
                : "text-ink-subtle hover:text-ink hover:bg-surface-2"
            )}
          >
            {presetLabel(preset)}
          </button>
        ))}
      </div>
    </div>
  )
}
