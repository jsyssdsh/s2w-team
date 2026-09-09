import { defineConfig } from "@playwright/test";

// baseURL is the FastAPI server, not `next dev` -- lib/api.ts does relative
// fetch() with no CORS/base-url config, so the static export must be served
// same-origin from the backend (matches the single-container Dockerfile
// topology): `pnpm build` in frontend/, copy frontend/out -> backend/static,
// then run the backend on :8000.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:8000",
    headless: true,
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
