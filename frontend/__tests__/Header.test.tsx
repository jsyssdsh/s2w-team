import { render, screen } from "@testing-library/react"
import Header from "@/components/Header"

jest.mock("next/navigation", () => ({
  usePathname: () => "/farm",
}))

describe("Header", () => {
  it("renders the brand name", () => {
    render(<Header />)
    expect(screen.getByText("울퉁불퉁 농장 AI")).toBeInTheDocument()
  })

  it("renders links to every screen", () => {
    render(<Header />)
    expect(screen.getByRole("link", { name: "홈" })).toHaveAttribute("href", "/")
    expect(screen.getByRole("link", { name: "농가 대시보드" })).toHaveAttribute("href", "/farm")
    expect(screen.getByRole("link", { name: "유통업체 대시보드" })).toHaveAttribute("href", "/distributor")
    expect(screen.getByRole("link", { name: "유휴토지 지도" })).toHaveAttribute("href", "/idle-land")
  })

  it("marks the current page as active", () => {
    render(<Header />)
    expect(screen.getByRole("link", { name: "농가 대시보드" })).toHaveAttribute("aria-current", "page")
    expect(screen.getByRole("link", { name: "홈" })).not.toHaveAttribute("aria-current")
  })
})
