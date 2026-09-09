import { render, screen } from "@testing-library/react"
import IdleLandCard from "@/components/IdleLandCard"
import type { Farmland } from "@/lib/types"

const plot: Farmland = {
  id: "farmland-a",
  owner_user_id: "user-landowner-a",
  address: "충남 논산시 강경읍 A지구",
  region: "충남 논산시",
  area_pyeong: 900,
  monthly_rent_krw: 650000,
  has_water_access: true,
  has_cold_storage_access: true,
  distance_to_wholesaler_km: 24,
  soil_status: "양토, 배수 양호",
  condition_grade: "최상",
  status: "idle",
  latitude: 36.1605,
  longitude: 126.883,
}

describe("IdleLandCard", () => {
  it("renders the address, status, area and rent", () => {
    render(<IdleLandCard plot={plot} />)
    expect(screen.getByText("충남 논산시 강경읍 A지구")).toBeInTheDocument()
    expect(screen.getByText("상태 최상")).toBeInTheDocument()
    expect(screen.getByText("900평")).toBeInTheDocument()
  })

  it("links to the plot's detail page", () => {
    render(<IdleLandCard plot={plot} />)
    expect(screen.getByRole("link")).toHaveAttribute("href", "/idle-land/detail?id=farmland-a")
  })
})
