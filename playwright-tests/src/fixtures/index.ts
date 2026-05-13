import { test as base, expect, Page, BrowserContext } from "@playwright/test";
import { LoginPage, DashboardPage } from "@pages/index";
import { ApiClient } from "@api/ApiClient";
import { env } from "@config/env";

type Fixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  apiClient: ApiClient;
  authenticatedPage: Page;
  authContext: BrowserContext;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  apiClient: async ({}, use) => {
    const client = new ApiClient(env.apiUrl);
    await use(client);
  },

  authContext: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: "test-results/auth.json",
    });
    await use(context);
    await context.close();
  },

  authenticatedPage: async ({ authContext }, use) => {
    const page = await authContext.newPage();
    await use(page);
    await page.close();
  },
});

export { expect } from "@playwright/test";
