"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { getAccessToken } from "@/lib/auth"
import { API_BASE_URL } from "@/lib/constants"

type LiveEvent = { type: string; data: Record<string, unknown> }

function buildLiveWsUrl(): string {
  if (typeof window === "undefined") return ""
  const token = getAccessToken()
  const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : ""
  if (API_BASE_URL.startsWith("http")) {
    const wsBase = API_BASE_URL.replace(/^http/, "ws").replace(/\/api\/v1$/, "")
    return `${wsBase}/api/v1/ws/live${tokenQuery}`
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:"
  return `${proto}//${window.location.host}/api/ws/live${tokenQuery}`
}

export function useLiveUpdates(onEvent?: (event: LiveEvent) => void) {
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  const connect = useCallback(() => {
    if (typeof window === "undefined") return
    const url = buildLiveWsUrl()
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (msg) => {
      try {
        const payload = JSON.parse(msg.data) as LiveEvent
        onEventRef.current?.(payload)
      } catch {
        /* ignore */
      }
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  return { connected, reconnect: connect }
}
