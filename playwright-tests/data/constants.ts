export const TIMEOUTS = {
  MINUTE: 60000,
  THIRTY_SECONDS: 30000,
  FIFTEEN_SECONDS: 15000,
  TEN_SECONDS: 10000,
  FIVE_SECONDS: 5000,
  THREE_SECONDS: 3000,
  SECOND: 1000,
};

export const ROUTES = {
  LOGIN: "/login",
  DASHBOARD: "/dashboard",
  TESTS: "/dashboard/tests",
  AGENTS: "/dashboard/agents",
  RUNS: "/dashboard/runs",
  ANALYSIS: "/analysis/requirements",
  API: {
    HEALTH: "/api/health",
    LOGIN: "/api/v1/auth/login",
    TESTS: "/api/v1/tests",
    AGENTS: "/api/v1/agents",
  },
};

export const SELECTORS = {
  EMAIL_INPUT: '[data-testid="email-input"]',
  PASSWORD_INPUT: '[data-testid="password-input"]',
  SUBMIT_BUTTON: '[data-testid="login-submit"]',
  ERROR_MESSAGE: '[data-testid="login-error"]',
  STAT_CARD: '[data-testid="stat-card"]',
  STAT_VALUE: '[data-testid="stat-value"]',
  CREATE_BUTTON: '[data-testid="create-btn"]',
};
