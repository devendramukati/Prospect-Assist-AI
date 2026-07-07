import { getBackendHealth } from "@/lib/api-client";

export default async function HomePage() {
  const backendHealth = await getBackendHealth();

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-3xl font-semibold">Prospect-Assist-AI</h1>
      <p className="text-[var(--viz-text-secondary)]">
        Behavioural analytics for retail lending lead qualification &mdash; see the{" "}
        <a href="/dashboard" className="underline">
          dashboard
        </a>
        .
      </p>
      <div className="grid w-full grid-cols-2 gap-4">
        <div className="rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4 shadow-sm">
          <p className="text-sm text-[var(--viz-text-muted)]">Frontend</p>
          <p className="mt-1 font-medium text-[var(--viz-status-good)]">ok</p>
        </div>
        <div className="rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-4 shadow-sm">
          <p className="text-sm text-[var(--viz-text-muted)]">Scoring service</p>
          <p
            className="mt-1 font-medium"
            style={{ color: backendHealth ? "var(--viz-status-good)" : "var(--viz-status-critical)" }}
          >
            {backendHealth ? backendHealth.status : "unreachable"}
          </p>
        </div>
      </div>
    </main>
  );
}
