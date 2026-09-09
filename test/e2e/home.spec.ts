import { test, expect } from "@playwright/test";

// SPEC 4.1: home shows three role entry points. next.config.ts sets
// trailingSlash: true (fixes the static-export + FastAPI routing gap this
// suite flagged), so every route URL ends in "/".

test.describe("홈 화면", () => {
  test("농가/유통업체/유휴토지 3개 진입점이 보인다", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "농가 대시보드", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "유통업체 대시보드", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "유휴토지 지도", exact: true })).toBeVisible();
  });

  test("농가 대시보드 진입점을 클릭하면 /farm으로 이동한다", async ({ page }) => {
    await page.goto("/");
    // Header also has a nav link with the exact same accessible name, so
    // scope to the entry-card section (labelled "화면 선택") to stay unique.
    const entrySection = page.getByRole("region", { name: "화면 선택" });
    await entrySection.getByRole("link", { name: /^농가 대시보드/ }).click();

    await expect(page).toHaveURL(/\/farm\/$/);
    await expect(page.getByRole("heading", { name: "농가 대시보드", level: 1 })).toBeVisible();
  });

  test("유통업체 대시보드 진입점을 클릭하면 /distributor로 이동한다", async ({ page }) => {
    await page.goto("/");
    const entrySection = page.getByRole("region", { name: "화면 선택" });
    await entrySection.getByRole("link", { name: /^유통업체 대시보드/ }).click();

    await expect(page).toHaveURL(/\/distributor\/$/);
    await expect(page.getByRole("heading", { name: "유통업체 대시보드", level: 1 })).toBeVisible();
  });

  test("유휴토지 지도 진입점을 클릭하면 /idle-land로 이동한다", async ({ page }) => {
    await page.goto("/");
    const entrySection = page.getByRole("region", { name: "화면 선택" });
    await entrySection.getByRole("link", { name: /^유휴토지 지도/ }).click();

    await expect(page).toHaveURL(/\/idle-land\/$/);
  });
});
