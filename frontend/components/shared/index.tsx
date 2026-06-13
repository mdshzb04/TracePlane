"use client"

import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { STATUS_COLORS } from "@/lib/constants"

interface StatusBadgeProps {
  status: string
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const normalized = status?.toLowerCase() ?? ""

  if (normalized === "success") {
    return (
      <span
        className={cn("inline-flex items-center justify-center", className)}
        title="Success"
        aria-label="Success"
      >
        <Check className="w-4 h-4 text-success" strokeWidth={2.5} />
      </span>
    )
  }

  const colorClass = STATUS_COLORS[normalized] || "bg-ink-tertiary/20 text-ink-tertiary"
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-pill px-2 py-0.5 text-caption font-medium",
        colorClass,
        className
      )}
    >
      {status}
    </span>
  )
}

interface PageHeaderProps {
  title: string
  subtitle?: string
  children?: React.ReactNode
}

export function PageHeader({ title, subtitle, children }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="section-title">{title}</h1>
        {subtitle && <p className="body-text mt-1">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  )
}

export function LoadingState() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-ink-subtle text-body">Loading...</div>
    </div>
  )
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-ink-subtle text-body-sm">{message}</div>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <div className="text-danger text-body">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary">
          Retry
        </button>
      )}
    </div>
  )
}

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("card p-5", className)}>
      {children}
    </div>
  )
}

export function Table({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-left border-collapse">
        {children}
      </table>
    </div>
  )
}

export function TableHead({ children }: { children: React.ReactNode }) {
  return (
    <thead>
      <tr className="border-b border-hairline">
        {children}
      </tr>
    </thead>
  )
}

export function TableHeader({ children, className }: { children?: React.ReactNode; className?: string }) {
  return (
    <th className={cn("px-4 py-3 text-caption font-medium text-ink-subtle uppercase tracking-wide", className)}>
      {children}
    </th>
  )
}

export function TableRow({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <tr className={cn("border-b border-hairline hover:bg-surface-2/50 transition-colors", className)}>
      {children}
    </tr>
  )
}

export function TableCell({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={cn("px-4 py-3 text-body-sm text-ink-muted", className)}>
      {children}
    </td>
  )
}

export function Modal({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-surface-1 border border-hairline rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-hairline">
          <h3 className="text-card-title font-medium text-ink">{title}</h3>
          <button onClick={onClose} className="text-ink-subtle hover:text-ink">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

export function Input({
  label,
  error,
  className,
  ...props
}: {
  label?: string
  error?: string
} & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className={className}>
      {label && <label className="block text-body-sm text-ink-muted mb-1.5">{label}</label>}
      <input className="input w-full" {...props} />
      {error && <p className="text-danger text-caption mt-1">{error}</p>}
    </div>
  )
}

export function TextArea({
  label,
  error,
  className,
  ...props
}: {
  label?: string
  error?: string
} & React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <div className={className}>
      {label && <label className="block text-body-sm text-ink-muted mb-1.5">{label}</label>}
      <textarea className="input w-full min-h-[100px] resize-y" {...props} />
      {error && <p className="text-danger text-caption mt-1">{error}</p>}
    </div>
  )
}

export function Select({
  label,
  options,
  className,
  ...props
}: {
  label?: string
  options: { value: string; label: string }[]
} & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className={className}>
      {label && <label className="block text-body-sm text-ink-muted mb-1.5">{label}</label>}
      <select className="input w-full appearance-none cursor-pointer" {...props}>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export { MetricSkeletonGrid, TableSkeleton, ChartSkeletonGrid } from "./skeletons"

export function Badge({
  children,
  variant = "default",
}: {
  children: React.ReactNode
  variant?: "default" | "primary" | "success" | "danger" | "warning"
}) {
  const variants = {
    default: "bg-surface-2 text-ink-muted",
    primary: "bg-primary/20 text-primary",
    success: "bg-success/20 text-success",
    danger: "bg-danger/20 text-danger",
    warning: "bg-warning/20 text-warning",
  }
  return (
    <span className={`inline-flex items-center rounded-pill px-2 py-0.5 text-caption font-medium ${variants[variant]}`}>
      {children}
    </span>
  )
}