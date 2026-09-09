import { render, screen } from "@testing-library/react"
import TransactionList from "@/components/TransactionList"
import type { Transaction } from "@/lib/types"

const txn: Transaction = {
  id: "txn-1",
  shipment_plan_id: "shipment-tomato-main",
  wholesaler_id: "wholesaler-b",
  retailer_id: null,
  counterparty_type: "wholesaler",
  recommendation_id: null,
  quantity_kg: 1000,
  unit_price_krw_per_kg: 2580,
  transport_cost_krw: 80000,
  commission_krw: 77400,
  net_profit_krw: 2422600,
  status: "requested",
  requested_at: "2026-08-10T00:00:00Z",
  updated_at: "2026-08-10T00:00:00Z",
}

describe("TransactionList", () => {
  it("shows an empty message when there are no transactions", () => {
    render(<TransactionList transactions={[]} />)
    expect(screen.getByText("등록된 거래 요청이 없습니다.")).toBeInTheDocument()
  })

  it("renders counterparty type, quantity, price and status", () => {
    render(<TransactionList transactions={[txn]} />)
    expect(screen.getByText("도매처")).toBeInTheDocument()
    expect(screen.getByText("1,000kg")).toBeInTheDocument()
    expect(screen.getByText("요청됨")).toBeInTheDocument()
  })
})
