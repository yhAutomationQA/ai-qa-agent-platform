"use client";

import { cn } from "@/lib/utils";
import type { AiInsight } from "@/lib/dashboard-types";
import {
  Brain,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  Zap,
  ShieldAlert,
  RefreshCw,
} from "lucide-react";

interface AIInsightsPanelProps {
  insights: AiInsight[];
}

const typeConfig = {
  anomaly: {
    icon: <Zap className="h-4 w-4" />,
    label: "Anomaly",
    border: "border-purple-500/30",
    bg: "bg-purple-500/10",
    text: "text-purple-400",
  },
  pattern: {
    icon: <TrendingUp className="h-4 w-4" />,
    label: "Pattern",
    border: "border-blue-500/30",
    bg: "bg-blue-500/10",
    text: "text-blue-400",
  },
  suggestion: {
    icon: <Lightbulb className="h-4 w-4" />,
    label: "Suggestion",
    border: "border-green-500/30",
    bg: "bg-green-500/10",
    text: "text-green-400",
  },
  warning: {
    icon: <AlertTriangle className="h-4 w-4" />,
    label: "Warning",
    border: "border-orange-500/30",
    bg: "bg-orange-500/10",
    text: "text-orange-400",
  },
  improvement: {
    icon: <RefreshCw className="h-4 w-4" />,
    label: "Improvement",
    border: "border-cyan-500/30",
    bg: "bg-cyan-500/10",
    text: "text-cyan-400",
  },
};

const severityIcon = {
  critical: <ShieldAlert className="h-4 w-4 text-red-400" />,
  warning: <AlertTriangle className="h-4 w-4 text-yellow-400" />,
  info: <Lightbulb className="h-4 w-4 text-blue-400" />,
};

export function AIInsightsPanel({ insights }: AIInsightsPanelProps) {
  if (insights.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-surface-400">
        <Brain className="mr-2 h-4 w-4" />
        No AI insights available
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {insights.map((insight) => (
        <InsightCard key={insight.id} insight={insight} />
      ))}
    </div>
  );
}

function InsightCard({ insight }: { insight: AiInsight }) {
  const config = typeConfig[insight.type];

  return (
    <div
      className={cn(
        "rounded-lg border bg-surface-800/80 p-4 transition hover:bg-surface-800",
        config.border
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-md",
            config.bg,
            config.text
          )}
        >
          {config.icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium text-white">{insight.title}</p>
            {severityIcon[insight.severity]}
          </div>
          <p className="mt-1 text-sm leading-relaxed text-surface-400">
            {insight.description}
          </p>
          <div className="mt-2 flex items-center gap-2 text-xs text-surface-500">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
                config.bg,
                config.text
              )}
            >
              {config.icon}
              {config.label}
            </span>
            {insight.category && (
              <>
                <span>&middot;</span>
                <span>{insight.category}</span>
              </>
            )}
            <span>&middot;</span>
            <span>{formatRelativeTime(insight.timestamp)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
