import { Page } from "@playwright/test";
import { mkdirSync } from "fs";
import { resolve } from "path";

const SCREENSHOT_DIR = resolve("test-results", "screenshots");

export async function captureScreenshot(
  page: Page,
  name: string
): Promise<string> {
  mkdirSync(SCREENSHOT_DIR, { recursive: true });
  const timestamp = Date.now();
  const path = resolve(SCREENSHOT_DIR, `${name}-${timestamp}.png`);
  await page.screenshot({ path, fullPage: true });
  return path;
}

export async function captureElementScreenshot(
  page: Page,
  selector: string,
  name: string
): Promise<string> {
  mkdirSync(SCREENSHOT_DIR, { recursive: true });
  const timestamp = Date.now();
  const path = resolve(SCREENSHOT_DIR, `${name}-${timestamp}.png`);
  const element = page.locator(selector);
  await element.screenshot({ path });
  return path;
}
