import { Page } from "@playwright/test";

interface RetryOptions {
  maxAttempts?: number;
  delay?: number;
  timeout?: number;
}

export async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const { maxAttempts = 3, delay = 1000 } = options;
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (attempt < maxAttempts) {
        console.warn(
          `[Retry] Attempt ${attempt}/${maxAttempts} failed: ${(error as Error).message}`
        );
        await new Promise((r) => setTimeout(r, delay * attempt));
      }
    }
  }

  throw lastError;
}

export async function retryUntil(
  page: Page,
  selector: string,
  options: RetryOptions = {}
): Promise<void> {
  const { maxAttempts = 5, delay = 2000 } = options;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const visible = await page.locator(selector).isVisible().catch(() => false);
    if (visible) return;

    if (attempt < maxAttempts) {
      await page.waitForTimeout(delay * attempt);
    }
  }

  throw new Error(
    `[RetryUntil] Element "${selector}" not visible after ${maxAttempts} attempts`
  );
}

export async function retryAssertion(
  assertion: () => Promise<void>,
  options: RetryOptions = {}
): Promise<void> {
  return retry(assertion, options);
}
