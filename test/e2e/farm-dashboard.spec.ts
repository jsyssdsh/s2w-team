import { test, expect } from "@playwright/test";

// SPEC 4.2 / 5.1 / 5.2: 농가 대시보드 flow -- shipment summary, smart-farm
// sensors, then the AI wholesaler ranking with net-profit and rationale.
// Navigates via the home entry card (see home.spec.ts for why: direct
// page.goto("/farm") 404s in this static-export + FastAPI topology).

async function gotoFarmDashboard(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByRole("region", { name: "화면 선택" }).getByRole("link", { name: /^농가 대시보드/ }).click();
  await expect(page.getByRole("heading", { name: "농가 대시보드", level: 1 })).toBeVisible();
}

test.describe("농가 대시보드", () => {
  test("작물 요약과 스마트팜 센서 상태가 표시된다", async ({ page }) => {
    await gotoFarmDashboard(page);

    // Seeded demo farmer (user-farmer-kim) has a tomato shipment plan active by default.
    await expect(page.getByRole("heading", { name: "토마토", level: 2 })).toBeVisible();
    await expect(page.getByText("예상 수확량")).toBeVisible();
    await expect(page.getByText("현재 도매가")).toBeVisible();

    const smartFarmSection = page.getByRole("region", { name: "스마트팜 상태" });
    await expect(smartFarmSection.getByText("온도")).toBeVisible();
    await expect(smartFarmSection.getByText("습도")).toBeVisible();
    await expect(smartFarmSection.getByText("토양수분")).toBeVisible();
    await expect(smartFarmSection.getByText("조도")).toBeVisible();
  });

  test("AI 추천 도매처 목록에 예상 순수익과 추천 근거가 표시된다", async ({ page }) => {
    await gotoFarmDashboard(page);

    const section = page.getByRole("region", { name: "AI 추천 도매처" });
    await expect(section).toBeVisible({ timeout: 15_000 });

    const items = section.getByRole("listitem");
    await expect(items).not.toHaveCount(0);

    // Ranked options each carry a net-profit figure and an explanation
    // sentence (SPEC 5.2's "예상 순수익" / recommendation rationale).
    const first = items.first();
    await expect(first.getByText(/순수익 ₩/)).toBeVisible();
    await expect(first.getByText(/1순위/)).toBeVisible();
    await expect(first.locator("p")).not.toBeEmpty();
  });

  test("작물 등록 -> AI 유통 추천 -> 추천 근거 확인", async ({ page }) => {
    await gotoFarmDashboard(page);

    await page.getByRole("button", { name: "작물 등록" }).click();
    const form = page.getByRole("form", { name: "작물 등록" });
    await expect(form).toBeVisible();

    await form.getByLabel("예상 수확량(kg)").fill("500");
    await form.getByLabel("출하 예정일").fill("2026-09-20");
    await form.getByRole("button", { name: "등록" }).click();

    // New plan becomes active -> its crop button appears selected and the
    // AI wholesaler recommendation reloads for it automatically.
    await expect(form).toBeHidden();
    const wholesalerSection = page.getByRole("region", { name: "AI 추천 도매처" });
    await expect(wholesalerSection).toBeVisible({ timeout: 15_000 });
    await expect(wholesalerSection.getByRole("listitem").first().locator("p")).not.toBeEmpty();
  });
});
