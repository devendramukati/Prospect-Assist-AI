"use client";

import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { TIER_COLORS } from "@/components/TierBadge";
import type { Tier } from "@/lib/types";

const TIER_ORDER: Tier[] = ["Serious", "Quality", "Interested", "Not Qualified"];

interface TierBarChartProps {
  data: { tier: Tier; count: number }[];
}

export function TierBarChart({ data }: TierBarChartProps) {
  const ordered = TIER_ORDER.map((tier) => data.find((d) => d.tier === tier) ?? { tier, count: 0 });

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={ordered} layout="vertical" margin={{ top: 8, right: 32, bottom: 8, left: 8 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="tier"
          width={110}
          tickLine={false}
          axisLine={false}
          tick={{ fill: "var(--viz-text-secondary)", fontSize: 13 }}
        />
        <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={24} isAnimationActive={false}>
          {ordered.map((entry) => (
            <Cell key={entry.tier} fill={TIER_COLORS[entry.tier]} />
          ))}
          <LabelList dataKey="count" position="right" fill="var(--viz-text-primary)" fontSize={13} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
