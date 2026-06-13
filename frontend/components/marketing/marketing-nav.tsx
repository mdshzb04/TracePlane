"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { Menu, Moon, Sun, X, Github } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
import { TraceplaneIcon } from "@/components/brand/traceplane-icon"
import { GITHUB_REPO_URL, PRODUCT_NAME } from "@/lib/brand"
import { cn } from "@/lib/utils"
import { SectionLink } from "@/components/marketing/section-link"

const NAV_LINKS = [
  { href: "#sdk", label: "SDK", id: "sdk" },
  { href: "#architecture", label: "Architecture", id: "architecture" },
  { href: "#observability", label: "Observability", id: "observability" },
] as const

const NAV_OFFSET = 96

function getSectionsByScrollOrder() {
  return [...NAV_LINKS]
    .map((link) => ({ link, el: document.getElementById(link.id) }))
    .filter((s): s is { link: (typeof NAV_LINKS)[number]; el: HTMLElement } => Boolean(s.el))
    .sort((a, b) => a.el.offsetTop - b.el.offsetTop)
}

function resolveActiveSection(): string {
  const sections = getSectionsByScrollOrder()
  if (!sections.length) return ""

  const scrollLine = window.scrollY + NAV_OFFSET
  const firstTop = sections[0].el.offsetTop

  // Hero / top of page — no nav pill
  if (scrollLine < firstTop - 48) return ""

  let current = ""
  for (const { link, el } of sections) {
    if (el.offsetTop <= scrollLine) current = link.id
  }
  return current
}

function MarketingLogo() {
  return (
    <Link
      href="/"
      className="group inline-flex items-center gap-2.5 shrink-0 transition-transform duration-200 hover:scale-[1.02] active:scale-[0.98]"
    >
      <TraceplaneIcon size={30} className="transition-transform duration-300 group-hover:rotate-[-2deg]" />
      <span className="text-[17px] font-semibold tracking-[-0.02em] text-ink">{PRODUCT_NAME}</span>
    </Link>
  )
}

function NavLink({
  href,
  label,
  active,
  onClick,
}: {
  href: string
  label: string
  active: boolean
  onClick?: () => void
}) {
  return (
    <SectionLink
      href={href}
      onClick={onClick}
      className={cn(
        "relative px-3.5 py-1.5 text-[14px] font-medium tracking-[-0.01em] transition-all duration-200 rounded-full",
        active
          ? "text-ink bg-surface-2 shadow-[inset_0_0_0_1px_rgb(var(--tp-hairline))]"
          : "text-ink-subtle hover:text-ink hover:bg-surface-1/60 group"
      )}
    >
      {label}
      {!active && (
        <span className="absolute inset-x-3.5 -bottom-0.5 h-px scale-x-0 bg-primary/60 transition-transform duration-200 group-hover:scale-x-100" />
      )}
    </SectionLink>
  )
}

function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        "relative z-10 inline-flex items-center justify-center w-9 h-9 rounded-lg text-ink-subtle hover:text-ink hover:bg-surface-1/80 transition-all duration-200",
        className
      )}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
    >
      {theme === "dark" ? <Sun className="w-[18px] h-[18px]" /> : <Moon className="w-[18px] h-[18px]" />}
    </button>
  )
}

