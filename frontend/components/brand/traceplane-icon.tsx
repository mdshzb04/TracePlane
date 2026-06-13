import { cn } from "@/lib/utils"

type TraceplaneIconProps = {
  className?: string
  size?: number
}

/** Traceplane icon mark — crisp SVG for nav and compact placements. */
export function TraceplaneIcon({ className, size = 32 }: TraceplaneIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("shrink-0", className)}
      aria-hidden
    >
      <path
        d="M5 21.5L16 27.5L27 21.5L16 15.5L5 21.5Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
        className="text-primary/90"
      />
      <path
        d="M5 15.5L16 21.5L27 15.5L16 9.5L5 15.5Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
        className="text-primary"
      />
      <path
        d="M5 9.5L16 15.5L27 9.5L16 3.5L5 9.5Z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
        className="text-primary/80"
      />
      <circle cx="11" cy="17" r="1.6" fill="currentColor" className="text-ink" />
      <path
        d="M11.8 16.2L21.5 9.2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        className="text-primary"
      />
      <path
        d="M19.5 9.2H21.5V11.2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-primary"
      />
    </svg>
  )
}
