"use client";

import { cn } from "@/lib/utils";
import { formatDuration, formatDate } from "@/lib/utils";
import type { FailureItem } from "@/lib/dashboard-types";
import { XCircle, AlertTriangle, Clock, RotateCcw, ExternalLink } from "lucide-react";

interface RecentFailuresProps {
  failures: FailureItem[];
}

const categoryColors: Record<string, string> = {
  assertion: "text-red-400 bg-red-500/10 border-red-500/30",
  timeout: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
  api: "text-orange-400 bg-orange-500/10 border-orange-500/30",
  infrastructure: "text-purple-400 bg-purple-500/10 border-purple-500/30",
  network: "text-blue-400 bg-blue-500/10 border-blue-500/30",
  flaky: "text-cyan-400 bg-cyan-500/10 border-cyan-500/30",
  ui: "text-pink-400 bg-pink-500/10 border-pink-500/30",
  permission: "text-red-400 bg-red-500/10 border-red-500/30",
  data: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  unknown: "text-surface-400 bg-surface-500/10 border-surface-500/30",
};

export function RecentFailures({ failures }: RecentFailuresProps) {
  if (failures.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-surface-400">
        <CheckCircleIcon /> No recent failures
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {failures.map((failure) => (
        <FailureRow key={failure.id} failure={failure} />
      ))}
    </div>
  );
}

function FailureRow({ failure }: { failure: FailureItem }) {
  const catColor = categoryColors[failure.category] || categoryColors.unknown;

  return (
    <div className="group rounded-lg border border-surface-700 bg-surface-800 p-3 transition hover:border-surface-600">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-red-500/10 text-red-400">
          <XCircle className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-medium text-white">
              {failure.testName}
            </p>
            <span
              className={cn(
                "inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
                catColor
              )}
            >
              {failure.category}
            </span>
          </div>
          <p className="mt-1 truncate text-xs text-surface-400">
            {failure.errorMessage}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-surface-500">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(failure.timestamp)}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDuration(failure.durationMs)}
            </span>
            {failure.retryCount > 0 && (
              <span className="flex items-center gap-1">
                <RotateCcw className="h-3 w-3" />
                Retried {failure.retryCount}x
              </span>
            )}
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium",
                failure.riskLevel === "critical" && "bg-red-500/20 text-red-400",
                failure.riskLevel === "high" && "bg-orange-500/20 text-orange-400",
                failure.riskLevel === "medium" && "bg-yellow-500/20 text-yellow-400",
                failure.riskLevel === "low" && "bg-surface-500/20 text-surface-400"
              )}
            >
              <AlertTriangle className="h-3 w-3" />
              {failure.riskLevel}
            </span>
            {failure.screenshotUrl && (
              <a
                href={failure.screenshotUrl}
                className="flex items-center gap-1 text-primary-400 hover:text-primary-300"
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink className="h-3 w-3" />
                Screenshot
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function CheckCircleIcon() {
  return (
    <svg
      className="mr-2 h-4 w-4 text-green-400"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}
