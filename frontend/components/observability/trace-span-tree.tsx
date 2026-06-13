"use client"

import { useState } from "react"
import { ChevronDown, ChevronRight, Cpu, Wrench, AlertCircle, Layers } from "lucide-react"
import { TraceSpanNode } from "@/types"
import { CostDisplay } from "./cost-badge"

const SPAN_ICONS: Record<string, typeof Layers> = {
  root: Layers,
  llm: Cpu,
  tool: Wrench,
  error: AlertCircle,
  custom: Layers,
}

function SpanRow({ span, depth = 0 }: { span: TraceSpanNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 2)
  const Icon = SPAN_ICONS[span.span_type] || Layers
  const hasChildren = span.children.length > 0

  return (
    <div>
      <button
        type="button"
        onClick={() => hasChildren && setOpen(!open)}
        className="w-full flex items-center gap-2 py-2 px-2 rounded-md hover:bg-surface-2 text-left"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {hasChildren ? (
          open ? <ChevronDown className="w-3.5 h-3.5 text-ink-subtle shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-ink-subtle shrink-0" />
        ) : (
          <span className="w-3.5" />
        )}
        <Icon className={`w-3.5 h-3.5 shrink-0 ${span.span_type === "error" ? "text-warning" : "text-primary"}`} />
        <span className="text-body-sm text-ink flex-1 truncate">{span.name}</span>
        <span className="caption-text text-ink-tertiary">{span.span_type}</span>
        {span.latency_ms != null && <span className="caption-text text-ink-muted">{span.latency_ms}ms</span>}
        {span.estimated_cost != null && span.estimated_cost > 0 && (
          <span className="caption-text text-success"><CostDisplay value={span.estimated_cost} /></span>
        )}
      </button>
      {open && span.children.map((child) => (
        <SpanRow key={child.id} span={child} depth={depth + 1} />
      ))}
    </div>
  )
}

export function TraceSpanTree({ spans }: { spans: TraceSpanNode[] }) {
  if (!spans.length) {
    return <p className="caption-text text-ink-tertiary py-4 text-center">No spans recorded</p>
  }
  return (
    <div className="border border-hairline rounded-lg overflow-hidden">
      {spans.map((span) => (
        <SpanRow key={span.id} span={span} />
      ))}
    </div>
  )
}
