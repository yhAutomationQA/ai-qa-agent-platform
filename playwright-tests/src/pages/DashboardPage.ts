import { Locator } from "@playwright/test";
import { BasePage } from "./BasePage";

export class DashboardPage extends BasePage {
  get url(): string {
    return "/dashboard";
  }

  get heading(): Locator {
    return this.page.locator("h1");
  }

  get testCasesTab(): Locator {
    return this.page.locator('[data-testid="tab-test-cases"]');
  }

  get agentsTab(): Locator {
    return this.page.locator('[data-testid="tab-agents"]');
  }

  get runsTab(): Locator {
    return this.page.locator('[data-testid="tab-runs"]');
  }

  get analysisTab(): Locator {
    return this.page.locator('[data-testid="tab-analysis"]');
  }

  get createButton(): Locator {
    return this.page.locator('[data-testid="create-btn"]');
  }

  get statCards(): Locator {
    return this.page.locator('[data-testid="stat-card"]');
  }

  get userAvatar(): Locator {
    return this.page.locator('[data-testid="user-avatar"]');
  }

  get logoutButton(): Locator {
    return this.page.locator('[data-testid="logout-btn"]');
  }

  async getStatValue(label: string): Promise<string> {
    const card = this.page.locator(`[data-testid="stat-card"]`, {
      hasText: label,
    });
    return (await card.locator('[data-testid="stat-value"]').textContent()) || "";
  }

  async navigateToTestCases(): Promise<void> {
    await this.testCasesTab.click();
    await this.page.waitForURL(/\/dashboard\/tests/);
  }

  async navigateToAgents(): Promise<void> {
    await this.agentsTab.click();
    await this.page.waitForURL(/\/dashboard\/agents/);
  }

  async navigateToRuns(): Promise<void> {
    await this.runsTab.click();
    await this.page.waitForURL(/\/dashboard\/runs/);
  }

  async logout(): Promise<void> {
    await this.userAvatar.click();
    await this.logoutButton.click();
    await this.page.waitForURL(/\/login/);
  }
}
