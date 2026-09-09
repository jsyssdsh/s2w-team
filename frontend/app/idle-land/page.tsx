"use client"

import { useEffect, useMemo, useState } from "react"
import Header from "@/components/Header"
import StatRow from "@/components/StatRow"
import IdleLandMap from "@/components/IdleLandMap"
import IdleLandCard from "@/components/IdleLandCard"
import { listFarmlands, ApiError } from "@/lib/api"
import type { Farmland } from "@/lib/types"

export default function IdleLandMapPage() {
  const [plots, setPlots] = useState<Farmland[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    listFarmlands()
      .then((res) => {
        if (active) setPlots(res)
      })
      .catch((err) => {
        if (active) {
          setLoadError(err instanceof ApiError ? err.message : "유휴토지 목록을 불러오지 못했습니다")
        }
      })
    return () => {
      active = false
    }
  }, [])

  // SPEC 4.4 lists 4 summary figures (운영 중/전환 완료/오늘 신청량/AI 추천
  // 거래); only the first two are derivable from GET /api/farmlands's status
  // field today. The other two need a lease-application concept and a
  // recommendation-count endpoint that don't exist yet -- asked backend
  // rather than showing invented numbers.
  const counts = useMemo(() => {
    const result = { idle: 0, matched: 0, operating: 0 }
    for (const plot of plots ?? []) result[plot.status] += 1
    return result
  }, [plots])

  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <h1 className="font-display text-2xl font-bold text-ink">유휴토지 지도</h1>

        {loadError && (
          <div className="rounded border border-status-bad/40 bg-status-bad/5 px-4 py-3 text-sm text-status-bad">
            {loadError}
          </div>
        )}

        {!plots && !loadError && (
          <div className="rounded border border-dashed border-line px-4 py-10 text-center text-sm text-ink-muted">
            유휴토지 데이터를 불러오는 중입니다
          </div>
        )}

        {plots && (
          <>
            <StatRow
              stats={[
                { label: "운영 중", value: `${counts.operating}건`, accent: "forest" },
                { label: "매칭 완료", value: `${counts.matched}건`, accent: "ink" },
                { label: "유휴", value: `${counts.idle}건`, accent: "wheat" },
              ]}
            />

            <section aria-labelledby="map-heading">
              <h2 id="map-heading" className="mb-3 font-display text-lg font-bold text-ink">
                토지 현황
              </h2>
              <IdleLandMap plots={plots} />
            </section>

            <section aria-labelledby="plots-heading">
              <h2 id="plots-heading" className="mb-3 font-display text-lg font-bold text-ink">
                토지 목록
              </h2>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {plots.map((plot) => (
                  <IdleLandCard key={plot.id} plot={plot} />
                ))}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
