import { render, screen } from "@testing-library/react"
import StatRow, { type Stat } from "@/components/StatRow"

describe("StatRow", () => {
  it("renders each stat's label and value", () => {
    const stats: Stat[] = [
      { label: "운영 중", value: "12건", accent: "forest" },
      { label: "전환 완료", value: "4건" },
    ]
    render(<StatRow stats={stats} />)
    expect(screen.getByText("운영 중")).toBeInTheDocument()
    expect(screen.getByText("12건")).toBeInTheDocument()
    expect(screen.getByText("전환 완료")).toBeInTheDocument()
    expect(screen.getByText("4건")).toBeInTheDocument()
  })
})
