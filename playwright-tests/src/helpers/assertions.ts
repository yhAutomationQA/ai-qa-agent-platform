import { expect, Page } from "@playwright/test";

export async function assertUrl(
  page: Page,
  expectedPattern: RegExp
): Promise<void> {
  await expect(page).toHaveURL(expectedPattern, { timeout: 10000 });
}

export async function assertElementVisible(
  page: Page,
  selector: string
): Promise<void> {
  await expect(page.locator(selector)).toBeVisible({ timeout: 5000 });
}

export async function assertElementHidden(
  page: Page,
  selector: string
): Promise<void> {
  await expect(page.locator(selector)).toBeHidden({ timeout: 5000 });
}

export async function assertText(
  page: Page,
  selector: string,
  expectedText: string | RegExp
): Promise<void> {
  await expect(page.locator(selector)).toContainText(expectedText, {
    timeout: 5000,
  });
}

export async function assertInputValue(
  page: Page,
  selector: string,
  expectedValue: string
): Promise<void> {
  await expect(page.locator(selector)).toHaveValue(expectedValue, {
    timeout: 5000,
  });
}

export async function assertCount(
  page: Page,
  selector: string,
  expectedCount: number
): Promise<void> {
  await expect(page.locator(selector)).toHaveCount(expectedCount, {
    timeout: 5000,
  });
}
