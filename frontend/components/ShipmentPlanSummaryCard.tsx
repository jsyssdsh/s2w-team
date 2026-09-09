import type { PriceForecastResponse, ShipmentPlan, WholesalerRecommendationResponse } from "@/lib/types"
import { formatDate, formatKg, formatKrw } from "@/lib/format"

interface ShipmentPlanSummaryCardProps {
  plan: ShipmentPlan
  farmerName: string
  priceForecast: PriceForecastResponse | null
  wholesalerRecommendation: WholesalerRecommendationResponse | null
}

export default function ShipmentPlanSummaryCard({
  plan,
  farmerName,
  priceForecast,
  wholesalerRecommendation,
}: ShipmentPlanSummaryCardProps) {
  const recommendedOption =
    priceForecast?.options.find((o) => o.date === priceForecast.recommended_date) ?? priceForecast?.options[0]
  const topWholesaler = wholesalerRecommendation?.options[0]

  return (
    <div className="rounded border border-line bg-paper-raised p-5">
      <div className="flex items-baseline justify-between">
        <h2 className="font-display text-xl font-bold text-ink">{plan.crop_name}</h2>
        <span className="text-xs text-ink-muted">{farmerName} 농가 -- {plan.grade} 등급</span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <dt className="text-xs text-ink-muted">예상 수확량</dt>
          <dd className="font-data text-lg font-medium text-ink">{formatKg(plan.expected_yield_kg)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">출하 예정일</dt>
          <dd className="font-data text-lg font-medium text-ink">{formatDate(plan.planned_shipment_date)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">현재 도매가</dt>
          <dd className="font-data text-lg font-medium text-wheat">
            {recommendedOption ? `${formatKrw(recommendedOption.expected_wholesale_price_per_kg)}/kg` : "분석 중"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-ink-muted">AI 추천 유통처</dt>
          <dd className="text-lg font-medium text-ink">{topWholesaler?.wholesaler_name ?? "분석 중"}</dd>
        </div>
      </dl>

      {topWholesaler && (
        <div className="mt-3 border-t border-line pt-3 text-sm text-status-good">
          예상 순수익 {formatKrw(topWholesaler.net_profit_krw)}
        </div>
      )}
    </div>
  )
}
