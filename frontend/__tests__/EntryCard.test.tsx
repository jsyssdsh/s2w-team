import { render, screen } from "@testing-library/react"
import EntryCard from "@/components/EntryCard"

describe("EntryCard", () => {
  it("renders title, description and links to href", () => {
    render(
      <EntryCard href="/farm" title="농가 대시보드" description="설명 텍스트" accent="#2f5233" />
    )
    expect(screen.getByText("농가 대시보드")).toBeInTheDocument()
    expect(screen.getByText("설명 텍스트")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /농가 대시보드/ })).toHaveAttribute("href", "/farm")
  })
})
