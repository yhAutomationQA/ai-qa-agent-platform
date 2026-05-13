import type { TestUser } from "@src/types";
import { env } from "@config/env";

export const users: Record<string, TestUser> = {
  admin: {
    email: env.testUser.email,
    password: env.testUser.password,
    displayName: "Admin User",
    role: "admin",
  },
  viewer: {
    email: "viewer@test.com",
    password: "Viewer@123",
    displayName: "Viewer User",
    role: "viewer",
  },
  editor: {
    email: "editor@test.com",
    password: "Editor@123",
    displayName: "Editor User",
    role: "editor",
  },
  invalid: {
    email: "invalid@test.com",
    password: "WrongPass123!",
    displayName: "Invalid User",
  },
};

export function getUser(role: keyof typeof users): TestUser {
  const user = users[role];
  if (!user) throw new Error(`Unknown user role: ${role}`);
  return user;
}
