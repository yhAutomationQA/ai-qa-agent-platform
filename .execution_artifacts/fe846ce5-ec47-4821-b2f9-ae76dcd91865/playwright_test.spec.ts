test("login", async ({ page }) => {
  await page.goto("/login");
  await page.fill("#email", "user@example.com");
  await page.fill("#password", "validPass123");
  await page.click("#login-btn");
  await expect(page).toHaveURL("/dashboard");
});