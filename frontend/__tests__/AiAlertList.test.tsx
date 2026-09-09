import { render, screen } from "@testing-library/react"
import AiAlertList from "@/components/AiAlertList"
import type { AiAlert } from "@/lib/types"

describe("AiAlertList", () => {
  it("shows an empty message when there are no alerts", () => {
    render(<AiAlertList alerts={[]} />)
    expect(screen.getByText("현재 표시할 AI 분석 알림이 없습니다.")).toBeInTheDocument()
  })

  it("renders each alert message with a severity label", () => {
    const alerts: AiAlert[] = [
      { id: "1", severity: "warning", message: "시장 가격 상승 가능성이 있습니다", createdAt: "2026-08-10T09:00:00Z" },
      { id: "2", severity: "info", message: "즉시 출하 가능", createdAt: "2026-08-10T10:00:00Z" },
    ]
    render(<AiAlertList alerts={alerts} />)
    expect(screen.getByText("시장 가격 상승 가능성이 있습니다")).toBeInTheDocument()
    expect(screen.getByText("즉시 출하 가능")).toBeInTheDocument()
    expect(screen.getByText("주의")).toBeInTheDocument()
    expect(screen.getByText("안내")).toBeInTheDocument()
  })
})