export function MarketingNav() {
  const [scrolled, setScrolled] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [activeSection, setActiveSection] = useState<string>("")
  const scrollLockRef = useRef<string | null>(null)

  const navigateToSection = useCallback((id: string) => {
    scrollLockRef.current = id
    setActiveSection(id)
    window.setTimeout(() => {
      if (scrollLockRef.current === id) scrollLockRef.current = null
    }, 900)
  }, [])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  useEffect(() => {
    const update = () => {
      if (scrollLockRef.current) {
        setActiveSection(scrollLockRef.current)
        return
      }
      setActiveSection(resolveActiveSection())
    }

    const onSectionNav = (e: Event) => {
      const id = (e as CustomEvent<{ id: string }>).detail?.id
      if (id && NAV_LINKS.some((l) => l.id === id)) navigateToSection(id)
    }

    update()
    window.addEventListener("scroll", update, { passive: true })
    window.addEventListener("hashchange", update)
    window.addEventListener("resize", update)
    window.addEventListener("sectionnav", onSectionNav)
    return () => {
      window.removeEventListener("scroll", update)
      window.removeEventListener("hashchange", update)
      window.removeEventListener("resize", update)
      window.removeEventListener("sectionnav", onSectionNav)
    }
  }, [navigateToSection])

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? "hidden" : ""
    return () => {
      document.body.style.overflow = ""
    }
  }, [drawerOpen])

  const closeDrawer = useCallback(() => setDrawerOpen(false), [])

  return (
    <>
      <header
        className={cn(
          "sticky top-0 z-50 transition-all duration-300 ease-out",
          scrolled
            ? "bg-canvas/75 dark:bg-canvas/80 backdrop-blur-xl border-b border-hairline shadow-[0_1px_0_0_rgb(var(--tp-hairline)/0.5),0_8px_32px_-8px_rgb(0_0_0/0.12)]"
            : "bg-transparent border-b border-transparent"
        )}
      >
        <div className="max-w-[1200px] mx-auto px-5 sm:px-6 lg:px-8 h-[72px] flex items-center">
          {/* Desktop: logo | centered nav | actions */}
          <div className="hidden lg:grid lg:grid-cols-[1fr_auto_1fr] lg:items-center lg:w-full">
            <div className="justify-self-start">
              <MarketingLogo />
            </div>

            <nav className="justify-self-center flex items-center gap-1">
              {NAV_LINKS.map((link) => (
                <NavLink
                  key={link.id}
                  href={link.href}
                  label={link.label}
                  active={activeSection === link.id}
                  onClick={() => navigateToSection(link.id)}
                />
              ))}
            </nav>

            <div className="justify-self-end flex items-center gap-2">
              <ThemeToggle />
              <Link
                href="/login"
                className="inline-flex items-center h-9 px-4 rounded-lg text-[14px] font-medium text-ink-subtle hover:text-ink hover:bg-surface-1/70 transition-all duration-200"
              >
                Sign In
              </Link>
              <a
                href={GITHUB_REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-ink-subtle hover:text-ink hover:bg-surface-1/70 transition-all duration-200"
                aria-label="GitHub"
              >
                <Github className="w-[18px] h-[18px]" />
              </a>
              <Link
                href="/login"
                className="inline-flex items-center h-9 px-4 rounded-lg text-[14px] font-medium bg-primary text-on-primary shadow-[0_0_0_1px_rgb(var(--tp-primary)/0.2),0_4px_20px_-4px_rgb(var(--tp-primary)/0.55)] hover:shadow-[0_0_0_1px_rgb(var(--tp-primary)/0.35),0_8px_28px_-4px_rgb(var(--tp-primary)/0.65)] hover:bg-primary-hover transition-all duration-250"
              >
                Get Started
              </Link>
            </div>
          </div>

          {/* Mobile */}
          <div className="flex lg:hidden items-center justify-between w-full gap-3">
            <MarketingLogo />
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="inline-flex items-center h-9 px-3.5 sm:px-4 rounded-lg text-[13px] sm:text-[14px] font-medium bg-primary text-on-primary shadow-[0_4px_18px_-4px_rgb(var(--tp-primary)/0.55)] hover:bg-primary-hover transition-all duration-200"
              >
                Get Started
              </Link>
              <button
                type="button"
                onClick={() => setDrawerOpen(true)}
                className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-ink-subtle hover:text-ink hover:bg-surface-1/80 transition-all duration-200"
                aria-label="Open menu"
              >
                <Menu className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile drawer */}
      <div
        className={cn(
          "fixed inset-0 z-[60] lg:hidden transition-opacity duration-300",
          drawerOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        aria-hidden={!drawerOpen}
      >
        <button
          type="button"
          className="absolute inset-0 bg-canvas/60 backdrop-blur-sm"
          onClick={closeDrawer}
          aria-label="Close menu"
        />
        <div
          className={cn(
            "absolute top-0 right-0 h-full w-[min(100%,320px)] bg-canvas border-l border-hairline shadow-[-12px_0_40px_rgb(0_0_0/0.15)] transition-transform duration-300 ease-out flex flex-col",
            drawerOpen ? "translate-x-0" : "translate-x-full"
          )}
        >
          <div className="flex items-center justify-between h-[72px] px-5 border-b border-hairline">
            <span className="text-[14px] font-medium text-ink-subtle">Menu</span>
            <button
              type="button"
              onClick={closeDrawer}
              className="inline-flex items-center justify-center w-9 h-9 rounded-lg text-ink-subtle hover:text-ink hover:bg-surface-1 transition-colors"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <nav className="flex flex-col gap-1 p-4">
            {NAV_LINKS.map((link) => (
              <SectionLink
                key={link.id}
                href={link.href}
                onClick={() => {
                  navigateToSection(link.id)
                  closeDrawer()
                }}
                className={cn(
                  "px-4 py-3 rounded-lg text-[15px] font-medium transition-colors duration-200",
                  activeSection === link.id
                    ? "text-ink bg-surface-2"
                    : "text-ink-subtle hover:text-ink hover:bg-surface-1"
                )}
              >
                {link.label}
              </SectionLink>
            ))}
          </nav>

          <div className="mt-auto p-4 border-t border-hairline space-y-2">
            <div className="flex items-center justify-between px-2 py-1">
              <span className="text-[13px] text-ink-subtle">Theme</span>
              <ThemeToggle />
            </div>
            <Link
              href="/login"
              onClick={closeDrawer}
              className="flex items-center justify-center w-full h-10 rounded-lg text-[14px] font-medium text-ink-subtle hover:text-ink border border-hairline hover:bg-surface-1 transition-all duration-200"
            >
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}
