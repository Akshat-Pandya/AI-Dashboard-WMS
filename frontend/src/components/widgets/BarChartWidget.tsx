import React from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
  type TooltipProps,
} from "recharts";
import { R } from "@/tokens/brand";

interface Props {
  data: unknown;
  props?: Record<string, unknown>;
}

const AUTO_COLORS = [
  "#E8001C", "#3B82F6", "#10B981", "#F59E0B",
  "#8B5CF6", "#EC4899", "#14B8A6", "#F97316",
];

const LABEL: Record<string, string> = {
  total_on_hand:   "On Hand",
  total_available: "Available",
  total_reserved:  "Reserved",
  low_stock_skus:  "Low Stock SKUs",
  zero_stock_skus: "Zero Stock SKUs",
  total_skus:      "Total SKUs",
  avg_available:   "Avg Available",
};

// ── Normalise any incoming shape into { bars, keys, colors } ─────────────────
function normalise(raw: unknown): {
  bars: Record<string, unknown>[];
  keys: string[];
  colors: string[];
} | null {
  if (!raw || typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;

  // Already shaped: { bars: [], keys: [], colors: [] }
  if (Array.isArray(obj.bars) && Array.isArray(obj.keys)) {
    return {
      bars:   obj.bars as Record<string, unknown>[],
      keys:   obj.keys as string[],
      colors: (obj.colors as string[]) ?? AUTO_COLORS,
    };
  }

  // compare_zones shape: { zones: [{ zone, total_on_hand, low_stock_skus, ... }] }
  if (Array.isArray(obj.zones) && (obj.zones as unknown[]).length > 0) {
    const zones = obj.zones as Record<string, unknown>[];
    const numericKeys = Object.keys(zones[0]).filter(
      (k) => k !== "zone" && typeof zones[0][k] === "number"
    );
    const bars = zones.map((z) => ({
      zone: z.zone,
      ...Object.fromEntries(numericKeys.map((k) => [LABEL[k] ?? k, z[k]])),
    }));
    const keys   = numericKeys.map((k) => LABEL[k] ?? k);
    const colors = AUTO_COLORS.slice(0, keys.length);
    return { bars, keys, colors };
  }

  return null;
}

// ── Tooltip ───────────────────────────────────────────────────────────────────
const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: R.white, border: `1px solid ${R.border}`, borderRadius: 3,
      padding: "10px 14px", boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
      fontFamily: "'Barlow', sans-serif",
    }}>
      <p style={{ fontSize: 10, fontWeight: 700, color: R.textSecondary, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </p>
      {payload.map((p, i) => (
        <p key={i} style={{ fontSize: 13, fontWeight: 600, marginBottom: 2 }}>
          <span style={{ color: p.fill }}>{p.name}</span>
          <span style={{ color: R.textPrimary }}>{": "}{(p.value ?? 0).toLocaleString()}</span>
        </p>
      ))}
    </div>
  );
};

// ── Component ─────────────────────────────────────────────────────────────────
export const BarChartWidget: React.FC<Props> = ({ data }) => {
  const shaped = normalise(data);

  if (!shaped || shaped.bars.length === 0) {
    return (
      <p style={{ color: R.textMuted, fontSize: 13, fontFamily: "'Barlow', sans-serif" }}>
        No chart data available.
      </p>
    );
  }

  const { bars, keys, colors } = shaped;

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={bars} margin={{ top: 8, right: 8, left: -10, bottom: 0 }} barGap={6}>
        <CartesianGrid strokeDasharray="3 3" stroke={R.borderLight} vertical={false} />
        <XAxis
          dataKey="zone"
          tick={{ fontSize: 12, fill: R.textSecondary, fontFamily: "'Barlow', sans-serif", fontWeight: 600 }}
          axisLine={false} tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: R.textMuted, fontFamily: "'Barlow', sans-serif" }}
          axisLine={false} tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: R.bg }} />
        <Legend wrapperStyle={{ fontSize: 12, fontFamily: "'Barlow', sans-serif", paddingTop: 12, fontWeight: 600 }} />
        {keys.map((key, i) => (
          <Bar
            key={key}
            dataKey={key}
            fill={colors[i] ?? AUTO_COLORS[i % AUTO_COLORS.length]}
            radius={[3, 3, 0, 0]}
            maxBarSize={64}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};