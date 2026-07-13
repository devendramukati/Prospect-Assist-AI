import type { Metadata } from "next";

import { AppHeader } from "@/components/AppHeader";

import "./globals.css";

export const metadata: Metadata = {
  title: "Prospect-Assist-AI",
  description: "Behavioural analytics for retail lending lead qualification",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[var(--viz-page-plane)] text-[var(--viz-text-primary)]">
        <AppHeader />
        {children}
      </body>
    </html>
  );
}
