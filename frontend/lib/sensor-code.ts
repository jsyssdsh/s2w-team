// Mirrors app.market.make_code/metric_of on the backend: the sensor SSE
// stream keys every series as "{smart_farm_id}:{metric}".

import type { SensorMetric } from "./types"

export function makeSensorCode(smartFarmId: string, metric: SensorMetric): string {
  return `${smartFarmId}:${metric}`
}

export function parseSensorCode(code: string): { smartFarmId: string; metric: string } | null {
  const idx = code.lastIndexOf(":")
  if (idx === -1) return null
  return { smartFarmId: code.slice(0, idx), metric: code.slice(idx + 1) }
}
