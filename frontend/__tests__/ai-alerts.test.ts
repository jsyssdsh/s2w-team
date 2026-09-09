import { buildAiAlerts } from "@/lib/ai-alerts"
import type { PriceForecastResponse } from "@/lib/types"

const forecast: PriceForecastResponse = {
  crop_name: "토마토",
  summary: "8월 초 출하가 유리합니다",
  recommended_date: "2026-08-10",
  recommendation_reason: "공급량 감소로 가격 상승이 예상됩니다",
  options: [
    {
      date: "2026-08-10",
      expected_wholesale_price_per_kg: 2580,
      expected_revenue: 2580000,
      price_change_percent: 5.3,
      market_supply_condition: "공급량 감소 예상",
      explanation: "",
      system_guidance: "출하 유지 권장",
    },
    {
      date: "2026-08-17",
      expected_wholesale_price_per_kg: 2320,
      expected_revenue: 2320000,
      price_change_percent: -5.3,
      market_supply_condition: "공급량 증가 예상",
      explanation: "",
      system_guidance: "조기 출하 검토",
    },
  ],
}

describe("buildAiAlerts", () => {
  it("includes the forecast summary and recommendation as info alerts", () => {
    const alerts = buildAiAlerts(forecast)
    expect(alerts[0]).toMatchObject({ severity: "info", message: "8월 초 출하가 유리합니다" })
    expect(alerts[1].message).toContain("공급량 감소로 가격 상승이 예상됩니다")
  })

  it("marks a 검토 guidance as a warning and others as info", () => {
    const alerts = buildAiAlerts(forecast)
    const optionAlerts = alerts.filter((a) => a.id.startsWith("forecast-option-"))
    const warn = optionAlerts.find((a) => a.message.includes("조기 출하 검토"))
    const info = optionAlerts.find((a) => a.message.includes("출하 유지 권장"))
    expect(warn?.severity).toBe("warning")
    expect(info?.severity).toBe("info")
  })
})
