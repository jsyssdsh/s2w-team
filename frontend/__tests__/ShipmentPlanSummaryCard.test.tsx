import { render, screen } from "@testing-library/react"
import ShipmentPlanSummaryCard from "@/components/ShipmentPlanSummaryCard"
import type { PriceForecastResponse, ShipmentPlan, WholesalerRecommendationResponse } from "@/lib/types"

const plan: ShipmentPlan = {
  id: "shipment-tomato-main",
  farmer_user_id: "user-farmer-kim",
  smart_farm_id: "smart-farm-tomato",
  crop_id: "crop-tomato",
  crop_name: "토마토",
  region: "충남 논산시",
  expected_yield_kg: 1000,
  planned_shipment_date: "2026-08-10",
  grade: "특상품",
  status: "planned",
}

describe("ShipmentPlanSummaryCard", () => {
  it("renders the crop, farmer, yield and shipment date", () => {
    render(
      <ShipmentPlanSummaryCard plan={plan} farmerName="김농부" priceForecast={null} wholesalerRecommendation={null} />
    )
    expect(screen.getByText("토마토")).toBeInTheDocument()
    expect(screen.getByText(/김농부 농가/)).toBeInTheDocument()
    expect(screen.getByText("1,000kg")).toBeInTheDocument()
  })

  it("shows 분석 중 while price forecast and wholesaler recommendation are not loaded", () => {
    render(
      <ShipmentPlanSummaryCard plan={plan} farmerName="김농부" priceForecast={null} wholesalerRecommendation={null} />
    )
    expect(screen.getAllByText("분석 중").length).toBe(2)
  })

  it("shows the recommended date's price and top wholesaler once loaded", () => {
    const priceForecast: PriceForecastResponse = {
      crop_name: "토마토",
      summary: "요약",
      recommended_date: "2026-08-10",
      recommendation_reason: "이유",
      options: [
        {
          date: "2026-08-10",
          expected_wholesale_price_per_kg: 2580,
          expected_revenue: 2580000,
          price_change_percent: 5.3,
          market_supply_condition: "공급량 감소 예상",
          explanation: "설명",
          system_guidance: "출하 유지 권장",
        },
      ],
    }
    const wholesalerRecommendation: WholesalerRecommendationResponse = {
      crop_name: "토마토",
      recommended_wholesaler: "B 도매처",
      recommendation_reason: "운송비가 낮습니다",
      options: [
        {
          wholesaler_id: "wholesaler-b",
          wholesaler_name: "B 도매처",
          purchase_unit_price_krw_per_kg: 2580,
          sellable_quantity_kg: 1000,
          transport_cost_krw: 80000,
          net_profit_krw: 2422600,
          rank: 1,
          explanation: "운송비가 낮습니다",
        },
      ],
    }
    render(
      <ShipmentPlanSummaryCard
        plan={plan}
        farmerName="김농부"
        priceForecast={priceForecast}
        wholesalerRecommendation={wholesalerRecommendation}
      />
    )
    expect(screen.getByText("B 도매처")).toBeInTheDocument()
    expect(screen.getByText(/예상 순수익/)).toBeInTheDocument()
  })
})
