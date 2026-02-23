import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { R } from "@/tokens/brand";
import type { LineChartData } from "@/types";

interface Props {
  data: LineChartData;
}

export const LineChartWidget: React.FC<Props> = ({ data }) => {
  const points = Array.isArray(data?.points) ? data.points : [];
  const keys = Array.isArray(data?.keys) ? data.keys : [];
  const colors = Array.isArray(data?.colors) ? data.colors : [];

  if (keys.length === 0 || points.length === 0) {
    return (
      <p style={{ color: "#9CA3AF", fontSize: 13, fontFamily: "'Barlow', sans-serif" }}>
        No chart data available.
      </p>
    );
  }

  // Detect x-axis key — first non-numeric string field
  const firstRow = points[0] as Record<string, unknown>;
  const xKey = Object.keys(firstRow).find(
    (k) => !keys.includes(k) && typeof firstRow[k] === "string"
  ) ?? "x";

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={points} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={R.borderLight} vertical={false} />
        <XAxis
          dataKey={xKey}
          tick={{ fontSize: 11, fill: R.textMuted, fontFamily: "'Barlow', sans-serif" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: R.textMuted, fontFamily: "'Barlow', sans-serif" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 3,
            border: `1px solid ${R.border}`,
            fontSize: 12,
            fontFamily: "'Barlow', sans-serif",
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12, fontFamily: "'Barlow', sans-serif" }} />
        {keys.map((key, i) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={colors[i] ?? R.red}
            strokeWidth={2.5}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};