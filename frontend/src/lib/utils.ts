import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function statusColor(status: string): string {
  const colors: Record<string, string> = {
    passed: "text-green-400",
    failed: "text-red-400",
    running: "text-blue-400",
    pending: "text-yellow-400",
    error: "text-red-500",
    cancelled: "text-surface-400",
    idle: "text-surface-400",
  };
  return colors[status] || "text-surface-400";
}
