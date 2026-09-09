import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import ShipmentPlanForm from "@/components/ShipmentPlanForm"
import { createShipmentPlan, getCrops } from "@/lib/api"

jest.mock("@/lib/api", () => ({
  createShipmentPlan: jest.fn(),
  getCrops: jest.fn(),
  ApiError: class ApiError extends Error {},
}))

describe("ShipmentPlanForm", () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(getCrops as jest.Mock).mockResolvedValue([{ id: "crop-tomato", name: "토마토", unit: "kg" }])
  })

  it("loads crops into the dropdown", async () => {
    render(<ShipmentPlanForm farmerId="user-farmer-kim" onCreated={jest.fn()} onCancel={jest.fn()} />)
    await waitFor(() => expect(screen.getByRole("option", { name: "토마토" })).toBeInTheDocument())
  })

  it("shows a validation message when required fields are missing", async () => {
    render(<ShipmentPlanForm farmerId="user-farmer-kim" onCreated={jest.fn()} onCancel={jest.fn()} />)
    await waitFor(() => expect(getCrops).toHaveBeenCalled())
    fireEvent.click(screen.getByRole("button", { name: "등록" }))
    expect(screen.getByText("작물, 예상 수확량, 출하 예정일을 입력하세요")).toBeInTheDocument()
    expect(createShipmentPlan).not.toHaveBeenCalled()
  })

  it("submits the form and calls onCreated with the new plan", async () => {
    const created = {
      id: "shipment-new",
      farmer_user_id: "user-farmer-kim",
      smart_farm_id: null,
      crop_id: "crop-tomato",
      crop_name: "토마토",
      region: null,
      expected_yield_kg: 500,
      planned_shipment_date: "2026-09-01",
      grade: "특상품",
      status: "planned",
    }
    ;(createShipmentPlan as jest.Mock).mockResolvedValue(created)
    const onCreated = jest.fn()
    render(<ShipmentPlanForm farmerId="user-farmer-kim" onCreated={onCreated} onCancel={jest.fn()} />)
    await waitFor(() => expect(getCrops).toHaveBeenCalled())

    fireEvent.change(screen.getByLabelText(/예상 수확량/), { target: { value: "500" } })
    fireEvent.change(screen.getByLabelText(/출하 예정일/), { target: { value: "2026-09-01" } })
    fireEvent.click(screen.getByRole("button", { name: "등록" }))

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(created))
    expect(createShipmentPlan).toHaveBeenCalledWith({
      farmer_user_id: "user-farmer-kim",
      crop_id: "crop-tomato",
      expected_yield_kg: 500,
      planned_shipment_date: "2026-09-01",
      grade: "특상품",
      region: null,
    })
  })

  it("calls onCancel when the cancel button is clicked", () => {
    const onCancel = jest.fn()
    render(<ShipmentPlanForm farmerId="user-farmer-kim" onCreated={jest.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByRole("button", { name: "취소" }))
    expect(onCancel).toHaveBeenCalledTimes(1)
  })
})
