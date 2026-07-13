"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import type { ConsentRequest, FIPInfo } from "@/lib/types";

const SCORING_SERVICE_URL = process.env.NEXT_PUBLIC_SCORING_SERVICE_URL ?? "http://localhost:8000";

type Step = "select-bank" | "pending" | "approved" | "fetched";

export function LinkAccountModal({ externalRef }: { externalRef: string }) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [fips, setFips] = useState<FIPInfo[]>([]);
  const [selectedFipId, setSelectedFipId] = useState<string>("");
  const [consent, setConsent] = useState<ConsentRequest | null>(null);
  const [fetchedAccountLabel, setFetchedAccountLabel] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || fips.length > 0) return;
    fetch(`${SCORING_SERVICE_URL}/consents/fips`)
      .then((response) => response.json())
      .then((data: { fips: FIPInfo[] }) => {
        setFips(data.fips);
        setSelectedFipId(data.fips[0]?.fip_id ?? "");
      })
      .catch(() => setError("Could not reach the scoring service."));
  }, [isOpen, fips.length]);

  const step: Step = !consent
    ? "select-bank"
    : consent.status === "pending"
      ? "pending"
      : fetchedAccountLabel
        ? "fetched"
        : "approved";

  async function handleRequestConsent() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${SCORING_SERVICE_URL}/consents/${encodeURIComponent(externalRef)}/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fip_id: selectedFipId }),
      });
      if (!response.ok) throw new Error("request failed");
      setConsent(await response.json());
    } catch {
      setError("Could not create the consent request.");
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove() {
    if (!consent) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${SCORING_SERVICE_URL}/consents/${consent.id}/approve`, { method: "POST" });
      if (!response.ok) throw new Error("approve failed");
      setConsent(await response.json());
    } catch {
      setError("Could not approve the consent.");
    } finally {
      setLoading(false);
    }
  }

  async function handleFetch() {
    if (!consent) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${SCORING_SERVICE_URL}/consents/${consent.id}/fetch`, { method: "POST" });
      if (!response.ok) throw new Error("fetch failed");
      const data = await response.json();
      setFetchedAccountLabel(`${data.account.bank_name} (${data.account.masked_account_number})`);
    } catch {
      setError("Could not fetch account data.");
    } finally {
      setLoading(false);
    }
  }

  function handleClose() {
    const wasFetched = step === "fetched";
    setIsOpen(false);
    setConsent(null);
    setFetchedAccountLabel(null);
    setError(null);
    if (wasFetched) router.refresh();
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="text-sm underline text-[var(--viz-text-secondary)]"
      >
        Link another bank account via Account Aggregator
      </button>

      {isOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-md rounded-lg border border-[var(--viz-border)] bg-[var(--viz-surface-1)] p-6">
            <h2 className="text-lg font-semibold">Link another bank account</h2>
            <p className="mt-1 text-xs text-[var(--viz-text-muted)]">
              Simulates the RBI Account Aggregator consent flow via {consent?.aa_handle ?? "customer@finvu"} — the
              regulated way a bank cross-checks a customer&apos;s other accounts, instead of asking for a manual PDF.
            </p>

            {error ? (
              <p className="mt-3 text-sm" style={{ color: "var(--viz-status-critical)" }}>
                {error}
              </p>
            ) : null}

            {step === "select-bank" ? (
              <div className="mt-4 space-y-3">
                <label className="block text-sm text-[var(--viz-text-secondary)]">
                  Bank to pull statement from
                  <select
                    value={selectedFipId}
                    onChange={(event) => setSelectedFipId(event.target.value)}
                    className="mt-1 w-full rounded border border-[var(--viz-border)] bg-transparent p-2 text-sm text-[var(--viz-text-primary)]"
                  >
                    {fips.map((fip) => (
                      <option key={fip.fip_id} value={fip.fip_id} style={{ color: "#111827", backgroundColor: "#FFFFFF" }}>
                        {fip.name}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  type="button"
                  disabled={loading || !selectedFipId}
                  onClick={handleRequestConsent}
                  className="w-full rounded py-2 text-sm font-medium text-white disabled:opacity-50"
                  style={{ backgroundColor: "var(--viz-series-1)" }}
                >
                  {loading ? "Requesting..." : "Request consent"}
                </button>
              </div>
            ) : null}

            {step === "pending" && consent ? (
              <div className="mt-4 space-y-3 text-sm">
                <p>
                  Consent requested from <span className="font-medium">{consent.fip_name}</span> for{" "}
                  {consent.data_range_from} &ndash; {consent.data_range_to}.
                </p>
                <p className="text-xs text-[var(--viz-text-muted)]">
                  Purpose: {consent.purpose}. Expires {new Date(consent.expires_at).toLocaleDateString()}.
                </p>
                <p className="text-xs text-[var(--viz-text-muted)]">
                  Waiting for the customer to approve in their AA app...
                </p>
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleApprove}
                  className="w-full rounded py-2 text-sm font-medium text-white disabled:opacity-50"
                  style={{ backgroundColor: "var(--viz-series-1)" }}
                >
                  {loading ? "Approving..." : "Simulate customer approval"}
                </button>
              </div>
            ) : null}

            {step === "approved" && consent ? (
              <div className="mt-4 space-y-3 text-sm">
                <p style={{ color: "var(--viz-status-good)" }}>Consent approved.</p>
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleFetch}
                  className="w-full rounded py-2 text-sm font-medium text-white disabled:opacity-50"
                  style={{ backgroundColor: "var(--viz-series-1)" }}
                >
                  {loading ? "Fetching..." : "Fetch account data"}
                </button>
              </div>
            ) : null}

            {step === "fetched" ? (
              <div className="mt-4 space-y-3 text-sm">
                <p style={{ color: "var(--viz-status-good)" }}>
                  Linked {fetchedAccountLabel}. Capacity assessment now includes this account.
                </p>
              </div>
            ) : null}

            <button
              type="button"
              onClick={handleClose}
              className="mt-4 w-full rounded border border-[var(--viz-border)] py-2 text-sm text-[var(--viz-text-secondary)]"
            >
              {step === "fetched" ? "Close and refresh" : "Cancel"}
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}
