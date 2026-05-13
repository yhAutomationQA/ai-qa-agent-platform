import { Page, Locator, expect } from "@playwright/test";

export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly testCasesTab: Locator;
  readonly agentsTab: Locator;
  readonly runsTab: Locator;
  readonly createTestButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.locator("h1");
    this.testCasesTab = page.locator('[data-testid="tab-test-cases"]');
    this.agentsTab = page.locator('[data-testid="tab-agents"]');
    this.runsTab = page.locator('[data-testid="tab-runs"]');
    this.createTestButton = page.locator('[data-testid="create-test-btn"]');
  }

  async goto(): Promise<void> {
    await this.page.goto("/dashboard");
  }

  async waitForLoad(): Promise<void> {
    await expect(this.heading).toBeVisible();
  }

  async navigateToTestCases(): Promise<void> {
    await this.testCasesTab.click();
  }

  async navigateToAgents(): Promise<void> {
    await this.agentsTab.click();
  }

  async navigateToRuns(): Promise<void> {
    await this.runsTab.click();
  }
}
