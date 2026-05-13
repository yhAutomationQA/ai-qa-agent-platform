"use client";

import { cn } from "@/lib/utils";
import type { DashboardSummary, StatCardProps } from "@/lib/dashboard-types";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  PlayCircle,
  XCircle,
  Bot,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

const iconMap: Record<string, React.ReactNode> = {
  totalTests: <Activity className="h-5 w-5" />,
  passed: <CheckCircle2 className="h-5 w-5" />,
  failed: <XCircle className="h-5 w-5" />,
  passRate: <TrendingUp className="h-5 w-5" />,
  totalRuns: <PlayCircle className="h-5 w-5" />,
  activeAgents: <Bot className="h-5 w-5" />,
  totalDuration: <Clock className="h-5 w-5" />,
  errors: <AlertTriangle className="h-5 w-5" />,
};

const colorMap: Record<string, StatCardProps["color"]> = {
  totalTests: "primary",
  passed: "green",
  failed: "red",
  passRate: "green",
  totalRuns: "primary",
  activeAgents: "primary",
  totalDuration: "surface",
  errors: "red",
};

export function SummaryCards({ summary }: { summary: DashboardSummary }) {
  const cards: StatCardProps[] = [
    {
      label: "Total Tests",
      value: summary.totalTests.toLocaleString(),
      icon: iconMap.totalTests,
      color: colorMap.totalTests,
    },
    {
      label: "Passed",
      value: summary.passed.toLocaleString(),
      sublabel: `${summary.passRate}% pass rate`,
      trend: summary.passRate >= 90 ? "up" : "down",
      icon: iconMap.passed,
      color: colorMap.passed,
    },
    {
      label: "Failed",
      value: summary.failed.toLocaleString(),
      sublabel: `${summary.errored} errored`,
      trend: summary.failed > 0 ? "down" : "neutral",
      icon: iconMap.failed,
      color: colorMap.failed,
    },
    {
      label: "Runs",
      value: summary.totalRuns.toLocaleString(),
      sublabel: formatDuration(summary.totalDurationMs),
      icon: iconMap.totalRuns,
      color: colorMap.totalRuns,
    },
    {
      label: "Active Agents",
      value: summary.activeAgents,
      icon: iconMap.activeAgents,
      color: colorMap.activeAgents,
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} />
      ))}
    </div>
  );
}

function StatCard({ label, value, sublabel, trend, icon, color = "surface" }: StatCardProps) {
  const colorStyles: Record<string, string> = {
    primary:
      "border-primary-500/30 bg-primary-500/10 text-primary-400",
    green: "border-green-500/30 bg-green-500/10 text-green-400",
    red: "border-red-500/30 bg-red-500/10 text-red-400",
    yellow: "border-yellow-500/30 bg-yellow-500/10 text-yellow-400",
    surface: "border-surface-600 bg-surface-800 text-surface-300",
  };

  return (
    <div className="group relative overflow-hidden rounded-xl border border-surface-700 bg-surface-800 p-5 transition hover:border-surface-600 hover:shadow-lg">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-surface-400">
            {label}
          </p>
          <p className="mt-1.5 text-2xl font-bold text-white">{value}</p>
          {sublabel && (
            <p className="mt-0.5 flex items-center gap-1 text-xs text-surface-400">
              {trend === "up" && <TrendingUp className="h-3 w-3 text-green-400" />}
              {trend === "down" && <TrendingDown className="h-3 w-3 text-red-400" />}
              {sublabel}
            </p>
          )}
        </div>
        {icon && (
          <div
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-lg",
              colorStyles[color] || colorStyles.surface
            )}
          >
            {icon}
          </div>
        )}
      </div>
      <div
        className={cn(
          "absolute inset-x-0 bottom-0 h-0.5",
          color === "green" && "bg-green-500",
          color === "red" && "bg-red-500",
          color === "primary" && "bg-primary-500",
          color === "yellow" && "bg-yellow-500",
          color === "surface" && "bg-surface-600"
        )}
      />
    </div>
  );
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(0)}m ${Math.round((ms % 60000) / 1000)}s`;
  return `${(ms / 3600000).toFixed(1)}h`;
}
