"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { motion, useMotionValue } from "framer-motion"
import { Code2, Cloud, BarChart3 } from "lucide-react"
import { TraceplaneIcon } from "@/components/brand/traceplane-icon"
import { cn } from "@/lib/utils"

const PURPLE = "#8B5CF6"
const INDIGO = "#6366F1"

const STEPS = [
  {
    step: "01",
    icon: Code2,
    label: "Application",
    detail: "Instrument with one SDK call",
    role: "entry" as const,
  },
  {
    step: "02",
    icon: TraceplaneIcon,
    label: "Traceplane SDK",
    detail: "Captures traces, tokens, and cost",
    isLogo: true,
    role: "core" as const,
  },
  {
    step: "03",
    icon: Cloud,
    label: "Traceplane Engine",
    detail: "Ingests and processes telemetry",
    role: "core" as const,
  },
  {
    step: "04",
    icon: BarChart3,
    label: "Observability",
    detail: "Dashboards, alerts, and insights",
    role: "destination" as const,
  },
] as const

const OBS_EVENTS = [
  "Trace Captured",
  "Latency Measured",
  "Cost Recorded",
  "Success Rate Updated",
] as const

const CENTERS = [0.125, 0.375, 0.625, 0.875] as const

const TRAVEL_MS = 5400
const EVENT_STEP_MS = 420
const RIPPLE_MS = 900

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms))

async function sleepPausable(
  ms: number,
  isPaused: () => boolean,
  isCancelled: () => boolean,
) {
  const start = performance.now()
  let pausedMs = 0
  let pauseStart = 0

  while (true) {
    if (isCancelled()) return
    if (isPaused()) {
      if (!pauseStart) pauseStart = performance.now()
      await sleep(80)
      continue
    }
    if (pauseStart) {
      pausedMs += performance.now() - pauseStart
      pauseStart = 0
    }
    if (performance.now() - start - pausedMs >= ms) return
    await sleep(40)
  }
}

function easeInOut(t: number) {
  return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2
}

function segmentIntensity(segIndex: number, progress: number) {
  const norm = Math.min(progress / 0.75, 1)
  const start = segIndex * 0.25
  const end = (segIndex + 1) * 0.25
  if (norm >= end) return 1
  if (norm <= start) return 0.14
  return 0.14 + 0.86 * ((norm - start) / 0.25)
}

function isSegmentHighlighted(segIndex: number, hovered: number | null) {
  if (hovered === null) return false
  return segIndex === hovered - 1 || segIndex === hovered
}

function animateProgress(
  motionVal: ReturnType<typeof useMotionValue<number>>,
  target: number,
  durationMs: number,
  isPaused: () => boolean,
  isCancelled: () => boolean,
) {
  const from = motionVal.get()
  const delta = target - from

  return new Promise<void>((resolve) => {
    const start = performance.now()
    let pausedMs = 0
    let pauseStart = 0

    const frame = (now: number) => {
      if (isCancelled()) {
        resolve()
        return
      }

      if (isPaused()) {
        if (!pauseStart) pauseStart = now
        requestAnimationFrame(frame)
        return
      }

      if (pauseStart) {
        pausedMs += now - pauseStart
        pauseStart = 0
      }

      const elapsed = now - start - pausedMs
      const t = Math.min(elapsed / durationMs, 1)
      motionVal.set(from + delta * easeInOut(t))

      if (t >= 1) resolve()
      else requestAnimationFrame(frame)
    }

    requestAnimationFrame(frame)
  })
}

