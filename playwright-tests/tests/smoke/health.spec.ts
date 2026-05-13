import { test, expect } from "@playwright/test";
import { env } from "@config/env";

test.describe("Health Check", { tag: "@smoke" }, () => {
  test("application should be reachable", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.status()).toBeLessThan(500);
  });

  test("should return valid HTML", async ({ page }) => {
    await page.goto("/");
    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
  });

  test("should load without console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto("/");
    expect(errors).toHaveLength(0);
  });
});

test.describe("API Health", { tag: "@smoke" }, () => {
  test("health endpoint should return 200", async ({ request }) => {
    const response = await request.get(`${env.apiUrl.replace("/api/v1", "")}/health`);
    expect(response.status()).toBe(200);
  });

  test("health endpoint should report status", async ({ request }) => {
    const response = await request.get(`${env.apiUrl.replace("/api/v1", "")}/health`);
    const body = await response.json();
    expect(body).toHaveProperty("status");
    expect(body.status).toBe("healthy");
  });
});
