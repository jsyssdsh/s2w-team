"use client"

import { useEffect, useState } from "react"
import Header from "@/components/Header"
import StatRow from "@/components/StatRow"
import RecommendedShipmentList from "@/components/RecommendedShipmentList"
import MarketAnalysisPanel from "@/components/MarketAnalysisPanel"
import { getWholesalerDashboard, ApiError } from "@/lib/api"
import { useEventStream } from "@/lib/use-event-stream"
import { formatKrw } from "@/lib/format"
import type { SeriesStreamEvent, SeriesUpdate, WholesalerDashboard } from "@/lib/types"

// Demo wholesaler id until the platform has login (SPEC 4.1 "향후 수정 계획").
const WHOLESALER_ID = "wholesaler-a"

export default function DistributorDashboardPage() {
  const [dashboard, setDashboard] = useState<WholesalerDashboard | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [prices, setPrices] = useState<Record<string, SeriesUpdate>>({})

  useEffect(() => {
    let active = true
    getWholesalerDashboard(WHOLESALER_ID)
      .then((data) => {
        if (active) setDashboard(data)
      })
      .catch((err) => {
        if (active) {
          setLoadError(err instanceof ApiError ? err.message : "유통업체 대시보드를 불러오지 못했습니다")
        }
      })
    return () => {
      active = false
    }
  }, [])

  useEventStream<SeriesStreamEvent>("/api/stream/prices", (data) => {
    setPrices((prev) => ({ ...prev, ...data }))
  })

  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <h1 className="font-display text-2xl font-bold text-ink">유통업체 대시보드</h1>

        {loadError && (
          <div className="rounded border border-status-bad/40 bg-status-bad/5 px-4 py-3 text-sm text-status-bad">
            {loadError}
          </div>
        )}

        {!dashboard && !loadError && (
          <div className="rounded border border-dashed border-line px-4 py-10 text-center text-sm text-ink-muted">
            유통업체 데이터를 불러오는 중입니다
          </div>
        )}

        {dashboard && (
          <>
            <h2 className="font-display text-lg font-bold text-ink">{dashboard.wholesaler_name}</h2>
            <StatRow
              stats={[
                { label: "공급 가능 건수", value: `${dashboard.supply_available_count}건`, accent: "ink" },
                { label: "AI 추천 건수", value: `${dashboard.ai_recommended_count}건`, accent: "forest" },
                { label: "예상 금액", value: formatKrw(dashboard.expected_amount_krw), accent: "wheat" },
              ]}
            />

            <section aria-labelledby="recommended-farms-heading">
              <h2 id="recommended-farms-heading" className="mb-3 font-display text-lg font-bold text-ink">
                AI 추천 농가 출하 계획
              </h2>
              <RecommendedShipmentList
                shipments={dashboard.recommended_farmer_shipments}
                wholesalerId={dashboard.wholesaler_id}
              />
            </section>

            <section aria-labelledby="market-analysis-heading">
              <h2 id="market-analysis-heading" className="mb-3 font-display text-lg font-bold text-ink">
                실시간 시장 분석
              </h2>
              <MarketAnalysisPanel prices={prices} />
            </section>
          </>
        )}
      </main>
    </div>
  )
}
