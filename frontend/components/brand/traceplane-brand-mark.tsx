import Link from "next/link"
import { TraceplaneIcon } from "@/components/brand/traceplane-icon"
import { PRODUCT_NAME } from "@/lib/brand"
import { cn } from "@/lib/utils"

type TraceplaneBrandMarkProps = {
  href?: string | null
  iconSize?: number
  className?: string
  labelClassName?: string
}

/** Landing-page logo treatment — icon + wordmark, shared in marketing and app shell. */
export function TraceplaneBrandMark({
  href = "/dashboard",
  iconSize = 30,
  className,
  labelClassName,
}: TraceplaneBrandMarkProps) {
  const content = (
    <>
      <TraceplaneIcon
        size={iconSize}
        className="transition-transform duration-300 group-hover:rotate-[-2deg]"
      />
      <span
        className={cn(
          "text-[17px] font-semibold tracking-[-0.02em] text-ink",
          labelClassName
        )}
      >
        {PRODUCT_NAME}
      </span>
    </>
  )

  if (!href) {
    return <span className={cn("inline-flex items-center gap-2.5 shrink-0", className)}>{content}</span>
  }

  return (
    <Link
      href={href}
      prefetch
      className={cn(
        "group inline-flex items-center gap-2.5 shrink-0 transition-transform duration-200 hover:scale-[1.02] active:scale-[0.98] hover:opacity-90",
        className
      )}
    >
      {content}
    </Link>
  )
}
