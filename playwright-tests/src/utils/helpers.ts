import { Page } from "@playwright/test";

export async function waitForPageStable(page: Page): Promise<void> {
  await page.waitForLoadState("networkidle");
  await page.waitForLoadState("domcontentloaded");
}

export async function capturePageState(page: Page): Promise<{
  url: string;
  title: string;
  html: string;
}> {
  return {
    url: page.url(),
    title: await page.title(),
    html: await page.content(),
  };
}

export function generateTestEmail(): string {
  const ts = Date.now();
  return `test-user-${ts}@example.com`;
}

export function generateTestName(prefix: string = "test"): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;
}
