"use client"

import { useCallback, useEffect, useSyncExternalStore } from "react"
import { systemService } from "@/services/api"
import { isSdkInstalledMarked } from "@/lib/onboarding-storage"
import type { OnboardingStatus } from "@/types"

const CACHE_KEY = "tp_onboarding_status"
const CACHE_TTL_MS = 5 * 60 * 1000

type Snapshot = {
  status: OnboardingStatus | null
  loading: boolean
  error: string | null
}

const listeners = new Set<() => void>()
let snapshot: Snapshot = { status: readCache(), loading: !readCache(), error: null }
let inflight: Promise<void> | null = null
let pollTimer: ReturnType<typeof setInterval> | null = null
let subscribers = 0

function readCache(): OnboardingStatus | null {
  if (typeof window === "undefined") return null
  try {
    const raw = sessionStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const { at, data } = JSON.parse(raw) as { at: number; data: OnboardingStatus }
    if (Date.now() - at > CACHE_TTL_MS) return null
    return data
  } catch {
    return null
  }
}

function writeCache(data: OnboardingStatus) {
  sessionStorage.setItem(CACHE_KEY, JSON.stringify({ at: Date.now(), data }))
}

function emit() {
  listeners.forEach((l) => l())
}

function applyStatus(data: OnboardingStatus) {
  const sdkMarked = isSdkInstalledMarked()
  const steps = data.steps.map((step) =>
    step.id === "sdk_installed" ? { ...step, complete: step.complete || sdkMarked } : step
  )
  const status = { ...data, steps }
  snapshot = { status, loading: false, error: null }
  writeCache(status)
  emit()
}

async function fetchOnboarding() {
  if (inflight) return inflight
  inflight = (async () => {
    try {
      const data = await systemService.onboarding()
      applyStatus(data)
    } catch (err) {
      const cached = snapshot.status ?? readCache()
      snapshot = {
        status: cached,
        loading: false,
        error: err instanceof Error ? err.message : "Failed to load onboarding status",
      }
      emit()
    } finally {
      inflight = null
    }
  })()
  return inflight
}

function subscribe(cb: () => void) {
  listeners.add(cb)
  return () => listeners.delete(cb)
}

function getSnapshot() {
  return snapshot
}

const SERVER_SNAPSHOT: Snapshot = { status: null, loading: true, error: null }

function getServerSnapshot() {
  return SERVER_SNAPSHOT
}

const GLOBAL_POLL_MS = 60_000

function startPolling() {
  subscribers += 1
  if (subscribers === 1) {
    if (!snapshot.status) void fetchOnboarding()
    else snapshot = { ...snapshot, loading: false }
    pollTimer = setInterval(() => void fetchOnboarding(), GLOBAL_POLL_MS)
  }
}

function stopPolling() {
  subscribers -= 1
  if (subscribers === 0 && pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

export function useOnboarding(_pollMs?: number) {
  const state = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)

  useEffect(() => {
    startPolling()
    return () => stopPolling()
  }, [])

  const refresh = useCallback(() => fetchOnboarding(), [])

  return { ...state, refresh }
}
