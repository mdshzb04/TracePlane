import { ExecutionEvent, TraceEvent } from "@/types"

type TimelineEvent = ExecutionEvent | TraceEvent

const EVENT_LABELS: Record<string, string> = {
  "execution.started": "Execution started",
  "model.call.started": "LLM call started",
  "model.call.completed": "LLM call completed",
  "tool.invoked": "Tool invoked",
  "tool.completed": "Tool completed",
  "trigger.received": "Trigger received",
  "router.evaluated": "Router evaluated",
  "output.generated": "Output generated",
  "execution.completed": "Execution completed",
  "execution.failed": "Execution failed",
  "execution.timeout": "Execution timed out",
}

export function ExecutionTimeline({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return <p className="caption-text">No events recorded for this execution</p>
  }

  return (
    <div className="relative border-l border-hairline ml-3 space-y-4">
      {events.map((event) => (
        <div key={event.id} className="relative pl-6">
          <div className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full bg-primary border-2 border-canvas" />
          <div className="flex items-center gap-3 mb-1">
            <span className="text-body-sm font-medium text-ink">
              {EVENT_LABELS[event.event_type] || event.event_type}
            </span>
            <span className="caption-text">{new Date(event.timestamp).toLocaleString()}</span>
          </div>
          {event.event_data && Object.keys(event.event_data).length > 0 && (
            <pre className="mono-text text-caption text-ink-tertiary bg-surface-2 rounded p-2 overflow-auto max-h-32">
              {JSON.stringify(event.event_data, null, 2)}
            </pre>
          )}
        </div>
      ))}
    </div>
  )
}
