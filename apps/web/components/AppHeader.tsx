"use client";

import { Landmark } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/leads", label: "Leads" },
];

// Chrome-only banking tone (navy + gold) — deliberately separate from the
// validated dataviz chart palette in globals.css, which stays untouched.
const NAVY = "#0B1F3A";
const GOLD = "#C8952C";

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header style={{ backgroundColor: NAVY }}>
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="flex items-center gap-3">
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-white"
              style={{ backgroundColor: GOLD }}
              aria-hidden
            >
              <Landmark className="h-5 w-5" strokeWidth={2.25} />
            </span>
            <div className="leading-tight">
              <p className="text-sm font-semibold text-white">Prospect-Assist-AI</p>
              <p className="text-[11px]" style={{ color: "#B8C4D9" }}>
                Retail Lending Intelligence
              </p>
            </div>
          </Link>

          <span
            className="hidden items-center gap-2 whitespace-nowrap rounded-full border px-3.5 py-1.5 text-[11px] font-medium leading-none sm:flex"
            style={{ borderColor: "rgba(200,149,44,0.5)", color: GOLD }}
          >
            <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: GOLD }} />
            IDBI Innovate 2026 &middot; Track 02
          </span>
        </div>

        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className="rounded px-3 py-1.5 text-sm font-medium transition-colors"
                style={{
                  color: isActive ? NAVY : "#E2E8F0",
                  backgroundColor: isActive ? GOLD : "transparent",
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
