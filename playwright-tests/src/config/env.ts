export interface EnvConfig {
  baseUrl: string;
  apiUrl: string;
  headless: boolean;
  retries: number;
  workers: number;
  timeout: number;
  testUser: {
    email: string;
    password: string;
  };
}

export function loadEnv(): EnvConfig {
  return {
    baseUrl: process.env.BASE_URL || "http://localhost:3000",
    apiUrl: process.env.API_URL || "http://localhost:8000/api/v1",
    headless: process.env.HEADLESS !== "false",
    retries: Number(process.env.TEST_RETRIES) || 2,
    workers: Number(process.env.TEST_WORKERS) || 4,
    timeout: Number(process.env.TIMEOUT) || 30000,
    testUser: {
      email: process.env.TEST_USER_EMAIL || "admin@test.com",
      password: process.env.TEST_USER_PASSWORD || "Admin@123",
    },
  };
}

export const env = loadEnv();
