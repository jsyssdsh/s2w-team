import { render, screen, waitFor } from "@testing-library/react"
import { fireEvent } from "@testing-library/react"
import ChatPanel from "@/components/ChatPanel"
import { sendChatMessage } from "@/lib/api"

jest.mock("@/lib/api", () => ({
  sendChatMessage: jest.fn(),
  ApiError: class ApiError extends Error {},
}))

describe("ChatPanel", () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it("starts collapsed as a floating open button", () => {
    render(<ChatPanel />)
    expect(screen.getByRole("button", { name: "AI 어시스턴트 열기" })).toBeInTheDocument()
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
  })

  it("opens the panel when the button is clicked", () => {
    render(<ChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: "AI 어시스턴트 열기" }))
    expect(screen.getByRole("dialog", { name: "AI 어시스턴트" })).toBeInTheDocument()
  })

  it("sends a message with a session id and renders the assistant's reply", async () => {
    ;(sendChatMessage as jest.Mock).mockResolvedValue({
      message: "토마토 시세는 상승세입니다",
      tool_calls: [],
      session_id: "session-1",
    })
    render(<ChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: "AI 어시스턴트 열기" }))

    fireEvent.change(screen.getByPlaceholderText("메시지를 입력하세요"), { target: { value: "토마토 시세 알려줘" } })
    fireEvent.click(screen.getByRole("button", { name: "전송" }))

    expect(screen.getByText("토마토 시세 알려줘")).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText("토마토 시세는 상승세입니다")).toBeInTheDocument())
    expect(sendChatMessage).toHaveBeenCalledWith("토마토 시세 알려줘", expect.any(String))
  })

  it("renders a tool call outcome alongside the reply", async () => {
    ;(sendChatMessage as jest.Mock).mockResolvedValue({
      message: "거래 요청을 보냈습니다",
      tool_calls: [{ name: "create_trade_request", arguments: {}, result: { id: "txn-1" }, error: null }],
    })
    render(<ChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: "AI 어시스턴트 열기" }))
    fireEvent.change(screen.getByPlaceholderText("메시지를 입력하세요"), { target: { value: "B 도매처에 거래 요청 보내줘" } })
    fireEvent.click(screen.getByRole("button", { name: "전송" }))

    await waitFor(() => expect(screen.getByText(/create_trade_request/)).toBeInTheDocument())
  })

  it("shows an error message if the request fails", async () => {
    ;(sendChatMessage as jest.Mock).mockRejectedValue(new Error("network error"))
    render(<ChatPanel />)
    fireEvent.click(screen.getByRole("button", { name: "AI 어시스턴트 열기" }))

    fireEvent.change(screen.getByPlaceholderText("메시지를 입력하세요"), { target: { value: "안녕" } })
    fireEvent.click(screen.getByRole("button", { name: "전송" }))

    await waitFor(() => expect(screen.getByText("응답을 받지 못했습니다")).toBeInTheDocument())
  })
})
