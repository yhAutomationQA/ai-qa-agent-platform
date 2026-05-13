import { FullConfig } from "@playwright/test";
import { env } from "./env";

async function globalSetup(config: FullConfig): Promise<void> {
  const { baseURL } = config.projects[0].use;

  console.log("═══════════════════════════════════════════");
  console.log("  Global Setup");
  console.log("═══════════════════════════════════════════");
  console.log(`  Target URL: ${baseURL}`);
  console.log(`  API URL:    ${env.apiUrl}`);
  console.log(`  Browser:    ${config.projects.map((p) => p.name).join(", ")}`);
  console.log(`  Headless:   ${env.headless}`);
  console.log(`  Retries:    ${env.retries}`);
  console.log(`  Workers:    ${env.workers}`);
  console.log("═══════════════════════════════════════════\n");
}

export default globalSetup;
