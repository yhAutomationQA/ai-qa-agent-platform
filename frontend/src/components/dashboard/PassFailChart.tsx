"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { DashboardSummary } from "@/lib/dashboard-types";

interface PassFailChartProps {
  summary: DashboardSummary;
}

const COLORS = {
  passed: "#22c55e",
  failed: "#ef4444",
  skipped: "#eab308",
  errored: "#f97316",
};

export function PassFailChart({ summary }: PassFailChartProps) {
  const data = [
    { name: "Passed", value: summary.passed, color: COLORS.passed },
    { name: "Failed", value: summary.failed, color: COLORS.failed },
    { name: "Skipped", value: summary.skipped, color: COLORS.skipped },
    { name: "Errored", value: summary.errored, color: COLORS.errored },
  ].filter((d) => d.value > 0);

  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-surface-400">
        No test data available
      </div>
    );
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "8px",
              color: "#f1f5f9",
              fontSize: "13px",
            }}
            formatter={(value: number, name: string) => [
              `${value} (${((value / total) * 100).toFixed(1)}%)`,
              name,
            ]}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value: string) => (
              <span className="text-sm text-surface-300">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
