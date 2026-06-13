"use client"

import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

export function CopyToast({ message, visible }: { message: string; visible: boolean }) {
  return (
    <p
      className={cn(
        "text-caption text-success inline-flex items-center gap-1.5 transition-all duration-200",
        visible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-0.5 pointer-events-none h-0 overflow-hidden"
      )}
      role="status"
      aria-live="polite"
    >
      <Check className="w-3.5 h-3.5 shrink-0" strokeWidth={2.5} />
      {message}
    </p>
  )
}
