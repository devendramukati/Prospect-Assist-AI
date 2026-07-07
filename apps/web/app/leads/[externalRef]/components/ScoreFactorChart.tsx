"use client";

import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

import type { ScoreFactor } from "@/lib/types";

const FACTOR_COLORS: Record<string, string> = {
  intent: "var(--viz-series-1)",
  capacity: "var(--viz-series-2)",
  discipline: "var(--viz-series-3)",
};

const FACTOR_LABELS: Record<string, string> = {
  intent: "Intent",
  capacity: "Capacity",
  discipline: "Discipline",
};

export function ScoreFactorChart({ factors }: { factors: ScoreFactor[] }) {
  const data = factors.map((factor) => ({ ...factor, label: FACTOR_LABELS[factor.factor] ?? factor.factor }));

  return (
    <div>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 40, bottom: 8, left: 8 }}>
          <XAxis type="number" hide domain={[0, 1]} />
          <YAxis
            type="category"
            dataKey="label"
            width={90}
            tickLine={false}
            axisLine={false}
            tick={{ fill: "var(--viz-text-secondary)", fontSize: 13 }}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={24} isAnimationActive={false}>
            {data.map((entry) => (
              <Cell key={entry.factor} fill={FACTOR_COLORS[entry.factor]} />
            ))}
            <LabelList
              dataKey="score"
              position="right"
              formatter={(value: number) => value.toFixed(2)}
              fill="var(--viz-text-primary)"
              fontSize={13}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-[var(--viz-text-secondary)]">
        {data.map((entry) => (
          <span key={entry.factor} className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: FACTOR_COLORS[entry.factor] }} aria-hidden />
            {entry.label} (weight {(entry.weight * 100).toFixed(0)}%)
          </span>
        ))}
      </div>
    </div>
  );
}
