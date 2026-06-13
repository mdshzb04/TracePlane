"use client"

import { useEffect, useState } from "react"
import { Menu, LogOut, Moon, Sun } from "lucide-react"
import { authService } from "@/services/api"
import { User } from "@/types"
import { useTheme } from "@/components/theme-provider"

interface TopNavProps {
  onMenuClick: () => void
}

export function TopNav({ onMenuClick }: TopNavProps) {
  const [user, setUser] = useState<User | null>(null)
  const { theme, toggleTheme } = useTheme()

  useEffect(() => {
    authService.me().then(setUser).catch(() => setUser(null))
  }, [])

  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : user?.email?.[0]?.toUpperCase() ?? "A"

  return (
    <header className="h-14 bg-canvas/90 backdrop-blur-md border-b border-hairline flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden text-ink-subtle hover:text-ink p-1.5 rounded-md hover:bg-surface-1"
          aria-label="Open navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleTheme}
          className="text-ink-subtle hover:text-ink p-1.5 rounded-md hover:bg-surface-1 transition-colors"
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Light mode" : "Dark mode"}
        >
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <button
          onClick={() => authService.logout()}
          className="text-ink-subtle hover:text-ink p-1.5 rounded-md hover:bg-surface-1 transition-colors"
          aria-label="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
        <div className="w-8 h-8 rounded-full bg-surface-2 border border-hairline flex items-center justify-center" title={user?.email}>
          <span className="text-caption text-ink-muted font-medium">{initials}</span>
        </div>
      </div>
    </header>
  )
}
