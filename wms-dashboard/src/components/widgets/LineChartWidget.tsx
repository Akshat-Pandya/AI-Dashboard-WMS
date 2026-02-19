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

export const LineChartWidget: React.FC<Props> = ({ data }) => (
  <ResponsiveContainer width="100%" height={220}>
    <LineChart
      data={data.points ?? []}
      margin={{ top: 8, right: 8, left: -10, bottom: 0 }}
    >
      <CartesianGrid strokeDasharray="3 3" stroke={R.borderLight} vertical={false} />
      <XAxis
        dataKey="x"
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
      <Legend
        wrapperStyle={{ fontSize: 12, fontFamily: "'Barlow', sans-serif" }}
      />
      {(data.keys ?? []).map((key, i) => (
        <Line
          key={key}
          type="monotone"
          dataKey={key}
          stroke={data.colors?.[i] ?? R.red}
          strokeWidth={2.5}
          dot={false}
        />
      ))}
    </LineChart>
  </ResponsiveContainer>
);
