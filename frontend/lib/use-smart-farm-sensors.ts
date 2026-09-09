"use client"

// Combines the one-shot evaluated reading (GET .../sensors/latest, which
// carries the crop's real min/max thresholds and the backend's own
// status/control_action text) with the live SSE value stream, so a tile
// updates in real time without losing the threshold context needed to know
// whether the new value is still in range.

import { useEffect, useState } from "react"
import { getLatestSensorReadings } from "./api"
import { parseSensorCode } from "./sensor-code"
import { useEventStream } from "./use-event-stream"
import type { SensorEvaluation, SensorMetric, SeriesStreamEvent } from "./types"

export type EvaluationsByFarm = Record<string, Partial<Record<SensorMetric, SensorEvaluation>>>

function reEvaluate(previous: SensorEvaluation, value: number): SensorEvaluation {
  let status = "정상"
  let control_action = null as string | null
  if (previous.min_value !== null && value < previous.min_value) {
    status = "기준미달"
    control_action = previous.control_action
  } else if (previous.max_value !== null && value > previous.max_value) {
    status = "기준초과"
    control_action = previous.control_action
  }
  return { ...previous, value, status, control_action }
}

export function useSmartFarmSensors(smartFarmIds: string[], cropId: string | undefined) {
  const [evaluations, setEvaluations] = useState<EvaluationsByFarm>({})
  const idsKey = smartFarmIds.join(",")

  useEffect(() => {
    if (smartFarmIds.length === 0) return
    let active = true

    Promise.all(
      smartFarmIds.map(async (farmId) => {
        const readings = await getLatestSensorReadings(farmId, cropId)
        return [farmId, readings] as const
      })
    )
      .then((results) => {
        if (!active) return
        setEvaluations((prev) => {
          const next = { ...prev }
          for (const [farmId, readings] of results) {
            const byMetric: Partial<Record<SensorMetric, SensorEvaluation>> = {}
            for (const r of readings) byMetric[r.metric] = r
            next[farmId] = byMetric
          }
          return next
        })
      })
      .catch(() => {
        // Leave whatever was already loaded; the panel shows its own
        // waiting/empty state when a farm has no entry yet.
      })

    return () => {
      active = false
    }
    // idsKey is a stable string form of the smartFarmIds array identity
  }, [idsKey, cropId, smartFarmIds])

  // No ref needed: useEventStream keeps its own ref to the latest callback
  // (assigned in an effect there), so a fresh closure each render is fine.
  function handleStreamMessage(data: SeriesStreamEvent) {
    setEvaluations((prev) => {
      let changed = false
      const next = { ...prev }
      for (const [code, update] of Object.entries(data)) {
        const parsed = parseSensorCode(code)
        if (!parsed) continue
        if (!smartFarmIds.includes(parsed.smartFarmId)) continue
        const metric = parsed.metric as SensorMetric
        const existing = next[parsed.smartFarmId]?.[metric]
        if (!existing) continue
        next[parsed.smartFarmId] = {
          ...next[parsed.smartFarmId],
          [metric]: reEvaluate(existing, update.price),
        }
        changed = true
      }
      return changed ? next : prev
    })
  }

  const connectionStatus = useEventStream<SeriesStreamEvent>(
    smartFarmIds.length > 0 ? "/api/stream/sensors" : null,
    handleStreamMessage
  )

  return { evaluations, connectionStatus }
}
