/** Browser: same-origin proxy via Next.js rewrite (/api → backend). SSR: direct backend URL. */
export const API_BASE_URL =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "/api"
    : process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1"

export const STATUS_COLORS: Record<string, string> = {
  active: "bg-success/20 text-success",
  inactive: "bg-ink-tertiary/20 text-ink-tertiary",
  triggered: "bg-warning/20 text-warning",
  info: "bg-primary/20 text-primary",
  warning: "bg-warning/20 text-warning",
  critical: "bg-danger/20 text-danger",
  deprecated: "bg-warning/20 text-warning",
  running: "bg-primary/20 text-primary",
  success: "bg-success/20 text-success",
  failed: "bg-danger/20 text-danger",
  timeout: "bg-warning/20 text-warning",
  cancelled: "bg-ink-tertiary/20 text-ink-tertiary",
}

export const ROLE_COLORS: Record<string, string> = {
  admin: "bg-primary/20 text-primary",
  developer: "bg-success/20 text-success",
  viewer: "bg-ink-tertiary/20 text-ink-tertiary",
}
