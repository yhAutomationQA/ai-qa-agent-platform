"use client";

import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

interface DashboardLayoutProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function DashboardLayout({
  title,
  subtitle,
  actions,
  children,
  className,
}: DashboardLayoutProps) {
  return (
    <div className={cn("min-h-screen bg-surface-900", className)}>
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Header title={title} subtitle={subtitle} actions={actions} />
        {children}
      </div>
    </div>
  );
}

function Header({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">{title}</h1>
        {subtitle && (
          <p className="mt-1 text-sm text-surface-400">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}

interface DashboardCardProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  fullHeight?: boolean;
}

export function DashboardCard({
  title,
  subtitle,
  action,
  children,
  className,
  fullHeight = false,
}: DashboardCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-surface-700 bg-surface-800/50 p-5",
        fullHeight && "flex flex-col",
        className
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">{title}</h3>
          {subtitle && (
            <p className="mt-0.5 text-xs text-surface-400">{subtitle}</p>
          )}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className={cn(fullHeight && "flex-1")}>{children}</div>
    </div>
  );
}
