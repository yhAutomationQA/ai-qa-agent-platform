import { defineConfig, devices } from "@playwright/test";
import { resolve } from "path";
import { config } from "dotenv";

config({ path: resolve(__dirname, ".env") });

const CI = !!process.env.CI;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: CI,
  retries: CI ? 2 : 0,
  workers: CI ? 4 : undefined,
  maxFailures: CI ? 10 : undefined,

  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: CI ? "never" : "on-failure" }],
    ["json", { outputFile: "test-results/results.json" }],
    ["junit", { outputFile: "test-results/junit.xml" }],
    ["./src/reporters/custom-reporter.ts"],
  ],

  timeout: Number(process.env.TIMEOUT) || 30000,
  expect: { timeout: 10000 },

  use: {
    baseURL: process.env.BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 10000,
    navigationTimeout: 15000,
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
    {
      name: "chromium-mobile",
      use: { ...devices["Pixel 5"] },
    },
  ],

  outputDir: "test-results/artifacts",
  globalSetup: resolve(__dirname, "src/config/global-setup.ts"),
  globalTeardown: resolve(__dirname, "src/config/global-teardown.ts"),
});
