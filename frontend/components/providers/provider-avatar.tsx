"use client"

import { memo, useState } from "react"
import { Boxes } from "lucide-react"
import { PROVIDER_LOGOS, type UiProviderId } from "@/lib/provider-brands"

type ProviderAvatarProps = {
  providerId: string
  name: string
  size?: number
}

/** Circular provider logo — PNG assets are pre-masked to a circle. */
export const ProviderAvatar = memo(function ProviderAvatar({
  providerId,
  name,
  size = 52,
}: ProviderAvatarProps) {
  const [failed, setFailed] = useState(false)
  const logo = PROVIDER_LOGOS[providerId as UiProviderId]

  return (
    <div
      className="shrink-0 rounded-full overflow-hidden"
      style={{ width: size, height: size }}
      aria-hidden
    >
      {logo && !failed ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={logo}
          alt=""
          className="h-full w-full object-cover"
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="h-full w-full flex items-center justify-center">
          <Boxes className="w-5 h-5 text-ink-tertiary" strokeWidth={1.75} />
        </div>
      )}
      <span className="sr-only">{name}</span>
    </div>
  )
})
