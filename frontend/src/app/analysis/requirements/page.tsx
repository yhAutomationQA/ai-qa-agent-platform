"use client";

import { useState } from "react";
import apiClient from "@/lib/api";

type InputMode = "jira" | "manual";

interface JiraInputs {
  url: string;
  email: string;
  token: string;
  issueKey: string;
}

interface ManualInputs {
  summary: string;
  description: string;
  acceptanceCriteria: string;
}

interface Scenario {
  title: string;
  steps?: string[];
  expected_result?: string;
  priority?: string;
}

interface EdgeCase {
  title: string;
  description?: string;
  category?: string;
  severity?: string;
}

interface NegativeScenario {
  title: string;
  description?: string;
  attack_vector?: string;
}

interface RiskArea {
  area: string;
  description?: string;
  likelihood?: string;
  impact?: string;
  mitigation?: string;
}

interface MissingRequirement {
  title: string;
  description?: string;
  priority?: string;
}

interface Summary {
  overall_purpose?: string;
  complexity?: string;
  key_functionality?: string[];
}

interface AnalysisOutput {
  summary: Summary;
  functional_scenarios: Scenario[];
  edge_cases: EdgeCase[];
  negative_scenarios: NegativeScenario[];
  risk_areas: RiskArea[];
  missing_requirements: MissingRequirement[];
  metadata: {
    model_used?: string;
    total_tokens?: number;
    processing_time_ms?: number;
    source_issue_key?: string;
  };
}

const defaultJira: JiraInputs = {
  url: "",
  email: "",
  token: "",
  issueKey: "",
};
const defaultManual: ManualInputs = {
  summary: "",
  description: "",
  acceptanceCriteria: "",
};

export default function RequirementAnalysisPage() {
  const [mode, setMode] = useState<InputMode>("manual");
  const [jira, setJira] = useState<JiraInputs>(defaultJira);
  const [manual, setManual] = useState<ManualInputs>(defaultManual);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisOutput | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      if (mode === "jira") {
        const { data } = await apiClient.get(
          `/analysis/requirements/${jira.issueKey}`,
          {
            headers: {
              "X-Jira-Url": jira.url,
              "X-Jira-Email": jira.email,
              "X-Jira-Token": jira.token,
            },
          }
        );
        setResult(data);
      } else {
        const params: Record<string, string> = { summary: manual.summary };
        if (manual.description) params.description = manual.description;
        if (manual.acceptanceCriteria)
          params.acceptance_criteria = manual.acceptanceCriteria;
        const { data } = await apiClient.post(
          "/analysis/requirements/from-text",
          null,
          { params }
        );
        setResult(data);
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || err.message || "Analysis failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const updateJira = (field: keyof JiraInputs, value: string) =>
    setJira((prev) => ({ ...prev, [field]: value }));

  const updateManual = (field: keyof ManualInputs, value: string) =>
    setManual((prev) => ({ ...prev, [field]: value }));

  const canSubmit =
    mode === "jira"
      ? jira.url && jira.email && jira.token && jira.issueKey
      : manual.summary.trim().length > 0;

  return (
    <div className="min-h-screen bg-surface-900 p-8 text-white">
      <h1 className="mb-6 text-3xl font-bold">Requirement Analysis</h1>

      <ModeToggle mode={mode} onChange={setMode} />

      <div className="mb-8 rounded-xl border border-surface-700 bg-surface-800 p-6">
        {mode === "jira" ? (
          <JiraForm inputs={jira} onChange={updateJira} />
        ) : (
          <ManualForm inputs={manual} onChange={updateManual} />
        )}

        <button
          onClick={handleAnalyze}
          disabled={!canSubmit || loading}
          className="mt-6 rounded-lg bg-primary-600 px-6 py-2.5 font-semibold text-white transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze Requirements"}
        </button>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-700 bg-red-900/50 p-4 text-red-300">
          {error}
        </div>
      )}

      {result && <AnalysisResults data={result} />}
    </div>
  );
}

function ModeToggle({
  mode,
  onChange,
}: {
  mode: InputMode;
  onChange: (m: InputMode) => void;
}) {
  return (
    <div className="mb-6 flex gap-2">
      <button
        onClick={() => onChange("manual")}
        className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
          mode === "manual"
            ? "bg-primary-600 text-white"
            : "bg-surface-700 text-surface-300 hover:bg-surface-600"
        }`}
      >
        Manual Text
      </button>
      <button
        onClick={() => onChange("jira")}
        className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
          mode === "jira"
            ? "bg-primary-600 text-white"
            : "bg-surface-700 text-surface-300 hover:bg-surface-600"
        }`}
      >
        Jira Issue
      </button>
    </div>
  );
}

