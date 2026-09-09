"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Header from "@/components/Header"
import ShipmentPlanSummaryCard from "@/components/ShipmentPlanSummaryCard"
import ShipmentPlanForm from "@/components/ShipmentPlanForm"
import QuickActionBar from "@/components/QuickActionBar"
import SmartFarmStatus from "@/components/SmartFarmStatus"
import AiAlertList from "@/components/AiAlertList"
import PriceTrendChart from "@/components/PriceTrendChart"
import WholesalerRecommendationList from "@/components/WholesalerRecommendationList"
import TransactionList from "@/components/TransactionList"
import {
  getFarmerDashboard,
  getPriceForecast,
  getWholesalerRecommendation,
  listTransactions,
  ApiError,
} from "@/lib/api"
import { buildAiAlerts } from "@/lib/ai-alerts"
import { useSmartFarmSensors } from "@/lib/use-smart-farm-sensors"
import type {
  FarmerDashboard,
  PriceForecastResponse,
  ShipmentPlan,
  Transaction,
  WholesalerRecommendationResponse,
} from "@/lib/types"

// Demo farmer id until the platform has login (SPEC 4.1 "향후 수정 계획").
// Matches the backend's seeded demo persona so shipment plans/transactions
// created here are visible to the same account the chat assistant acts on.
const FARM_ID = "user-farmer-kim"

