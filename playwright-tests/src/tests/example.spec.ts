import { test, expect } from "@fixtures/base";

test.describe("Dashboard", () => {
  test("should load the dashboard page", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.locator("h1")).toBeVisible();
  });

  test("should display navigation tabs", async ({ dashboardPage }) => {
    await dashboardPage.goto();
    await dashboardPage.waitForLoad();
    await expect(dashboardPage.testCasesTab).toBeVisible();
    await expect(dashboardPage.agentsTab).toBeVisible();
    await expect(dashboardPage.runsTab).toBeVisible();
  });
});

test.describe("Login", () => {
  test("should show error on invalid credentials", async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login("invalid@test.com", "wrongpassword");
    await expect(loginPage.errorMessage).toBeVisible();
  });
});
