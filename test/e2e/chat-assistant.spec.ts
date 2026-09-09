import { test, expect } from "@playwright/test";

// SPEC "채팅 어시스턴트 패널": floating panel on every page, POST /api/chat,
// including the create_trade_request tool-call path (LLM_MOCK's keyword
// matcher -- see backend/app/llm/mock.py's _CREATE_REQUEST_RE). Also checks
// the session_id / user_id separation frontend just wired: each browser
// gets its own client-generated session_id (localStorage), independent of
// the backend's fixed demo-farmer user_id.

test.describe("채팅 어시스턴트", () => {
  test("패널을 열고 메시지를 보내면 응답을 받는다", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "AI 어시스턴트 열기" }).click();

    const dialog = page.getByRole("dialog", { name: "AI 어시스턴트" });
    await expect(dialog).toBeVisible();

    await dialog.getByPlaceholder("메시지를 입력하세요").fill("안녕하세요");
    await dialog.getByRole("button", { name: "전송" }).click();

    // First bubble is the echoed user message, second is the assistant reply.
    await expect(dialog.getByText("안녕하세요").first()).toBeVisible();
    await expect(dialog.getByText(/울퉁불퉁 농장 AI 어시스턴트입니다/)).toBeVisible({ timeout: 10_000 });
  });

  test("거래 요청 문장을 보내면 create_trade_request 툴콜이 실행된다", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "AI 어시스턴트 열기" }).click();
    const dialog = page.getByRole("dialog", { name: "AI 어시스턴트" });

    await dialog.getByPlaceholder("메시지를 입력하세요").fill("토마토 300kg B에 거래 요청");

    const [response] = await Promise.all([
      page.waitForResponse((res) => res.url().includes("/api/chat") && res.request().method() === "POST"),
      dialog.getByRole("button", { name: "전송" }).click(),
    ]);

    const body = await response.json();
    expect(body.tool_calls).toHaveLength(1);
    expect(body.tool_calls[0].name).toBe("create_trade_request");
    expect(body.tool_calls[0].error).toBeNull();
    expect(body.tool_calls[0].result.counterparty_type).toBe("wholesaler");
    expect(body.tool_calls[0].result.status).toBe("requested");

    // Tool outcome is surfaced under the assistant bubble as "<name>: 완료".
    await expect(dialog.getByText("create_trade_request: 완료")).toBeVisible();
  });

  test("서로 다른 브라우저(세션)는 각자 다른 session_id로 대화 기록이 분리된다", async ({ browser }) => {
    const contextA = await browser.newContext();
    const contextB = await browser.newContext();
    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();

    async function sendAndCaptureSessionId(page: import("@playwright/test").Page, message: string) {
      await page.goto("/");
      await page.getByRole("button", { name: "AI 어시스턴트 열기" }).click();
      const dialog = page.getByRole("dialog", { name: "AI 어시스턴트" });
      await dialog.getByPlaceholder("메시지를 입력하세요").fill(message);
      // Wait for the response, not just the request -- the backend inserts
      // both chat_messages rows (user, then assistant) before it responds,
      // so reading history right after the request is sent (not answered)
      // races the insert and flakes.
      const [response] = await Promise.all([
        page.waitForResponse((res) => res.url().includes("/api/chat") && res.request().method() === "POST"),
        dialog.getByRole("button", { name: "전송" }).click(),
      ]);
      const payload = response.request().postDataJSON() as { session_id: string };
      return payload.session_id;
    }

    const markerA = `세션A 확인용 ${Date.now()}`;
    const markerB = `세션B 확인용 ${Date.now()}`;
    const [sessionIdA, sessionIdB] = await Promise.all([
      sendAndCaptureSessionId(pageA, markerA),
      sendAndCaptureSessionId(pageB, markerB),
    ]);

    expect(sessionIdA).toBeTruthy();
    expect(sessionIdB).toBeTruthy();
    expect(sessionIdA).not.toBe(sessionIdB);

    const api = pageA.request;
    const historyA = await (await api.get(`/api/chat/history?session_id=${sessionIdA}`)).json();
    const historyB = await (await api.get(`/api/chat/history?session_id=${sessionIdB}`)).json();

    expect(historyA.some((m: { content: string }) => m.content === markerA)).toBe(true);
    expect(historyA.some((m: { content: string }) => m.content === markerB)).toBe(false);
    expect(historyB.some((m: { content: string }) => m.content === markerB)).toBe(true);
    expect(historyB.some((m: { content: string }) => m.content === markerA)).toBe(false);

    await contextA.close();
    await contextB.close();
  });
});
