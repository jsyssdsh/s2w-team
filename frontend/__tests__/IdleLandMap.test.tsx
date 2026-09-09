import { render, screen } from "@testing-library/react"
import IdleLandMap from "@/components/IdleLandMap"
import type { Farmland } from "@/lib/types"

function plot(overrides: Partial<Farmland>): Farmland {
  return {
    id: "farmland-a",
    owner_user_id: "user-landowner-a",
    address: "A 농지",
    region: "충남 논산시",
    area_pyeong: 900,
    monthly_rent_krw: 650000,
    has_water_access: true,
    has_cold_storage_access: true,
    distance_to_wholesaler_km: 24,
    soil_status: null,
    condition_grade: "최상",
    status: "idle",
    latitude: null,
    longitude: null,
    ...overrides,
  }
}

describe("IdleLandMap", () => {
  it("shows an empty message when there are no plots", () => {
    render(<IdleLandMap plots={[]} />)
    expect(screen.getByText("표시할 유휴토지가 없습니다")).toBeInTheDocument()
  })

  it("plots real coordinates as markers when every plot has them", () => {
    render(
      <IdleLandMap
        plots={[
          plot({ id: "a", address: "A 농지", latitude: 36.16, longitude: 126.88 }),
          plot({ id: "b", address: "B 농지", latitude: 36.15, longitude: 126.89, condition_grade: "개선필요" }),
        ]}
      />
    )
    expect(screen.getByRole("img", { name: "유휴토지 위치와 상태를 나타낸 지도" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "A 농지, 상태 최상" })).toHaveAttribute(
      "href",
      "/idle-land/detail?id=a"
    )
    expect(screen.getByRole("link", { name: "B 농지, 개선 필요" })).toBeInTheDocument()
  })

  it("falls back to grouping by region when any plot is missing coordinates", () => {
    render(
      <IdleLandMap
        plots={[
          plot({ id: "a", address: "A 농지", region: "충남 논산시", latitude: 36.16, longitude: 126.88 }),
          plot({ id: "b", address: "B 농지", region: "충남 부여군", latitude: null, longitude: null }),
        ]}
      />
    )
    expect(screen.queryByRole("img")).not.toBeInTheDocument()
    expect(screen.getByText(/충남 논산시/)).toBeInTheDocument()
    expect(screen.getByText(/충남 부여군/)).toBeInTheDocument()
  })

  it("falls back to a placeholder region label when region is missing", () => {
    render(<IdleLandMap plots={[plot({ region: null })]} />)
    expect(screen.getByText(/지역 미상/)).toBeInTheDocument()
  })
})
