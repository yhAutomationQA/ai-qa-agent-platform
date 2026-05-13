async function globalTeardown(): Promise<void> {
  console.log("\n═══════════════════════════════════════════");
  console.log("  Global Teardown — cleaning up");
  console.log("═══════════════════════════════════════════");
}

export default globalTeardown;
