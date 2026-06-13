"use client"

import { useEffect } from "react"
import { scrollToSectionWithRetry } from "@/lib/scroll-to-section"
import {
  MarketingNav,
  MarketingHero,
  FeatureGrid,
  MarketingFooter,
  MarketingWorkflow,
} from "@/components/marketing"
import { ProviderShowcase } from "@/components/marketing/provider-showcase"

/** Client boundary for landing page — keeps SDK tabs and theme toggle interactive. */
export function MarketingLandingPage() {
  useEffect(() => {
    const scrollToHash = () => {
      const id = window.location.hash.replace("#", "")
      if (!id) return
      void scrollToSectionWithRetry(id)
    }

    // Defer so section layout (incl. client-mounted blocks) is ready
    const t = window.setTimeout(scrollToHash, 50)
    window.addEventListener("hashchange", scrollToHash)
    return () => {
      window.clearTimeout(t)
      window.removeEventListener("hashchange", scrollToHash)
    }
  }, [])

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <MarketingNav />
      <main>
        <MarketingHero />
        <FeatureGrid />
        <ProviderShowcase />
        <div id="architecture" className="scroll-mt-24">
          <MarketingWorkflow />
        </div>
      </main>
      <MarketingFooter />
    </div>
  )
}
