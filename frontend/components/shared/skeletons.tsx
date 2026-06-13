import { cn } from "@/lib/utils"

function Bone({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-md bg-surface-3/80", className)} />
}

export function MetricSkeletonGrid({ count = 4 }: { count?: number }) {
  return (
    <div className={cn("grid gap-3 mb-6", count === 6 ? "grid-cols-2 sm:grid-cols-3 lg:grid-cols-6" : "grid-cols-2 md:grid-cols-4")}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="panel-lift rounded-lg p-4 space-y-2">
          <Bone className="h-3 w-20" />
          <Bone className="h-7 w-24" />
        </div>
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="panel-lift rounded-lg overflow-hidden">
      <div className="border-b border-hairline px-4 py-3 flex gap-4">
        {Array.from({ length: cols }).map((_, i) => (
          <Bone key={i} className="h-3 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="border-b border-hairline/60 px-4 py-3 flex gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <Bone key={c} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

export function ChartSkeletonGrid({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="panel-lift rounded-lg p-4 h-[220px] flex flex-col gap-3">
          <Bone className="h-4 w-32" />
          <Bone className="flex-1 w-full" />
        </div>
      ))}
    </div>
  )
}
