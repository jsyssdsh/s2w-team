import { render, screen } from "@testing-library/react"
import WholesalerRecommendationList from "@/components/WholesalerRecommendationList"
import type { WholesalerOption } from "@/lib/types"

const options: WholesalerOption[] = [
  {
    wholesaler_id: "wholesaler-a",
    wholesaler_name: "A 도매처",
    purchase_unit_price_krw_per_kg: 2550,
    sellable_quantity_kg: 1000,
    transport_cost_krw: 180000,
    net_profit_krw: 2395000,
    rank: 2,
    explanation: "안정적인 매입단가",
  },
  {
    wholesaler_id: "wholesaler-b",
    wholesaler_name: "B 도매처",
    purchase_unit_price_krw_per_kg: 2580,
    sellable_quantity_kg: 1000,
    transport_cost_krw: 80000,
    net_profit_krw: 2422600,
    rank: 1,
    explanation: "운송비가 가장 낮습니다",
  },
]

describe("WholesalerRecommendationList", () => {
  it("shows an empty message when there are no options", () => {
    render(<WholesalerRecommendationList options={[]} />)
    expect(screen.getByText("추천 가능한 도매처가 아직 없습니다.")).toBeInTheDocument()
  })

  it("orders options by backend-provided rank", () => {
    render(<WholesalerRecommendationList options={options} />)
    const items = screen.getAllByRole("listitem")
    expect(items[0]).toHaveTextContent("B 도매처")
    expect(items[0]).toHaveTextContent("1순위")
    expect(items[1]).toHaveTextContent("A 도매처")
    expect(items[1]).toHaveTextContent("2순위")
  })

  it("renders each option's rationale", () => {
    render(<WholesalerRecommendationList options={options} />)
    expect(screen.getByText("운송비가 가장 낮습니다")).toBeInTheDocument()
  })
})
