"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import Header from "@/components/Header"
import LandOverviewPanel from "@/components/LandOverviewPanel"
import SmartFarmStatus from "@/components/SmartFarmStatus"
import SensorHistoryChart from "@/components/SensorHistoryChart"
import { getFarmlandDetail, getSensorHistory, ApiError } from "@/lib/api"
import { useSmartFarmSensors } from "@/lib/use-smart-farm-sensors"
import type { FarmlandDetail, SensorMetric, SensorReadingRow } from "@/lib/types"

const METRICS: { metric: SensorMetric; label: string }[] = [
  { metric: "temperature", label: "온도" },
  { metric: "humidity", label: "습도" },
  { metric: "soil_moisture", label: "토양수분" },
  { metric: "light", label: "조도" },
]

function IdleLandDetailContent() {
  const searchParams = useSearchParams()
  const id = searchParams.get("id")

  const [land, setLand] = useState<FarmlandDetail | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [historyMetric, setHistoryMetric] = useState<SensorMetric>("temperature")
  const [historyRows, setHistoryRows] = useState<SensorReadingRow[]>([])

  useEffect(() => {
    if (!id) return
    let active = true
    getFarmlandDetail(id)
      .then((data) => {
        if (!active) return
        setLand(data)
        setLoadError(null)
      })
      .catch((err) => {
        if (active) {
          setLoadError(err instanceof ApiError ? err.message : "유휴토지 상세 정보를 불러오지 못했습니다")
        }
      })
    return () => {
      active = false
    }
  }, [id])

  const smartFarmId = land?.smart_farm?.id
  const smartFarmIds = useMemo(() => (smartFarmId ? [smartFarmId] : []), [smartFarmId])
  const { evaluations, connectionStatus } = useSmartFarmSensors(smartFarmIds, undefined)

  useEffect(() => {
    if (!smartFarmId) return
    let active = true
    const end = new Date()
    const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
    getSensorHistory(smartFarmId, historyMetric, start.toISOString(), end.toISOString())
      .then((rows) => {
        if (active) setHistoryRows(rows)
      })
      .catch(() => {
        if (active) setHistoryRows([])
      })
    return () => {
      active = false
    }
  }, [smartFarmId, historyMetric])

  const missingIdError = id ? null : "유휴토지 id가 지정되지 않았습니다"
  const displayError = missingIdError ?? loadError

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-ink">유휴토지 상세</h1>
        <Link href="/idle-land" prefetch={false} className="text-sm text-forest-deep hover:underline">
          지도로 돌아가기
        </Link>
      </div>

      {displayError && (
        <div className="rounded border border-status-bad/40 bg-status-bad/5 px-4 py-3 text-sm text-status-bad">
          {displayError}
        </div>
      )}

      {!land && !displayError && (
        <div className="rounded border border-dashed border-line px-4 py-10 text-center text-sm text-ink-muted">
          토지 정보를 불러오는 중입니다
        </div>
      )}

      {land && (
        <>
          <LandOverviewPanel land={land} />

          {land.smart_farm && (
            <>
              <section aria-labelledby="sensor-heading" className="rounded border border-line bg-paper-raised p-5">
                <h2 id="sensor-heading" className="mb-3 font-display text-lg font-bold text-ink">
                  실시간 센서
                </h2>
                <SmartFarmStatus readings={evaluations[land.smart_farm.id] ?? {}} connectionStatus={connectionStatus} />
              </section>

              <section aria-labelledby="sensor-history-heading">
                <div className="mb-3 flex items-center justify-between">
                  <h2 id="sensor-history-heading" className="font-display text-lg font-bold text-ink">
                    센서 변화 그래프
                  </h2>
                  <div className="flex gap-1">
                    {METRICS.map((m) => (
                      <button
                        key={m.metric}
                        type="button"
                        onClick={() => setHistoryMetric(m.metric)}
                        className={`rounded border px-2 py-1 text-xs ${
                          historyMetric === m.metric
                            ? "border-forest bg-forest text-paper-raised"
                            : "border-line text-ink-muted hover:border-forest hover:text-forest-deep"
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>
                <SensorHistoryChart rows={historyRows} />
              </section>
            </>
          )}
        </>
      )}
    </main>
  )
}

export default function IdleLandDetailPage() {
  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <Suspense
        fallback={
          <main className="mx-auto max-w-6xl px-6 py-8 text-sm text-ink-muted">불러오는 중입니다</main>
        }
      >
        <IdleLandDetailContent />
      </Suspense>
    </div>
  )
}
