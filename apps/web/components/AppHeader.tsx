"use client";

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
        <Link href="/dashboard" className="flex items-center gap-2.5">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-md text-sm font-bold text-white"
            style={{ backgroundColor: GOLD }}
            aria-hidden
          >
            PA
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-white">Prospect-Assist-AI</p>
            <p className="text-[11px]" style={{ color: "#B8C4D9" }}>
              Retail Lending Intelligence
            </p>
          </div>
        </Link>

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
