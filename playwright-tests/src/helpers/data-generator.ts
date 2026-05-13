let counter = 0;

export function generateEmail(prefix = "test"): string {
  counter++;
  return `${prefix}.${Date.now()}.${counter}@example.com`;
}

export function generateName(prefix = "Test"): string {
  counter++;
  return `${prefix} ${Date.now()} ${counter}`;
}

export function generatePassword(length = 12): string {
  const upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const lower = "abcdefghijklmnopqrstuvwxyz";
  const digits = "0123456789";
  const special = "!@#$%^&*";
  const all = upper + lower + digits + special;

  let password = "";
  password += upper[Math.floor(Math.random() * upper.length)];
  password += lower[Math.floor(Math.random() * lower.length)];
  password += digits[Math.floor(Math.random() * digits.length)];
  password += special[Math.floor(Math.random() * special.length)];

  for (let i = password.length; i < length; i++) {
    password += all[Math.floor(Math.random() * all.length)];
  }

  return password
    .split("")
    .sort(() => Math.random() - 0.5)
    .join("");
}

export function generateTestCase(title?: string) {
  return {
    title: title || generateName("TestCase"),
    description: `Auto-generated test case at ${new Date().toISOString()}`,
    priority: ["low", "medium", "high", "critical"][
      Math.floor(Math.random() * 4)
    ],
  };
}
