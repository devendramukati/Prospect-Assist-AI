"use client";

import { Bar, BarChart, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

import type { Tier } from "@/lib/types";

const TIER_ORDER: Tier[] = ["Serious", "Quality", "Interested", "Not Qualified"];

interface DisciplineFlagRateChartProps {
  data: { tier: Tier; ratePct: number }[];
}

export function DisciplineFlagRateChart({ data }: DisciplineFlagRateChartProps) {
  const ordered = TIER_ORDER.map((tier) => data.find((d) => d.tier === tier) ?? { tier, ratePct: 0 });

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={ordered} layout="vertical" margin={{ top: 8, right: 40, bottom: 8, left: 8 }}>
        <XAxis type="number" hide domain={[0, 100]} />
        <YAxis
          type="category"
          dataKey="tier"
          width={110}
          tickLine={false}
          axisLine={false}
          tick={{ fill: "var(--viz-text-secondary)", fontSize: 13 }}
        />
        <Bar
          dataKey="ratePct"
          fill="var(--viz-status-warning)"
          radius={[0, 4, 4, 0]}
          maxBarSize={24}
          isAnimationActive={false}
        >
          <LabelList
            dataKey="ratePct"
            position="right"
            formatter={(value: number) => `${value}%`}
            fill="var(--viz-text-primary)"
            fontSize={13}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
