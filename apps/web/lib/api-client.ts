import type { LeadExplainResponse, LeadsResponse } from "./types";

const SCORING_SERVICE_URL = process.env.SCORING_SERVICE_URL ?? "http://localhost:8000";

export async function getBackendHealth(): Promise<{ status: string; service: string } | null> {
  try {
    const response = await fetch(`${SCORING_SERVICE_URL}/health`, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function getLeads(): Promise<LeadsResponse | null> {
  try {
    const response = await fetch(`${SCORING_SERVICE_URL}/leads`, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export async function getLeadExplain(externalRef: string): Promise<LeadExplainResponse | null> {
  try {
    const response = await fetch(`${SCORING_SERVICE_URL}/leads/${encodeURIComponent(externalRef)}/explain`, {
      cache: "no-store",
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export function getUnderwritingReportUrl(externalRef: string): string {
  return `${SCORING_SERVICE_URL}/leads/${encodeURIComponent(externalRef)}/underwriting-report`;
}
