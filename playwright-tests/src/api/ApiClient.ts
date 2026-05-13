import { APIRequestContext, request } from "@playwright/test";
import { env } from "@config/env";
import type { ApiResponse, AuthToken } from "@src/types";

export class ApiClient {
  private context: APIRequestContext | null = null;
  private token: string | null = null;

  constructor(private baseUrl: string = env.apiUrl) {}

  private async getContext(): Promise<APIRequestContext> {
    if (!this.context) {
      this.context = await request.newContext({
        baseURL: this.baseUrl,
        extraHTTPHeaders: {
          "Content-Type": "application/json",
          ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
        },
      });
    }
    return this.context;
  }

  async login(email: string, password: string): Promise<AuthToken> {
    const ctx = await this.getContext();
    const res = await ctx.post("/auth/login", {
      data: { email, password },
    });
    const body = await res.json();
    this.token = body.accessToken;
    return body;
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    const ctx = await this.getContext();
    const res = await ctx.get(path);
    return {
      status: res.status(),
      data: await res.json(),
      headers: res.headers(),
    };
  }

  async post<T>(path: string, data?: unknown): Promise<ApiResponse<T>> {
    const ctx = await this.getContext();
    const res = await ctx.post(path, { data });
    return {
      status: res.status(),
      data: await res.json(),
      headers: res.headers(),
    };
  }

  async put<T>(path: string, data?: unknown): Promise<ApiResponse<T>> {
    const ctx = await this.getContext();
    const res = await ctx.put(path, { data });
    return {
      status: res.status(),
      data: await res.json(),
      headers: res.headers(),
    };
  }

  async delete<T>(path: string): Promise<ApiResponse<T>> {
    const ctx = await this.getContext();
    const res = await ctx.delete(path);
    return {
      status: res.status(),
      data: await res.json(),
      headers: res.headers(),
    };
  }

  async health(): Promise<ApiResponse<{ status: string }>> {
    return this.get("/health");
  }

  async dispose(): Promise<void> {
    if (this.context) {
      await this.context.dispose();
      this.context = null;
    }
  }
}
