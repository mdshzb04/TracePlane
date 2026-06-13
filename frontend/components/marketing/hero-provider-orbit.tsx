"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { TraceplaneIcon } from "@/components/brand/traceplane-icon"
import { PROVIDER_BRANDS, UI_PROVIDER_IDS, type UiProviderId } from "@/lib/provider-brands"

const PROVIDERS = [...UI_PROVIDER_IDS] as UiProviderId[]

const ICON = 44
const ORBIT_R = 130
const ORBIT_SPEED = 0.0028
const CELL = 34

/** 13 slots forming a centered letter T (7 top bar + 6 stem). */
const T_LAYOUT: { x: number; y: number }[] = [
  { x: -3 * CELL, y: -70 },
  { x: -2 * CELL, y: -70 },
  { x: -1 * CELL, y: -70 },
  { x: 0, y: -70 },
  { x: CELL, y: -70 },
  { x: 2 * CELL, y: -70 },
  { x: 3 * CELL, y: -70 },
  { x: 0, y: -32 },
  { x: 0, y: 6 },
  { x: 0, y: 44 },
  { x: 0, y: 82 },
  { x: 0, y: 120 },
  { x: 0, y: 158 },
]

const PULSE_ORDER = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

const SPRING = { type: "spring" as const, stiffness: 130, damping: 22, mass: 0.85 }
const SPRING_SOFT = { type: "spring" as const, stiffness: 100, damping: 26, mass: 1 }
const FADE = { duration: 0.45, ease: [0.22, 1, 0.36, 1] as const }

const T_FORM_MS = 720
const LOGO_DELAY_MS = 680
const PULSE_START_MS = 1180
const PULSE_STEP_MS = 95

type Phase = "orbit" | "brand" | "exit"

function orbitPosition(index: number, angle: number) {
  const a = (index / PROVIDERS.length) * Math.PI * 2 - Math.PI / 2 + angle
  return {
    x: Math.cos(a) * ORBIT_R,
    y: Math.sin(a) * ORBIT_R,
  }
}

