"use client"

import { useEffect, useState } from "react"

const RECOVERY_KEY = "traceplane-style-recovery"

function stylesLoaded(): boolean {
  if (typeof window === "undefined") return true

  const htmlBg = getComputedStyle(document.documentElement).backgroundColor
  const bodyBg = getComputedStyle(document.body).backgroundColor
  const bodyColor = getComputedStyle(document.body).color
  const canvasLoaded =
    htmlBg === "rgb(1, 1, 2)" ||
    bodyBg === "rgb(1, 1, 2)" ||
    htmlBg === "rgb(255, 255, 255)" ||
    bodyBg === "rgb(255, 255, 255)" ||
    bodyColor === "rgb(247, 248, 248)" ||
    bodyColor === "rgb(17, 24, 39)"

  if (canvasLoaded) return true

  const nextStyles = Array.from(document.styleSheets).some((sheet) => {
    try {
      return Boolean(sheet.href?.includes("_next/static"))
    } catch {
      return false
    }
  })

  return nextStyles
}

function shouldRecoverFromError(message: string): boolean {
  const lower = message.toLowerCase()
  return (
    lower.includes("loading chunk") ||
    lower.includes("chunkloaderror") ||
    lower.includes("failed to fetch dynamically imported module") ||
    lower.includes("cannot find module")
  )
}

/**
 * Dev-only guard: auto-reloads once when CSS/chunks fail to load (stale .next cache).
 */
export function DevStyleRecovery() {
  const [showBanner, setShowBanner] = useState(false)

  useEffect(() => {
    if (process.env.NODE_ENV === "production") return

    function recover(reason: string) {
      const attempts = Number(sessionStorage.getItem(RECOVERY_KEY) || "0")
      if (attempts < 2) {
        sessionStorage.setItem(RECOVERY_KEY, String(attempts + 1))
        console.warn(`[dev] recovering from stale assets (${reason}) — hard reloading`)
        const url = new URL(window.location.href)
        url.searchParams.set("_cb", String(Date.now()))
        window.location.replace(url.toString())
        return
      }
      setShowBanner(true)
    }

    function probe() {
      if (document.readyState !== "complete") return
      if (!stylesLoaded()) recover("missing stylesheets")
    }

    const onError = (event: ErrorEvent) => {
      const target = event.target
      if (target instanceof HTMLLinkElement && target.rel === "stylesheet") {
        recover("stylesheet load error")
        return
      }
      if (target instanceof HTMLScriptElement && target.src.includes("_next")) {
        recover("script load error")
        return
      }
      if (event.message && shouldRecoverFromError(event.message)) {
        recover(event.message)
      }
    }

    const onRejection = (event: PromiseRejectionEvent) => {
      const reason = String(event.reason ?? "")
      if (shouldRecoverFromError(reason)) recover(reason)
    }

    const timer = window.setTimeout(probe, 700)
    window.addEventListener("load", probe)
    window.addEventListener("error", onError, true)
    window.addEventListener("unhandledrejection", onRejection)

    return () => {
      window.clearTimeout(timer)
      window.removeEventListener("load", probe)
      window.removeEventListener("error", onError, true)
      window.removeEventListener("unhandledrejection", onRejection)
    }
  }, [])

  useEffect(() => {
    if (process.env.NODE_ENV === "production") return
    if (stylesLoaded()) sessionStorage.removeItem(RECOVERY_KEY)
  }, [])

  if (!showBanner) return null

  return (
    <div className="fixed inset-x-0 top-0 z-[9999] border-b border-amber-500/40 bg-amber-950 px-4 py-3 text-center text-sm text-amber-100">
      Styles failed to load (stale dev cache). Run{" "}
      <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono">npm run dev:clean</code> in{" "}
      <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono">frontend/</code>, or stop using{" "}
      <code className="rounded bg-black/40 px-1.5 py-0.5 font-mono">npx next dev</code> directly.
    </div>
  )
}