export function MarketingWorkflow() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const [phase, setPhase] = useState<"travel" | "events" | "ripple">("travel")
  const [eventIndex, setEventIndex] = useState(-1)
  const [showRipple, setShowRipple] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [progressVal, setProgressVal] = useState(0)

  const progress = useMotionValue(0)
  const isPausedRef = useRef(false)
  const loopGenRef = useRef(0)

  useEffect(() => setMounted(true), [])

  useEffect(() => {
    if (!mounted) return
    return progress.on("change", (v) => setProgressVal(v))
  }, [mounted, progress])

  const runLoop = useCallback(async () => {
    const gen = ++loopGenRef.current
    const cancelled = () => loopGenRef.current !== gen
    const paused = () => isPausedRef.current

    while (!cancelled()) {
      setPhase("travel")
      setEventIndex(-1)
      setShowRipple(false)
      progress.set(0)

      await animateProgress(progress, 0.75, TRAVEL_MS, paused, cancelled)
      if (cancelled()) break

      while (paused() && !cancelled()) await sleep(80)
      if (cancelled()) break

      setPhase("events")
      for (let i = 0; i < OBS_EVENTS.length; i++) {
        while (paused() && !cancelled()) await sleep(80)
        if (cancelled()) break
        setEventIndex(i)
        await sleepPausable(EVENT_STEP_MS, paused, cancelled)
      }
      setEventIndex(-1)
      if (cancelled()) break

      while (paused() && !cancelled()) await sleep(80)
      if (cancelled()) break

      setPhase("ripple")
      setShowRipple(true)
      await sleepPausable(RIPPLE_MS, paused, cancelled)
      setShowRipple(false)
    }
  }, [progress])

  useEffect(() => {
    if (!mounted) return
    runLoop()
    return () => {
      loopGenRef.current++
    }
  }, [mounted, runLoop])

  const pauseFlow = useCallback((index: number) => {
    isPausedRef.current = true
    setHoveredIndex(index)
  }, [])

  const resumeFlow = useCallback(() => {
    isPausedRef.current = false
    setHoveredIndex(null)
  }, [])

  if (!mounted) {
    return (
      <section className="relative border-t border-hairline overflow-hidden">
        <div className="relative max-w-[1200px] mx-auto px-5 sm:px-6 lg:px-8 py-12 sm:py-14">
          <div className="h-[280px]" />
        </div>
      </section>
    )
  }

  return (
    <section className="relative border-t border-hairline overflow-hidden">
      <div className="arch-section-grid absolute inset-0 pointer-events-none" aria-hidden />
      <div className="arch-section-vignette absolute inset-0 pointer-events-none" aria-hidden />
      <div className="arch-noise absolute inset-0 pointer-events-none" aria-hidden />

      <div className="relative max-w-[1200px] mx-auto px-5 sm:px-6 lg:px-8 py-12 sm:py-14">
        <div className="text-center max-w-lg mx-auto mb-8 sm:mb-9">
          <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-ink-tertiary mb-2.5">
            Architecture
          </p>
          <h2 className="text-[24px] sm:text-[28px] font-semibold text-ink tracking-tight">
            From request to insight, automatically
          </h2>
          <p className="text-[13px] text-ink-muted/90 mt-2.5 leading-relaxed">
            Every LLM call flows through Traceplane — no manual logging, no glue code.
          </p>
        </div>

        <div className="hidden lg:block relative pt-1 pb-2">
          <motion.div
            className="arch-platform-glow absolute left-[20%] right-[20%] top-[18%] bottom-[8%] z-0"
            aria-hidden
            animate={{ opacity: hoveredIndex !== null ? 0.72 : 1 }}
            transition={{ duration: 0.3 }}
          />

          <TelemetryConnectors
            progress={progressVal}
            hoveredIndex={hoveredIndex}
            className="absolute left-0 right-0 top-[92px] h-[3px] z-[2]"
          />

          <TelemetryParticles progress={progressVal} className="absolute inset-0 z-[3] pointer-events-none" />

          <div className="grid grid-cols-4 gap-8 relative z-[4]">
            {STEPS.map((item, index) => (
              <ArchFlowCard
                key={item.label}
                {...item}
                index={index}
                isHovered={hoveredIndex === index}
                isDestination={item.role === "destination"}
                showRipple={showRipple && item.role === "destination"}
                events={item.role === "destination" && phase === "events" ? OBS_EVENTS : null}
                activeEventIndex={item.role === "destination" ? eventIndex : -1}
                pulseArrival={item.role === "destination" && progressVal >= 0.72 && phase === "travel"}
                onHoverStart={() => pauseFlow(index)}
                onHoverEnd={resumeFlow}
              />
            ))}
          </div>
        </div>

        <div className="lg:hidden space-y-0">
          {STEPS.map((item, i) => (
            <div key={item.label}>
              <ArchFlowCard
                {...item}
                index={i}
                isHovered={false}
                isDestination={item.role === "destination"}
                showRipple={false}
                events={null}
                activeEventIndex={-1}
                compact
              />
              {i < STEPS.length - 1 && (
                <VerticalConnector active={progressVal > (i + 1) * 0.2} />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function TelemetryConnectors({
  progress,
  hoveredIndex,
  className,
}: {
  progress: number
  hoveredIndex: number | null
  className?: string
}) {
  return (
    <div className={className} aria-hidden>
      <svg className="absolute inset-0 w-full h-[20px] -top-[8px] overflow-visible" preserveAspectRatio="none">
        {[0, 1, 2].map((seg) => {
          const x1 = `${CENTERS[seg] * 100}%`
          const x2 = `${CENTERS[seg + 1] * 100}%`
          const lit = segmentIntensity(seg, progress)
          const highlighted = isSegmentHighlighted(seg, hoveredIndex)
          const opacity = highlighted ? Math.max(lit, 0.65) : lit

          return (
            <g key={seg}>
              <line
                x1={x1}
                y1="10"
                x2={x2}
                y2="10"
                stroke={INDIGO}
                strokeWidth="1"
                strokeOpacity={0.08 + opacity * 0.06}
              />
              <motion.line
                x1={x1}
                y1="10"
                x2={x2}
                y2="10"
                stroke={PURPLE}
                strokeWidth="1.5"
                strokeLinecap="round"
                animate={{ strokeOpacity: 0.12 + opacity * 0.55 }}
                transition={{ duration: 0.3 }}
              />
              {highlighted && (
                <motion.line
                  x1={x1}
                  y1="10"
                  x2={x2}
                  y2="10"
                  stroke={PURPLE}
                  strokeWidth="2"
                  strokeLinecap="round"
                  initial={{ strokeOpacity: 0 }}
                  animate={{ strokeOpacity: 0.35 }}
                  transition={{ duration: 0.3 }}
                />
              )}
            </g>
          )
        })}
      </svg>
    </div>
  )
}

function TelemetryParticles({
  progress,
  className,
}: {
  progress: number
  className?: string
}) {
  const offsets = [0, 0.05, 0.1, 0.18]

  return (
    <div className={className} aria-hidden>
      {offsets.map((offset, i) => {
        const p = Math.max(0, Math.min((progress - offset * 0.12) / 0.75, 1))
        const seg = Math.min(Math.floor(p * 3), 2)
        const t = p * 3 - seg
        const x = (CENTERS[seg] + (CENTERS[seg + 1] - CENTERS[seg]) * t) * 100
        const visible = p > 0 && progress < 0.76

        return (
          <motion.div
            key={i}
            className="telemetry-particle absolute top-[88px]"
            style={{ left: `${x}%` }}
            animate={{
              opacity: visible ? 0.3 + (1 - i * 0.2) * 0.55 : 0,
              x: "-50%",
            }}
            transition={{ duration: 0.15, ease: "linear" }}
          />
        )
      })}
    </div>
  )
}

function VerticalConnector({ active }: { active: boolean }) {
  return (
    <div className="flex justify-center py-2" aria-hidden>
      <div className="relative w-[2px] h-10 rounded-full overflow-hidden bg-violet-500/8">
        <motion.div
          className="absolute inset-x-0 top-0 h-3 rounded-full"
          style={{
            background: `linear-gradient(180deg, transparent, ${PURPLE}, transparent)`,
          }}
          animate={{ opacity: active ? 0.7 : 0.2, y: active ? 28 : 0 }}
          transition={{ duration: 0.45, ease: [0.42, 0, 0.58, 1] }}
        />
      </div>
    </div>
  )
}

function ArchFlowCard({
  step,
  icon: Icon,
  label,
  detail,
  isLogo,
  role,
  isHovered,
  isDestination,
  showRipple,
  events,
  activeEventIndex,
  pulseArrival,
  onHoverStart,
  onHoverEnd,
  compact,
}: {
  step: string
  icon: typeof Code2 | typeof TraceplaneIcon
  label: string
  detail: string
  isLogo?: boolean
  role: "entry" | "core" | "destination"
  index: number
  isHovered: boolean
  isDestination: boolean
  showRipple: boolean
  events: readonly string[] | null
  activeEventIndex: number
  pulseArrival?: boolean
  onHoverStart?: () => void
  onHoverEnd?: () => void
  compact?: boolean
}) {
  const isCore = role === "core"

  return (
    <motion.div
      className={cn(
        "arch-flow-card relative w-full",
        isCore && "arch-flow-card--core",
        isDestination && "arch-flow-card--destination",
        compact && "arch-flow-card--compact",
      )}
      onMouseEnter={onHoverStart}
      onMouseLeave={onHoverEnd}
      animate={{
        boxShadow: isHovered
          ? "0 0 0 1px rgb(139 92 246 / 0.32), 0 0 40px rgb(139 92 246 / 0.14)"
          : isDestination
            ? "0 0 40px -8px rgb(139 92 246 / 0.28)"
            : "0 0 0 transparent",
      }}
      transition={{ duration: 0.3 }}
    >
      <motion.div
        className="arch-flow-card-glass pointer-events-none absolute inset-0 rounded-xl"
        animate={{ opacity: isHovered ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />

      {isCore && <div className="arch-flow-card-ambient pointer-events-none absolute inset-0 rounded-xl" aria-hidden />}

      <ObservabilityRipple show={showRipple && isDestination} />

      <span className="relative text-[10px] font-mono text-ink-tertiary tracking-wide">{step}</span>

      <motion.div
        className={cn(
          "relative mt-3 mb-3 flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border",
          isCore
            ? "border-violet-500/28 bg-violet-500/[0.1]"
            : isDestination
              ? "border-violet-500/22 bg-violet-500/[0.08]"
              : "border-hairline bg-surface-2/80",
        )}
        animate={{
          boxShadow: isHovered
            ? "0 0 0 1px rgb(139 92 246 / 0.35), 0 0 28px rgb(139 92 246 / 0.18)"
            : pulseArrival
              ? "0 0 0 1px rgb(139 92 246 / 0.4), 0 0 32px rgb(139 92 246 / 0.28)"
              : isDestination
                ? "0 0 24px rgb(139 92 246 / 0.14)"
                : isCore
                  ? "0 0 18px rgb(139 92 246 / 0.1)"
                  : "0 0 0 transparent",
        }}
        transition={{ duration: 0.3 }}
      >
        {isLogo ? (
          <TraceplaneIcon size={26} />
        ) : (
          <Icon
            className={cn(
              "h-[26px] w-[26px]",
              isCore || isDestination ? "text-violet-400/90" : "text-ink-muted",
            )}
            strokeWidth={1.5}
          />
        )}
      </motion.div>

      <h3 className="relative text-[14px] font-semibold text-ink leading-tight px-1">{label}</h3>
      <p className="relative mt-1.5 text-[12px] text-ink-subtle leading-snug line-clamp-2 px-0.5">{detail}</p>

      {events && (
        <div className="absolute left-1/2 top-[calc(100%+8px)] w-full max-w-[200px] -translate-x-1/2 pointer-events-none h-[18px]">
          {events.map((evt, i) => (
            <motion.div
              key={evt}
              className="absolute inset-x-0 flex items-center justify-center gap-1.5 text-[10px] font-medium text-violet-300/90"
              initial={false}
              animate={{
                opacity: activeEventIndex === i ? 1 : 0,
                y: activeEventIndex === i ? 0 : 4,
              }}
              transition={{ duration: 0.28, ease: "easeOut" }}
            >
              <span className="text-violet-400/80">✓</span>
              {evt}
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  )
}

function ObservabilityRipple({ show }: { show: boolean }) {
  if (!show) return null
  return (
    <>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="arch-obs-ripple pointer-events-none absolute left-1/2 top-[52px] rounded-full"
          style={{ x: "-50%", y: "-50%" }}
          initial={{ opacity: 0.35, scale: 0.25 }}
          animate={{ opacity: 0, scale: 3.2 + i * 0.6 }}
          transition={{
            duration: 1 + i * 0.2,
            ease: [0.42, 0, 0.58, 1],
            delay: i * 0.14,
          }}
        />
      ))}
    </>
  )
}
