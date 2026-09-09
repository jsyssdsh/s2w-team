import { render, screen } from "@testing-library/react"
import LandOverviewPanel from "@/components/LandOverviewPanel"
import type { FarmlandDetail } from "@/lib/types"

const land: FarmlandDetail = {
  id: "farmland-existing",
  owner_user_id: "user-landowner-existing",
  address: "충남 논산시 연무읍 D지구",
  region: "충남 논산시",
  area_pyeong: 1200,
  monthly_rent_krw: 600000,
  has_water_access: true,
  has_cold_storage_access: true,
  distance_to_wholesaler_km: 17,
  soil_status: "양토, 배수 양호",
  condition_grade: "양호",
  status: "operating",
  latitude: 36.1074,
  longitude: 127.0512,
  smart_farm: {
    id: "smart-farm-tomato",
    farm_type: "시설하우스 수경재배",
    operation_start_date: "2026-03-01",
    latest_sensor_readings: { temperature: 25 },
  },
}

describe("LandOverviewPanel", () => {
  it("renders address, status badge and occupancy label", () => {
    render(<LandOverviewPanel land={land} />)
    expect(screen.getByText("충남 논산시 연무읍 D지구")).toBeInTheDocument()
    expect(screen.getByText("상태 양호")).toBeInTheDocument()
    expect(screen.getByText(/운영 중/)).toBeInTheDocument()
  })

  it("renders the smart farm type and operation start date when present", () => {
    render(<LandOverviewPanel land={land} />)
    expect(screen.getByText("시설하우스 수경재배")).toBeInTheDocument()
  })

  it("omits the smart farm block when there is none", () => {
    render(<LandOverviewPanel land={{ ...land, smart_farm: null }} />)
    expect(screen.queryByText("스마트팜 유형")).not.toBeInTheDocument()
  })
})
