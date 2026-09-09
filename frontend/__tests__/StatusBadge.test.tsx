import { render, screen } from "@testing-library/react"
import StatusBadge from "@/components/StatusBadge"

describe("StatusBadge", () => {
  it("labels 최상 condition in Korean, not just color", () => {
    render(<StatusBadge grade="최상" />)
    expect(screen.getByText("상태 최상")).toBeInTheDocument()
  })

  it("labels 양호 condition", () => {
    render(<StatusBadge grade="양호" />)
    expect(screen.getByText("상태 양호")).toBeInTheDocument()
  })

  it("labels 개선필요 condition", () => {
    render(<StatusBadge grade="개선필요" />)
    expect(screen.getByText("개선 필요")).toBeInTheDocument()
  })

  it("always pairs the label with an icon so color is not the only signal", () => {
    const { container } = render(<StatusBadge grade="개선필요" />)
    expect(container.querySelector("svg")).toBeInTheDocument()
  })
})
