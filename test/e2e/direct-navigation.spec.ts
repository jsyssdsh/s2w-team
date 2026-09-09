import { test, expect } from "@playwright/test";

// Regression test for a real bug found while writing the click-through specs:
// next.config.ts's static export (output: "export") wrote route pages as
// sibling *.html files (e.g. farm.html) next to Next's RSC-payload
// directories (farm/), and FastAPI's StaticFiles(html=True) mount only
// auto-resolves index.html *inside* a directory. Client-side <Link>
// navigation worked (it never re-requests the HTML document), but a direct
// page.goto -- exactly what a bookmark, shared link, or browser refresh
// does -- hard 404'd on every route except "/". Fixed with
// next.config.ts's trailingSlash: true (export now writes farm/index.html
// etc.), confirmed against the rebuilt Docker image by devops.
//
// This must not be skipped or weakened -- it is the only spec in this
// suite that actually exercises page.goto() on these routes instead of
// clicking a Link, which is what let the original bug slip past every
// other spec here.

test.describe("직접 진입 (새로고침/북마크/공유 링크) 회귀 테스트", () => {
  test("/ 로 직접 진입하면 200과 함께 홈이 렌더링된다", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.status()).toBe(200);
    await expect(page.getByRole("heading", { name: "농가 대시보드", exact: true })).toBeVisible();
  });

  test("/farm/ 로 직접 진입하면 200과 함께 농가 대시보드가 렌더링된다", async ({ page }) => {
    const response = await page.goto("/farm/");
    expect(response?.status()).toBe(200);
    await expect(page.getByRole("heading", { name: "농가 대시보드", level: 1 })).toBeVisible();
    // Not just the shell -- confirm data actually loaded via the API.
    await expect(page.getByText("예상 수확량")).toBeVisible();
  });

  test("/distributor/ 로 직접 진입하면 200과 함께 유통업체 대시보드가 렌더링된다", async ({ page }) => {
    const response = await page.goto("/distributor/");
    expect(response?.status()).toBe(200);
    await expect(page.getByRole("heading", { name: "유통업체 대시보드", level: 1 })).toBeVisible();
    await expect(page.getByText("공급 가능 건수")).toBeVisible();
  });

  test("/idle-land/ 로 직접 진입하면 200과 함께 유휴토지 지도가 렌더링된다", async ({ page }) => {
    const response = await page.goto("/idle-land/");
    expect(response?.status()).toBe(200);
    await expect(page.getByRole("heading", { name: "유휴토지 지도", level: 1 })).toBeVisible();
    await expect(page.getByRole("img", { name: "유휴토지 위치와 상태를 나타낸 지도" })).toBeVisible();
  });

  test("/idle-land/detail/?id=... 로 직접 진입해도 쿼리 파라미터가 유실되지 않는다", async ({ page, request }) => {
    // Pull a real farmland id from the API rather than hardcoding one, so
    // this doesn't silently stop testing anything if the seed changes.
    const farmlands = await (await request.get("/api/farmlands")).json();
    expect(farmlands.length).toBeGreaterThan(0);
    const target = farmlands[0];

    // Deliberately request the pre-trailingSlash form (no trailing slash
    // before the query string) -- this is what a real bookmarked/shared
    // link looks like, and it's the form that's easiest to lose the query
    // string on if a redirect implementation mishandles it.
    const response = await page.goto(`/idle-land/detail?id=${target.id}`);
    expect(response?.status()).toBe(200);
    await expect(page).toHaveURL(new RegExp(`/idle-land/detail/\\?id=${target.id}$`));

    await expect(page.getByRole("heading", { name: "유휴토지 상세" })).toBeVisible();
    // Proves the id query param actually reached the client, not just that
    // *a* detail page rendered -- this address is specific to `target`.
    await expect(page.getByRole("heading", { name: target.address, level: 2 })).toBeVisible();
  });
});
