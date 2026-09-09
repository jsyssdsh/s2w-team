import { render, screen } from "@testing-library/react"
import SensorHistoryChart from "@/components/SensorHistoryChart"
import type { SensorReadingRow } from "@/lib/types"

function row(overrides: Partial<SensorReadingRow>): SensorReadingRow {
  return {
    id: "reading-1",
    smart_farm_id: "smart-farm-tomato",
    metric: "temperature",
    value: 25,
    unit: "°C",
    measured_at: "2026-08-10T09:00:00Z",
    ...overrides,
  }
}

describe("SensorHistoryChart", () => {
  it("shows a loading message when fewer than two readings are available", () => {
    render(<SensorHistoryChart rows={[]} />)
    expect(screen.getByText("센서 변화 데이터를 불러오는 중입니다")).toBeInTheDocument()
  })

  it("renders a chart container when enough readings exist", () => {
    const { container } = render(
      <SensorHistoryChart
        rows={[row({ value: 25, measured_at: "2026-08-10T09:00:00Z" }), row({ value: 29.4, measured_at: "2026-08-10T10:00:00Z" })]}
      />
    )
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument()
  })
})
