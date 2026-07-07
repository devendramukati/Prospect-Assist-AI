import { getLeads } from "@/lib/api-client";

import { LeadsTable } from "./components/LeadsTable";

export default async function LeadsPage() {
  const data = await getLeads();

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-2xl font-semibold">Leads</h1>
      <p className="mt-2 text-[var(--viz-text-secondary)]">
        {data ? `${data.count} scored lead${data.count === 1 ? "" : "s"}.` : "Could not reach the scoring service."}
      </p>

      {data ? <div className="mt-6"><LeadsTable leads={data.leads} /></div> : null}
    </main>
  );
}
