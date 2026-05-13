import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-surface-900 text-white">
      <div className="mx-auto max-w-7xl px-4 py-16">
        <header className="mb-16 text-center">
          <h1 className="mb-4 text-5xl font-bold">AI QA Agent Platform</h1>
          <p className="text-xl text-surface-400">
            Enterprise-grade AI-powered testing and quality assurance
          </p>
        </header>

        <div className="grid gap-8 md:grid-cols-3">
          <Card
            title="Test Cases"
            description="Create and manage AI-powered test cases"
            href="/dashboard/tests"
          />
          <Card
            title="Agents"
            description="Configure and monitor QA agents"
            href="/dashboard/agents"
          />
          <Card
            title="Test Runs"
            description="Execute and analyze test runs"
            href="/dashboard/runs"
          />
        </div>

        <div className="mt-12 flex justify-center gap-4">
          <Link
            href="/dashboard"
            className="rounded-lg bg-primary-600 px-6 py-3 font-medium hover:bg-primary-700"
          >
            Go to Dashboard
          </Link>
          <a
            href="/docs"
            className="rounded-lg border border-surface-600 px-6 py-3 font-medium hover:bg-surface-800"
          >
            Documentation
          </a>
        </div>
      </div>
    </main>
  );
}

function Card({
  title,
  description,
  href,
}: {
  title: string;
  description: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="group rounded-xl border border-surface-700 bg-surface-800 p-6 transition hover:border-primary-500 hover:shadow-lg"
    >
      <h2 className="mb-2 text-xl font-semibold group-hover:text-primary-400">
        {title}
      </h2>
      <p className="text-surface-400">{description}</p>
    </Link>
  );
}
