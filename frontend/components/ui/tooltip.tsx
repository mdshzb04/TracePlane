"use client"

import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { cn } from "@/lib/utils"

export function TooltipProvider({
  children,
  delayDuration = 200,
}: {
  children: React.ReactNode
  delayDuration?: number
}) {
  return (
    <TooltipPrimitive.Provider delayDuration={delayDuration}>
      {children}
    </TooltipPrimitive.Provider>
  )
}

export function InfoTooltip({
  content,
  children,
  side = "top",
  className,
}: {
  content: React.ReactNode
  children: React.ReactNode
  side?: "top" | "right" | "bottom" | "left"
  className?: string
}) {
  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>
        <span className={cn("inline-flex", className)}>{children}</span>
      </TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          side={side}
          sideOffset={6}
          className="z-50 max-w-xs rounded-md border border-hairline bg-surface-1 px-2.5 py-1.5 text-caption text-ink shadow-lg"
        >
          {content}
          <TooltipPrimitive.Arrow className="fill-surface-1" />
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  )
}
