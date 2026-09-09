"use client"

import { useEffect, useRef, useState } from "react"
import type { ConnectionStatus, SensorEvaluation, SensorMetric } from "@/lib/types"

const METRIC_LABEL: Record<SensorMetric, string> = {
  temperature: "온도",
  humidity: "습도",
  soil_moisture: "토양수분",
  light: "조도",
}

const METRIC_ORDER: SensorMetric[] = ["temperature", "humidity", "soil_moisture", "light"]

function formatValue(metric: SensorMetric, value: number, unit: string | undefined): string {
  if (metric === "temperature") return `${value.toFixed(1)}${unit ?? "°C"}`
  return `${value.toFixed(0)}${unit ?? "%"}`
}

interface MetricProps {
  metric: SensorMetric
  evaluation: SensorEvaluation
  flashKey: number
}

function Metric({ metric, evaluation, flashKey }: MetricProps) {
  const [flash, setFlash] = useState(false)
  const mounted = useRef(false)
  const outOfRange = evaluation.status !== "정상"

  useEffect(() => {
    if (!mounted.current) {
      mounted.current = true
      return
    }
    setFlash(true)
    const t = setTimeout(() => setFlash(false), 600)
    return () => clearTimeout(t)
  }, [flashKey])

  return (
    <div
      className={`rounded border px-3 py-2.5 ${
        outOfRange ? "border-status-bad/40 bg-status-bad/5" : "border-line bg-paper-raised"
      } ${flash ? "value-flash" : ""}`}
    >
      <div className="text-xs text-ink-muted">{METRIC_LABEL[metric]}</div>
      <div className={`font-data text-xl font-medium ${outOfRange ? "text-status-bad" : "text-ink"}`}>
        {formatValue(metric, evaluation.value, undefined)}
      </div>
      <div className={`mt-0.5 text-[11px] ${outOfRange ? "text-status-bad" : "text-ink-faint"}`}>
        {evaluation.control_action ?? evaluation.status}
      </div>
    </div>
  )
}

interface SmartFarmStatusProps {
  readings: Partial<Record<SensorMetric, SensorEvaluation>>
  connectionStatus: ConnectionStatus
}

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  connected: "실시간 연동 중",
  connecting: "연결 중",
  disconnected: "연결 끊김 - 재시도 중",
}

export default function SmartFarmStatus({ readings, connectionStatus }: SmartFarmStatusProps) {
  const available = METRIC_ORDER.filter((m) => readings[m])

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <span
          aria-hidden="true"
          className={`h-2 w-2 rounded-full ${
            connectionStatus === "connected"
              ? "bg-status-good sensor-live-dot"
              : connectionStatus === "connecting"
              ? "bg-status-warn"
              : "bg-status-bad"
          }`}
        />
        <span className="text-xs text-ink-muted">{STATUS_LABEL[connectionStatus]}</span>
      </div>

      {available.length === 0 ? (
        <div className="rounded border border-dashed border-line px-3 py-6 text-center text-xs text-ink-muted">
          센서 데이터를 기다리는 중입니다
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {available.map((metric) => {
            const evaluation = readings[metric]
            if (!evaluation) return null
            return <Metric key={metric} metric={metric} evaluation={evaluation} flashKey={evaluation.value} />
          })}
        </div>
      )}
    </div>
  )
}
