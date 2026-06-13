"use client"

import { Check, Circle } from "lucide-react"
import { cn } from "@/lib/utils"

type ProgressItem = {
  label: string
  complete: boolean
}

export function SdkSetupProgress({ items }: { items: ProgressItem[] }) {
  return (
    <div className="panel-lift rounded-lg p-4 sm:p-5">
      <h2 className="text-body-sm font-medium text-ink mb-4">Setup Progress</h2>
      <ul className="space-y-3">
        {items.map((item) => (
          <li key={item.label} className="flex items-center gap-3">
            {item.complete ? (
              <span
                className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-success/40 bg-success/15 text-success"
                aria-hidden
              >
                <Check className="w-3 h-3" strokeWidth={2.5} />
              </span>
            ) : (
              <Circle className="w-5 h-5 shrink-0 text-ink-tertiary" strokeWidth={1.75} aria-hidden />
            )}
            <span className={cn("text-body-sm", item.complete ? "text-ink" : "text-ink-subtle")}>
              {item.label}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
