import { test, expect } from "@playwright/test";

// SPEC 4.3: 유통업체 대시보드 -- summary stats, AI-recommended farm shipments,
// and "거래 요청 보내기" actually calling POST /api/transactions. Navigates
// via the home entry card (see home.spec.ts: direct page.goto("/distributor")
// 404s in this static-export + FastAPI topology).

async function gotoDistributorDashboard(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByRole("region", { name: "화면 선택" }).getByRole("link", { name: /^유통업체 대시보드/ }).click();
  await expect(page.getByRole("heading", { name: "유통업체 대시보드", level: 1 })).toBeVisible();
}

test.describe("유통업체 대시보드", () => {
  test("요약 3지표와 AI 추천 농가 출하 목록이 표시된다", async ({ page }) => {
    await gotoDistributorDashboard(page);

    await expect(page.getByText("공급 가능 건수")).toBeVisible();
    await expect(page.getByText("AI 추천 건수")).toBeVisible();
    await expect(page.getByText("예상 금액")).toBeVisible();

    const section = page.getByRole("region", { name: "AI 추천 농가 출하 계획" });
    await expect(section).toBeVisible();
    await expect(section.getByRole("button", { name: "거래 요청 보내기" }).first()).toBeVisible();
  });

  test("거래 요청 보내기를 누르면 실제 거래가 생성된다", async ({ page }) => {
    await gotoDistributorDashboard(page);

    const section = page.getByRole("region", { name: "AI 추천 농가 출하 계획" });
    const firstRow = section.getByRole("row").nth(1); // nth(0) is the header row
    const requestButton = firstRow.getByRole("button", { name: "거래 요청 보내기" });
    await expect(requestButton).toBeVisible();

    const [response] = await Promise.all([
      page.waitForResponse((res) => res.url().includes("/api/transactions") && res.request().method() === "POST"),
      requestButton.click(),
    ]);

    expect(response.status()).toBe(201);
    const body = await response.json();
    expect(body.status).toBe("requested");
    expect(body.counterparty_type).toBe("wholesaler");

    // Button reflects the sent state and is disabled against double-submit.
    await expect(firstRow.getByRole("button", { name: "요청 완료" })).toBeVisible();
    await expect(firstRow.getByRole("button", { name: "요청 완료" })).toBeDisabled();
  });

  test("실시간 시장 분석 패널에 품목별 가격이 표시된다", async ({ page }) => {
    await gotoDistributorDashboard(page);

    const section = page.getByRole("region", { name: "실시간 시장 분석" });
    // Fed by the /api/stream/prices SSE feed -- allow it a moment to arrive.
    await expect(section.getByText("토마토")).toBeVisible({ timeout: 15_000 });
    await expect(section.getByText(/₩[\d,]+\/kg/).first()).toBeVisible();
  });
});