function JiraForm({
  inputs,
  onChange,
}: {
  inputs: JiraInputs;
  onChange: (f: keyof JiraInputs, v: string) => void;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <InputField
        label="Jira URL"
        value={inputs.url}
        placeholder="https://your-domain.atlassian.net"
        onChange={(v) => onChange("url", v)}
      />
      <InputField
        label="Email"
        value={inputs.email}
        placeholder="user@example.com"
        onChange={(v) => onChange("email", v)}
      />
      <InputField
        label="API Token"
        value={inputs.token}
        placeholder="your-api-token"
        type="password"
        onChange={(v) => onChange("token", v)}
      />
      <InputField
        label="Issue Key"
        value={inputs.issueKey}
        placeholder="PROJ-123"
        onChange={(v) => onChange("issueKey", v)}
      />
    </div>
  );
}

function ManualForm({
  inputs,
  onChange,
}: {
  inputs: ManualInputs;
  onChange: (f: keyof ManualInputs, v: string) => void;
}) {
  return (
    <div className="grid gap-4">
      <InputField
        label="Summary *"
        value={inputs.summary}
        placeholder="Requirement summary"
        onChange={(v) => onChange("summary", v)}
      />
      <div>
        <label className="mb-1 block text-sm text-surface-400">
          Description
        </label>
        <textarea
          value={inputs.description}
          placeholder="Requirement description..."
          rows={3}
          onChange={(e) => onChange("description", e.target.value)}
          className="w-full rounded-lg border border-surface-600 bg-surface-700 px-3 py-2 text-white placeholder-surface-500 focus:border-primary-500 focus:outline-none"
        />
      </div>
      <InputField
        label="Acceptance Criteria"
        value={inputs.acceptanceCriteria}
        placeholder="Comma-separated criteria"
        onChange={(v) => onChange("acceptanceCriteria", v)}
      />
    </div>
  );
}

function InputField({
  label,
  value,
  placeholder,
  type,
  onChange,
}: {
  label: string;
  value: string;
  placeholder?: string;
  type?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm text-surface-400">{label}</label>
      <input
        type={type || "text"}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-surface-600 bg-surface-700 px-3 py-2 text-white placeholder-surface-500 focus:border-primary-500 focus:outline-none"
      />
    </div>
  );
}

function AnalysisResults({ data }: { data: AnalysisOutput }) {
  return (
    <div className="space-y-6">
      <SummarySection summary={data.summary} metadata={data.metadata} />
      <ScenarioSection
        title="Functional Scenarios"
        items={data.functional_scenarios}
        empty="No functional scenarios identified"
      />
      <ScenarioSection
        title="Edge Cases"
        items={data.edge_cases}
        empty="No edge cases identified"
        variant="edge"
      />
      <ScenarioSection
        title="Negative Scenarios"
        items={data.negative_scenarios}
        empty="No negative scenarios identified"
        variant="negative"
      />
      <RiskSection items={data.risk_areas} />
      <GapSection items={data.missing_requirements} />
    </div>
  );
}

