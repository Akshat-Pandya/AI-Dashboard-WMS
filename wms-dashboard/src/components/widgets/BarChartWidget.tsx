import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  type TooltipProps,
} from "recharts";
import { R } from "@/tokens/brand";
import type { BarChartData } from "@/types";

interface Props {
  data: BarChartData;
}

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: R.white,
        border: `1px solid ${R.border}`,
        borderRadius: 3,
        padding: "10px 14px",
        boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
        fontFamily: "'Barlow', sans-serif",
      }}
    >
      <p
        style={{
          fontSize: 10,
          fontWeight: 700,
          color: R.textSecondary,
          marginBottom: 6,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        {label}
      </p>
      {payload.map((p, i) => (
        <p key={i} style={{ fontSize: 13, fontWeight: 600, marginBottom: 2 }}>
          <span style={{ color: p.fill }}>{p.name}</span>
          <span style={{ color: R.textPrimary }}>
            {": "}
            {(p.value ?? 0).toLocaleString()}
          </span>
        </p>
      ))}
    </div>
  );
};

export const BarChartWidget: React.FC<Props> = ({ data }) => (
  <ResponsiveContainer width="100%" height={220}>
    <BarChart
      data={data.bars}
      margin={{ top: 8, right: 8, left: -10, bottom: 0 }}
      barGap={6}
    >
      <CartesianGrid strokeDasharray="3 3" stroke={R.borderLight} vertical={false} />
      <XAxis
        dataKey="zone"
        tick={{
          fontSize: 12,
          fill: R.textSecondary,
          fontFamily: "'Barlow', sans-serif",
          fontWeight: 600,
        }}
        axisLine={false}
        tickLine={false}
      />
      <YAxis
        tick={{ fontSize: 11, fill: R.textMuted, fontFamily: "'Barlow', sans-serif" }}
        axisLine={false}
        tickLine={false}
      />
      <Tooltip content={<CustomTooltip />} cursor={{ fill: R.bg }} />
      <Legend
        wrapperStyle={{
          fontSize: 12,
          fontFamily: "'Barlow', sans-serif",
          paddingTop: 12,
          fontWeight: 600,
        }}
      />
      {data.keys.map((key, i) => (
        <Bar
          key={key}
          dataKey={key}
          fill={data.colors[i]}
          radius={[3, 3, 0, 0]}
          maxBarSize={64}
        />
      ))}
    </BarChart>
  </ResponsiveContainer>
);
