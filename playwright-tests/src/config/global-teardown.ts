import { FullConfig } from "@playwright/test";

async function globalTeardown(config: FullConfig): Promise<void> {
  console.log("[Global Teardown] Playwright test run completed");
}

export default globalTeardown;
