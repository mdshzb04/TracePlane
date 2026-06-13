import Link from "next/link"
import { TraceplaneIcon } from "@/components/brand/traceplane-icon"
import { PRODUCT_NAME } from "@/lib/brand"

export function MarketingFooter() {
  return (
    <footer className="marketing-footer w-full border-t border-hairline bg-canvas">
      <div className="marketing-footer-glow" aria-hidden />

      <div className="relative max-w-[1200px] mx-auto px-5 sm:px-6 lg:px-8 py-16 sm:py-[4.5rem]">
        <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex flex-col gap-3.5">
            <Link
              href="/"
              className="inline-flex items-center gap-3 w-fit hover:opacity-90 transition-opacity duration-200"
            >
              <TraceplaneIcon size={28} />
              <span className="text-[16px] font-semibold tracking-tight text-ink">{PRODUCT_NAME}</span>
            </Link>
            <p className="text-[13px] text-ink-muted leading-relaxed max-w-[260px]">
              Production observability for AI agents
            </p>
          </div>

          <div className="flex flex-col gap-2 sm:items-end sm:text-right">
            <p className="text-[13px] text-ink-subtle">© 2026 Traceplane</p>
            <p className="text-[13px] text-ink-muted tracking-wide">Trace · Monitor · Optimize</p>
          </div>
        </div>
      </div>
    </footer>
  )
}
