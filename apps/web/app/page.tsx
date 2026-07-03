import { getBackendHealth } from "@/lib/api-client";

export default async function HomePage() {
  const backendHealth = await getBackendHealth();

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-3xl font-semibold">Prospect-Assist-AI</h1>
      <p className="text-slate-600">
        Behavioural analytics for retail lending lead qualification &mdash; deployment skeleton.
      </p>
      <div className="grid w-full grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Frontend</p>
          <p className="mt-1 font-medium text-emerald-600">ok</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Scoring service</p>
          <p className={`mt-1 font-medium ${backendHealth ? "text-emerald-600" : "text-red-600"}`}>
            {backendHealth ? backendHealth.status : "unreachable"}
          </p>
        </div>
      </div>
    </main>
  );
}
