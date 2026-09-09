"use client"

import { useEffect, useRef, useState } from "react"
import type { ToolCallOutcome } from "@/lib/types"
import { sendChatMessage, ApiError } from "@/lib/api"
import { getOrCreateChatSessionId } from "@/lib/chat-session"

interface DisplayMessage {
  id: string
  role: "user" | "assistant"
  content: string
  toolCalls?: ToolCallOutcome[]
}

// Floating assistant available from every screen (SPEC "채팅 어시스턴트 패널")
// rather than pinned to one dashboard, since a farmer or distributor may want
// to ask about or act on data while looking at any page.
//
// session_id (client-generated, kept in localStorage) separates this
// browser's conversation history from everyone else's; it is independent of
// the backend's user_id, which stays at its default demo farmer so the
// chat's trade-request tools keep finding real seeded shipment plans
// (confirmed with backend -- see lib/api.ts sendChatMessage).
export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: text }])
    setInput("")
    setLoading(true)

    try {
      const res = await sendChatMessage(text, getOrCreateChatSessionId())
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: res.message, toolCalls: res.tool_calls },
      ])
    } catch (err) {
      const content = err instanceof ApiError ? err.message : "응답을 받지 못했습니다"
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content }])
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label="AI 어시스턴트 열기"
        className="fixed bottom-5 right-5 z-40 rounded-full bg-forest px-4 py-3 text-sm font-medium text-paper-raised shadow-lg transition-transform hover:scale-105"
      >
        AI 어시스턴트
      </button>
    )
  }

  return (
    <div
      role="dialog"
      aria-label="AI 어시스턴트"
      className="fixed bottom-5 right-5 z-40 flex h-[32rem] w-80 flex-col rounded border border-line bg-paper-raised shadow-xl"
    >
      <div className="flex items-center justify-between border-b border-line px-3 py-2">
        <h2 className="font-display text-sm font-bold text-ink">AI 어시스턴트</h2>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          aria-label="AI 어시스턴트 닫기"
          className="text-ink-muted hover:text-ink"
        >
          닫기
        </button>
      </div>

      <div ref={scrollRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
        {messages.length === 0 && (
          <p className="mt-4 text-center text-xs text-ink-muted">
            시세, 추천 도매처, 거래 실행에 대해 물어보세요.
          </p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`text-sm ${msg.role === "user" ? "text-right" : "text-left"}`}>
            <div
              className={`inline-block max-w-[90%] rounded px-3 py-2 text-left ${
                msg.role === "user" ? "bg-forest text-paper-raised" : "bg-paper text-ink"
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="mt-2 space-y-1 border-t border-line/40 pt-2 text-xs">
                  {msg.toolCalls.map((tc, i) => (
                    <div key={i} className={tc.error ? "text-status-bad" : "text-forest-deep"}>
                      {tc.name}: {tc.error ?? "완료"}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-ink-muted">답변을 생각하는 중...</div>}
      </div>

      <div className="border-t border-line p-2">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="메시지를 입력하세요"
            disabled={loading}
            className="flex-1 rounded border border-line bg-paper px-2 py-1.5 text-sm text-ink placeholder:text-ink-faint focus:outline-none focus:border-forest disabled:opacity-50"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="rounded bg-forest px-3 py-1.5 text-sm font-medium text-paper-raised transition-colors hover:bg-forest-deep disabled:opacity-50"
          >
            전송
          </button>
        </div>
      </div>
    </div>
  )
}
