import { test, expect } from "@playwright/test";

// SPEC 4.4 / 4.5: 유휴토지 지도 -> 상세 -> 실시간 센서 갱신. Map renders as a
// coordinate-based scatter plot (role="img", aria-label "유휴토지 위치와
// 상태를 나타낸 지도"), each plot a <Link> with
// aria-label="{주소}, {상태 라벨}" (labels: 상태 최상/상태 양호/개선 필요,
// shared with StatusBadge via lib/condition-grade.ts). Confirmed with
// frontend -- seeded farmland-a/b/c/existing all carry real coordinates.

test.describe("유휴토지 지도", () => {
  test("지도에 상태별로 색상이 구분된 마커가 표시된다", async ({ page }) => {
    await page.goto("/idle-land/");

    const map = page.getByRole("img", { name: "유휴토지 위치와 상태를 나타낸 지도" });
    await expect(map).toBeVisible();

    // Seeded data spans all three condition grades -- confirms the map
    // isn't just rendering one status for every plot.
    await expect(map.getByRole("link", { name: /상태 최상$/ }).first()).toBeVisible();
    await expect(map.getByRole("link", { name: /상태 양호$/ })).toBeVisible();
    await expect(map.getByRole("link", { name: /개선 필요$/ })).toBeVisible();
  });

  test("마커를 클릭하면 해당 토지의 상세 페이지로 이동한다", async ({ page }) => {
    await page.goto("/idle-land/");

    const map = page.getByRole("img", { name: "유휴토지 위치와 상태를 나타낸 지도" });
    const marker = map.getByRole("link", { name: "충남 논산시 강경읍 A지구, 상태 최상" });
    await marker.click();

    await expect(page).toHaveURL(/\/idle-land\/detail\/\?id=farmland-a$/);
    await expect(page.getByRole("heading", { name: "유휴토지 상세" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "충남 논산시 강경읍 A지구", level: 2 })).toBeVisible();

    // SPEC 4.5: area, water access, cold-storage access, soil status.
    // farmland-a has no smart_farm in the seed (see db/seed.sql -- only
    // farmland-existing does), so the smart-farm/sensor sections don't
    // apply here; that's covered by the farmland-existing case below.
    await expect(page.getByText("900평")).toBeVisible();
    await expect(page.getByText("양토, 배수 양호")).toBeVisible();
  });

  test("상세 페이지의 실시간 센서 값이 갱신된다", async ({ page }) => {
    await page.goto("/idle-land/detail/?id=farmland-existing");

    const sensorSection = page.getByRole("region", { name: "실시간 센서" });
    await expect(sensorSection.getByText("실시간 연동 중")).toBeVisible({ timeout: 15_000 });

    const tempValue = sensorSection.getByText(/\d+\.\d°C/);
    await expect(tempValue).toBeVisible();
    const initial = await tempValue.textContent();

    await expect(tempValue).not.toHaveText(initial ?? "", { timeout: 10_000 });
  });
});
