// Client-generated chat session id. Without one, every visitor's chat
// messages land in the same backend thread (per team-lead: the DAL groups
// by session_id, so no id means every browser shares one conversation).
// Generated once per browser and kept in localStorage so a page refresh
// continues the same thread instead of starting a new one.

const STORAGE_KEY = "s2w-chat-session-id"

export function getOrCreateChatSessionId(): string {
  if (typeof window === "undefined") return ""

  try {
    const existing = window.localStorage.getItem(STORAGE_KEY)
    if (existing) return existing

    const created = crypto.randomUUID()
    window.localStorage.setItem(STORAGE_KEY, created)
    return created
  } catch {
    // Storage unavailable (private browsing, disabled cookies, etc.) --
    // fall back to a session that only lives for this render.
    return crypto.randomUUID()
  }
}
