"use client";

import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

interface ConversionComparisonChartProps {
  baselinePct: number;
  targetedPct: number;
}

export function ConversionComparisonChart({ baselinePct, targetedPct }: ConversionComparisonChartProps) {
  const data = [
    { label: "All leads (baseline)", pct: Math.round(baselinePct * 1000) / 10 },
    { label: "Serious + Quality (targeted)", pct: Math.round(targetedPct * 1000) / 10 },
  ];

  return (
    <ResponsiveContainer width="100%" height={140}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 48, bottom: 8, left: 8 }}>
        <XAxis type="number" hide domain={[0, 100]} />
        <YAxis
          type="category"
          dataKey="label"
          width={190}
          tickLine={false}
          axisLine={false}
          tick={{ fill: "var(--viz-text-secondary)", fontSize: 13 }}
        />
        <Bar dataKey="pct" radius={[0, 4, 4, 0]} maxBarSize={24} isAnimationActive={false}>
          <Cell fill="var(--viz-baseline)" />
          <Cell fill="var(--viz-series-1)" />
          <LabelList
            dataKey="pct"
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
