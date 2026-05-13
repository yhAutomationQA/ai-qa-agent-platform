import { ApiClient } from "./ApiClient";
import type { ApiResponse, TestCase } from "@src/types";

export class ApiUtils {
  constructor(private client: ApiClient) {}

  async createTest(data: {
    title: string;
    description?: string;
    priority?: string;
  }): Promise<ApiResponse<TestCase>> {
    return this.client.post("/tests", data);
  }

  async getTest(id: string): Promise<ApiResponse<TestCase>> {
    return this.client.get(`/tests/${id}`);
  }

  async listTests(): Promise<ApiResponse<TestCase[]>> {
    return this.client.get("/tests");
  }

  async deleteTest(id: string): Promise<ApiResponse<void>> {
    return this.client.delete(`/tests/${id}`);
  }

  async waitForCondition(
    check: () => Promise<boolean>,
    { timeout = 15000, interval = 1000 } = {}
  ): Promise<boolean> {
    const start = Date.now();
    while (Date.now() - start < timeout) {
      if (await check()) return true;
      await new Promise((r) => setTimeout(r, interval));
    }
    return false;
  }
}
