"use client"

import type { MouseEvent, ReactNode } from "react"
import { scrollToSectionWithRetry } from "@/lib/scroll-to-section"

type SectionLinkProps = {
  href: string
  children: ReactNode
  className?: string
  onClick?: () => void
}

/** Same-page section link with reliable smooth scroll (works from footer/nav). */
export function SectionLink({ href, children, className, onClick }: SectionLinkProps) {
  const handleClick = async (e: MouseEvent<HTMLAnchorElement>) => {
    if (!href.startsWith("#")) return

    e.preventDefault()
    const id = href.slice(1)
    const scrolled = await scrollToSectionWithRetry(id)

    if (scrolled) {
      window.history.pushState(null, "", href)
      window.dispatchEvent(new HashChangeEvent("hashchange"))
      window.dispatchEvent(new CustomEvent("sectionnav", { detail: { id } }))
    } else {
      window.location.hash = id
    }

    onClick?.()
  }

  return (
    <a href={href} onClick={handleClick} className={className}>
      {children}
    </a>
  )
}
