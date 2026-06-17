"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Bot,
  BarChart3,
  GitBranch,
  Settings,
  X,
  Wrench,
  Key,
  LayoutDashboard,
  Bell,
  Code2,
  Plug,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { TraceplaneBrandMark } from "@/components/brand/traceplane-brand-mark"

const navGroups = [
  {
    label: "Overview",
    items: [{ href: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Observe",
    items: [
      { href: "/agents", label: "Agents", icon: Bot },
      { href: "/traces", label: "Trace Explorer", icon: GitBranch },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
    ],
  },
  {
    label: "Investigate",
    items: [
      { href: "/tools", label: "Tool Analytics", icon: Wrench },
      { href: "/alerts", label: "Alerts", icon: Bell },
    ],
  },
  {
    label: "Administration",
    items: [
      { href: "/sdk", label: "SDK", icon: Code2 },
      { href: "/settings/providers", label: "Providers", icon: Plug },
      { href: "/settings/api-keys", label: "API Keys", icon: Key },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
]

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname()

  return (
    <>
      <div
        className={cn("fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden", open ? "block" : "hidden")}
        onClick={onClose}
      />
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 h-full w-60 bg-surface-1 border-r border-hairline",
          "transform transition-transform duration-200 ease-out lg:translate-x-0 lg:static lg:z-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between h-14 px-4 border-b border-hairline bg-canvas">
          <TraceplaneBrandMark href="/dashboard" iconSize={30} />
          <button onClick={onClose} className="lg:hidden text-ink-subtle hover:text-ink" aria-label="Close menu">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-3 space-y-5 overflow-y-auto h-[calc(100%-3.5rem)]">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="px-3 mb-1.5 text-caption text-ink-tertiary uppercase tracking-wider">{group.label}</p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/settings" && pathname?.startsWith(item.href + "/"))
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-md text-body-sm transition-all duration-150",
                        isActive
                          ? "bg-surface-2 text-ink font-medium border border-hairline"
                          : "text-ink-subtle hover:text-ink hover:bg-surface-2/60"
                      )}
                    >
                      <item.icon className={cn("w-4 h-4", isActive && "text-primary")} />
                      {item.label}
                    </Link>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>
    </>
  )
}
