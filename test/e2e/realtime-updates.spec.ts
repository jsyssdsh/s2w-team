import { test, expect } from "@playwright/test";

// SPEC "SSE 실시간 가격/센서 갱신": /api/stream/sensors (2s tick, backend/app/
// market/sensor_simulator.py) drives 농가 대시보드's smart-farm readings,
// /api/stream/prices (1s tick) drives 유통업체 대시보드's market panel.
// Both are mean-reverting random walks, so waiting a few ticks should
// reliably produce a different displayed value without pinning down the
// exact number.

test.describe("SSE 실시간 갱신", () => {
  test("농가 대시보드의 스마트팜 센서 값이 실시간으로 갱신된다", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("region", { name: "화면 선택" }).getByRole("link", { name: /^농가 대시보드/ }).click();

    const smartFarmSection = page.getByRole("region", { name: "스마트팜 상태" });
    await expect(smartFarmSection.getByText("실시간 연동 중")).toBeVisible({ timeout: 15_000 });

    const tempValue = smartFarmSection.getByText(/\d+\.\d°C/);
    await expect(tempValue).toBeVisible();
    const initial = await tempValue.textContent();

    await expect(tempValue).not.toHaveText(initial ?? "", { timeout: 10_000 });
  });

  test("유통업체 대시보드의 시세가 실시간으로 갱신된다", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("region", { name: "화면 선택" }).getByRole("link", { name: /^유통업체 대시보드/ }).click();

    const marketSection = page.getByRole("region", { name: "실시간 시장 분석" });
    const tomatoRow = marketSection.getByText("토마토").locator("..");
    await expect(tomatoRow.getByText(/₩[\d,]+\/kg/)).toBeVisible({ timeout: 15_000 });

    const priceCell = tomatoRow.getByText(/₩[\d,]+\/kg/);
    const initial = await priceCell.textContent();

    await expect(priceCell).not.toHaveText(initial ?? "", { timeout: 10_000 });
  });
});