export function HeroProviderOrbit() {
  const [mounted, setMounted] = useState(false)
  const [phase, setPhase] = useState<Phase>("orbit")
  const [hovered, setHovered] = useState<UiProviderId | null>(null)
  const [showLogo, setShowLogo] = useState(false)
  const [showTagline, setShowTagline] = useState(false)
  const [pulseStep, setPulseStep] = useState(-1)
  const [assembling, setAssembling] = useState(false)
  const [tick, setTick] = useState(0)
  const orbitAngle = useRef(0)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])

  useEffect(() => setMounted(true), [])
  useEffect(() => () => clearTimers(), [clearTimers])

  useEffect(() => {
    if (!mounted || phase !== "orbit") return
    let raf = 0
    const step = () => {
      orbitAngle.current += ORBIT_SPEED
      setTick((t) => t + 1)
      raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [mounted, phase])

  const runPulse = useCallback(() => {
    PULSE_ORDER.forEach((idx, i) => {
      const t = setTimeout(() => setPulseStep(idx), i * PULSE_STEP_MS)
      timers.current.push(t)
    })
    const end = setTimeout(() => {
      setPulseStep(-1)
      setShowTagline(true)
    }, PULSE_ORDER.length * PULSE_STEP_MS + 120)
    timers.current.push(end)
  }, [])

  const engage = useCallback(
    (id: UiProviderId) => {
      if (phase === "brand") {
        setHovered(id)
        return
      }
      clearTimers()
      setHovered(id)
      setPhase("brand")
      setShowLogo(false)
      setShowTagline(false)
      setPulseStep(-1)
      setAssembling(true)

      timers.current.push(
        setTimeout(() => setAssembling(false), T_FORM_MS),
        setTimeout(() => setShowLogo(true), LOGO_DELAY_MS),
        setTimeout(() => runPulse(), PULSE_START_MS),
      )
    },
    [phase, clearTimers, runPulse],
  )

  const disengage = useCallback(() => {
    if (phase === "orbit") return
    clearTimers()
    setShowLogo(false)
    setShowTagline(false)
    setPulseStep(-1)
    setAssembling(false)
    setHovered(null)

    // Logo fades first while T holds, then providers dissolve back to orbit
    const dissolveDelay = phase === "brand" ? 320 : 0
    timers.current.push(
      setTimeout(() => setPhase("exit"), dissolveDelay),
      setTimeout(() => setPhase("orbit"), dissolveDelay + 620),
    )
  }, [phase, clearTimers])

  if (!mounted) {
    return (
      <div className="relative h-[380px] md:h-[420px] w-full max-w-[440px] mx-auto lg:mx-0 lg:ml-auto" />
    )
  }

  void tick

  const inBrand = phase === "brand"
  const pulseProgress =
    pulseStep < 0 ? 0 : (pulseStep + 1) / PULSE_ORDER.length

  return (
    <div
      className="hero-orbit-root relative h-[380px] md:h-[420px] w-full max-w-[440px] mx-auto lg:mx-0 lg:ml-auto select-none"
      onMouseLeave={disengage}
      aria-label="Provider logos orbit — hover to form Traceplane T"
    >
      {/* Ambient center glow */}
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-violet-500/10 blur-3xl"
        animate={{ opacity: inBrand ? 0.6 : 0.32, scale: inBrand ? 1.08 : 1 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />

      {/* T topology — subtle network path */}
      <motion.svg
        className="pointer-events-none absolute left-1/2 top-1/2 z-[5] -translate-x-1/2 -translate-y-1/2 overflow-visible"
        width={260}
        height={280}
        viewBox="-130 -90 260 280"
        initial={false}
        animate={{ opacity: inBrand ? 0.55 : 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        aria-hidden
      >
        <defs>
          <linearGradient id="hero-t-pulse" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgb(139 92 246)" stopOpacity="0.15" />
            <stop offset={`${pulseProgress * 100}%`} stopColor="rgb(167 139 250)" stopOpacity="0.65" />
            <stop offset={`${pulseProgress * 100}%`} stopColor="rgb(139 92 246)" stopOpacity="0.12" />
            <stop offset="100%" stopColor="rgb(139 92 246)" stopOpacity="0.08" />
          </linearGradient>
        </defs>
        <path
          d={`M ${T_LAYOUT[0].x} ${T_LAYOUT[0].y} L ${T_LAYOUT[6].x} ${T_LAYOUT[6].y} M 0 -70 L 0 158`}
          fill="none"
          stroke="url(#hero-t-pulse)"
          strokeWidth="1.25"
          strokeLinecap="round"
          className="hero-orbit-t-path"
        />
      </motion.svg>

      {/* Telemetry pulse orb */}
      <AnimatePresence>
        {inBrand && pulseStep >= 0 && (
          <motion.div
            key="pulse-orb"
            className="hero-orbit-pulse-orb pointer-events-none absolute left-1/2 top-1/2 z-[25]"
            initial={{ opacity: 0, scale: 0.6 }}
            animate={{
              x: T_LAYOUT[pulseStep].x,
              y: T_LAYOUT[pulseStep].y,
              opacity: 1,
              scale: 1,
            }}
            exit={{ opacity: 0, scale: 0.5 }}
            transition={{ type: "spring", stiffness: 280, damping: 28, mass: 0.45 }}
            style={{ marginLeft: -6, marginTop: -6, width: 12, height: 12 }}
          />
        )}
      </AnimatePresence>

      {/* Center logo + glow */}
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 z-20 flex flex-col items-center"
        initial={false}
        animate={{
          opacity: showLogo ? 1 : 0,
          scale: showLogo ? 1 : 0.88,
          y: showLogo ? 18 : 28,
        }}
        transition={FADE}
        style={{ x: "-50%" }}
      >
        <div className="hero-orbit-logo-glow absolute inset-0 -m-6 rounded-full" />
        <TraceplaneIcon size={44} className="relative z-[1] text-primary" />
      </motion.div>

      {/* Tagline */}
      <motion.p
        className="pointer-events-none absolute left-1/2 top-[calc(50%+118px)] z-20 -translate-x-1/2 whitespace-nowrap text-[11px] font-medium tracking-wide text-ink-muted"
        initial={false}
        animate={{ opacity: showTagline ? 1 : 0, y: showTagline ? 0 : 6 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        One SDK. Every provider.
      </motion.p>

      {PROVIDERS.map((id, index) => {
        const pos =
          phase === "brand"
            ? T_LAYOUT[index]
            : orbitPosition(index, orbitAngle.current)
        const isHovered = hovered === id
        const isPulseLit = pulseStep === index
        const label = PROVIDER_BRANDS[id].name

        return (
          <motion.div
            key={id}
            className="absolute left-1/2 top-1/2 z-10"
            initial={false}
            animate={{
              x: pos.x,
              y: pos.y,
              scale: isPulseLit ? 1.1 : isHovered ? 1.16 : 1,
              zIndex: isHovered ? 30 : isPulseLit ? 22 : 10,
            }}
            transition={phase === "exit" ? SPRING_SOFT : SPRING}
            style={{ width: ICON, height: ICON, marginLeft: -ICON / 2, marginTop: -ICON / 2 }}
          >
            {/* Motion trail while assembling */}
            <motion.span
              className="hero-orbit-trail pointer-events-none absolute -inset-2 rounded-full"
              animate={{
                opacity: assembling ? 0.7 : inBrand ? 0.35 : 0.5,
                scale: assembling ? [1, 1.35, 1] : 1,
              }}
              transition={
                assembling
                  ? { duration: 0.55, ease: "easeOut" }
                  : { duration: 0.35, ease: "easeOut" }
              }
            />

            <button
              type="button"
              className="relative h-full w-full rounded-full border-0 bg-transparent p-0 cursor-default focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              onMouseEnter={() => engage(id)}
              onFocus={() => engage(id)}
              aria-label={label}
            >
              <motion.span
                className={`hero-orbit-icon-wrap relative z-[1] block h-full w-full rounded-full ${
                  isPulseLit ? "hero-orbit-icon-pulse" : ""
                }`}
                animate={{
                  boxShadow: isPulseLit
                    ? "0 0 0 2px rgb(139 92 246 / 0.55), 0 8px 32px rgb(139 92 246 / 0.35)"
                    : "0 8px 28px rgba(0,0,0,0.28)",
                }}
                transition={{ duration: 0.12, ease: "easeOut" }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={PROVIDER_BRANDS[id].logo}
                  alt=""
                  draggable={false}
                  className="hero-orbit-icon h-full w-full rounded-full object-cover"
                />
              </motion.span>
            </button>

            <motion.span
              className="pointer-events-none absolute left-1/2 -translate-x-1/2 top-[calc(100%+6px)] whitespace-nowrap rounded-md bg-surface-2/95 border border-hairline px-2 py-0.5 text-[10px] font-medium text-ink-muted shadow-lg"
              initial={false}
              animate={{ opacity: isHovered ? 1 : 0, y: isHovered ? 0 : 4 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
            >
              {label}
            </motion.span>
          </motion.div>
        )
      })}
    </div>
  )
}
