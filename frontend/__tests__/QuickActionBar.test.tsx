import { fireEvent, render, screen } from "@testing-library/react"
import QuickActionBar from "@/components/QuickActionBar"

describe("QuickActionBar", () => {
  it("renders all four quick actions", () => {
    render(
      <QuickActionBar
        onRegisterCrop={jest.fn()}
        onRefreshWholesalerRecommendation={jest.fn()}
        onRefreshPriceForecast={jest.fn()}
        onShowTransactions={jest.fn()}
      />
    )
    expect(screen.getByRole("button", { name: "작물 등록" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "AI 유통 추천" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "가격 분석" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "거래 현황" })).toBeInTheDocument()
  })

  it("invokes the matching callback when an action is clicked", () => {
    const onRegisterCrop = jest.fn()
    render(
      <QuickActionBar
        onRegisterCrop={onRegisterCrop}
        onRefreshWholesalerRecommendation={jest.fn()}
        onRefreshPriceForecast={jest.fn()}
        onShowTransactions={jest.fn()}
      />
    )
    fireEvent.click(screen.getByRole("button", { name: "작물 등록" }))
    expect(onRegisterCrop).toHaveBeenCalledTimes(1)
  })

  it("disables every action while busy", () => {
    render(
      <QuickActionBar
        onRegisterCrop={jest.fn()}
        onRefreshWholesalerRecommendation={jest.fn()}
        onRefreshPriceForecast={jest.fn()}
        onShowTransactions={jest.fn()}
        busy
      />
    )
    expect(screen.getByRole("button", { name: "작물 등록" })).toBeDisabled()
  })
})
