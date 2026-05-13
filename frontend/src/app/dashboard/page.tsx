"use client";

import { useState } from "react";
import { DashboardLayout, DashboardCard } from "@/components/dashboard/DashboardLayout";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { PassFailChart } from "@/components/dashboard/PassFailChart";
import { QualityTrendChart } from "@/components/dashboard/QualityTrendChart";
import { RiskIndicators } from "@/components/dashboard/RiskIndicators";
import { AIInsightsPanel } from "@/components/dashboard/AIInsightsPanel";
import { RecentFailures } from "@/components/dashboard/RecentFailures";
import { useDashboard } from "@/lib/hooks/useDashboard";
import type { TimeRange } from "@/lib/dashboard-types";
import { RefreshCw, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

const timeRanges: { label: string; value: TimeRange }[] = [
  { label: "24h", value: "24h" },
  { label: "7d", value: "7d" },
  { label: "30d", value: "30d" },
  { label: "90d", value: "90d" },
];

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>("7d");
  const { data, isLoading, isError, refetch } = useDashboard(timeRange);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (isError) {
    return <ErrorState onRetry={() => refetch()} />;
  }

  if (!data) return null;

  return (
    <DashboardLayout
      title="QA Dashboard"
      subtitle={`${data.summary.totalRuns} runs · ${data.summary.activeAgents} active agents`}
      actions={
        <div className="flex items-center gap-2">
          <TimeRangeSelector
            ranges={timeRanges}
            selected={timeRange}
            onSelect={setTimeRange}
          />
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 rounded-lg border border-surface-600 bg-surface-800 px-3 py-2 text-xs font-medium text-surface-300 transition hover:border-surface-500 hover:text-white"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        <SummaryCards summary={data.summary} />

        <div className="grid gap-6 lg:grid-cols-3">
          <DashboardCard
            title="Pass / Fail Distribution"
            className="lg:col-span-1"
          >
            <PassFailChart summary={data.summary} />
          </DashboardCard>

          <DashboardCard
            title="Quality Trend"
            subtitle="Daily pass/fail over time"
            className="lg:col-span-2"
          >
            <QualityTrendChart trends={data.trends} />
          </DashboardCard>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <DashboardCard
            title="Risk Indicators"
            subtitle="Sorted by risk score"
          >
            <RiskIndicators risks={data.risks} />
          </DashboardCard>

          <DashboardCard
            title="AI Insights"
            subtitle="Automated analysis and recommendations"
          >
            <AIInsightsPanel insights={data.insights} />
          </DashboardCard>
        </div>

        <DashboardCard
          title="Recent Failures"
          subtitle={`${data.recentFailures.length} failures in selected period`}
        >
          <RecentFailures failures={data.recentFailures} />
        </DashboardCard>
      </div>
    </DashboardLayout>
  );
}

function TimeRangeSelector({
  ranges,
  selected,
  onSelect,
}: {
  ranges: { label: string; value: TimeRange }[];
  selected: TimeRange;
  onSelect: (value: TimeRange) => void;
}) {
  return (
    <div className="flex overflow-hidden rounded-lg border border-surface-600">
      {ranges.map((r) => (
        <button
          key={r.value}
          onClick={() => onSelect(r.value)}
          className={cn(
            "px-3 py-2 text-xs font-medium transition",
            selected === r.value
              ? "bg-primary-600 text-white"
              : "bg-surface-800 text-surface-400 hover:text-white"
          )}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-surface-900 p-8">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 h-8 w-48 animate-pulse rounded bg-surface-700" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="h-28 animate-pulse rounded-xl bg-surface-800"
            />
          ))}
        </div>
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="h-64 animate-pulse rounded-xl bg-surface-800 lg:col-span-1" />
          <div className="h-64 animate-pulse rounded-xl bg-surface-800 lg:col-span-2" />
        </div>
      </div>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-900">
      <div className="text-center">
        <AlertTriangle className="mx-auto h-12 w-12 text-yellow-400" />
        <h2 className="mt-4 text-lg font-semibold text-white">
          Failed to load dashboard
        </h2>
        <p className="mt-2 text-sm text-surface-400">
          Unable to fetch dashboard data. The backend may be unavailable.
        </p>
        <button
          onClick={onRetry}
          className="mt-6 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-primary-700"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
