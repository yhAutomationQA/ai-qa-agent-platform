export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-surface-900 p-8 text-white">
      <h1 className="mb-8 text-3xl font-bold">Dashboard</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Test Cases" value="0" />
        <StatCard label="Active Agents" value="0" />
        <StatCard label="Runs Today" value="0" />
        <StatCard label="Success Rate" value="0%" />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-surface-700 bg-surface-800 p-6">
      <p className="text-sm text-surface-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
    </div>
  );
}
