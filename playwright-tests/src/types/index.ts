import { Page, Locator, APIResponse } from "@playwright/test";

export interface TestUser {
  email: string;
  password: string;
  displayName?: string;
  role?: "admin" | "viewer" | "editor";
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthToken {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface ApiResponse<T = unknown> {
  status: number;
  data: T;
  headers: Record<string, string>;
}

export interface TestCase {
  id: string;
  title: string;
  description: string;
  priority: "low" | "medium" | "high" | "critical";
  status: "draft" | "active" | "archived";
}

export interface ScreenshotOptions {
  fullPage?: boolean;
  quality?: number;
  timeout?: number;
}

export interface TestContext {
  page: Page;
  authenticatedPage: Page;
  loginPage: import("@pages/index").LoginPage;
  dashboardPage: import("@pages/index").DashboardPage;
  apiClient: import("@api/ApiClient").ApiClient;
}
