import { Page, Locator, expect } from "@playwright/test";

export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  abstract get url(): string;

  async goto(): Promise<void> {
    await this.page.goto(this.url, { waitUntil: "networkidle" });
  }

  async waitForLoad(): Promise<void> {
    await this.page.waitForLoadState("networkidle");
  }

  async getTitle(): Promise<string> {
    return this.page.title();
  }

  async getUrl(): Promise<string> {
    return this.page.url();
  }

  async screenshot(name?: string): Promise<void> {
    const fileName = name || this.constructor.name;
    await this.page.screenshot({
      path: `test-results/screenshots/${fileName}-${Date.now()}.png`,
      fullPage: true,
    });
  }

  async reload(): Promise<void> {
    await this.page.reload({ waitUntil: "networkidle" });
  }

  protected locator(selector: string): Locator {
    return this.page.locator(selector);
  }

  protected async waitForElement(
    selector: string,
    timeout = 10000
  ): Promise<Locator> {
    const el = this.locator(selector);
    await el.waitFor({ state: "visible", timeout });
    return el;
  }

  async fillField(selector: string, value: string): Promise<void> {
    const el = await this.waitForElement(selector);
    await el.clear();
    await el.fill(value);
  }

  async clickElement(selector: string): Promise<void> {
    const el = await this.waitForElement(selector);
    await el.click();
  }

  async getText(selector: string): Promise<string> {
    const el = await this.waitForElement(selector);
    return (await el.textContent()) || "";
  }

  async isVisible(selector: string): Promise<boolean> {
    try {
      await this.waitForElement(selector, 3000);
      return true;
    } catch {
      return false;
    }
  }

  async selectOption(selector: string, value: string): Promise<void> {
    await this.locator(selector).selectOption(value);
  }
}
