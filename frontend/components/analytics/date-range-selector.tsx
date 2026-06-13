"use client"

import { cn } from "@/lib/utils"
import { DateRange, DateRangePreset, presetLabel } from "@/lib/analytics-range"

const PRESETS: DateRangePreset[] = ["24h", "7d", "30d", "90d", "custom"]

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
              if (preset === "custom") {
                onChange({ ...range, preset: "custom" })
                return
              }
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
      {range.preset === "custom" && (
        <div className="flex items-center gap-2">
          <input
            type="datetime-local"
            value={toLocalInput(range.start)}
            onChange={(e) =>
              onChange({ ...range, start: new Date(e.target.value), preset: "custom" })
            }
            className="rounded-md border border-hairline bg-surface-1 px-2 py-1.5 text-caption text-ink"
          />
          <span className="text-ink-tertiary text-caption">→</span>
          <input
            type="datetime-local"
            value={toLocalInput(range.end)}
            onChange={(e) =>
              onChange({ ...range, end: new Date(e.target.value), preset: "custom" })
            }
            className="rounded-md border border-hairline bg-surface-1 px-2 py-1.5 text-caption text-ink"
          />
        </div>
      )}
    </div>
  )
}

function toLocalInput(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
