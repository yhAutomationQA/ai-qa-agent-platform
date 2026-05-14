"use client";

import { useQuery } from "@tanstack/react-query";
import type { DashboardData, TimeRange } from "@/lib/dashboard-types";

function generateMockDashboardData(): DashboardData {
  const passed = 142;
  const failed = 18;
  const skipped = 5;
  const errored = 3;
  const totalTests = passed + failed + skipped + errored;

  const now = Date.now();
  const trends: DashboardData["trends"] = Array.from({ length: 14 }, (_, i) => {
    const dayPassed = Math.floor(80 + Math.random() * 60);
    const dayFailed = Math.floor(2 + Math.random() * 15);
    const daySkipped = Math.floor(Math.random() * 5);
    const total = dayPassed + dayFailed + daySkipped;
    return {
      date: new Date(now - (13 - i) * 86400000).toISOString().split("T")[0],
      passed: dayPassed,
      failed: dayFailed,
      skipped: daySkipped,
      passRate: Math.round((dayPassed / total) * 100),
    };
  });

  const risks: DashboardData["risks"] = [
    {
      testName: "User Authentication Flow",
      riskLevel: "critical",
      score: 0.92,
      category: "permission",
      impactedAreas: ["Authentication", "Security", "Login"],
    },
    {
      testName: "Payment Processing",
      riskLevel: "high",
      score: 0.78,
      category: "api",
      impactedAreas: ["Payments", "Integrations"],
    },
    {
      testName: "Data Export - Large Dataset",
      riskLevel: "high",
      score: 0.71,
      category: "timeout",
      impactedAreas: ["Data Export", "Performance"],
    },
    {
      testName: "User Profile Update",
      riskLevel: "medium",
      score: 0.55,
      category: "assertion",
      impactedAreas: ["User Management"],
    },
    {
      testName: "Search Functionality",
      riskLevel: "low",
      score: 0.28,
      category: "ui",
      impactedAreas: ["Search", "UI"],
    },
  ];

  const recentFailures: DashboardData["recentFailures"] = [
    {
      id: "f1",
      testName: "Login with invalid credentials shows error",
      suite: "AuthSuite",
      errorMessage:
        "AssertionError: Expected error text 'Invalid credentials' but found empty",
      category: "assertion",
      riskLevel: "high",
      timestamp: new Date(now - 600000).toISOString(),
      durationMs: 3450,
      retryCount: 2,
    },
    {
      id: "f2",
      testName: "Payment checkout - credit card validation",
      suite: "PaymentSuite",
      errorMessage:
        "TimeoutError: waitForSelector('.payment-confirm') exceeded 30000ms",
      category: "timeout",
      riskLevel: "high",
      timestamp: new Date(now - 1800000).toISOString(),
      durationMs: 30120,
      retryCount: 1,
    },
    {
      id: "f3",
      testName: "GET /api/users returns user list",
      suite: "ApiSuite",
      errorMessage: "Expected 200, got 503 - Service Unavailable",
      category: "api",
      riskLevel: "critical",
      timestamp: new Date(now - 3600000).toISOString(),
      durationMs: 5200,
      retryCount: 3,
    },
    {
      id: "f4",
      testName: "Dashboard loads within 5 seconds",
      suite: "PerformanceSuite",
      errorMessage: "Timed out after 10000ms waiting for LCP metric",
      category: "timeout",
      riskLevel: "medium",
      timestamp: new Date(now - 7200000).toISOString(),
      durationMs: 10100,
      retryCount: 0,
    },
    {
      id: "f5",
      testName: "User registration - duplicate email",
      suite: "RegistrationSuite",
      errorMessage: "AssertionError: Expected 422, got 500",
      category: "api",
      riskLevel: "medium",
      timestamp: new Date(now - 14400000).toISOString(),
      durationMs: 2800,
      retryCount: 1,
    },
  ];

  const insights: DashboardData["insights"] = [
    {
      id: "i1",
      type: "anomaly",
      title: "Failure rate spike detected",
      description:
        "Test failures increased by 23% in the last hour compared to the same window yesterday. 5 of 7 failures are in the payment suite.",
      severity: "critical",
      timestamp: new Date(now - 300000).toISOString(),
      category: "PaymentSuite",
    },
    {
      id: "i2",
      type: "pattern",
      title: "Flaky tests identified",
      description:
        "3 tests show intermittent failure patterns. 'Dashboard data loading' failed 4 out of last 10 runs. Consider quarantining.",
      severity: "warning",
      timestamp: new Date(now - 1800000).toISOString(),
    },
    {
      id: "i3",
      type: "suggestion",
      title: "Retry would likely succeed",
      description:
        "2 timeout failures show zero progress between attempts, suggesting infrastructure throttling rather than application bugs.",
      severity: "info",
      timestamp: new Date(now - 3600000).toISOString(),
    },
    {
      id: "i4",
      type: "warning",
      title: "Authentication service degradation",
      description:
        "Auth Suite has 100% failure rate in the last 15 minutes. All 4 tests fail with 503 errors from the auth endpoint.",
      severity: "warning",
      timestamp: new Date(now - 900000).toISOString(),
      category: "AuthSuite",
    },
    {
      id: "i5",
      type: "improvement",
      title: "Test data stale for User Suite",
      description:
        "User profile tests use data created 48+ hours ago. 2 failures are likely due to expired test data rather than code regressions.",
      severity: "info",
      timestamp: new Date(now - 7200000).toISOString(),
      category: "UserSuite",
    },
  ];

  return {
    summary: {
      totalTests,
      passed,
      failed,
      skipped,
      errored,
      passRate: Math.round((passed / totalTests) * 100),
      totalDurationMs: 2845000,
      totalRuns: 47,
      activeAgents: 4,
    },
    trends,
    risks,
    recentFailures,
    insights,
  };
}

let backendAvailable: boolean | null = null;

async function checkBackend(): Promise<boolean> {
  if (backendAvailable !== null) return backendAvailable;
  try {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const res = await fetch(`${base.replace(/\/api\/v1\/?$/, "")}/api`, {
      method: "GET",
      signal: AbortSignal.timeout(2000),
    });
    backendAvailable = res.ok;
  } catch {
    backendAvailable = false;
  }
  return backendAvailable;
}

export function useDashboard(timeRange: TimeRange = "7d") {
  return useQuery<DashboardData>({
    queryKey: ["dashboard", timeRange],
    queryFn: async () => {
      const alive = await checkBackend();
      if (!alive) return generateMockDashboardData();

      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${base}/dashboard?range=${timeRange}`, {
        signal: AbortSignal.timeout(5000),
      });
      if (!res.ok) return generateMockDashboardData();
      return (await res.json()) as DashboardData;
    },
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}
