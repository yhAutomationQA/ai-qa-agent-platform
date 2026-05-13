"use client";

import { cn } from "@/lib/utils";
import type { RiskItem } from "@/lib/dashboard-types";
import { AlertTriangle, ChevronRight, ShieldAlert, ShieldX } from "lucide-react";

interface RiskIndicatorsProps {
  risks: RiskItem[];
}

export function RiskIndicators({ risks }: RiskIndicatorsProps) {
  if (risks.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-surface-400">
        <ShieldAlert className="mr-2 h-4 w-4" />
        No risks detected
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {risks.map((risk, i) => (
        <RiskRow key={`${risk.testName}-${i}`} risk={risk} />
      ))}
    </div>
  );
}

function RiskRow({ risk }: { risk: RiskItem }) {
  const levelConfig = {
    critical: {
      bar: "bg-red-500",
      badge: "bg-red-500/20 text-red-400 border-red-500/30",
      icon: <ShieldX className="h-4 w-4" />,
    },
    high: {
      bar: "bg-orange-500",
      badge: "bg-orange-500/20 text-orange-400 border-orange-500/30",
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    medium: {
      bar: "bg-yellow-500",
      badge: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    low: {
      bar: "bg-surface-500",
      badge: "bg-surface-500/20 text-surface-400 border-surface-500/30",
      icon: <ShieldAlert className="h-4 w-4" />,
    },
  };

  const config = levelConfig[risk.riskLevel];

  return (
    <div className="group cursor-pointer rounded-lg border border-surface-700 bg-surface-800 p-3 transition hover:border-surface-600">
      <div className="flex items-center gap-3">
        <div className={cn("flex h-8 w-8 items-center justify-center rounded-md", config.badge)}>
          {config.icon}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-medium text-white">
              {risk.testName}
            </p>
            <span
              className={cn(
                "inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider",
                config.badge
              )}
            >
              {risk.riskLevel}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-surface-400">
            <span>{risk.category}</span>
            {risk.impactedAreas.length > 0 && (
              <>
                <span>&middot;</span>
                <span className="truncate">{risk.impactedAreas.join(", ")}</span>
              </>
            )}
          </div>
        </div>
        <div className="flex w-16 flex-col items-end gap-1">
          <span className="text-xs font-medium text-white">
            {(risk.score * 100).toFixed(0)}%
          </span>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-700">
            <div
              className={cn("h-full rounded-full transition-all", config.bar)}
              style={{ width: `${risk.score * 100}%` }}
            />
          </div>
        </div>
        <ChevronRight className="h-4 w-4 shrink-0 text-surface-500 transition group-hover:text-surface-300" />
      </div>
    </div>
  );
}
