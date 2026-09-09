import { render, screen } from "@testing-library/react"
import PriceTrendChart from "@/components/PriceTrendChart"

describe("PriceTrendChart", () => {
  it("shows a loading message when fewer than two options are available", () => {
    render(<PriceTrendChart options={[]} crop="토마토" recommendedDate="2026-08-10" />)
    expect(screen.getByText("시세 데이터를 불러오는 중입니다")).toBeInTheDocument()
  })

  it("renders a chart container when enough options exist", () => {
    const { container } = render(
      <PriceTrendChart
        crop="토마토"
        recommendedDate="2026-08-10"
        options={[
          {
            date: "2026-08-08",
            expected_wholesale_price_per_kg: 2450,
            expected_revenue: 2450000,
            price_change_percent: 0,
            market_supply_condition: "공급량 보통",
            explanation: "",
            system_guidance: "즉시 출하 가능",
          },
          {
            date: "2026-08-10",
            expected_wholesale_price_per_kg: 2580,
            expected_revenue: 2580000,
            price_change_percent: 5.3,
            market_supply_condition: "공급량 감소 예상",
            explanation: "",
            system_guidance: "출하 유지 권장",
          },
        ]}
      />
    )
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument()
  })
})
