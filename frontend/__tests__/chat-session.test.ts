import { getOrCreateChatSessionId } from "@/lib/chat-session"

describe("getOrCreateChatSessionId", () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it("creates and persists a session id on first call", () => {
    const id = getOrCreateChatSessionId()
    expect(id).toMatch(/^[0-9a-f-]{36}$/)
    expect(window.localStorage.getItem("s2w-chat-session-id")).toBe(id)
  })

  it("returns the same id across calls so a refresh continues the thread", () => {
    const first = getOrCreateChatSessionId()
    const second = getOrCreateChatSessionId()
    expect(second).toBe(first)
  })

  it("falls back to a fresh id when storage throws", () => {
    const getItemSpy = jest.spyOn(window.localStorage.__proto__, "getItem").mockImplementation(() => {
      throw new Error("storage disabled")
    })
    const id = getOrCreateChatSessionId()
    expect(id).toMatch(/^[0-9a-f-]{36}$/)
    getItemSpy.mockRestore()
  })
})
