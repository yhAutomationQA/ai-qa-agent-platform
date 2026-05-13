import { test, expect } from "@fixtures/index";
import { getUser } from "@data/users";
import { ROUTES } from "@data/constants";
import { generatePassword } from "@helpers/data-generator";

test.describe("Login Page", { tag: "@login" }, () => {
  test.beforeEach(async ({ loginPage }) => {
    await loginPage.goto();
  });

  test("should display login form", async ({ loginPage }) => {
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.submitButton).toBeVisible();
    await expect(loginPage.submitButton).toBeEnabled();
  });

  test("should login with valid admin credentials", async ({
    loginPage,
    page,
  }) => {
    const admin = getUser("admin");
    await loginPage.login(admin.email, admin.password);
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("should show error with invalid credentials", async ({
    loginPage,
  }) => {
    const invalid = getUser("invalid");
    await loginPage.login(invalid.email, invalid.password);
    const error = await loginPage.expectLoginError();
    expect(error.length).toBeGreaterThan(0);
  });

  test("should show error on empty email", async ({ loginPage }) => {
    const admin = getUser("admin");
    await loginPage.fillField('[data-testid="password-input"]', admin.password);
    await loginPage.clickElement('[data-testid="login-submit"]');
    const error = await loginPage.expectLoginError();
    expect(error).toContain("email");
  });

  test("should show error on empty password", async ({ loginPage }) => {
    const admin = getUser("admin");
    await loginPage.fillField('[data-testid="email-input"]', admin.email);
    await loginPage.clickElement('[data-testid="login-submit"]');
    const error = await loginPage.expectLoginError();
    expect(error).toContain("password");
  });

  test("should show error on empty form", async ({ loginPage }) => {
    await loginPage.clickElement('[data-testid="login-submit"]');
    const error = await loginPage.expectLoginError();
    expect(error.length).toBeGreaterThan(0);
  });

  test("should trim whitespace from email", async ({ loginPage }) => {
    const admin = getUser("admin");
    await loginPage.login(`  ${admin.email}  `, admin.password);
    await expect(loginPage.page).toHaveURL(/\/dashboard/);
  });

  test("should not reveal password in DOM", async ({ loginPage }) => {
    await loginPage.fillField(
      '[data-testid="password-input"]',
      "super-secret-password"
    );
    const type = await loginPage.passwordInput.getAttribute("type");
    expect(type).toBe("password");
  });

  test("should show forgot password link", async ({ loginPage }) => {
    await expect(loginPage.forgotPasswordLink).toBeVisible();
  });
});

test.describe("Login API", { tag: "@api" }, () => {
  test("should return token on valid login", async ({ apiClient }) => {
    const admin = getUser("admin");
    const token = await apiClient.login(admin.email, admin.password);
    expect(token.accessToken).toBeTruthy();
    expect(token.expiresIn).toBeGreaterThan(0);
  });

  test("should return 401 on invalid login", async ({ apiClient }) => {
    const res = await apiClient
      .post("/auth/login", {
        email: "wrong@test.com",
        password: "wrongpass",
      })
      .catch((e) => e.response);
    expect(res.status).toBe(401);
  });
});