export default function FarmDashboardPage() {
  const [dashboard, setDashboard] = useState<FarmerDashboard | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [activePlanId, setActivePlanId] = useState<string | null>(null)

  const [priceForecast, setPriceForecast] = useState<PriceForecastResponse | null>(null)
  const [wholesalerRecommendation, setWholesalerRecommendation] = useState<WholesalerRecommendationResponse | null>(
    null
  )
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)
  const [recommendationsError, setRecommendationsError] = useState<string | null>(null)

  const [showForm, setShowForm] = useState(false)
  const [showTransactions, setShowTransactions] = useState(false)
  const [transactions, setTransactions] = useState<Transaction[] | null>(null)
  const [transactionsLoading, setTransactionsLoading] = useState(false)

  useEffect(() => {
    let active = true
    getFarmerDashboard(FARM_ID)
      .then((data) => {
        if (!active) return
        setDashboard(data)
        const defaultPlan = data.shipment_plans.find((p) => p.status === "planned") ?? data.shipment_plans[0]
        setActivePlanId(defaultPlan?.id ?? null)
        setLoadError(null)
      })
      .catch((err) => {
        if (active) setLoadError(err instanceof ApiError ? err.message : "농가 대시보드를 불러오지 못했습니다")
      })
    return () => {
      active = false
    }
  }, [])

  const activePlan = useMemo(
    () => dashboard?.shipment_plans.find((p) => p.id === activePlanId) ?? null,
    [dashboard, activePlanId]
  )

  const loadRecommendations = useCallback((planId: string) => {
    setRecommendationsLoading(true)
    setRecommendationsError(null)
    Promise.all([getPriceForecast(planId), getWholesalerRecommendation(planId)])
      .then(([forecast, wholesaler]) => {
        setPriceForecast(forecast)
        setWholesalerRecommendation(wholesaler)
      })
      .catch((err) => {
        setRecommendationsError(err instanceof ApiError ? err.message : "AI 분석을 불러오지 못했습니다")
      })
      .finally(() => setRecommendationsLoading(false))
  }, [])

  useEffect(() => {
    if (!activePlanId) return
    // setTimeout (rather than calling loadRecommendations directly) keeps
    // the state updates it makes out of the synchronous effect body.
    const timer = setTimeout(() => loadRecommendations(activePlanId), 0)
    return () => clearTimeout(timer)
  }, [activePlanId, loadRecommendations])

  const smartFarmIds = useMemo(() => dashboard?.smart_farms.map((f) => f.id) ?? [], [dashboard])
  const { evaluations: sensorEvaluations, connectionStatus: sensorStatus } = useSmartFarmSensors(
    smartFarmIds,
    activePlan?.crop_id
  )

  function handlePlanCreated(plan: ShipmentPlan) {
    setDashboard((prev) => (prev ? { ...prev, shipment_plans: [...prev.shipment_plans, plan] } : prev))
    setActivePlanId(plan.id)
    setShowForm(false)
  }

  function handleShowTransactions() {
    const next = !showTransactions
    setShowTransactions(next)
    if (next && activePlanId) {
      setTransactionsLoading(true)
      listTransactions(activePlanId)
        .then(setTransactions)
        .catch(() => setTransactions([]))
        .finally(() => setTransactionsLoading(false))
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <h1 className="font-display text-2xl font-bold text-ink">농가 대시보드</h1>

        {loadError && (
          <div className="rounded border border-status-bad/40 bg-status-bad/5 px-4 py-3 text-sm text-status-bad">
            {loadError}
          </div>
        )}

        {!dashboard && !loadError && (
          <div className="rounded border border-dashed border-line px-4 py-10 text-center text-sm text-ink-muted">
            농가 데이터를 불러오는 중입니다
          </div>
        )}

        {dashboard && (
          <>
            {dashboard.shipment_plans.length === 0 ? (
              <p className="text-sm text-ink-muted">등록된 출하 계획이 없습니다. 작물을 등록해 보세요.</p>
            ) : (
              <>
                {dashboard.shipment_plans.length > 1 && (
                  <div className="flex flex-wrap gap-2">
                    {dashboard.shipment_plans.map((plan) => (
                      <button
                        key={plan.id}
                        type="button"
                        onClick={() => setActivePlanId(plan.id)}
                        className={`rounded border px-3 py-1 text-sm ${
                          plan.id === activePlanId
                            ? "border-forest bg-forest text-paper-raised"
                            : "border-line text-ink-muted hover:border-forest hover:text-forest-deep"
                        }`}
                      >
                        {plan.crop_name}
                      </button>
                    ))}
                  </div>
                )}

                {activePlan && (
                  <ShipmentPlanSummaryCard
                    plan={activePlan}
                    farmerName={dashboard.farmer_name}
                    priceForecast={priceForecast}
                    wholesalerRecommendation={wholesalerRecommendation}
                  />
                )}
              </>
            )}

            <QuickActionBar
              onRegisterCrop={() => setShowForm((v) => !v)}
              onRefreshWholesalerRecommendation={() => activePlanId && loadRecommendations(activePlanId)}
              onRefreshPriceForecast={() => activePlanId && loadRecommendations(activePlanId)}
              onShowTransactions={handleShowTransactions}
              busy={recommendationsLoading}
            />

            {showForm && (
              <ShipmentPlanForm farmerId={FARM_ID} onCreated={handlePlanCreated} onCancel={() => setShowForm(false)} />
            )}

            {showTransactions && (
              <section aria-labelledby="transactions-heading">
                <h2 id="transactions-heading" className="mb-3 font-display text-lg font-bold text-ink">
                  거래 현황
                </h2>
                {transactionsLoading ? (
                  <p className="text-sm text-ink-muted">불러오는 중입니다</p>
                ) : (
                  <TransactionList transactions={transactions ?? []} />
                )}
              </section>
            )}

            <section aria-labelledby="smart-farm-heading" className="rounded border border-line bg-paper-raised p-5">
              <h2 id="smart-farm-heading" className="mb-3 font-display text-lg font-bold text-ink">
                스마트팜 상태
              </h2>
              {smartFarmIds.length === 0 ? (
                <p className="text-sm text-ink-muted">등록된 스마트팜이 없습니다.</p>
              ) : (
                smartFarmIds.map((farmId) => (
                  <SmartFarmStatus
                    key={farmId}
                    readings={sensorEvaluations[farmId] ?? {}}
                    connectionStatus={sensorStatus}
                  />
                ))
              )}
            </section>

            {recommendationsError && (
              <div className="rounded border border-status-bad/40 bg-status-bad/5 px-4 py-3 text-sm text-status-bad">
                {recommendationsError}
              </div>
            )}

            {priceForecast && (
              <div className="grid gap-6 md:grid-cols-2">
                <section aria-labelledby="price-trend-heading" id="price-trend">
                  <h2 id="price-trend-heading" className="mb-3 font-display text-lg font-bold text-ink">
                    출하일별 시세 분석
                  </h2>
                  <PriceTrendChart
                    options={priceForecast.options}
                    crop={priceForecast.crop_name}
                    recommendedDate={priceForecast.recommended_date}
                  />
                </section>

                <section aria-labelledby="alerts-heading">
                  <h2 id="alerts-heading" className="mb-3 font-display text-lg font-bold text-ink">
                    AI 분석 알림
                  </h2>
                  <AiAlertList alerts={buildAiAlerts(priceForecast)} />
                </section>
              </div>
            )}

            {wholesalerRecommendation && (
              <section aria-labelledby="distributor-recommendations-heading" id="distributor-recommendations">
                <h2 id="distributor-recommendations-heading" className="mb-3 font-display text-lg font-bold text-ink">
                  AI 추천 도매처
                </h2>
                <WholesalerRecommendationList options={wholesalerRecommendation.options} />
              </section>
            )}
          </>
        )}
      </main>
    </div>
  )
}
