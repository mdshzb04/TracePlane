"use client"

import { PROVIDER_BRANDS, UI_PROVIDER_IDS } from "@/lib/provider-brands"

/** Monochrome provider logos with hover label — used in SDK section. */
export function ProviderLogoStrip({ className }: { className?: string }) {
  return (
    <div
      className={
        className ??
        "mt-8 mb-8 flex flex-wrap items-center justify-center gap-x-7 gap-y-5 sm:gap-x-9"
      }
    >
      {UI_PROVIDER_IDS.map((id) => (
        <div
          key={id}
          className="social-proof-logo group flex flex-col items-center gap-2"
          title={PROVIDER_BRANDS[id].name}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={PROVIDER_BRANDS[id].logo}
            alt={PROVIDER_BRANDS[id].name}
            width={40}
            height={40}
            className="h-10 w-10 rounded-full object-cover transition-transform duration-[280ms] ease-out group-hover:scale-105"
          />
          <span className="text-[11px] text-ink-tertiary opacity-0 group-hover:opacity-100 transition-opacity duration-[280ms] pointer-events-none">
            {PROVIDER_BRANDS[id].name}
          </span>
        </div>
      ))}
    </div>
  )
}
