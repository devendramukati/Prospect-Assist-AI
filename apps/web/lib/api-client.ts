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
