import { render, screen } from "@testing-library/react"
import MarketAnalysisPanel from "@/components/MarketAnalysisPanel"
import type { SeriesUpdate } from "@/lib/types"

function update(overrides: Partial<SeriesUpdate>): SeriesUpdate {
  return {
    code: "양파",
    price: 1200,
    previous_price: 1250,
    timestamp: 0,
    change: -50,
    change_percent: -4.5,
    direction: "down",
    ...overrides,
  }
}

describe("MarketAnalysisPanel", () => {
  it("shows an empty message when there are no prices", () => {
    render(<MarketAnalysisPanel prices={{}} />)
    expect(screen.getByText("실시간 시장 분석 데이터가 없습니다.")).toBeInTheDocument()
  })

  it("renders each crop with price and change percent", () => {
    render(<MarketAnalysisPanel prices={{ 양파: update({}) }} />)
    expect(screen.getByText("양파")).toBeInTheDocument()
    expect(screen.getByText("-4.5%")).toHaveClass("text-status-bad")
  })
})
