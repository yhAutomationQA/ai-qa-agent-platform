export interface DashboardSummary {
  totalTests: number;
  passed: number;
  failed: number;
  skipped: number;
  errored: number;
  passRate: number;
  totalDurationMs: number;
  totalRuns: number;
  activeAgents: number;
}

export interface TrendPoint {
  date: string;
  passed: number;
  failed: number;
  skipped: number;
  passRate: number;
}

export interface RiskItem {
  testName: string;
  riskLevel: "critical" | "high" | "medium" | "low";
  score: number;
  category: string;
  impactedAreas: string[];
}

export interface FailureItem {
  id: string;
  testName: string;
  suite: string;
  errorMessage: string;
  category: string;
  riskLevel: string;
  timestamp: string;
  durationMs: number;
  retryCount: number;
  screenshotUrl?: string;
}

export interface AiInsight {
  id: string;
  type: "anomaly" | "pattern" | "suggestion" | "warning" | "improvement";
  title: string;
  description: string;
  severity: "info" | "warning" | "critical";
  timestamp: string;
  category?: string;
}

export interface DashboardData {
  summary: DashboardSummary;
  trends: TrendPoint[];
  risks: RiskItem[];
  recentFailures: FailureItem[];
  insights: AiInsight[];
}

export interface ChartConfig {
  width?: number;
  height?: number;
  className?: string;
}

export interface StatCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ReactNode;
  color?: "primary" | "green" | "red" | "yellow" | "surface";
}

export type TimeRange = "24h" | "7d" | "30d" | "90d";
