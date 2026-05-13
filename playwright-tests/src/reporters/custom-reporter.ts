import type {
  FullConfig,
  FullResult,
  Suite,
  TestCase,
  TestResult,
} from "@playwright/test/reporter";
import { writeFileSync, mkdirSync } from "fs";
import { resolve } from "path";

const OUTPUT_DIR = resolve("test-results");
const REPORT_FILE = resolve(OUTPUT_DIR, "custom-report.json");

interface TestReportEntry {
  title: string;
  file: string;
  status: string;
  duration: number;
  error?: string;
  retry: number;
  project: string;
  screenshots: string[];
  video?: string;
}

export default class CustomReporter {
  private startTime: number = 0;
  private entries: TestReportEntry[] = [];

  onBegin(config: FullConfig, suite: Suite): void {
    this.startTime = Date.now();
    console.log(`\n[CustomReporter] Starting run — ${suite.allTests().length} tests\n`);
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    const entry: TestReportEntry = {
      title: test.title,
      file: test.location.file,
      status: result.status,
      duration: result.duration,
      retry: result.retry,
      project: test.parent.project()?.name || "unknown",
      screenshots: [],
    };

    if (result.errors.length > 0) {
      entry.error = result.errors
        .map((e) => e.message)
        .filter(Boolean)
        .join("\n");
    }

    for (const attachment of result.attachments) {
      if (attachment.contentType?.startsWith("image/")) {
        entry.screenshots.push(attachment.path || "");
      }
      if (attachment.name === "video") {
        entry.video = attachment.path;
      }
    }

    this.entries.push(entry);
  }

  onEnd(result: FullResult): void {
    const duration = ((Date.now() - this.startTime) / 1000).toFixed(1);
    const passed = this.entries.filter((e) => e.status === "passed").length;
    const failed = this.entries.filter((e) => e.status === "failed").length;
    const skipped = this.entries.filter((e) => e.status === "skipped").length;

    const report = {
      duration: `${duration}s`,
      summary: { total: this.entries.length, passed, failed, skipped },
      status: result.status,
      timestamp: new Date().toISOString(),
      tests: this.entries,
    };

    mkdirSync(OUTPUT_DIR, { recursive: true });
    writeFileSync(REPORT_FILE, JSON.stringify(report, null, 2));

    console.log(`\n[CustomReporter] Run complete — ${duration}s`);
    console.log(`  Passed: ${passed}  Failed: ${failed}  Skipped: ${skipped}`);
    console.log(`  Report: ${REPORT_FILE}\n`);
  }
}
