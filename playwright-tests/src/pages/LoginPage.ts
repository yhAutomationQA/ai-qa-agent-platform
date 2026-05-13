import { Locator } from "@playwright/test";
import { BasePage } from "./BasePage";

export class LoginPage extends BasePage {
  get url(): string {
    return "/login";
  }

  get emailInput(): Locator {
    return this.page.locator('[data-testid="email-input"]');
  }

  get passwordInput(): Locator {
    return this.page.locator('[data-testid="password-input"]');
  }

  get submitButton(): Locator {
    return this.page.locator('[data-testid="login-submit"]');
  }

  get errorMessage(): Locator {
    return this.page.locator('[data-testid="login-error"]');
  }

  get rememberMeCheckbox(): Locator {
    return this.page.locator('[data-testid="remember-me"]');
  }

  get forgotPasswordLink(): Locator {
    return this.page.locator('[data-testid="forgot-password"]');
  }

  async login(email: string, password: string): Promise<void> {
    await this.fillField('[data-testid="email-input"]', email);
    await this.fillField('[data-testid="password-input"]', password);
    await this.clickElement('[data-testid="login-submit"]');
    await this.page.waitForLoadState("networkidle");
  }

  async expectLoginError(): Promise<string> {
    await this.errorMessage.waitFor({ state: "visible", timeout: 5000 });
    return (await this.errorMessage.textContent()) || "";
  }

  async expectSuccessfulLogin(): Promise<void> {
    await this.page.waitForURL(/\/dashboard/, { timeout: 10000 });
  }

  async isLoaded(): Promise<boolean> {
    return this.submitButton.isVisible();
  }
}
