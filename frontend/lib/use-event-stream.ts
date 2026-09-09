"use client"

// Generic SSE consumer shared by the price-stream and sensor-stream hooks.
// Reconnects with backoff so a dropped connection (backend restart, network
// blip) recovers on its own instead of leaving the dashboard stale.

import { useEffect, useRef, useState } from "react"
import type { ConnectionStatus } from "./types"

const RECONNECT_DELAY_MS = 3000

export function useEventStream<T>(url: string | null, onMessage: (data: T) => void) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting")
  const onMessageRef = useRef(onMessage)

  // Keep the latest callback available to the subscription without
  // re-subscribing on every render (assigned in an effect, not render body).
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    if (!url) return

    let source: EventSource | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let cancelled = false

    function connect() {
      setStatus("connecting")
      source = new EventSource(url as string)

      source.onopen = () => {
        if (!cancelled) setStatus("connected")
      }

      source.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as T
          onMessageRef.current(data)
        } catch {
          // Ignore malformed frames rather than tearing down the stream
        }
      }

      source.onerror = () => {
        if (cancelled) return
        setStatus("disconnected")
        source?.close()
        reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      source?.close()
    }
  }, [url])

  // No URL yet (e.g. dashboard still loading its id) -- report disconnected
  // without a matching setState, since there is nothing to synchronize.
  return url ? status : "disconnected"
}
