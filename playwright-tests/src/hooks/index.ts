import { test } from "@fixtures/index";
import { captureScreenshot } from "@helpers/screenshot";

test.beforeEach(async ({ page }, testInfo) => {
  console.log(
    `[Hook] Starting: ${testInfo.title} (${testInfo.project.name})`
  );
});

test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== "passed") {
    const name = `${testInfo.title.replace(/\s+/g, "-")}-${testInfo.project.name}`;
    await captureScreenshot(page, name);
    console.log(
      `[Hook] Failed: ${testInfo.title} — screenshot saved`
    );
  }

  console.log(
    `[Hook] ${testInfo.status === "passed" ? "Passed" : "Failed"}: ${testInfo.title} (${testInfo.duration}ms)`
  );
});
