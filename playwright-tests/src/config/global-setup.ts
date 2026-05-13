import { FullConfig } from "@playwright/test";

async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL = config.projects[0].use.baseURL;
  console.log(`[Global Setup] Starting Playwright tests against: ${baseURL}`);
  console.log("[Global Setup] Browser:", process.env.PLAYWRIGHT_BROWSER || "chromium");
  console.log("[Global Setup] Headless:", process.env.PLAYWRIGHT_HEADLESS !== "false");
}

export default globalSetup;