function SummarySection({
  summary,
  metadata,
}: {
  summary: Summary;
  metadata: AnalysisOutput["metadata"];
}) {
  return (
    <div className="rounded-xl border border-surface-700 bg-surface-800 p-6">
      <h2 className="mb-4 text-xl font-bold">Summary</h2>
      <div className="grid gap-4 md:grid-cols-3">
        {summary.overall_purpose && (
          <div className="md:col-span-3">
            <span className="text-sm text-surface-400">Purpose</span>
            <p className="mt-1">{summary.overall_purpose}</p>
          </div>
        )}
        <div>
          <span className="text-sm text-surface-400">Complexity</span>
          <Badge
            variant={
              summary.complexity === "high"
                ? "error"
                : summary.complexity === "low"
                  ? "success"
                  : "warning"
            }
          >
            {summary.complexity || "N/A"}
          </Badge>
        </div>
        <div>
          <span className="text-sm text-surface-400">Key Functionality</span>
          <ul className="mt-1 list-inside list-disc text-sm text-surface-200">
            {(summary.key_functionality || []).map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
        <div>
          <span className="text-sm text-surface-400">Metadata</span>
          <p className="mt-1 text-xs text-surface-300">
            {metadata.model_used && <>Model: {metadata.model_used}<br /></>}
            {metadata.total_tokens != null && <>Tokens: {metadata.total_tokens}<br /></>}
            {metadata.processing_time_ms != null && (
              <>Time: {(metadata.processing_time_ms / 1000).toFixed(1)}s<br /></>
            )}
            {metadata.source_issue_key && <>Source: {metadata.source_issue_key}</>}
          </p>
        </div>
      </div>
    </div>
  );
}

function ScenarioSection({
  title,
  items,
  empty,
  variant = "default",
}: {
  title: string;
  items: (Scenario | EdgeCase | NegativeScenario)[];
  empty: string;
  variant?: "default" | "edge" | "negative";
}) {
  const borderColor =
    variant === "edge"
      ? "border-yellow-700"
      : variant === "negative"
        ? "border-red-700"
        : "border-primary-700";

  return (
    <div
      className={`rounded-xl border bg-surface-800 p-6 ${borderColor}`}
    >
      <h2 className="mb-4 text-xl font-bold">{title}</h2>
      {items.length === 0 ? (
        <p className="text-surface-400">{empty}</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {items.map((item, i) => (
            <ScenarioCard key={i} item={item} variant={variant} />
          ))}
        </div>
      )}
    </div>
  );
}

function ScenarioCard({
  item,
  variant,
}: {
  item: Scenario | EdgeCase | NegativeScenario;
  variant: string;
}) {
  const s = item as Scenario;
  const e = item as EdgeCase;
  const n = item as NegativeScenario;

  const priorityColor =
    s.priority === "high"
      ? "error"
      : s.priority === "low"
        ? "success"
        : "warning";

  const severityColor =
    e.severity === "high"
      ? "error"
      : e.severity === "low"
        ? "success"
        : "warning";

  return (
    <div className="rounded-lg border border-surface-700 bg-surface-900 p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="font-semibold">{item.title}</h3>
        {s.priority && <Badge variant={priorityColor}>{s.priority}</Badge>}
        {e.severity && <Badge variant={severityColor}>{e.severity}</Badge>}
        {e.category && (
          <Badge variant="default">{e.category}</Badge>
        )}
        {n.attack_vector && (
          <Badge variant="default">{n.attack_vector}</Badge>
        )}
      </div>
      {s.steps && s.steps.length > 0 && (
        <ol className="mb-1 list-inside list-decimal text-sm text-surface-300">
          {s.steps.map((step, j) => <li key={j}>{step}</li>)}
        </ol>
      )}
      {s.expected_result && (
        <p className="mt-1 text-xs text-surface-400">
          Expected: {s.expected_result}
        </p>
      )}
      {(e.description || n.description) && (
        <p className="mt-1 text-xs text-surface-400">
          {e.description || n.description}
        </p>
      )}
    </div>
  );
}

function RiskSection({ items }: { items: RiskArea[] }) {
  if (items.length === 0) return null;
  return (
    <div className="rounded-xl border border-orange-700 bg-surface-800 p-6">
      <h2 className="mb-4 text-xl font-bold">Risk Areas</h2>
      <div className="grid gap-3">
        {items.map((r, i) => (
          <div
            key={i}
            className="rounded-lg border border-surface-700 bg-surface-900 p-4"
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h3 className="font-semibold">{r.area}</h3>
              {r.likelihood && <Badge variant="warning">{r.likelihood}</Badge>}
              {r.impact && <Badge variant="error">{r.impact}</Badge>}
            </div>
            {r.description && (
              <p className="mb-1 text-sm text-surface-300">
                {r.description}
              </p>
            )}
            {r.mitigation && (
              <p className="text-xs text-primary-400">
                Mitigation: {r.mitigation}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function GapSection({ items }: { items: MissingRequirement[] }) {
  if (items.length === 0) return null;
  return (
    <div className="rounded-xl border border-red-700 bg-surface-800 p-6">
      <h2 className="mb-4 text-xl font-bold">Missing Requirements</h2>
      <div className="grid gap-3">
        {items.map((m, i) => (
          <div
            key={i}
            className="rounded-lg border border-surface-700 bg-surface-900 p-4"
          >
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-red-300">{m.title}</h3>
              {m.priority && <Badge variant="error">{m.priority}</Badge>}
            </div>
            {m.description && (
              <p className="text-sm text-surface-300">{m.description}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function Badge({
  variant,
  children,
}: {
  variant: "success" | "warning" | "error" | "default";
  children: string;
}) {
  const colors: Record<string, string> = {
    success: "bg-green-900 text-green-300",
    warning: "bg-yellow-900 text-yellow-300",
    error: "bg-red-900 text-red-300",
    default: "bg-surface-700 text-surface-300",
  };
  return (
    <span
      className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${colors[variant]}`}
    >
      {children}
    </span>
  );
}
