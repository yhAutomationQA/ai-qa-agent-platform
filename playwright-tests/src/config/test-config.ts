export const testConfig = {
  baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000",
  apiURL: process.env.API_TEST_BASE_URL || "http://localhost:8000",
  browser: process.env.PLAYWRIGHT_BROWSER || "chromium",
  headless: process.env.PLAYWRIGHT_HEADLESS !== "false",
  timeout: parseInt(process.env.PLAYWRIGHT_TIMEOUT || "30000", 10),
  retries: parseInt(process.env.PLAYWRIGHT_RETRIES || "2", 10),
  workers: parseInt(process.env.PLAYWRIGHT_WORKERS || "4", 10),

  users: {
    admin: {
      email: process.env.TEST_ADMIN_EMAIL || "admin@test.com",
      password: process.env.TEST_ADMIN_PASSWORD || "admin123",
    },
    viewer: {
      email: process.env.TEST_VIEWER_EMAIL || "viewer@test.com",
      password: process.env.TEST_VIEWER_PASSWORD || "viewer123",
    },
  },

  timeouts: {
    navigation: 30000,
    element: 10000,
    api: 15000,
    animation: 1000,
  },
};
