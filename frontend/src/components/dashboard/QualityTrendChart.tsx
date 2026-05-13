"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { TrendPoint } from "@/lib/dashboard-types";

interface QualityTrendChartProps {
  trends: TrendPoint[];
}

export function QualityTrendChart({ trends }: QualityTrendChartProps) {
  if (trends.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center text-surface-400">
        No trend data available
      </div>
    );
  }

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={trends}
          margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
        >
          <defs>
            <linearGradient id="passedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="failedGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="passRateGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: "#334155" }}
            tickFormatter={(val: string) => {
              const d = new Date(val);
              return `${d.getMonth() + 1}/${d.getDate()}`;
            }}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: "#334155" }}
          />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "8px",
              color: "#f1f5f9",
              fontSize: "13px",
            }}
            labelFormatter={(val: string) => {
              const d = new Date(val);
              return d.toLocaleDateString("en-US", {
                weekday: "short",
                month: "short",
                day: "numeric",
              });
            }}
          />
          <Legend
            verticalAlign="top"
            height={40}
            formatter={(value: string) => (
              <span className="text-sm text-surface-300">{value}</span>
            )}
          />
          <Area
            type="monotone"
            dataKey="passed"
            stroke="#22c55e"
            fill="url(#passedGrad)"
            strokeWidth={2}
            name="Passed"
          />
          <Area
            type="monotone"
            dataKey="failed"
            stroke="#ef4444"
            fill="url(#failedGrad)"
            strokeWidth={2}
            name="Failed"
          />
          <Area
            type="monotone"
            dataKey="passRate"
            stroke="#3b82f6"
            fill="url(#passRateGrad)"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Pass Rate %"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
