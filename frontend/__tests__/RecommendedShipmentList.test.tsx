import { render, screen, waitFor } from "@testing-library/react"
import { fireEvent } from "@testing-library/react"
import RecommendedShipmentList from "@/components/RecommendedShipmentList"
import { createTransaction } from "@/lib/api"
import type { RecommendedFarmerShipment } from "@/lib/types"

jest.mock("@/lib/api", () => ({
  createTransaction: jest.fn(),
  ApiError: class ApiError extends Error {},
}))

const shipments: RecommendedFarmerShipment[] = [
  {
    shipment_plan_id: "shipment-tomato-main",
    farmer_user_id: "user-farmer-kim",
    crop_name: "토마토",
    expected_yield_kg: 1000,
    planned_shipment_date: "2026-08-10",
    grade: "특상품",
    recommended_trade_price_krw_per_kg: 2580,
  },
]

describe("RecommendedShipmentList", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("shows an empty message when there are no shipments", () => {
    render(<RecommendedShipmentList shipments={[]} wholesalerId="wholesaler-b" />)
    expect(screen.getByText("추천 가능한 농가 출하 계획이 아직 없습니다.")).toBeInTheDocument()
  })

  it("renders shipment details", () => {
    render(<RecommendedShipmentList shipments={shipments} wholesalerId="wholesaler-b" />)
    expect(screen.getByText("토마토")).toBeInTheDocument()
    expect(screen.getByText("특상품")).toBeInTheDocument()
    expect(screen.getByText("1,000kg")).toBeInTheDocument()
  })

  it("sends a trade request as a transaction and shows confirmation", async () => {
    ;(createTransaction as jest.Mock).mockResolvedValue({ id: "txn-1", status: "requested" })
    render(<RecommendedShipmentList shipments={shipments} wholesalerId="wholesaler-b" />)

    fireEvent.click(screen.getByRole("button", { name: "거래 요청 보내기" }))

    await waitFor(() => expect(screen.getByRole("button", { name: "요청 완료" })).toBeInTheDocument())
    expect(createTransaction).toHaveBeenCalledWith({
      shipment_plan_id: "shipment-tomato-main",
      counterparty_type: "wholesaler",
      wholesaler_id: "wholesaler-b",
      quantity_kg: 1000,
      unit_price_krw_per_kg: 2580,
    })
  })

  it("shows an inline error if the request fails", async () => {
    ;(createTransaction as jest.Mock).mockRejectedValue(new Error("failed"))
    render(<RecommendedShipmentList shipments={shipments} wholesalerId="wholesaler-b" />)

    fireEvent.click(screen.getByRole("button", { name: "거래 요청 보내기" }))

    await waitFor(() => expect(screen.getByText("전송 실패, 다시 시도하세요")).toBeInTheDocument())
  })
})
