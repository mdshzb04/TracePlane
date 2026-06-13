"use client"

import Link from "next/link"
import { useState } from "react"
import { PRODUCT_ICON, PRODUCT_LOGO, PRODUCT_LOGO_ASPECT, PRODUCT_LOGO_LIGHT, PRODUCT_NAME } from "@/lib/brand"
import { cn } from "@/lib/utils"

type TraceplaneLogoProps = {
  href?: string | null
  height?: number
  className?: string
  priority?: boolean
  variant?: "dark" | "light"
}

/** Traceplane horizontal wordmark — plain img so cache-busted paths load reliably. */
export function TraceplaneLogo({
  href = "/dashboard",
  height = 32,
  className,
  priority = false,
  variant = "dark",
}: TraceplaneLogoProps) {
  const [failed, setFailed] = useState(false)
  const width = Math.round(height * PRODUCT_LOGO_ASPECT)
  const src = variant === "light" ? PRODUCT_LOGO_LIGHT : PRODUCT_LOGO

  const fallback = (
    <span className="inline-flex items-center gap-2 shrink-0">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={PRODUCT_ICON} alt="" width={height} height={height} className="rounded-sm object-contain" />
      <span
        className={cn(
          "text-[15px] font-semibold tracking-tight",
          variant === "light" ? "text-[#111827]" : "text-ink"
        )}
      >
        {PRODUCT_NAME}
      </span>
    </span>
  )

  const img = failed ? (
    fallback
  ) : (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={PRODUCT_NAME}
      width={width}
      height={height}
      className={cn("block shrink-0 object-contain object-left", className)}
      style={{ height, width: "auto", maxHeight: height }}
      decoding="async"
      loading={priority ? "eager" : "lazy"}
      onError={() => setFailed(true)}
    />
  )

  if (!href) return <span className="inline-flex items-center shrink-0">{img}</span>

  return (
    <Link href={href} className="inline-flex items-center shrink-0 hover:opacity-90 transition-opacity">
      {img}
    </Link>
  )
}
