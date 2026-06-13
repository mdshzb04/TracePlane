"use client"

import {
  LayoutDashboard,
  GitBranch,
  BarChart3,
  Bell,
  Bot,
  Settings,
} from "lucide-react"

/** Dashboard preview — theme-aware, fewer metrics. */
export function MarketingDashboardPreview() {
  return (
    <div className="rounded-xl border border-hairline bg-canvas shadow-[0_8px_30px_rgb(0_0_0/0.08)] overflow-hidden">
      <div className="flex min-h-[340px]">
        <aside className="hidden sm:flex w-44 shrink-0 flex-col border-r border-hairline bg-surface-1">
          <div className="h-11 px-3 flex items-center border-b border-hairline">
            <span className="text-[13px] font-medium text-ink-muted">Workspace</span>
          </div>
          <nav className="p-2 space-y-0.5 text-[13px]">
            {[
              { icon: LayoutDashboard, label: "Dashboard", active: true },
              { icon: GitBranch, label: "Traces" },
              { icon: Bot, label: "Agents" },
              { icon: BarChart3, label: "Analytics" },
              { icon: Bell, label: "Alerts" },
              { icon: Settings, label: "Settings" },
            ].map((item) => (
              <div
                key={item.label}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md ${
                  item.active ? "bg-canvas text-ink font-medium shadow-sm" : "text-ink-subtle"
                }`}
              >
                <item.icon className="w-3.5 h-3.5 shrink-0" />
                {item.label}
              </div>
            ))}
          </nav>
        </aside>

        <div className="flex-1 p-4 sm:p-5 min-w-0">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h3 className="text-[15px] font-semibold text-ink">Dashboard</h3>
            <div className="flex items-center gap-1 text-[12px]">
              {["24H", "7D", "1M"].map((r, i) => (
                <span
                  key={r}
                  className={`px-2 py-1 rounded-md ${
                    i === 2 ? "bg-primary text-on-primary" : "text-ink-subtle"
                  }`}
                >
                  {r}
                </span>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-3">
            {[
              { label: "Traces", value: "12,847", sub: "last 30 days", glow: "dash-metric--purple" },
              { label: "Cost", value: "$142.50", sub: "estimated", glow: "dash-metric--emerald" },
              { label: "Latency", value: "1.2s", sub: "p50", glow: "dash-metric--blue" },
              { label: "Success", value: "99.2%", sub: "rate", glow: "dash-metric--amber" },
            ].map((m) => (
              <div
                key={m.label}
                className={`dash-metric ${m.glow} rounded-lg border border-hairline bg-surface-1 p-3 cursor-default`}
              >
                <p className="text-[11px] text-ink-subtle uppercase tracking-wide">{m.label}</p>
                <p className="text-[20px] font-semibold text-ink mt-1 leading-none">{m.value}</p>
                <p className="text-[11px] text-ink-tertiary mt-1">{m.sub}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="dash-metric dash-metric--purple rounded-lg border border-hairline bg-surface-1 p-3 h-28 flex flex-col justify-between cursor-default">
              <p className="text-[12px] font-medium text-ink-muted">Requests over time</p>
              <div className="flex items-end gap-1 h-14">
                {[40, 55, 35, 70, 50, 65, 45, 80, 60, 75].map((h, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-sm bg-primary/70"
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>
            <div className="dash-metric dash-metric--blue rounded-lg border border-hairline bg-surface-1 p-3 h-28 cursor-default">
              <p className="text-[12px] font-medium text-ink-muted mb-2">Top models</p>
              <ul className="space-y-1.5 text-[12px] text-ink-subtle">
                <li className="flex justify-between"><span>gpt-4o-mini</span><span>6,241</span></li>
                <li className="flex justify-between"><span>claude-3-5-haiku</span><span>3,102</span></li>
                <li className="flex justify-between"><span>gemini-2.0-flash</span><span>1,890</span></li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
